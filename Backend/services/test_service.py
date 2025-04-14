import logging
import traceback
from typing import Dict, Any, Union
from datetime import datetime
from fastapi import BackgroundTasks, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase as Database
from bson import ObjectId

from models.test import TestModel, TestTypeEnum
from services.audio_processor import AudioProcessor, FastAudioProcessor
from services.evaluator import ResponseEvaluator
from services.test_generator import get_random_single_problem, generate_full_test, generate_comboset_test, generate_roleplay_test, generate_unexpected_test

from core.config import settings
from schemas.test import RandomProblemEvaluationResponse
from core.metrics import BACKGROUND_TASK_DURATION, ACTIVE_TASKS, track_time_async, ERROR_COUNTER

import asyncio

# 로깅 설정
logger = logging.getLogger(__name__)

# 두 가지 전역 인스턴스 생성
standard_audio_processor = AudioProcessor(model_name="whisper-large-v3")  # 정확성 우선
fast_audio_processor = FastAudioProcessor(model_name="whisper-large-v3")  # 속도 우선

evaluator = ResponseEvaluator()

async def get_test_by_user_id(db: Database, user_id: str):
    """
    사용자 ID로 최근 테스트 7개 조회 (성적이 있는 테스트만)
    """
    try:
        # user_id가 일치하는 테스트 중 최근 7개만 조회 (날짜 기준 내림차순)
        cursor = db.tests.find({"user_id": user_id}).sort("test_date", -1).limit(20)  # 더 많이 가져와서 필터링
        tests = await cursor.to_list(length=20)
        
        if not tests:
            return None
            
        # TestInfo 형태로 가공
        test_dates = []
        test_scores = []
        valid_tests = 0
        
        for test in tests:
            # test_score가 있고, total_score가 있는 테스트만 포함
            test_score = test.get("test_score")
            total_score = None
            
            if isinstance(test_score, dict):
                total_score = test_score.get("total_score")
            elif test_score:  # 문자열이나 다른 값이 있는 경우
                total_score = str(test_score)
                
            if total_score:  # 성적이 있는 경우에만 추가
                test_dates.append(test.get("test_date"))
                test_scores.append(total_score)
                valid_tests += 1
                
                # 7개를 모으면 중단
                if valid_tests >= 7:
                    break
        
        # 유효한 테스트가 없으면 None 반환
        if not test_dates:
            return None
                
        return {
            "test_date": test_dates,
            "test_score": test_scores
        }
        
    except Exception as e:
        print(f"테스트 조회 오류: {str(e)}")
        return None
    

async def create_test(
    db: Database, 
    test_type: int, 
    user_id: str
) -> Union[str, Dict]:
    """
    테스트 생성 서비스 함수
    - test_type 1: 15문제 (자기소개 1, 콤보셋 9, 롤플레잉 3, 돌발 2)
    - test_type 2: 랜덤 1문제
    - test_type 3: 콤보셋 3문제
    - test_type 4: 롤플레잉 3문제
    - test_type 5: 돌발 3문제
    
    Args:
        db: MongoDB 데이터베이스
        test_type: 테스트 유형
        user_id: 사용자 ID
        
    Returns:
        Union[str, Dict]: 생성된 테스트 ID (MongoDB ObjectId 문자열) 또는 랜덤 문제 정보(test_type이 2인 경우)
    """
    try:
        logger.info(f"테스트 생성 시작 - 유형: {test_type}, 사용자: {user_id}")
        
        # 사용자 정보 가져오기
        user_object_id = ObjectId(user_id)
        user = await db.users.find_one({"_id": user_object_id})
        
        if not user:
            logger.error(f"사용자 ID {user_id}에 해당하는 사용자를 찾을 수 없습니다.")
            raise ValueError(f"사용자 ID {user_id}에 해당하는 사용자를 찾을 수 없습니다.")
        
        # 사용자의 배경 정보 가져오기
        user_topics = user.get("background_survey", {}).get("info", [])
        logger.info(f"사용자 관심 주제: {user_topics}")
        
        # test_type이 2인 경우 랜덤 단일 문제 반환 (DB에 저장하지 않음)
        if test_type == 2:
            return await get_random_single_problem(db, user_id)
        
        # test_type을 열거형으로 변환
        test_type_enum = get_test_type_enum(test_type)

        # 기존 bool 값 계산
        is_half_test = test_type != 1  # 1번만 전체 테스트, 나머지는 half로 처리

        # 그 외의 경우 테스트 모델 생성 및 DB에 저장
        test_data = TestModel(
            test_type=is_half_test,  # 기존 bool 필드 설정
            test_type_str=test_type_enum,  # 새 열거형 필드 설정
            problem_data={},
            user_id=str(user_object_id),
            test_date=datetime.now()
        )
        
        # 테스트 타입에 따라 문제 생성
        if test_type == 1:
            # 15문제 테스트 생성
            await generate_full_test(db, test_data, user_topics)
        elif test_type == 3:
            # 콤보셋 3문제 테스트 생성
            await generate_comboset_test(db, test_data, user_topics)
        elif test_type == 4:
            # 롤플레잉 3문제 테스트 생성
            await generate_roleplay_test(db, test_data, user_topics)
        elif test_type == 5:
            # 돌발 3문제 테스트 생성
            await generate_unexpected_test(db, test_data, user_topics)

        # Test 모델을 MongoDB에 저장하기 위해 변환
        data_to_insert = test_data.model_dump(by_alias=True)
        
        # _id 필드가 없거나 None일 경우 제거하여 MongoDB가 자동으로 생성하도록 함
        if "_id" in data_to_insert and data_to_insert["_id"] is None:
            del data_to_insert["_id"]
        
        # MongoDB에 테스트 저장
        result = await db.tests.insert_one(data_to_insert)
        test_id = str(result.inserted_id)
        
        logger.info(f"테스트 생성 완료 - ID: {test_id}, 문제 수: {len(test_data.problem_data)}")
        return test_id
            
    except Exception as e:
        logger.error(f"테스트 생성 중 오류: {str(e)}", exc_info=True)
        raise

def get_test_type_enum(test_type: int) -> TestTypeEnum:
    """
    정수형 test_type을 TestTypeEnum으로 변환
    
    Args:
        test_type: 테스트 유형 정수 (1-5)
        
    Returns:
        TestTypeEnum: 열거형 테스트 유형
    """
    if test_type == 1:
        return TestTypeEnum.FULL_TEST
    elif test_type == 2:
        return TestTypeEnum.SINGLE_PROBLEM
    else:  # 3, 4, 5 (유형별 테스트)
        return TestTypeEnum.CATEGORICAL_TEST

async def process_audio_and_evaluate(
    db: Database,
    background_tasks: BackgroundTasks,
    test_id: str, 
    problem_id: str,
    audio_content: bytes,
    filename: str,
    is_last_problem: bool
) -> Dict[str, Any]:
    """
    오디오 파일을 처리하고 평가를 수행하는 함수
    
    Args:
        db: MongoDB 데이터베이스
        background_tasks: FastAPI의 BackgroundTasks
        test_id: 테스트 ID
        problem_id: 문제 ID
        audio_content: 오디오 파일 바이트 데이터
        filename: 오디오 파일 이름
        is_last_problem: 마지막 문제 여부
        
    Returns:
        Dict: 처리 상태 정보
    """
    try:
        # 테스트 정보 조회
        test = await db.tests.find_one({"_id": ObjectId(test_id)})
        if not test:
            logger.error(f"테스트 ID {test_id} 를 찾을 수 없습니다.")
            raise ValueError(f"테스트 ID {test_id} 를 찾을 수 없습니다.")
            
        # 문제 정보 조회
        problem = await db.problems.find_one({"_id": ObjectId(problem_id)})
        if not problem:
            logger.error(f"문제 ID {problem_id} 를 찾을 수 없습니다.")
            raise ValueError(f"문제 ID {problem_id} 를 찾을 수 없습니다.")
        
        # problem_number 찾기 (키 값)
        problem_number = None
        for key, value in test.get("problem_data", {}).items():
            if value.get("problem_id") == problem_id:
                problem_number = key
                break
                
        if not problem_number:
            logger.error(f"테스트 {test_id}에서 문제 {problem_id}를 찾을 수 없습니다.")
            raise ValueError(f"테스트 {test_id}에서 문제 {problem_id}를 찾을 수 없습니다.")
        
        # 백그라운드 작업으로 전환
        background_tasks.add_task(
            process_audio_background,
            db=db,
            test_id=test_id,
            problem_id=problem_id,
            problem_number=problem_number,
            audio_content=audio_content,
            is_last_problem=is_last_problem
        )
        
        # 즉시 상태 업데이트 및 응답
        await db.tests.update_one(
            {"_id": ObjectId(test_id)},
            {"$set": {
                f"problem_data.{problem_number}.processing_status": "processing",
                f"problem_data.{problem_number}.processing_message": "오디오 처리가 시작되었습니다.",
                f"problem_data.{problem_number}.processing_started_at": datetime.now()
            }}
        )
        
        return {
            "status": "processing",
            "message": "오디오 처리가 백그라운드에서 시작되었습니다.",
            "test_id": test_id,
            "problem_id": problem_id,
            "problem_number": problem_number
        }
            
    except Exception as e:
        logger.error(f"오디오 처리 시작 중 오류: {str(e)}", exc_info=True)
        # 오류 로깅 및 응답
        await db.errors.insert_one({
            "test_id": test_id,
            "problem_id": problem_id,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now(),
            "source": "process_audio_and_evaluate"
        })
        
        raise ValueError(f"오디오 처리 시작 중 오류가 발생했습니다: {str(e)}")

@track_time_async(BACKGROUND_TASK_DURATION, {"task_type": "audio_processing"})
async def process_audio_background(
    db: Database,
    test_id: str,
    problem_id: str,
    problem_number: str,
    audio_content: bytes,
    is_last_problem: bool
):
    """
    백그라운드에서 오디오 처리 및 평가 수행
    
    Args:
        db: MongoDB 데이터베이스
        test_id: 테스트 ID
        problem_id: 문제 ID
        problem_number: 문제 번호
        audio_content: 오디오 파일 바이트 데이터
        is_last_problem: 마지막 문제 여부
    """
    try:
        # 1. 상태 업데이트 - 오디오 처리 중
        await db.tests.update_one(
            {"_id": ObjectId(test_id)},
            {"$set": {
                f"problem_data.{problem_number}.processing_status": "transcribing",
                f"problem_data.{problem_number}.processing_message": "음성을 텍스트로 변환 중입니다."
            }}
        )
        
        # 2. AudioProcessor를 사용하여 오디오 텍스트 변환
        try:
            transcribed_text = standard_audio_processor.process_audio(audio_content)
            logger.info(f"음성 변환 완료: {transcribed_text[:50]}...")
        except Exception as e:
            logger.error(f"음성 변환 중 오류: {str(e)}", exc_info=True)
            transcribed_text = "음성 변환 중 오류가 발생했습니다. 녹음을 다시 시도해 주세요."
        
        # 3. 상태 업데이트 - 평가 중
        await db.tests.update_one(
            {"_id": ObjectId(test_id)},
            {"$set": {
                f"problem_data.{problem_number}.processing_status": "evaluating",
                f"problem_data.{problem_number}.processing_message": "응답 평가 중입니다.",
                f"problem_data.{problem_number}.user_response": transcribed_text
            }}
        )
        
        # 4. 문제 정보 가져오기
        problem = await db.problems.find_one({"_id": ObjectId(problem_id)})
        problem_category = problem.get("problem_category", "")
        topic_category = problem.get("topic_category", "")
        problem_content = problem.get("content", "")
        
        # 5. 테스트 생성 시간을 가져와 스크립트 저장
        test = await db.tests.find_one({"_id": ObjectId(test_id)})
        test_created_at = test.get("test_date", datetime.now())
        
        script_data = {
            "user_id": str(test["user_id"]),
            "problem_id": problem_id,
            "content": transcribed_text,
            "is_script": False,
            "created_at": test_created_at
        }
        
        await db.scripts.insert_one(script_data)
        
        # 6. 응답이 너무 짧으면 평가 생략
        if len(transcribed_text.split()) < 5:
            evaluation_result = {
                "score": "NL",
                "feedback": {
                    "paragraph": "응답이 너무 짧아 평가할 수 없습니다. 최소 한 문장 이상의 응답이 필요합니다.",
                    "vocabulary": "응답이 너무 짧아 어휘력을 평가할 수 없습니다.",
                    "spoken_amount": "발화량이 매우 부족합니다. 질문에 대해 충분한 길이로 답변해야 합니다."
                }
            }
        else:
            # 7. 매번 새로운 API 키로 평가기 생성
            evaluator_instance = ResponseEvaluator()
            
            # LangChain 평가 모델 호출
            evaluation_result = await evaluator_instance.evaluate_response(
                user_response=transcribed_text,
                problem_category=problem_category,
                topic_category=topic_category,
                problem=problem_content
            )
        
        score = evaluation_result.get("score", "IM2")
        feedback = evaluation_result.get("feedback", {})
        
        # 8. 테스트 문서 내 해당 문제의 평가 결과 업데이트
        await db.tests.update_one(
            {"_id": ObjectId(test_id)},
            {"$set": {
                f"problem_data.{problem_number}.score": score,
                f"problem_data.{problem_number}.feedback": feedback,
                f"problem_data.{problem_number}.processing_status": "completed",
                f"problem_data.{problem_number}.processing_message": "문제 평가가 완료되었습니다.",
                f"problem_data.{problem_number}.processing_completed_at": datetime.now()
            }}
        )
        
        logger.info(f"문제 {problem_number} 평가 완료 - 점수: {score}")
        
        # 9. 마지막 문제인 경우 종합 평가 수행
        if is_last_problem:
            await evaluate_overall_test_background(db, test_id)
            
    except Exception as e:
        logger.error(f"오디오 처리 및 평가 중 오류: {str(e)}", exc_info=True)
        
        # 오류 발생 시 상태 업데이트
        try:
            await db.tests.update_one(
                {"_id": ObjectId(test_id)},
                {"$set": {
                    f"problem_data.{problem_number}.processing_status": "failed",
                    f"problem_data.{problem_number}.processing_message": f"오류가 발생했습니다: {str(e)}",
                    f"problem_data.{problem_number}.processing_error": str(e),
                    f"problem_data.{problem_number}.processing_completed_at": datetime.now()
                }}
            )
            
            # 마지막 문제였다면 전체 피드백 상태도 업데이트
            if is_last_problem:
                await db.tests.update_one(
                    {"_id": ObjectId(test_id)},
                    {"$set": {
                        "overall_feedback_status": "failed",
                        "overall_feedback_message": f"전체 평가 중 오류가 발생했습니다: {str(e)}",
                        "overall_feedback_completed_at": datetime.now()
                    }}
                )
        except Exception as inner_error:
            logger.error(f"오류 상태 업데이트 중 추가 오류: {str(inner_error)}", exc_info=True)
        
        # 오류 로깅
        await db.errors.insert_one({
            "test_id": test_id,
            "problem_id": problem_id,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now(),
            "source": "process_audio_background"
        })


async def evaluate_overall_test_background(db: Database, test_id: str):
    """
    테스트 전체에 대한 종합 평가 수행
    
    Args:
        db: MongoDB 데이터베이스
        test_id: 테스트 ID
    """
    try:
        # 1. 상태 업데이트 - 종합 평가 중
        await db.tests.update_one(
            {"_id": ObjectId(test_id)},
            {"$set": {
                "overall_feedback_status": "processing",
                "overall_feedback_message": "전체 테스트 평가 중입니다."
            }}
        )
        
        # 2. 테스트 정보 가져오기
        test = await db.tests.find_one({"_id": ObjectId(test_id)})
        if not test:
            raise ValueError(f"테스트 ID {test_id}에 해당하는 테스트를 찾을 수 없습니다.")
            
        user_id = test.get("user_id")
        if not user_id:
            raise ValueError(f"테스트 ID {test_id}에 연결된 사용자 ID가 없습니다.")
        
        # 3. 문제별 상세 데이터 수집
        problem_details = {}
        for problem_number, problem_data in test.get("problem_data", {}).items():
            problem_details[problem_number] = problem_data
        
        # 4. ResponseEvaluator 인스턴스 생성 및 종합 평가 실행
        evaluator = ResponseEvaluator()
        evaluation_result = await evaluator.evaluate_overall_test(test, problem_details)
        
        # 5. 테스트 점수 및 피드백 업데이트
        await db.tests.update_one(
            {"_id": ObjectId(test_id)},
            {"$set": {
                "test_score": evaluation_result.get("test_score", {}),
                "test_feedback": evaluation_result.get("test_feedback", {}),
                "overall_feedback_status": "completed",
                "overall_feedback_message": "전체 테스트 평가가 완료되었습니다.",
                "overall_feedback_completed_at": datetime.now()
            }}
        )
        
        logger.info(f"테스트 {test_id}의 종합 평가가 완료되었습니다.")
        
        # 6. 사용자의 모든 테스트 가져오기
        user_tests = await db.tests.find(
            {"user_id": user_id, "test_score.total_score": {"$exists": True}}
        ).to_list(length=None)
        
        # 7. 테스트 점수 분류
        all_test_scores = {
            "total_score": [],
            "comboset_score": [],
            "roleplaying_score": [],
            "unexpected_score": []
        }
        
        # OPIC_LEVELS 정의
        OPIC_LEVELS = ["NL", "NM", "NH", "IL", "IM1", "IM2", "IM3", "IH", "AL"]
        
        for test_doc in user_tests:
            test_score = test_doc.get("test_score", {})
            
            # 각 카테고리별 점수 수집
            for category in all_test_scores.keys():
                score = test_score.get(category)
                if score and score != "N/A" and score in OPIC_LEVELS:
                    all_test_scores[category].append(score)
        
        # 8. 평균 점수 계산
        user_average_scores = {}
        
        for category, scores in all_test_scores.items():
            if not scores:
                user_average_scores[category] = None
                continue
                
            # 레벨을 숫자로 변환
            level_values = []
            for level in scores:
                try:
                    level_index = OPIC_LEVELS.index(level)
                    level_values.append(level_index)
                except (ValueError, IndexError):
                    # 유효하지 않은 레벨은 중간 레벨(IM2)로 처리
                    level_values.append(OPIC_LEVELS.index("IM2"))
            
            # 평균 계산 및 가장 가까운 레벨 반환
            average_value = sum(level_values) / len(level_values)
            closest_index = round(average_value)
            
            # 인덱스 범위 확인
            if closest_index < 0:
                closest_index = 0
            elif closest_index >= len(OPIC_LEVELS):
                closest_index = len(OPIC_LEVELS) - 1
            
            user_average_scores[category] = OPIC_LEVELS[closest_index]
        
        # 9. 사용자 평균 점수 업데이트
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "average_score": {
                    "total_score": user_average_scores.get("total_score"),
                    "comboset_score": user_average_scores.get("comboset_score"),
                    "roleplaying_score": user_average_scores.get("roleplaying_score"),
                    "unexpected_score": user_average_scores.get("unexpected_score")
                }
            }}
        )
        
        logger.info(f"사용자 {user_id}의 평균 점수가 업데이트되었습니다: {user_average_scores}")
        
    except Exception as e:
        logger.error(f"종합 평가 중 오류: {str(e)}", exc_info=True)
        
        # 오류 발생 시 상태 업데이트
        try:
            await db.tests.update_one(
                {"_id": ObjectId(test_id)},
                {"$set": {
                    "overall_feedback_status": "failed",
                    "overall_feedback_message": f"전체 평가 중 오류가 발생했습니다: {str(e)}",
                    "overall_feedback_completed_at": datetime.now()
                }}
            )
        except Exception as inner_error:
            logger.error(f"오류 상태 업데이트 중 추가 오류: {str(inner_error)}", exc_info=True)
        
        # 오류 로깅
        await db.errors.insert_one({
            "test_id": test_id,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now(),
            "source": "evaluate_overall_test_background"
        })


async def get_audio_content(test, audio_file):
    if audio_file:
        return await audio_file.read()
    
    audio_content = test.get("cached_audio_content")
    if not audio_content:
        raise HTTPException(
            status_code=400,
            detail="오디오 파일을 찾을 수 없습니다."
        )
    return audio_content

# 각 검증 및 처리 함수들
async def validate_user(current_user):
    return str(current_user.id)

async def validate_test(db, test_id):
    test = await db.tests.find_one({"_id": ObjectId(test_id)})
    if not test:
        raise HTTPException(status_code=404, detail="해당 테스트를 찾을 수 없습니다.")
    return test

async def get_problem_id(db, test_id):
    test = await db.tests.find_one({"_id": ObjectId(test_id)})
    problem_id = test.get("problem_data", {}).get("1", {}).get("problem_id")
    if not problem_id:
        raise HTTPException(status_code=404, detail="테스트의 문제를 찾을 수 없습니다.")
    return problem_id

async def validate_problem(db, test_id):
    test = await db.tests.find_one({"_id": ObjectId(test_id)})
    problem_id = test.get("problem_data", {}).get("1", {}).get("problem_id")
    problem = await db.problems.find_one({"_id": ObjectId(problem_id)})
    if not problem:
        raise HTTPException(status_code=404, detail="해당 문제를 찾을 수 없습니다.")
    return problem

async def validate_audio_file(audio_file):
    audio_filename = audio_file.filename
    file_extension = audio_filename.split(".")[-1].lower() if audio_filename else ""
    if file_extension not in ["mp3", "wav", "webm", "m4a"]:
        raise HTTPException(status_code=400, detail="지원되지 않는 파일 형식입니다.")
    
    # 파일 크기 제한
    max_size = 10 * 1024 * 1024  # 10MB
    audio_content = await audio_file.read()
    if len(audio_content) > max_size:
        raise HTTPException(status_code=400, detail=f"파일 크기가 너무 큽니다.")

async def transcribe_audio(audio_content, user_id):
    try:
        if not audio_content:
            raise ValueError("오디오 파일이 비어있습니다.")
        
        logger.info(f"음성 변환 시작 - 파일 크기: {len(audio_content)} 바이트")
        
        transcribed_text = fast_audio_processor.process_audio_fast(audio_content)
        
        logger.info(f"음성 변환 성공: {transcribed_text[:50]}...")
        return transcribed_text
    
    except Exception as e:
        logger.error(f"음성 변환 중 오류 발생: {str(e)}")
        raise


# async def evaluate_response(transcribed_text, problem_category, topic_category, problem_content):
#     try:
#         # 평가 수행
#         evaluator_instance = ResponseEvaluator()
#         return await evaluator_instance.evaluate_response(
#             user_response=transcribed_text,
#             problem_category=problem_category,
#             topic_category=topic_category,
#             problem=problem_content
#         )
#     except Exception as e:
#         logger.error(f"응답 평가 중 오류 발생: {str(e)}")
#         raise

async def evaluate_response(
    transcribed_text, 
    problem_category,
    topic_category,
    problem
):
    """사용자 응답 평가 실행"""
    logger.info(f"응답 평가 시작 - 문제 카테고리: {problem_category}, 토픽: {topic_category}")
    
    evaluator = ResponseEvaluator()
    max_retries = 10
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 평가 실행
            result = await evaluator.evaluate_response(
                transcribed_text, 
                problem_category, 
                topic_category, 
                problem
            )
            return result
            
        except Exception as e:
            retry_count += 1
            error_msg = str(e)
            
            # 할당량 오류 감지 및 재시도
            if "quota" in error_msg.lower() or "429" in error_msg or "rate limit" in error_msg:
                logger.warning(f"API 할당량 오류 발생 ({retry_count}/{max_retries}): {error_msg}")
                
                # 다음 시도 전에 잠시 대기 (지수 백오프 적용)
                await asyncio.sleep(2 * retry_count)  # 점점 더 긴 대기 시간
            else:
                logger.error(f"응답 평가 중 오류 발생 ({retry_count}/{max_retries}): {error_msg}")
                await asyncio.sleep(1)
                
            # 최대 재시도 횟수에 도달하면 예외 발생
            if retry_count >= max_retries:
                logger.error(f"최대 재시도 횟수에 도달했습니다: {error_msg}")
                raise ValueError(f"응답 평가 중 오류가 발생했습니다: {error_msg}")

async def save_script(db, user_id, problem_id, transcribed_text):
    script_data = {
        "user_id": user_id,
        "problem_id": problem_id,
        "content": transcribed_text,
        "is_script": False,
        "created_at": datetime.now()
    }
    await db.scripts.insert_one(script_data)

async def update_test_document(db, test_id, transcribed_text, evaluation_result):
    await db.tests.update_one(
        {"_id": ObjectId(test_id)},
        {"$set": {
            "random_problem.score": evaluation_result.get("score", ""),
            "random_problem.feedback": evaluation_result.get("feedback", {}),
            "random_problem.user_response": transcribed_text,
            "random_problem.processing_status": "completed",
            "random_problem.processing_completed_at": datetime.now()
        }}
    )

def create_evaluation_response(problem, user_id, transcribed_text, evaluation_result):
    return RandomProblemEvaluationResponse(**{
        "problem_id": str(problem["_id"]),
        "user_id": user_id,
        "problem_category": problem.get("problem_category", ""),
        "topic_category": problem.get("topic_category", ""),
        "problem_content": problem.get("content", ""),
        "transcribed_text": transcribed_text,
        "score": evaluation_result.get("score", ""),
        "feedback": evaluation_result.get("feedback", {}),
        "evaluated_at": datetime.now().isoformat()
    })

async def log_error(db, test_id, problem_id, error):
    await db.errors.insert_one({
        "test_id": test_id,
        "problem_id": problem_id,
        "error": str(error),
        "traceback": traceback.format_exc(),
        "timestamp": datetime.now(),
        "source": "evaluate_random_problem"
    })