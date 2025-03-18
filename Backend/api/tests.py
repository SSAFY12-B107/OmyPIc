from bson import ObjectId
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Depends, Path, status
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from db.mongodb import get_mongodb
from pymongo.database import Database
from datetime import datetime
from schemas.test import TestHistoryResponse, TestDetailResponse

from gtts import gTTS
import io
from services.s3_service import upload_audio_to_s3


router = APIRouter()

@router.get("/{user_pk}", response_model=TestHistoryResponse)
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


@router.post("/{test_type}")
async def make_test(
    db: Database = Depends(get_mongodb)
) -> Any:
    """
    모의고사 생성
    """
    pass



@router.get("/{problem_pk}/audio")
async def get_problem_audio(
    problem_pk: str = Path(..., description="문제 ID"),
    db: Database = Depends(get_mongodb)
) -> Dict[str, Any]:
    """
    문제 오디오 URL 제공
    
    지정된 문제 ID에 해당하는 문제의 오디오 URL을 제공합니다.
    오디오 URL이 없으면 생성하여 제공합니다.
    
    Args:
        problem_pk (str): 문제 ID
        db (Database): MongoDB 데이터베이스 연결
        
    Returns:
        JSONResponse: 오디오 URL을 포함한 JSON 응답
    """
    try:
        # ObjectId로 변환하여 문제 조회
        problem_id = ObjectId(problem_pk)
        problem = await db.problems.find_one({"_id": problem_id})
        
        if not problem:
            raise HTTPException(status_code=404, detail="문제를 찾을 수 없습니다.")
        
        # 이미 S3에 저장된 오디오 URL이 있는지 확인
        audio_s3_url = problem.get("audio_s3_url")
        
        # URL이 있으면 해당 URL 반환
        if audio_s3_url:
            return {
                "success": True,
                "audio_url": audio_s3_url,
                "from_cache": True
            }
        
        # 문제 내용 가져오기
        content = problem.get("content", "")
        
        if not content:
            raise HTTPException(status_code=404, detail="문제 내용이 없습니다.")
        
        # gTTS를 사용하여 텍스트를 음성으로 변환
        tts = gTTS(text=content, lang='ko', slow=False)
        
        # 메모리에 음성 파일 저장
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # S3에 업로드
        audio_data = audio_buffer.getvalue()
        s3_url = await upload_audio_to_s3(audio_data, str(problem_id))
        
        # MongoDB에 S3 URL 업데이트
        await db.problems.update_one(
            {"_id": problem_id},
            {"$set": {"audio_s3_url": s3_url}}
        )
        
        # 생성된 URL 반환
        return {
            "success": True,
            "audio_url": s3_url,
            "from_cache": False
        }
    
    except Exception as e:
        # ObjectId 변환 오류 또는 기타 예외 처리
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": f"오류가 발생했습니다: {str(e)}"}
        )


@router.post("/{test_pk}/end")
async def complete_test(
    db: Database = Depends(get_mongodb)
) -> Any:
    """
    시험 완료 - 마지막 문제 완료 또는 40분이 지났을 경우, 완료 처리
    """
    pass
