from fastapi import APIRouter, HTTPException, Depends, Path, status, Query, Response
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from typing import Any, Dict
from bson import ObjectId, errors as bson_errors
from motor.motor_asyncio import AsyncIOMotorDatabase as Database

from datetime import datetime
from db.mongodb import get_mongodb

import base64
import os
from gtts import gTTS
import io
from gtts import gTTS
from services.s3_service import upload_audio_to_s3

from schemas.test import TestHistoryResponse, TestDetailResponse
from services.test_service import create_test

router = APIRouter()

@router.get("/history/{user_pk}", response_model=TestHistoryResponse)
async def get_test_history(
    user_pk: str,
    db: Database = Depends(get_mongodb)
) -> Any:
    """
    모의고사 히스토리 조회
    """
    try:
        # 사용자 정보 조회
        user = await db.users.find_one({"_id": ObjectId(user_pk)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 사용자를 찾을 수 없습니다."
            )

        # 사용자의 테스트 내역 조회
        tests_cursor = db.tests.find({"user_id": user_pk})
        tests = await tests_cursor.to_list(length=None)

        # 조회된 테스트 데이터 변환
        test_history = []
        for test in tests:
            test_history.append({
                "id": str(test["_id"]),
                "test_date": test["test_date"],
                "test_type": test["test_type"],
                "test_score": test.get("test_score", None)
            })

        # 응답 생성
        response = {
            "average_score": user.get("average_score", None),
            "test_history": test_history
        }

        return response
    except Exception as e:
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"테스트 상세 조회 중 오류 발생: {str(e)}"
        )


@router.post("/{test_type}", response_model=TestDetailResponse)
async def make_test(
    test_type: int = Path(..., ge=0, le=1, description="테스트 유형: 0은 7문제, 1은 15문제"),
    user_id: str = Query(..., description="사용자 ID"),
    db: Database = Depends(get_mongodb)
) -> TestDetailResponse:
    """
    모의고사 생성 API 체크 합니다
    - test_type 0: 7문제 (콤보셋 3, 롤플레잉 2, 돌발 2)
    - test_type 1: 15문제 (자기소개 1, 콤보셋 9, 롤플레잉 3, 돌발 2)
    
    전달받은 사용자의 배경 정보(background_survey.info)를 기반으로
    관심사에 맞는 문제들로 테스트를 구성합니다.
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="사용자 ID가 필요합니다")
    
    try:
        # ObjectId 변환 검증
        ObjectId(user_id)
    except bson_errors.InvalidId:
        raise HTTPException(status_code=400, detail="유효하지 않은 사용자 ID 형식입니다")
    
    # 사용자 존재 여부 확인
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    try:
        # 테스트 서비스 함수 호출
        test_id = await create_test(db, test_type, user_id)
        
        # 생성된 테스트 정보 조회
        test_data = await db.tests.find_one({"_id": ObjectId(test_id)})
        if not test_data:
            raise HTTPException(status_code=404, detail="생성된 테스트를 찾을 수 없습니다")
        
        # ObjectId를 문자열로 변환
        test_data["_id"] = str(test_data["_id"])
        
        # TestDetailResponse 모델로 변환하여 반환
        return TestDetailResponse(**test_data)
    except bson_errors.InvalidId as e:
        # ObjectId 변환 오류
        raise HTTPException(status_code=400, detail=f"잘못된 ID 형식: {str(e)}")
    except Exception as e:
        # 로깅 추가 가능
        import traceback
        print(f"오류 발생: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"테스트 생성 중 오류 발생: {str(e)}")


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
        # 오류 처리
        raise HTTPException(status_code=500, detail=f"Error generating audio: {str(e)}")


@router.get("/{problem_pk}/audio/download")
async def download_problem_audio(
    problem_pk: str = Path(..., description="문제 ID"),
    db: Database = Depends(get_mongodb)
) -> Response:
    """
    문제 ID로 오디오 파일을 직접 다운로드/재생할 수 있는 엔드포인트
    
    Args:
        problem_pk (str): 문제 ID
        db (AsyncIOMotorDatabase): MongoDB 데이터베이스 연결
    
    Returns:
        Response: MP3 오디오 파일 스트림
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
        
        # 파일 스트리밍 응답
        return FileResponse(
            path=temp_audio_path, 
            media_type="audio/mp3", 
            filename=f"problem_{problem_pk}_audio.mp3"
        )
    
    except Exception as e:
        # 오류 처리
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
        # 오류 처리
        raise HTTPException(status_code=500, detail=f"Error generating audio: {str(e)}")


@router.post("/{test_pk}/end")
async def complete_test(
    db: Database = Depends(get_mongodb)
) -> Any:
    """
    시험 완료 - 마지막 문제 완료 또는 40분이 지났을 경우, 완료 처리
    """
    pass
