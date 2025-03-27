from fastapi import APIRouter, HTTPException, Depends, Path, status, Query, Response, UploadFile, File, BackgroundTasks, Body, Form
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
import traceback
from typing import Any, Dict, Union
from bson import ObjectId, errors as bson_errors
from motor.motor_asyncio import AsyncIOMotorDatabase as Database

from datetime import datetime
from db.mongodb import get_mongodb
from api.deps import get_current_user, get_current_user_for_multipart
from models.user import User

import base64
import os
import io
from gtts import gTTS
import logging

from schemas.test import TestHistoryResponse, TestDetailResponse, TestCreationResponse, SingleProblemResponse, RandomProblemEvaluationResponse
from services.audio_processor import AudioProcessor, FastAudioProcessor

from services.evaluator import ResponseEvaluator
from services.test_service import create_test, process_audio_background, get_random_single_problem

# 로깅 설정
logger = logging.getLogger(__name__)

# 두 가지 전역 인스턴스 생성 (Groq 기반)
standard_audio_processor = AudioProcessor(model_name="whisper-large-v3")  # 7문제, 15문제용
fast_audio_processor = FastAudioProcessor(model_name="whisper-large-v3")  # 랜덤 단일 문제용

evaluator = ResponseEvaluator()

router = APIRouter()

@router.get("/history", response_model=TestHistoryResponse)
async def get_test_history(
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_mongodb)
) -> Any:
    """
    로그인한 사용자의 모의고사 히스토리 조회
    """
    try:
        # 현재 사용자 정보 사용
        user_pk = str(current_user.id)
        
        # 디버깅을 위한 로깅 추가
        logger.info(f"사용자 정보: {current_user}")
        logger.info(f"사용자 limits 필드: {getattr(current_user, 'limits', None)}")
        
        # 사용자의 테스트 생성 횟수 정보 가져오기 (limits 필드 사용)
        limits = getattr(current_user, 'limits', {"test_count": 0, "random_problem": 0, "script_count": 0})
        
        # 남은 횟수 계산 (테스트와 랜덤 문제 모두 limits 필드에서 가져옴)
        test_counts = {
            "test_count": {
                "used": limits.get("test_count", 0),
                "limit": 2,
                "remaining": max(0, 2 - limits.get("test_count", 0))
            },
            "random_problem": {
                "used": limits.get("random_problem", 0),
                "limit": 3,
                "remaining": max(0, 3 - limits.get("random_problem", 0))
            },
            # script_count 추가 (요청된 경우)
            "script_count": {
                "used": limits.get("script_count", 0),
                "limit": 5,
                "remaining": max(0, 5 - limits.get("script_count", 0))
            }
        }

        # 사용자의 테스트 내역 조회
        tests_cursor = db.tests.find({"user_id": user_pk})
        tests = await tests_cursor.to_list(length=None)

        # 조회된 테스트 데이터 변환
        test_history = []
        for test in tests:
            test_history.append({
                "id": str(test["_id"]),
                "overall_feedback_status": test.get("overall_feedback_status", "미평가"),
                "test_date": test["test_date"],
                "test_type": test["test_type"],
                "test_score": test.get("test_score", None)
            })

        # 응답 생성
        average_score = getattr(current_user, 'average_score', None)
        
        response = {
            "average_score": average_score,
            "test_history": test_history,
            "test_counts": test_counts
        }

        # 최종 응답 로깅
        logger.info(f"테스트 히스토리 응답: {response}")
        
        return response
    except Exception as e:
        logger.error(f"테스트 히스토리 조회 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"테스트 히스토리 조회 중 오류 발생: {str(e)}"
        )
    

@router.get("/{test_pk}", response_model=TestDetailResponse)
async def get_test_detail(
    test_pk: str,
    db: Database = Depends(get_mongodb)
) -> Any:
    """
    모의고사 상세 조회
    """
    try:
        # ObjectId로 변환
        test_id = ObjectId(test_pk)
        
        # 테스트 조회
        test = await db.tests.find_one({"_id": test_id})
        
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="해당 테스트를 찾을 수 없습니다."
            )
        
        # MongoDB의 ObjectId를 문자열로 변환
        test["_id"] = str(test["_id"])
        
        # 사용자 ID가 ObjectId일 경우 문자열로 변환
        if "user_id" in test and test["user_id"] and isinstance(test["user_id"], ObjectId):
            test["user_id"] = str(test["user_id"])
        
        # problem_data 내 ObjectId 처리 (필요한 경우)
        if "problem_data" in test:
            for problem_key, problem_value in test["problem_data"].items():
                if isinstance(problem_value, dict) and "problem_id" in problem_value and isinstance(problem_value["problem_id"], ObjectId):
                    problem_value["problem_id"] = str(problem_value["problem_id"])
        
        return test
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="잘못된 테스트 ID 형식입니다."
        )
    except Exception as e:
        logger.error(f"테스트 상세 조회 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"테스트 상세 조회 중 오류 발생: {str(e)}"
        )


@router.post("/{test_type}", response_model=Union[TestCreationResponse, SingleProblemResponse])
async def make_test(
    test_type: int = Path(..., ge=0, le=2, description="테스트 유형: 0은 7문제, 1은 15문제, 2는 랜덤 1문제"),
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_mongodb)
) -> Union[TestCreationResponse, SingleProblemResponse]:
    """
    모의고사 생성 API
    - test_type 0: 7문제 (콤보셋 3, 롤플레잉 2, 돌발 2) - 속성, 실전 모의고사 도합 최대 3회
    - test_type 1: 15문제 (자기소개 1, 콤보셋 9, 롤플레잉 3, 돌발 2) 
    - test_type 2: 랜덤 1문제 (전체 문제 풀에서 랜덤 선택, DB에 저장하지 않음) - 최대 5회
    
    현재 로그인한 사용자의 배경 정보(background_survey.info)를 기반으로
    관심사에 맞는 문제들로 테스트를 구성합니다.
    """
    # 현재 인증된 사용자 정보 사용
    user_id = str(current_user.id)
    
    # 최신 사용자 정보 DB에서 다시 조회 (캐싱된 정보가 아닌 최신 상태 확인)
    latest_user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not latest_user:
        return JSONResponse(
            status_code=404,
            content={"detail": "사용자를 찾을 수 없습니다"}
        )
    
    # User.from_mongo 메서드를 사용하여 일관된 필드 접근
    user_obj = User.from_mongo(latest_user)
    
    # 로깅 추가 - 데이터 구조 확인
    logger.info(f"DB에서 가져온 사용자 정보: {latest_user}")
    logger.info(f"변환된 사용자 객체의 limits 필드: {user_obj.limits}")
    
    # User 객체의 limits 필드 사용
    limits = user_obj.limits
    
    # 테스트 타입에 따른 제한 확인
    if test_type == 0 or test_type == 1:  # 7문제 또는 15문제 테스트 (통합 카운트)
        test_count = limits.get("test_count", 0)
        logger.info(f"현재 test_count: {test_count}")
        if test_count >= 2:
            # 로깅 추가
            logger.warning(f"사용자 {user_id}의 test_count({test_count})가 제한(2)을 초과했습니다")
            return JSONResponse(
                status_code=403,
                content={"detail": "속성 모의고사와 실전 모의고사는 합산하여 최대 2회까지만 생성 가능합니다"}
            )
        
        # 무조건 limits 필드 사용
        limit_field = "limits.test_count"
    else:  # 랜덤 1문제
        random_problem_count = limits.get("random_problem", 0)
        logger.info(f"현재 random_problem_count: {random_problem_count}")
        if random_problem_count >= 3:
            # 로깅 추가
            logger.warning(f"사용자 {user_id}의 random_problem_count({random_problem_count})가 제한(3)을 초과했습니다")
            return JSONResponse(
                status_code=403,
                content={"detail": "맛보기 한 문제는 최대 3회까지만 생성 가능합니다"}
            )
        
        # 무조건 limits 필드 사용
        limit_field = "limits.random_problem"

    # 로깅 추가 - 업데이트 필드
    logger.info(f"테스트 카운트 업데이트 필드: {limit_field}")
    
    try:
        # 테스트 횟수 증가 - 무조건 limits 필드 사용
        update_result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {limit_field: 1}}
        )
        
        # 업데이트 확인 로깅
        logger.info(f"사용자 {user_id} 업데이트 결과: {update_result.modified_count}개 수정됨")
        
        # 업데이트 후 사용자 데이터 확인을 위한 재조회
        updated_user = await db.users.find_one({"_id": ObjectId(user_id)})
        logger.info(f"업데이트 후 사용자 데이터: {updated_user}")

        # 랜덤 단일 문제 요청인 경우 (test_type == 2)
        if test_type == 2:
            # 별도 함수로 랜덤 문제 하나만 가져옴 (DB에 저장하지 않음)
            random_problem = await get_random_single_problem(db, user_id)
            return SingleProblemResponse(**random_problem)
        else:
            # 기존 테스트 생성 로직 (DB에 저장)
            test_id = await create_test(db, test_type, user_id)
            
            # 생성된 테스트 정보 조회
            test_data = await db.tests.find_one({"_id": ObjectId(test_id)})
            if not test_data:
                # 테스트 횟수 롤백
                await db.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$inc": {limit_field: -1}}
                )
                return JSONResponse(
                    status_code=404,
                    content={"detail": "생성된 테스트를 찾을 수 없습니다"}
                )
            
            # ObjectId를 문자열로 변환
            test_data["_id"] = str(test_data["_id"])
            
            # TestCreationResponse 모델로 변환하여 반환
            return TestCreationResponse(**test_data)
        
    except bson_errors.InvalidId as e:
        # ObjectId 변환 오류
        return JSONResponse(
            status_code=400,
            content={"detail": f"잘못된 ID 형식: {str(e)}"}
        )
    except Exception as e:
        # 로깅 추가
        logger.error(f"테스트 생성 중 오류 발생: {str(e)}", exc_info=True)
        
        # 테스트 생성이 실패한 경우, 카운트 원복
        try:
            await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$inc": {limit_field: -1}}
            )
        except Exception as rollback_error:
            logger.error(f"카운트 롤백 중 오류: {str(rollback_error)}")
        
        return JSONResponse(
            status_code=500,
            content={"detail": f"테스트 생성 중 오류 발생: {str(e)}"}
        )


    

@router.delete("/{test_id}")
async def delete_test(
    test_id: str,
    db: Database = Depends(get_mongodb)
) -> Response:
    """
    테스트 삭제 엔드포인트
    """
    try:
        # 유효한 ObjectId인지 확인
        if not ObjectId.is_valid(test_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="유효하지 않은 테스트 ID 형식입니다."
            )
        
        # 테스트 조회
        test = await db.tests.find_one({"_id": ObjectId(test_id)})
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 ID의 테스트를 찾을 수 없습니다."
            )
        
        # 테스트 삭제
        result = await db.tests.delete_one({"_id": ObjectId(test_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="테스트 삭제에 실패했습니다."
            )
        
        # 204 No Content 반환 (성공적으로 삭제됨)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
        
    except HTTPException:
        # 이미 처리된 예외는 그대로 전달
        raise
    except Exception as e:
        logger.error(f"테스트 삭제 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"테스트 삭제 중 오류 발생: {str(e)}"
        )

@router.get("/{problem_pk}/audio")
async def get_problem_audio(
    problem_pk: str = Path(..., description="문제 ID"),
    db: Database = Depends(get_mongodb)
) -> Dict[str, Any]:
    """
    주어진 문제 ID로 문제 내용을 음성으로 변환하여 Base64 인코딩된 오디오 데이터를 반환합니다.

    Args:
        problem_pk (str): MongoDB에서 조회할 문제의 고유 ID
        db (AsyncIOMotorDatabase): MongoDB 데이터베이스 연결 세션

    Returns:
        Dict[str, Any]: 다음 키를 포함하는 딕셔너리
        - audio_base64 (str): Base64로 인코딩된 MP3 오디오 데이터
        - audio_type (str): 오디오 파일 유형 (mp3)
        - file_size_bytes (int): 오디오 파일의 바이트 크기
        - file_size_kb (float): 오디오 파일의 킬로바이트 크기

    Raises:
        HTTPException: 
            - 404: 문제를 찾을 수 없는 경우
            - 400: 문제 내용이 없는 경우
            - 500: 오디오 생성 중 예상치 못한 오류 발생 시
    """
    try:
        # MongoDB에서 문제 조회
        problem = await db.problems.find_one({"_id": ObjectId(problem_pk)})
        
        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")
        
        # 문제 내용 추출
        problem_content = problem.get('content', '')
        
        if not problem_content:
            raise HTTPException(status_code=400, detail="No content available for TTS")
        
        # 임시 오디오 파일 생성
        tts = gTTS(text=problem_content, lang='en')
        temp_audio_path = f"./temp_audio_{problem_pk}.mp3"
        tts.save(temp_audio_path)
        
        # 파일 크기 계산
        file_size = os.path.getsize(temp_audio_path)
        
        # 파일을 Base64로 인코딩
        with open(temp_audio_path, 'rb') as audio_file:
            encoded_audio = base64.b64encode(audio_file.read()).decode('utf-8')
        
        # 임시 파일 삭제
        os.remove(temp_audio_path)
        
        return {
            "audio_base64": encoded_audio,
            "audio_type": "mp3",
            "file_size_bytes": file_size,
            "file_size_kb": round(file_size / 1024, 2)
        }
    
    except Exception as e:
        logger.error(f"오디오 생성 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating audio: {str(e)}")


@router.get("/{problem_pk}/audio/play")
async def play_problem_audio(
    problem_pk: str = Path(..., description="문제 ID"),
    db: Database = Depends(get_mongodb)
) -> HTMLResponse:
    """
    브라우저에서 직접 오디오를 재생할 수 있는 HTML 페이지 반환
    
    Args:
        problem_pk (str): 문제 ID
        db (AsyncIOMotorDatabase): MongoDB 데이터베이스 연결
    
    Returns:
        HTMLResponse: 오디오 재생 HTML 페이지
    """
    try:
        # MongoDB에서 문제 조회
        problem = await db.problems.find_one({"_id": ObjectId(problem_pk)})
        
        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")
        
        # 문제 내용 추출
        problem_content = problem.get('content', '')
        
        if not problem_content:
            raise HTTPException(status_code=400, detail="No content available for TTS")
        
        # 임시 오디오 파일 생성
        tts = gTTS(text=problem_content, lang='en')
        temp_audio_path = f"./temp_audio_{problem_pk}.mp3"
        tts.save(temp_audio_path)
        
        # HTML 페이지 생성 - 상대 경로 사용
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Problem Audio Playback</title>
            <style>
                body {{ 
                    display: flex; 
                    justify-content: center; 
                    align-items: center; 
                    height: 100vh; 
                    margin: 0; 
                    font-family: Arial, sans-serif; 
                }}
                .container {{ 
                    text-align: center; 
                    padding: 20px; 
                    border: 1px solid #ddd; 
                    border-radius: 10px; 
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Problem Audio Playback</h1>
                <audio controls autoplay style="width: 300px;">
                    <source src="./download" type="audio/mp3">
                    Your browser does not support the audio element.
                </audio>
                <p>문제 내용: {problem_content}</p>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
    
    except Exception as e:
        logger.error(f"오디오 재생 페이지 생성 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating audio: {str(e)}")


@router.post("/{test_pk}/record/{problem_pk}")
async def record_answer(
    test_pk: str,
    problem_pk: str,
    audio_file: UploadFile = File(...),
    is_last_problem: bool = Body(False),
    background_tasks: BackgroundTasks = None,
    db: Database = Depends(get_mongodb)
) -> Any:
    """
    시험 보기 - 사용자의 녹음을 프론트에서 mp3로 넘겨주면, whisper가 텍스트로 변환.
    변환한 텍스트를 langchain 모델이 평가해서 해당 test의 test에 대한 점수와 피드백을 저장한다.
    
    만약, 요청을 보낼 때, 마지막 문제인 경우, 프론트에서 body parameter로 마지막 문제임을 넘겨주면,
    마지막 문제에 대한 평가를 한 이후에, 해당 test에 있는 모든 feedback을 종합하여 test에 대한 점수와 피드백을 저장한다.
    
    해당 로직은 front에서 다음 버튼을 누르면 다음 페이지로 바로 넘어가야 하기 때문에, 비동기 방식으로 작동하도록 한다.
    """
    try:
        # ObjectId 유효성 검사
        if not ObjectId.is_valid(test_pk) or not ObjectId.is_valid(problem_pk):
            raise HTTPException(status_code=400, detail="유효하지 않은 ID 형식입니다.")
        
        # 테스트 존재 확인
        test = await db.tests.find_one({"_id": ObjectId(test_pk)})
        if not test:
            raise HTTPException(status_code=404, detail="해당 테스트를 찾을 수 없습니다.")
            
        # 문제 존재 확인
        problem = await db.problems.find_one({"_id": ObjectId(problem_pk)})
        if not problem:
            raise HTTPException(status_code=404, detail="해당 문제를 찾을 수 없습니다.")
        
        # 테스트에 해당 문제가 포함되어 있는지 확인 및 문제 번호 찾기
        problem_number = None
        problem_exists = False
        for key, value in test.get("problem_data", {}).items():
            if value.get("problem_id") == problem_pk:
                problem_exists = True
                problem_number = key
                break
                
        if not problem_exists:
            raise HTTPException(status_code=404, detail="해당 테스트에 이 문제가 포함되어 있지 않습니다.")
        
        # 상태 필드 초기화
        await db.tests.update_one(
            {"_id": ObjectId(test_pk)},
            {"$set": {
                f"problem_data.{problem_number}.processing_status": "processing",
                f"problem_data.{problem_number}.processing_started_at": datetime.now()
            }}
        )
        
        if is_last_problem:
            # 마지막 문제인 경우 전체 피드백 상태 초기화
            await db.tests.update_one(
                {"_id": ObjectId(test_pk)},
                {"$set": {
                    "overall_feedback_status": "pending",
                    "overall_feedback_started_at": datetime.now()
                }}
            )
        
        # 파일 내용을 미리 읽어 메모리에 저장
        audio_content = await audio_file.read()
        audio_filename = audio_file.filename
        
        # 파일 유형 검사
        file_extension = audio_filename.split(".")[-1].lower() if audio_filename else ""
        if file_extension not in ["mp3", "wav", "webm", "m4a"]:
            raise HTTPException(
                status_code=400, 
                detail="지원되지 않는 파일 형식입니다. MP3, WAV, WEBM, M4A 형식만 지원합니다."
            )
        
        # 파일 크기 제한 (10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(audio_content) > max_size:
            raise HTTPException(
                status_code=400, 
                detail=f"파일 크기가 너무 큽니다. 최대 10MB까지만 지원합니다. (현재 크기: {len(audio_content)/1024/1024:.2f}MB)"
            )
        
        # 백그라운드 태스크로 오디오 처리 및 평가 진행
        background_tasks.add_task(
            process_audio_background,
            db,
            test_pk,
            problem_pk,
            problem_number,
            audio_content,
            is_last_problem
        )
        
        # 응답 생성
        return JSONResponse(
            status_code=202,
            content={
                "message": f"{problem_number}번째 문제의 녹음이 성공적으로 제출되었습니다. 평가가 진행 중입니다.",
                "test_id": test_pk,
                "problem_id": problem_pk,
                "problem_number": problem_number,
                "is_last_problem": is_last_problem
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"녹음 제출 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"오류가 발생했습니다: {str(e)}")


@router.post("/random-problem/evaluate", response_model=RandomProblemEvaluationResponse)
async def evaluate_random_problem(
    problem_id: str = Form(..., description="문제 ID"),
    audio_file: UploadFile = File(..., description="녹음된.mp3 파일"),
    current_user: User = Depends(get_current_user_for_multipart),
    db: Database = Depends(get_mongodb)
) -> RandomProblemEvaluationResponse:
    """
    랜덤 단일 문제 평가 API
    
    현재 로그인한 사용자의 녹음을 받아 해당 문제에 대한 즉시 피드백을 제공합니다.
    이 API는 데이터베이스에 결과를 저장하지 않습니다.
    """
    try:
        # 현재 사용자 ID 사용
        user_id = str(current_user.id)
        
        # ObjectId 유효성 검사
        if not ObjectId.is_valid(problem_id):
            return JSONResponse(
                status_code=400,
                content={"detail": "유효하지 않은 문제 ID 형식입니다."}
            )
        
        # 문제 존재 확인
        problem = await db.problems.find_one({"_id": ObjectId(problem_id)})
        if not problem:
            return JSONResponse(
                status_code=404,
                content={"detail": "해당 문제를 찾을 수 없습니다."}
            )
        
        # 파일 내용 읽기
        audio_content = await audio_file.read()
        audio_filename = audio_file.filename
        
        # 파일 유형 검사
        file_extension = audio_filename.split(".")[-1].lower() if audio_filename else ""
        if file_extension not in ["mp3", "wav", "webm", "m4a"]:
            return JSONResponse(
                status_code=400, 
                content={"detail": "지원되지 않는 파일 형식입니다. MP3, WAV, WEBM, M4A 형식만 지원합니다."}
            )
        
        # 파일 크기 제한 (10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(audio_content) > max_size:
            return JSONResponse(
                status_code=400, 
                content={"detail": f"파일 크기가 너무 큽니다. 최대 10MB까지만 지원합니다. (현재 크기: {len(audio_content)/1024/1024:.2f}MB)"}
            )
        
        # 문제 정보 가져오기
        problem_category = problem.get("problem_category", "")
        topic_category = problem.get("topic_category", "")
        problem_content = problem.get("content", "")
        
        # AudioProcessor를 사용하여 오디오 텍스트 변환
        try:
            start_time = datetime.now()
            logger.info(f"사용자 {user_id}의 랜덤 문제 응답 변환 시작 (경량 모델)...")
            
            # 경량 모델과 최적화 설정 사용
            transcribed_text = fast_audio_processor.process_audio_fast(audio_content)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"경량 음성 변환 완료: {transcribed_text[:50]}... (소요 시간: {processing_time:.2f}초)")
        except Exception as e:
            logger.error(f"경량 음성 변환 중 오류: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": "음성 변환 중 오류가 발생했습니다. 녹음을 다시 시도해 주세요."}
            )
        
        # 스크립트는 저장하지 않음, 단 응답이 너무 짧으면 평가 생략
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
            # 매번 새로운 API 키로 평가기 생성
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
        
        # 결과 응답 구성
        response = {
            "problem_id": problem_id,
            "user_id": user_id,
            "problem_category": problem_category,
            "topic_category": topic_category,
            "problem_content": problem_content,
            "transcribed_text": transcribed_text,
            "score": score,
            "feedback": feedback,
            "evaluated_at": datetime.now().isoformat()
        }
        
        logger.info(f"랜덤 문제 평가 완료 - 사용자: {user_id}, 점수: {score}")
        return RandomProblemEvaluationResponse(**response)
        
    except Exception as e:
        logger.error(f"랜덤 문제 평가 중 오류 발생: {str(e)}", exc_info=True)
        # 오류 로깅 (DB에 저장하지 않고 로그만 남김)
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": f"오류가 발생했습니다: {str(e)}"}
        )


# 모의고사 점수, 피드백 생성 비동기 처리를 위한 상태 확인 엔드포인트 - 개별 문제
@router.get("/{test_pk}/status/{problem_pk}")
async def check_problem_status(
    test_pk: str,
    problem_pk: str,
    db: Database = Depends(get_mongodb)
) -> Any:
    """문제별 처리 상태 확인 엔드포인트"""
    if not ObjectId.is_valid(test_pk) or not ObjectId.is_valid(problem_pk):
        raise HTTPException(status_code=400, detail="유효하지 않은 ID 형식입니다.")
    
    # 테스트 조회
    test = await db.tests.find_one({"_id": ObjectId(test_pk)})
    if not test:
        raise HTTPException(status_code=404, detail="해당 테스트를 찾을 수 없습니다.")
    
    # 문제 데이터 찾기
    problem_data = None
    for data in test.get("problem_data", {}).values():
        if data.get("problem_id") == problem_pk:
            problem_data = data
            break
    
    if not problem_data:
        raise HTTPException(status_code=404, detail="해당 문제를 찾을 수 없습니다.")
    
    # 상태 정보 추출
    processing_status = problem_data.get("processing_status", "not_started")
    processing_message = problem_data.get("processing_message", "아직 처리가 시작되지 않았습니다.")
    
    return {
        "status": processing_status,
        "message": processing_message,
        "started_at": problem_data.get("processing_started_at"),
        "completed_at": problem_data.get("processing_completed_at")
    }


# 모의고사 점수, 피드백 생성 비동기 처리를 위한 상태 확인 엔드포인트 - 전체 문제
@router.get("/{test_pk}/overall-status")
async def check_overall_test_status(
    test_pk: str,
    db: Database = Depends(get_mongodb)
) -> Any:
    """테스트 전체 상태 확인 엔드포인트"""
    if not ObjectId.is_valid(test_pk):
        raise HTTPException(status_code=400, detail="유효하지 않은 ID 형식입니다.")
    
    # 테스트 정보 조회
    test = await db.tests.find_one({"_id": ObjectId(test_pk)})
    if not test:
        raise HTTPException(status_code=404, detail="해당 테스트를 찾을 수 없습니다.")
    
    # 전체 피드백 상태 확인
    overall_status = test.get("overall_feedback_status", "not_started")
    overall_message = test.get("overall_feedback_message", "")
    
    # 문제별 상태 수집
    problem_statuses = []
    for key, data in test.get("problem_data", {}).items():
        problem_statuses.append({
            "problem_id": data.get("problem_id"),
            "status": data.get("processing_status", "not_started"),
            "message": data.get("processing_message", "")
        })
    
    # 모든 문제가 완료되었는지 확인
    all_problems_completed = all(
        status["status"] == "completed" 
        for status in problem_statuses
    )
    
    return {
        "overall_status": overall_status,
        "overall_message": overall_message,
        "all_problems_completed": all_problems_completed,
        "problem_statuses": problem_statuses,
        "started_at": test.get("overall_feedback_started_at"),
        "completed_at": test.get("overall_feedback_completed_at")
    }