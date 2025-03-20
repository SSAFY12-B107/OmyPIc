from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from fastapi.responses import HTMLResponse, FileResponse
from typing import Any, List, Dict, Optional, Union
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase as Database

from db.mongodb import get_mongodb
from schemas.problem import ProblemResponse, ProblemDetailResponse, BasicQuestionResponse, ScriptUpdateRequest, ScriptResponse

from gtts import gTTS
import os
import base64

router = APIRouter()

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


@router.get("/{problem_id}", response_model=ProblemDetailResponse, status_code=status.HTTP_200_OK)
async def get_problem_detail(
    problem_id: str = Path(..., description="조회할 문제 ID"),
    user_id: Optional[str] = Query(None, description="사용자 ID (제공 시 해당 사용자의 스크립트와 오답노트만 반환)"),
    db: Database = Depends(get_mongodb)
) -> ProblemDetailResponse:
    """
    문제 세부 정보 조회
    - problem_id: 조회할 문제 ID
    - user_id: (선택) 특정 사용자의 스크립트와 오답노트만 반환
    
    반환:
    - 문제 정보
    - 사용자 스크립트 (is_script=true)
    - 모의고사 오답노트 (is_script=false)
    """
    # 1. 문제 정보 조회
    try:
        # ObjectId로 변환 시도
        try:
            object_id = ObjectId(problem_id)
        except:
            # 유효하지 않은 ObjectId인 경우 오류 처리
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"유효하지 않은 문제 ID 형식입니다: {problem_id}"
            )
            
        problem = await db.problems.find_one({"_id": object_id})
        if not problem:
            # 디버깅을 위해 로그 추가
            print(f"문제를 찾을 수 없음: {problem_id}")
            
            # 데이터베이스에 존재하는 문제 ID 확인 (디버깅용)
            sample_problems = await db.problems.find().limit(3).to_list(length=3)
            sample_ids = [str(p.get("_id")) for p in sample_problems]
            print(f"데이터베이스에 존재하는 일부 문제 ID: {sample_ids}")
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID가 {problem_id}인 문제를 찾을 수 없습니다."
            )
        
        # ObjectId를 문자열로 변환
        problem_str_id = str(problem["_id"])
        problem["_id"] = problem_str_id
        
        # 2. 실제 데이터베이스에 저장된 스크립트 조회하기 위한 준비
        
        # 스크립트 쿼리 구성 - 실제 데이터 형식에 맞게 수정
        # 스크립트 예시에 따르면 problem_id 필드에 "string" 값이 들어있으므로 
        # 현재는 이를 기준으로 조회합니다. 추후 실제 problem_id가 저장되도록 수정해야 합니다.
        scripts_query = {}  # 모든 스크립트를 불러오는 것으로 시작
        
        # 특정 사용자의 스크립트만 조회하는 경우
        if user_id:
            scripts_query["user_id"] = user_id
        
        # 3. 사용자 스크립트 및 오답노트 조회 전 전체 스크립트를 불러와서 디버깅
        all_scripts_cursor = db.scripts.find().limit(10)
        all_scripts = await all_scripts_cursor.to_list(length=10)
        
        print(f"데이터베이스에서 찾은 스크립트 예시: {all_scripts}")
        
        # problem_id 필드가 있는지 확인하고 어떤 값이 있는지 확인
        problem_id_values = set()
        for script in all_scripts:
            if "problem_id" in script:
                problem_id_values.add(script["problem_id"])
        
        print(f"스크립트에서 발견된 problem_id 값들: {problem_id_values}")
        
        # 4. 사용자 스크립트 조회 (is_script=true)
        user_scripts_cursor = db.scripts.find({**scripts_query, "is_script": True}).sort("created_at", -1)
        user_scripts = await user_scripts_cursor.to_list(length=100)  # 최대 100개 조회
        
        # 5. 모의고사 오답노트 조회 (is_script=false)
        test_notes_cursor = db.scripts.find({**scripts_query, "is_script": False}).sort("created_at", -1)
        test_notes = await test_notes_cursor.to_list(length=100)  # 최대 100개 조회
        
        # ObjectId를 문자열로 변환
        for script in user_scripts:
            if "_id" in script:
                script["_id"] = str(script["_id"])
        
        for note in test_notes:
            if "_id" in note:
                note["_id"] = str(note["_id"])
        
        # 디버깅용 로그
        print(f"조회된 스크립트 수: {len(user_scripts)}")
        print(f"조회된 오답노트 수: {len(test_notes)}")
        
        # 6. 결과 반환
        return {
            "problem": problem,
            "user_scripts": user_scripts,
            "test_notes": test_notes
        }
        
    except Exception as e:
        # 상세한 오류 메시지 표시
        import traceback
        error_details = traceback.format_exc()
        print(f"오류 상세 정보: {error_details}")
        
        # 유효하지 않은 ObjectId 형식 등의 오류 처리
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"문제 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{problem_pk}/basic-question", response_model=BasicQuestionResponse, status_code=status.HTTP_200_OK)
async def get_basic_questions(
    problem_pk: str = Path(..., description="조회할 문제 ID"),
    db: Database = Depends(get_mongodb)
) -> BasicQuestionResponse:
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

@router.post("/{problem_pk}/custom-quesiton", response_model="", status_code=status.HTTP_201_CREATED)
async def make_custom_questions(
    db: Database = Depends(get_mongodb)
) -> Any:
    """
    스크립트 꼬리 질문 생성
    """
    pass

@router.post("/{problem_pk}/scripts", response_model="", status_code=status.HTTP_201_CREATED)
async def make_script(
    problem: None,
    db: Database = Depends(get_mongodb)
) -> Any:
    """
    스크립트 작성
    """
    pass

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
    스크립트 발음을 TTS로 변환하여 Base64 인코딩된 오디오 데이터 반환

    Args:
        script_pk (str): MongoDB에서 조회할 스크립트의 고유 ID
        db (Database): MongoDB 데이터베이스 연결 세션

    Returns:
        Dict[str, Any]: 다음 키를 포함하는 딕셔너리
        - audio_base64 (str): Base64로 인코딩된 MP3 오디오 데이터
        - audio_type (str): 오디오 파일 유형 (mp3)
        - file_size_bytes (int): 오디오 파일의 바이트 크기
        - file_size_kb (float): 오디오 파일의 킬로바이트 크기

    Raises:
        HTTPException: 
            - 404: 스크립트를 찾을 수 없는 경우
            - 400: 스크립트 내용이 없는 경우
            - 500: 오디오 생성 중 예상치 못한 오류 발생 시
    """
    try:
        # MongoDB에서 스크립트 조회
        script = await db.scripts.find_one({"_id": ObjectId(script_pk)})
        
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
        
        # 스크립트 내용 추출
        script_content = script.get('content', '')
        
        if not script_content:
            raise HTTPException(status_code=400, detail="No content available for TTS")
        
        # 임시 오디오 파일 생성
        tts = gTTS(text=script_content, lang='en')
        temp_audio_path = f"./temp_script_audio_{script_pk}.mp3"
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
        # 오류 처리
        raise HTTPException(status_code=500, detail=f"Error generating script audio: {str(e)}")


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
