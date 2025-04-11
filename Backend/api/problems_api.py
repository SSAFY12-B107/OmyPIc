from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from fastapi.responses import HTMLResponse, FileResponse
from typing import Any, List, Dict, Optional, Union
from bson import ObjectId, errors as bson_errors
from motor.motor_asyncio import AsyncIOMotorDatabase as Database
from datetime import datetime

from db.mongodb import get_mongodb
from schemas.problem import ProblemResponse, ProblemDetailResponse, QuestionResponse, ScriptUpdateRequest, ScriptResponse, CustomQuestionRequest, ScriptCreationRequest, ScriptCreationResponse, QuestionAnswers, ScriptCreationRequest

from gtts import gTTS
import os
import base64
from api.deps import get_current_user
from models.user import User

import logging
from dotenv import load_dotenv
import httpx

logger = logging.getLogger(__name__)

router = APIRouter()

# .env 파일에서 환경 변수 로드
load_dotenv()


@router.get("/{category}", response_model=List[ProblemResponse], status_code=status.HTTP_200_OK)
async def get_problems_by_category(
    category: str = Path(..., description="검색할 카테고리"),
    skip: int = Query(0, description="건너뛸 문서 수"),
    limit: int = Query(10, description="가져올 문서 수", ge=1, le=100),
    db: Database = Depends(get_mongodb)
) -> List[Dict[str, Any]]:
    """
    특정 카테고리에 해당하는 문제들을 조회합니다.
    
    - "고난도" 카테고리일 경우: topic_category가 국가설명, 산업/회사, 기술인 문제들 조회
    - "빈출" 카테고리일 경우: topic_category가 모임/축하, 예약/약속, 날씨, 재활용, 친구/가족, 은행, 패션인 문제들 조회
    - 그 외 카테고리: 해당 topic_category 값을 가진 문제들 조회
    """
    
    # 검색 조건 설정
    filter_condition = {}
    
    if category == "고난도":
        # 고난도 카테고리에 해당하는 topic_category 값들
        filter_condition = {
            "topic_category": {"$in": ["국가설명", "산업/회사", "기술"]}
        }
    elif category == "빈출":
        # 빈출 카테고리에 해당하는 topic_category 값들
        filter_condition = {
            "topic_category": {"$in": ["모임/축하", "예약/약속", "날씨", "재활용", "친구/가족", "은행", "패션"]}
        }
    else:
        # 그 외 일반 카테고리일 경우 해당 topic_category 값을 직접 검색
        filter_condition = {
            "topic_category": category
        }
    
    # 데이터베이스 쿼리 실행
    cursor = db.problems.find(filter_condition).skip(skip).limit(limit)
    problems = await cursor.to_list(length=limit)
    
    # ObjectId를 문자열로 변환
    for problem in problems:
        problem["_id"] = str(problem["_id"])
    
    return problems
    

@router.get("/detail/{problem_id}", response_model=ProblemDetailResponse, status_code=status.HTTP_200_OK)
async def get_problem_detail(
    problem_id: str = Path(..., description="조회할 문제 ID"),
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_mongodb)
) -> ProblemDetailResponse:
    """문제 세부 정보 조회"""
    
    try:
        # 1. ObjectId 변환 및 문제 조회
        try:
            object_id = ObjectId(problem_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"유효하지 않은 문제 ID 형식입니다: {problem_id}"
            )
            
        problem = await db.problems.find_one({"_id": object_id})
        if not problem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID가 {problem_id}인 문제를 찾을 수 없습니다."
            )
        
        # 2. 현재 사용자 ID로 쿼리 필터 준비
        user_id = str(current_user.id)  # 객체의 속성으로 접근
        query_filter = {
            "problem_id": problem_id,
            "user_id": user_id
        }
            
        # 3. 스크립트와 오답노트 동시 조회 (파이프라인 활용)
        scripts_pipeline = [
            {"$match": query_filter},
            {"$sort": {"created_at": -1}},
            {"$group": {
                "_id": "$is_script",
                "docs": {"$push": "$$ROOT"}
            }},
            {"$project": {
                "is_script": "$_id",
                "docs": {"$slice": ["$docs", 1]}  # 각 그룹에서 최신 1개만
            }}
        ]
        
        scripts_result = await db.scripts.aggregate(scripts_pipeline).to_list(length=None)
        
        # 4. 결과 정리
        user_scripts = []
        test_notes = []
        
        for group in scripts_result:
            if group["docs"]:
                # _id를 문자열로 변환
                for doc in group["docs"]:
                    if "_id" in doc:
                        doc["_id"] = str(doc["_id"])
                
                # 스크립트와 오답노트 구분
                if group["is_script"]:
                    user_scripts = group["docs"]
                else:
                    test_notes = group["docs"]
        
        print(f"Current user: {current_user}")
        print(f"Limits: {current_user.limits}")

        # 5. 스크립트 생성 제한 정보 조회
        # current_user는 User 객체이므로 속성으로 접근
        limits = current_user.limits
        script_count = limits.get("script_count", 0) if limits else 0
        
        script_limit = {
            "used": script_count,
            "limit": 5,  # 최대 제한 값
            "remaining": max(0, 5 - script_count)  # 남은 횟수
        }
        
        # 6. 결과 반환
        return {
            "problem": {
                "_id": str(problem["_id"]),  # 반드시 _id로 반환
                "content": problem.get("content", "")
            },
            "user_scripts": user_scripts,
            "test_notes": test_notes,
            "script_limit": script_limit  # 스크립트 제한 정보 추가
        }
        
    except HTTPException:
        # 이미 처리된 HTTP 예외는 그대로 전달
        raise
    except Exception as e:
        # 기타 예외는 로그로 남기고 400 오류로 처리
        import logging
        logging.error(f"문제 조회 중 오류: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"문제 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{problem_pk}/basic-question", response_model=QuestionResponse, status_code=status.HTTP_200_OK)
async def get_basic_questions(
    problem_pk: str = Path(..., description="조회할 문제 ID"),
    db: Database = Depends(get_mongodb)
) -> QuestionResponse:
    """
    문제에 해당하는 스크립트 기본 질문 조회
    - problem_pk: 조회할 문제 ID
    
    반환:
    - 문제 정보
    - 해당 문제 카테고리에 맞는 기본 질문 목록
    """
    try:
        # 1. 문제 정보 조회
        problem = await db.problems.find_one({"_id": ObjectId(problem_pk)})
        if not problem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID가 {problem_pk}인 문제를 찾을 수 없습니다."
            )
        
        # ObjectId를 문자열로 변환
        problem["_id"] = str(problem["_id"])
        
        # 2. 문제 카테고리 추출
        problem_category = problem.get("problem_category")
        if not problem_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="문제에 카테고리 정보가 없습니다."
            )
        
        # 3. 해당 카테고리에 맞는 질문 조회
        question_doc = await db.questions.find_one({"problem_category": problem_category})
        if not question_doc:
            # 질문이 없는 경우 빈 리스트 반환
            return {
                "questions": []
            }
        
        # 4. 결과 반환
        return {
            "content": problem.get('content',[]),
            "questions": question_doc.get("content", [])
        }
        
    except Exception as e:
        # 유효하지 않은 ObjectId 형식 등의 오류 처리
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"질문 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/{problem_pk}/custom-question", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def make_custom_questions(
    problem_pk: str = Path(..., description="문제 ID"),
    response_data: CustomQuestionRequest = Body(...),
    db: Database = Depends(get_mongodb)
) -> QuestionResponse:
    """
    스크립트 꼬리 질문 생성
    - problem_pk: 문제 ID
    - response_data: 사용자가 작성한 기본 질문 답변
    
    반환:
    - 문제 내용
    - 생성된 꼬리 질문 목록
    """
    try:
        # 1. 문제 정보 조회
        problem = await db.problems.find_one({"_id": ObjectId(problem_pk)})
        if not problem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID가 {problem_pk}인 문제를 찾을 수 없습니다."
            )
        
        # ObjectId를 문자열로 변환
        problem["_id"] = str(problem["_id"])
        
        # 2. 입력 데이터 검증
        if not response_data.question1 and not response_data.question2 and not response_data.question3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="최소한 한 글자는 입력해야 합니다."
            )
        
        # 3. 꼬리 질문 생성 로직 구현 - ai_script 모듈 활용
        try:
            # ai_script 모듈의 generate_follow_up_questions 함수 호출
            from services.ai_script import generate_follow_up_questions, generate_fallback_follow_up_questions
            
            # 사용자 답변 딕셔너리 생성
            answers = {
                "question1": response_data.question1,
                "question2": response_data.question2,
                "question3": response_data.question3
            }
            
            # AI 모델을 사용한 꼬리 질문 생성 시도
            try:
                custom_questions = await generate_follow_up_questions(problem_pk, answers)
            except Exception as ai_error:
                # AI 모델 사용 실패 시 대체 로직 사용
                import logging
                logging.error(f"AI 꼬리 질문 생성 실패: {str(ai_error)}")
                custom_questions = generate_fallback_follow_up_questions(answers)
                
        except ImportError as e:
            # ai_script 모듈 로딩 실패 시 간단한 질문으로 대체
            import logging
            logging.error(f"AI 스크립트 모듈 로딩 실패: {str(e)}")
            
            custom_questions = []
            if response_data.question1:
                custom_questions.append(f"방금 말씀하신 '{response_data.question1.split()[:3]}...'에 대해 좀 더 자세히 설명해 주실 수 있을까요?")
            if response_data.question2:
                custom_questions.append(f"'{response_data.question2.split()[:3]}...'에서 언급하신 부분의 구체적인 예를 들어주실 수 있을까요?")
            if response_data.question3:
                custom_questions.append(f"방금 언급하신 내용 중에서 가장 인상 깊었던 점은 무엇인가요?")
        
        # 4. 결과 반환
        return {
            "content": problem.get('content', ''),
            "questions": custom_questions
        }
        
    except Exception as e:
        # 유효하지 않은 ObjectId 형식 등의 오류 처리
        import logging
        logging.error(f"꼬리 질문 생성 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"꼬리 질문 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/{problem_pk}/scripts", response_model=ScriptCreationResponse, status_code=status.HTTP_201_CREATED)
async def make_script(
    problem_pk: str = Path(..., description="문제 ID"),
    script_data: ScriptCreationRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_mongodb)
) -> ScriptCreationResponse:
    """
    스크립트 작성
    - problem_pk: 문제 ID
    - script_data: 스크립트 생성 요청 데이터 (type에 따라 필요한 필드가 달라짐)
    
    반환:
    - 생성된 스크립트 정보
    
    제한:
    - 스크립트 생성은 사용자당 최대 5회까지만 가능합니다.
    """
    try:
        # 현재 사용자 정보 사용
        user_id = str(current_user.id)
        
        # 사용자의 스크립트 생성 횟수 확인
        limits = current_user.limits
        script_count = limits.get("script_count", 0) if limits else 0
        
        # 스크립트 생성 제한 확인
        if script_count >= 5:
            raise HTTPException(status_code=403, detail="스크립트 생성은 최대 5회까지만 가능합니다")
        
        # 스크립트 횟수 증가
        script_limit_field = "limits.script_count"
        
        try:
            # 스크립트 생성 카운트 증가
            await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$inc": {script_limit_field: 1}}
            )

            # 1. 문제 정보 조회
            problem = await db.problems.find_one({"_id": ObjectId(problem_pk)})
            if not problem:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"ID가 {problem_pk}인 문제를 찾을 수 없습니다."
                )
            
            # 2. 스크립트 타입에 따른 처리
            script_content = ""
            
            if script_data.type == "basic":
                if not script_data.basic_answers:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="기본 타입 스크립트에는 basic_answers가 필요합니다."
                    )
                    
                # 기본 답변을 사용하여 AI 스크립트 생성
                try:
                    from services.ai_script import generate_opic_script
                    
                    # Pydantic 모델을 딕셔너리로 변환
                    basic_dict = {
                        "answer1": script_data.basic_answers.answer1,
                        "answer2": script_data.basic_answers.answer2,
                        "answer3": script_data.basic_answers.answer3
                    }
                    
                    custom_dict = {}
                    if hasattr(script_data, 'custom_answers') and script_data.custom_answers:
                        custom_dict = {
                            "answer1": script_data.custom_answers.answer1,
                            "answer2": script_data.custom_answers.answer2,
                            "answer3": script_data.custom_answers.answer3
                        }
                    
                    script_content = await generate_opic_script(
                        problem_pk=problem_pk,
                        answers={
                            "basic_answers": basic_dict,
                            "custom_answers": custom_dict
                        }
                    )
                except Exception as e:
                    # AI 스크립트 생성 실패 시 에러 반환
                    logger.error(f"AI 스크립트 생성 실패: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"스크립트 생성에 실패했습니다: {str(e)}"
                    )
                
            elif script_data.type == "custom":
                if not script_data.basic_answers or not script_data.custom_answers:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="커스텀 타입 스크립트에는 basic_answers와 custom_answers가 모두 필요합니다."
                    )
                    
                # 기본 답변과 커스텀 답변을 사용하여 AI 스크립트 생성
                try:
                    from services.ai_script import generate_opic_script
                    
                    # Pydantic 모델을 딕셔너리로 변환
                    basic_dict = {
                        "answer1": script_data.basic_answers.answer1,
                        "answer2": script_data.basic_answers.answer2,
                        "answer3": script_data.basic_answers.answer3
                    }
                    
                    custom_dict = {
                        "answer1": script_data.custom_answers.answer1,
                        "answer2": script_data.custom_answers.answer2,
                        "answer3": script_data.custom_answers.answer3
                    }
                    
                    script_content = await generate_opic_script(
                        problem_pk=problem_pk,
                        answers={
                            "basic_answers": basic_dict, 
                            "custom_answers": custom_dict
                        }
                    )
                except Exception as e:
                    # AI 스크립트 생성 실패 시 에러 반환
                    logger.error(f"AI 스크립트 생성 실패: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"스크립트 생성에 실패했습니다: {str(e)}"
                    )
            
            # 3. 내용이 비어있는지 확인
            if not script_content:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="스크립트 내용이 비어 있습니다."
                )
            
            # 4. 스크립트 저장
            now = datetime.now()
            script_doc = {
                "user_id": user_id,  # 현재 사용자 ID 사용
                "problem_id": problem_pk,
                "content": script_content,
                "created_at": now,
                "is_script": True,
                "script_type": script_data.type
            }
            
            # MongoDB에 저장
            result = await db.scripts.insert_one(script_doc)
            script_id = str(result.inserted_id)
            
            # 5. 저장된 스크립트 반환
            return {
                "_id": script_id,
                "content": script_content,
                "created_at": now,
                "is_script": True,
                "script_type": script_data.type
            }
        
        except HTTPException:
            # 이미 발생한 HTTPException은 그대로 전달
            raise
        except Exception as e:
            # 로깅 추가
            logger.error(f"스크립트 생성 중 오류 발생: {str(e)}", exc_info=True)
            
            # 스크립트 생성이 실패한 경우, 카운트 원복
            try:
                await db.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$inc": {script_limit_field: -1}}
                )
            except Exception as rollback_error:
                logger.error(f"카운트 롤백 중 오류: {str(rollback_error)}")
            
            raise HTTPException(status_code=500, detail=f"스크립트 생성 중 오류 발생: {str(e)}")
    except Exception as e:
        # 최상위 예외 처리
        logger.error(f"요청 처리 중 예외 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"요청 처리 중 오류 발생: {str(e)}")


@router.patch("/scripts/{script_pk}", response_model=ScriptResponse, status_code=status.HTTP_200_OK)
async def update_script(
    script_pk: str = Path(..., description="수정할 스크립트 ID"),
    script_update: ScriptUpdateRequest = Body(...),
    db: Database = Depends(get_mongodb)
) -> Any:
    """
    스크립트 수정 - 스크립트 내용(content)만 수정 가능
    """
    try:
        # 스크립트 조회
        script = await db.scripts.find_one({"_id": ObjectId(script_pk)})
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID가 {script_pk}인 스크립트를 찾을 수 없습니다."
            )
        
        # 내용 업데이트
        update_result = await db.scripts.update_one(
            {"_id": ObjectId(script_pk)},
            {"$set": {"content": script_update.content}}
        )
        
        if update_result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_304_NOT_MODIFIED,
                detail="스크립트 내용이 변경되지 않았습니다."
            )
        
        # 업데이트된 스크립트 조회
        updated_script = await db.scripts.find_one({"_id": ObjectId(script_pk)})
        updated_script["_id"] = str(updated_script["_id"])
        
        return updated_script
        
    except Exception as e:
        if "ObjectId" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"유효하지 않은 스크립트 ID 형식입니다: {script_pk}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"스크립트 수정 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/scripts/{script_pk}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_script(
    script_pk: str = Path(..., description="삭제할 스크립트 ID"),
    db: Database = Depends(get_mongodb)
) -> None:
    """
    스크립트 삭제
    """
    try:
        # 스크립트 조회 (존재 여부 확인)
        script = await db.scripts.find_one({"_id": ObjectId(script_pk)})
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID가 {script_pk}인 스크립트를 찾을 수 없습니다."
            )
        
        # 스크립트 삭제
        delete_result = await db.scripts.delete_one({"_id": ObjectId(script_pk)})
        
        if delete_result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="스크립트 삭제에 실패했습니다."
            )
        
        # 204 No Content 상태 코드로 응답 (반환 데이터 없음)
        return None
        
    except Exception as e:
        if "ObjectId" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"유효하지 않은 스크립트 ID 형식입니다: {script_pk}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"스크립트 삭제 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/scripts/{script_pk}/audio", status_code=status.HTTP_200_OK)
async def listen_script(
    script_pk: str = Path(..., description="조회할 스크립트 ID"),
    db: Database = Depends(get_mongodb)
) -> Dict[str, Any]:
    """
    스크립트 발음을 gtts를 통해 변환하여 Base64 인코딩된 오디오 데이터 반환
    """
    try:
        # MongoDB에서 스크립트 조회
        script = await db.scripts.find_one({"_id": ObjectId(script_pk)})
        
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
        
        # 스크립트 내용 추출
        script_content = script.get('content', '')
        logger.debug(f"스크립트 내용 길이: {len(script_content)}")
        
        if not script_content:
            raise HTTPException(status_code=400, detail="No content available for TTS")
        
        # HTML 태그 제거 및 텍스트만 추출
        from bs4 import BeautifulSoup
        
        # HTML 파싱
        soup = BeautifulSoup(script_content, 'html.parser')
        
        # 텍스트만 추출 (HTML 태그 제거)
        clean_text = soup.get_text(separator=' ', strip=True)
        
        # 추가적인 텍스트 정리 (여러 공백, 특수 문자 등 처리)
        import re
        clean_text = re.sub(r'\s+', ' ', clean_text)  # 여러 공백을 하나로 치환
        clean_text = clean_text.strip()
        
        # 로깅을 통해 변환 전/후 내용 확인 (디버깅용)
        logger.debug(f"Original content length: {len(script_content)}")
        logger.debug(f"Cleaned text length: {len(clean_text)}")
        
        if not clean_text:
            raise HTTPException(status_code=400, detail="No valid text content after HTML removal")
        
        # gtts를 사용하여 TTS 생성
        import io
        
        # 메모리에 오디오 파일 생성
        tts = gTTS(text=clean_text, lang='en', slow=False)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        # MP3 파일을 Base64로 인코딩
        encoded_audio = base64.b64encode(mp3_fp.read()).decode('utf-8')
        file_size = mp3_fp.getbuffer().nbytes
        
        # 클라이언트에 응답 반환
        return {
            "audio_base64": encoded_audio,
            "audio_type": "audio/mp3",
            "file_size_bytes": file_size,
            "file_size_kb": round(file_size / 1024, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # 자세한 오류 정보 로깅
        logger.error(f"TTS 처리 중 예상치 못한 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"음성 생성 중 오류: {str(e)}")

@router.post("/scripts/{script_pk}/audio", status_code=status.HTTP_200_OK)
async def listen_script_post(
    script_pk: str = Path(..., description="조회할 스크립트 ID"),
    db: Database = Depends(get_mongodb)
) -> Dict[str, Any]:
    # GET 엔드포인트와 동일한 로직 구현
    return await listen_script(script_pk, db)


# 테스트용 라우터
@router.get("/scripts/{script_pk}/preview/play")
async def play_script_preview(
    script_pk: str = Path(..., description="스크립트 ID"),
    db: Database = Depends(get_mongodb)
) -> HTMLResponse:
    """
    브라우저에서 직접 스크립트 프리뷰 오디오를 재생할 수 있는 HTML 페이지 반환

    Args:
        script_pk (str): 스크립트 ID
        db (Database): MongoDB 데이터베이스 연결 세션

    Returns:
        HTMLResponse: 오디오 재생 HTML 페이지
    """
    try:
        # MongoDB에서 스크립트 조회
        script = await db.scripts.find_one({"_id": ObjectId(script_pk)})
        
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
        
        script_content = script.get('content', '')
        
        if not script_content:
            raise HTTPException(status_code=400, detail="No content available for TTS")
        
        # 임시 오디오 파일 생성
        tts = gTTS(text=script_content, lang='en')
        temp_audio_path = f"./temp_script_preview_{script_pk}.mp3"
        tts.save(temp_audio_path)
        
        # HTML 페이지 생성
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Script Preview Audio Playback</title>
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
                <h1>Script Preview Audio Playback</h1>
                <audio controls autoplay style="width: 300px;">
                    <source src="./download" type="audio/mp3">
                    Your browser does not support the audio element.
                </audio>
                <p>스크립트 내용: {script_content}</p>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
    
    except Exception as e:
        # 오류 처리
        raise HTTPException(status_code=500, detail=f"Error generating script preview audio: {str(e)}")

# 테스트용 라우터
@router.get("/scripts/{script_pk}/preview/download")
async def download_script_preview(
    script_pk: str = Path(..., description="스크립트 ID"),
    db: Database = Depends(get_mongodb)
) -> FileResponse:
    """
    스크립트 프리뷰 오디오 파일 다운로드

    Args:
        script_pk (str): 스크립트 ID
        db (Database): MongoDB 데이터베이스 연결 세션

    Returns:
        FileResponse: 오디오 파일 다운로드
    """
    try:
        # MongoDB에서 스크립트 조회
        script = await db.scripts.find_one({"_id": ObjectId(script_pk)})
        
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
        
        script_content = script.get('content', '')
        
        if not script_content:
            raise HTTPException(status_code=400, detail="No content available for TTS")
        
        # 임시 오디오 파일 생성
        tts = gTTS(text=script_content, lang='en')
        temp_audio_path = f"./temp_script_preview_{script_pk}.mp3"
        tts.save(temp_audio_path)
        
        # 파일 다운로드 응답
        return FileResponse(
            path=temp_audio_path, 
            media_type="audio/mp3", 
            filename=f"script_preview_{script_pk}.mp3"
        )
    
    except Exception as e:
        # 오류 처리
        raise HTTPException(status_code=500, detail=f"Error generating script preview audio: {str(e)}")

# 2차 배포 시 기능 추가
@router.post("/scripts/{script_pk}/record", response_model="", status_code=status.HTTP_201_CREATED)
async def practice_script(
    script_pk: str = Path(..., description="조회할 문제 ID"),
    db: Database = Depends(get_mongodb)
) -> Any:
    """
    스크립트 발음 연습
    """
    pass
