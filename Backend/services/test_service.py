from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import StreamingResponse, RedirectResponse
from motor.motor_asyncio import Database
from bson import ObjectId
from gtts import gTTS
import io
import uuid
import boto3
from botocore.exceptions import NoCredentialsError
import os
from typing import Any

from db.mongodb import get_mongodb
from core.config import settings




async def upload_audio_to_s3(audio_data, problem_id):
    """
    오디오 파일을 S3에 업로드하고 URL을 반환합니다.
    
    Args:
        audio_data (bytes): 업로드할 오디오 파일 데이터
        problem_id (str): 문제 ID
        
    Returns:
        str: S3에 업로드된 파일의 URL
    """
    try:
        # 파일명 생성 (문제 ID + 고유 식별자)
        file_name = f"problem_audio/{problem_id}/{uuid.uuid4()}.mp3"
        
        # S3에 업로드
        s3_client.put_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=file_name,
            Body=audio_data,
            ContentType='audio/mpeg'
        )
        
        # S3 URL 생성
        s3_url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{file_name}"
        
        return s3_url
    
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS 자격 증명을 찾을 수 없습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 업로드 중 오류가 발생했습니다: {str(e)}")