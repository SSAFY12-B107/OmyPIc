import logging
import traceback
from datetime import datetime
from bson import ObjectId
from celery import shared_task
from bson import ObjectId, errors as bson_errors

from db.mongodb import get_mongodb_sync
from services.audio_processor import AudioProcessor
from services.evaluator import ResponseEvaluator

import time

# 로깅 설정
logger = logging.getLogger(__name__)

@shared_task(bind=True, name="evaluate_random_problem")
def evaluate_random_problem_task(self, test_id, problem_id, user_id, audio_content_base64):
    try:
        # Base64 디코딩
        import base64
        audio_content = base64.b64decode(audio_content_base64)
        
        # MongoDB 연결
        db = get_mongodb_sync()
        
        # 문제 정보 가져오기
        problem = db.problems.find_one({"_id": ObjectId(problem_id)})
        
        # 음성 변환
        audio_processor = AudioProcessor(model_name="whisper-large-v3")
        transcribed_text = audio_processor.process_audio(audio_content)
        
        # 스크립트 저장
        script_data = {
            "user_id": user_id,
            "problem_id": problem_id,
            "content": transcribed_text,
            "is_script": False,
            "created_at": datetime.now()
        }
        db.scripts.insert_one(script_data)
        
        # 응답이 너무 짧으면 평가 생략
        if len(transcribed_text.split()) < 5:
            evaluation_result = {
                "score": "NL",
                "feedback": {
                    "paragraph": "응답이 너무 짧아 평가할 수 없습니다. 최소 한 문장 이상의 응답이 필요합니다.",
                    "vocabulary": "응답이 너무 짧아 어휘력을 평가할 수 없습니다.",
                    "delivery": "발화량이 매우 부족합니다. 질문에 대해 충분한 길이로 답변해야 합니다."
                }
            }
        else:
            # 응답 평가 - 재시도 로직 추가
            evaluator = ResponseEvaluator()
            
            # 최대 5번까지 재시도
            retry_count = 0
            max_retries = 5
            last_error = None
            
            while retry_count < max_retries:
                try:
                    evaluation_result = evaluator.evaluate_response_sync(
                        transcribed_text, 
                        problem.get("problem_category", ""),
                        problem.get("topic_category", ""),
                        problem.get("content", "")
                    )
                    
                    # 평가 결과 로깅
                    logger.info(f"평가 결과: {evaluation_result}")
                    
                    # 결과 검증
                    if not evaluation_result or not isinstance(evaluation_result, dict):
                        logger.warning(f"평가 결과가 유효하지 않습니다: {evaluation_result}")
                        evaluation_result = {
                            "score": "IL",
                            "feedback": {
                                "paragraph": "평가를 완료했으나 결과 형식이 올바르지 않습니다.",
                                "vocabulary": "기본 어휘력 평가입니다.",
                                "delivery": "기본 전달력 평가입니다."
                            }
                        }
                    
                    # 성공적으로 결과를 얻었으면 반복 종료
                    break
                    
                except Exception as e:
                    retry_count += 1
                    last_error = e
                    error_msg = str(e).lower()
                    
                    # API 할당량 초과 관련 오류인 경우
                    if any(term in error_msg for term in ["quota", "429", "rate limit", "exceeded"]):
                        logger.warning(f"API 할당량 오류 발생 ({retry_count}/{max_retries}): {error_msg}")
                        # 다음 시도 전에 잠시 대기
                        time.sleep(2 * retry_count)  # 점점 더 긴 대기 시간
                    else:
                        logger.error(f"평가 중 오류 발생 ({retry_count}/{max_retries}): {error_msg}")
                        time.sleep(1)
                    
                    # 마지막 시도에서도 실패한 경우
                    if retry_count >= max_retries:
                        logger.error(f"최대 재시도 횟수에 도달했습니다: {error_msg}")
                        evaluation_result = {
                            "score": "ERROR",
                            "feedback": {
                                "paragraph": f"평가 중 오류가 발생했습니다: {str(last_error)}",
                                "vocabulary": "평가를 완료할 수 없습니다.",
                                "delivery": "평가를 완료할 수 없습니다."
                            },
                            "error": str(last_error)
                        }
        
        # 테스트 문서 업데이트
        db.tests.update_one(
            {"_id": ObjectId(test_id)},
            {"$set": {
                "random_problem.score": evaluation_result.get("score", ""),
                "random_problem.feedback": evaluation_result.get("feedback", {}),
                "random_problem.user_response": transcribed_text,
                "random_problem.processing_status": "completed",
                "random_problem.processing_completed_at": datetime.now()
            }}
        )
        
        return {
            "status": "success",
            "test_id": test_id,
            "problem_id": problem_id,
            "evaluation": evaluation_result
        }
    
    except Exception as e:
        db = get_mongodb_sync()
        # 오류 상태 업데이트
        db.tests.update_one(
            {"_id": ObjectId(test_id)},
            {"$set": {
                "random_problem.processing_status": "failed",
                "random_problem.processing_message": f"오류 발생: {str(e)}",
                "random_problem.processing_completed_at": datetime.now()
            }}
        )
        # 오류 로깅
        db.errors.insert_one({
            "test_id": test_id,
            "problem_id": problem_id,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now(),
            "source": "evaluate_random_problem_task"
        })
        return {
            "status": "error",
            "test_id": test_id,
            "problem_id": problem_id,
            "error": str(e)
        }

@shared_task(bind=True, name="process_audio")
def process_audio_task(self, test_id, problem_id, problem_number, audio_content_bytes, is_last_problem=False):
    """
    오디오 파일을 처리하고 평가하는 Celery 작업
    
    Args:
        self: Celery 작업 인스턴스
        test_id: 테스트 ID
        problem_id: 문제 ID
        problem_number: 문제 번호
        audio_content_bytes: 원본 오디오 바이트 데이터
        is_last_problem: 마지막 문제 여부
    """
    # import base64 - 필요 없어졌으므로 제거
    
    try:
        # Base64 디코딩 제거 - 이미 bytes 타입으로 받음
        # audio_content = base64.b64decode(audio_content_base64)
        # audio_content_bytes는 이미 디코딩된 바이트 형태의 데이터임

        # ✅ MongoDB 동기 연결
        db = get_mongodb_sync()
        
        # 1. 상태 업데이트 - 오디오 처리 중
        db.tests.update_one(
            {"_id": ObjectId(test_id)},
            {"$set": {
                f"problem_data.{problem_number}.processing_status": "transcribing",
                f"problem_data.{problem_number}.processing_message": "음성을 텍스트로 변환 중입니다."
            }}
        )
        
        # 2. AudioProcessor를 사용하여 오디오 텍스트 변환
        try:
            audio_processor = AudioProcessor(model_name="whisper-large-v3")
            # audio_content_bytes를 직접 전달
            transcribed_text = audio_processor.process_audio_for_celery(audio_content_bytes)
            logger.info(f"음성 변환 완료: {transcribed_text[:50]}...")
        except Exception as e:
            logger.error(f"음성 변환 중 오류: {str(e)}", exc_info=True)
            transcribed_text = "음성 변환 중 오류가 발생했습니다. 녹음을 다시 시도해 주세요."
        
        # 3. 상태 업데이트 - 평가 중
        db.tests.update_one(
            {"_id": ObjectId(test_id)},
            {"$set": {
                f"problem_data.{problem_number}.processing_status": "evaluating",
                f"problem_data.{problem_number}.processing_message": "응답 평가 중입니다.",
                f"problem_data.{problem_number}.user_response": transcribed_text
            }}
        )
        
        try:
            problem_obj_id = ObjectId(problem_id)
        except bson_errors.InvalidId:
            raise ValueError(f"잘못된 problem_id 형식입니다: {problem_id}")

        problem = db.problems.find_one({"_id": problem_obj_id})
        if not isinstance(problem, dict):
            raise ValueError(f"문제 {problem_id} 를 찾을 수 없습니다.")

        problem_category = problem.get("problem_category", "")
        topic_category = problem.get("topic_category", "")
        problem_content = problem.get("content", "")
        
        # 5. 테스트 생성 시간을 가져와 스크립트 저장
        test = db.tests.find_one({"_id": ObjectId(test_id)})
        if not isinstance(test, dict):
            raise ValueError("테스트를 찾을 수 없습니다.")

        test_created_at = test.get("test_date", datetime.now())
        
        script_data = {
            "user_id": str(test["user_id"]),
            "problem_id": problem_id,
            "content": transcribed_text,
            "is_script": False,
            "created_at": test_created_at
        }
        
        db.scripts.insert_one(script_data)
        
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
            # 7. 평가기 생성 및 평가 수행 - 재시도 로직 추가
            evaluator_instance = ResponseEvaluator()
            
            # 최대 5번까지 재시도
            retry_count = 0
            max_retries = 5
            last_error = None
            
            while retry_count < max_retries:
                try:
                    # LangChain 평가 모델 호출 - 동기식
                    evaluation_result = evaluator_instance.evaluate_response_sync(
                        user_response=transcribed_text,
                        problem_category=problem_category,
                        topic_category=topic_category,
                        problem=problem_content
                    )
                    
                    # 평가 결과 로깅 - 로그에서 확인할 수 있도록
                    logger.info(f"평가 결과: {evaluation_result}")
                    
                    # 결과 검증 - None이나 빈 딕셔너리면 기본값 적용
                    if not evaluation_result or not isinstance(evaluation_result, dict):
                        logger.warning(f"평가 결과가 유효하지 않습니다: {evaluation_result}")
                        evaluation_result = {
                            "score": "IL",
                            "feedback": {
                                "paragraph": "평가를 완료했으나 결과 형식이 올바르지 않습니다.",
                                "vocabulary": "기본 어휘력 평가입니다.",
                                "delivery": "기본 전달력 평가입니다."
                            }
                        }
                    
                    # 성공적으로 결과를 얻었으면 반복 종료
                    break
                    
                except Exception as e:
                    retry_count += 1
                    last_error = e
                    error_msg = str(e).lower()
                    
                    # API 할당량 초과 관련 오류인 경우
                    if any(term in error_msg for term in ["quota", "429", "rate limit", "exceeded"]):
                        logger.warning(f"API 할당량 오류 발생 ({retry_count}/{max_retries}): {error_msg}")
                        # 다음 시도 전에 잠시 대기
                        time.sleep(2 * retry_count)  # 점점 더 긴 대기 시간
                    else:
                        logger.error(f"평가 중 오류 발생 ({retry_count}/{max_retries}): {error_msg}")
                        time.sleep(1)
                    
                    # 마지막 시도에서도 실패한 경우
                    if retry_count >= max_retries:
                        logger.error(f"최대 재시도 횟수에 도달했습니다: {error_msg}")
                        evaluation_result = {
                            "score": "ERROR",
                            "feedback": {
                                "paragraph": f"평가 중 오류가 발생했습니다: {str(last_error)}",
                                "vocabulary": "평가를 완료할 수 없습니다.",
                                "delivery": "평가를 완료할 수 없습니다."
                            },
                            "error": str(last_error)
                        }
        
        # 점수와 피드백 추출 - 더 안전한 방식으로
        score = evaluation_result.get("score", None)
        feedback = evaluation_result.get("feedback", {})
        if not isinstance(feedback, dict):
            feedback = {
                "paragraph": "피드백 형식이 올바르지 않습니다.",
                "vocabulary": "피드백 형식이 올바르지 않습니다.",
                "delivery": "피드백 형식이 올바르지 않습니다."
            }
        
        
        # 8. 테스트 문서 내 해당 문제의 평가 결과 업데이트
        db.tests.update_one(
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
        
        # 9. 마지막 문제인 경우 종합 평가를 위한 새 작업 실행
        if is_last_problem:
            evaluate_overall_test_task.delay(test_id)
            
        return {
            "status": "success",
            "test_id": test_id,
            "problem_id": problem_id,
            "score": score
        }
            
    except Exception as e:
        logger.error(f"오디오 처리 및 평가 중 오류: {str(e)}", exc_info=True)
        
        try:
            db = get_mongodb_sync()
            
            # 오류 발생 시 상태 업데이트
            db.tests.update_one(
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
                db.tests.update_one(
                    {"_id": ObjectId(test_id)},
                    {"$set": {
                        "overall_feedback_status": "failed",
                        "overall_feedback_message": f"전체 평가 중 오류가 발생했습니다: {str(e)}",
                        "overall_feedback_completed_at": datetime.now()
                    }}
                )
                
            # 오류 로깅
            db.errors.insert_one({
                "test_id": test_id,
                "problem_id": problem_id,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now(),
                "source": "process_audio_task"
            })
        except Exception as inner_error:
            logger.error(f"오류 상태 업데이트 중 추가 오류: {str(inner_error)}", exc_info=True)
            
        # 작업 실패 표시
        return {
            "status": "error",
            "test_id": test_id,
            "problem_id": problem_id,
            "error": str(e)
        }

@shared_task(bind=True, name="evaluate_overall_test")
def evaluate_overall_test_task(self, test_id):
    """전체 테스트 종합 평가 Celery 작업"""
    from services.evaluator import ResponseEvaluator

    try:
        db = get_mongodb_sync()

        # 1. 상태 초기화
        db.tests.update_one(
            {"_id": ObjectId(test_id)},
            {"$set": {
                "overall_feedback_status": "processing",
                "overall_feedback_message": "전체 테스트 평가 중입니다."
            }}
        )

        # 2. 테스트 조회
        test = db.tests.find_one({"_id": ObjectId(test_id)})

        # 로깅 추가: 테스트 데이터 구조 확인
        logger.info(f"테스트 데이터 구조: {test}")

        if not isinstance(test, dict):
            raise ValueError(f"테스트 ID {test_id}에 해당하는 테스트를 찾을 수 없습니다.")

        user_id = test.get("user_id")
        if not user_id or not isinstance(user_id, (str, ObjectId)):
            raise ValueError(f"테스트 ID {test_id}에 연결된 사용자 ID가 없습니다.")

        # 3. 문제별 상세 정보 수집
        problem_details = {}
        problem_data_raw = test.get("problem_data", {})
        if not isinstance(problem_data_raw, dict):
            raise ValueError("problem_data 필드가 올바르지 않습니다.")

        for problem_number, problem_data in problem_data_raw.items():
            problem_details[problem_number] = problem_data

        logger.info(f"전체 테스트 종합 평가 시작 - 문제 수: {len(problem_details)}")

        # 4. 평가기 생성 및 종합 평가 실행 - 재시도 로직 추가
        evaluator = ResponseEvaluator()

        # 최대 5번까지 재시도
        retry_count = 0
        max_retries = 5
        last_error = None

        while retry_count < max_retries:
            try:
                evaluation_result = evaluator.evaluate_overall_test_sync(test, problem_details)
                
                # 결과 로깅
                logger.info(f"종합 평가 결과: {evaluation_result}")
                
                # 결과 검증
                if not evaluation_result or not isinstance(evaluation_result, dict):
                    logger.warning("종합 평가 결과가 유효하지 않습니다")
                    evaluation_result = {
                        "test_score": {
                            "total_score": "IM2",
                            "comboset_score": "IM2",
                            "roleplaying_score": "IM2",
                            "unexpected_score": "IM2"
                        },
                        "test_feedback": {
                            "total_feedback": "평가 결과 형식이 올바르지 않아 기본 피드백을 제공합니다.",
                            "paragraph": "문단 구성력 평가를 완료할 수 없습니다.",
                            "vocabulary": "어휘력 평가를 완료할 수 없습니다.",
                            "delivery": "전달력 평가를 완료할 수 없습니다."
                        }
                    }
                
                # 성공적으로 결과를 얻었으면 반복 종료
                break
                
            except Exception as e:
                retry_count += 1
                last_error = e
                error_msg = str(e).lower()
                
                # API 할당량 초과 관련 오류인 경우
                if any(term in error_msg for term in ["quota", "429", "rate limit", "exceeded"]):
                    logger.warning(f"API 할당량 오류 발생 ({retry_count}/{max_retries}): {error_msg}")
                    # 다음 시도 전에 잠시 대기
                    time.sleep(2 * retry_count)  # 점점 더 긴 대기 시간
                else:
                    logger.error(f"종합 평가 중 오류 발생 ({retry_count}/{max_retries}): {error_msg}")
                    time.sleep(1)
                
                # 마지막 시도에서도 실패한 경우
                if retry_count >= max_retries:
                    logger.error(f"최대 재시도 횟수에 도달했습니다: {error_msg}")
                    raise ValueError(f"종합 평가 중 오류가 발생했습니다: {str(last_error)}")

        # 5. 점수 및 피드백 업데이트
        db.tests.update_one(
            {"_id": ObjectId(test_id)},
            {"$set": {
                "test_score": evaluation_result.get("test_score", {}),
                "test_feedback": evaluation_result.get("test_feedback", {}),
                "overall_feedback_status": "completed",
                "overall_feedback_message": "전체 테스트 평가가 완료되었습니다.",
                "overall_feedback_completed_at": datetime.now()
            }}
        )

        test_type_str = test.get("test_type_str", "N/A")
        logger.info(f"테스트 {test_type_str}의 종합 평가가 완료되었습니다.")

        # 6. 평균 점수 업데이트
        update_user_average_score_task.delay(str(user_id))

        return {
            "status": "success",
            "test_id": test_id
        }

    except Exception as e:
        logger.error(f"종합 평가 중 오류: {str(e)}", exc_info=True)
        try:
            db = get_mongodb_sync()
            db.tests.update_one(
                {"_id": ObjectId(test_id)},
                {"$set": {
                    "overall_feedback_status": "failed",
                    "overall_feedback_message": f"전체 평가 중 오류가 발생했습니다: {str(e)}",
                    "overall_feedback_completed_at": datetime.now()
                }}
            )
            db.errors.insert_one({
                "test_id": test_id,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now(),
                "source": "evaluate_overall_test_task"
            })
        except Exception as inner_error:
            logger.error(f"오류 상태 업데이트 중 추가 오류: {str(inner_error)}", exc_info=True)

        return {
            "status": "error",
            "test_id": test_id,
            "error": str(e)
        }



@shared_task(bind=True, name="update_user_average_score")
def update_user_average_score_task(self, user_id):
    """사용자 평균 점수 업데이트 Celery 작업"""
    try:
        from db.mongodb import get_mongodb_sync
        db = get_mongodb_sync()

        OPIC_LEVELS = ["NL", "NM", "NH", "IL", "IM1", "IM2", "IM3", "IH", "AL"]

        try:
            user_obj_id = ObjectId(user_id)
        except Exception:
            raise ValueError(f"잘못된 사용자 ID 형식입니다: {user_id}")

        user_tests = list(db.tests.find(
            {"user_id": user_id, "test_score.total_score": {"$exists": True}}
        ))

        all_test_scores = {
            "total_score": [],
            "comboset_score": [],
            "roleplaying_score": [],
            "unexpected_score": []
        }

        for test_doc in user_tests:
            test_score = test_doc.get("test_score", {})
            for category in all_test_scores.keys():
                score = test_score.get(category)
                if score and score != "N/A" and score in OPIC_LEVELS:
                    all_test_scores[category].append(score)

        user_average_scores = {}
        for category, scores in all_test_scores.items():
            if not scores:
                user_average_scores[category] = None
                continue

            level_values = [OPIC_LEVELS.index(level) for level in scores if level in OPIC_LEVELS]
            if not level_values:
                user_average_scores[category] = None
                continue

            average_value = sum(level_values) / len(level_values)
            closest_index = round(average_value)
            closest_index = max(0, min(closest_index, len(OPIC_LEVELS) - 1))
            user_average_scores[category] = OPIC_LEVELS[closest_index]

        db.users.update_one(
            {"_id": user_obj_id},
            {"$set": {
                "average_score": user_average_scores
            }}
        )

        logger.info(f"사용자 {user_id}의 평균 점수가 업데이트되었습니다: {user_average_scores}")

        return {
            "status": "success",
            "user_id": user_id,
            "average_scores": user_average_scores
        }

    except Exception as e:
        logger.error(f"평균 점수 업데이트 중 오류: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "user_id": user_id,
            "error": str(e)
        }
