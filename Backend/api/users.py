from fastapi import APIRouter, HTTPException, status, Query, Path, Body, Depends, Response
from typing import List, Optional
from schemas.user import UserCreate, UserResponse, UserUpdate, UserDetailResponse, UserUpdateSchema
from motor.motor_asyncio import AsyncIOMotorDatabase as Database
from db.mongodb import get_mongodb

from services import user as user_service
from services import test_service
from bson import ObjectId
from datetime import datetime, timezone, date
from fastapi.responses import JSONResponse

from models.user import User
from api.deps import get_current_user

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate = Body(...), db = Depends(get_mongodb)):
    """새 사용자를 생성합니다."""
    try:
        # 현재 시간 설정 (UTC 시간대 없이)
        current_time = datetime.now().replace(tzinfo=None)
        
        # 백그라운드 서베이 데이터 처리 - dict로 변환
        if user_data.background_survey:
            background_survey = {
                "profession": user_data.background_survey.profession,
                "is_student": user_data.background_survey.is_student,
                "studied_lecture": user_data.background_survey.studied_lecture,
                "living_place": user_data.background_survey.living_place,
                "info": user_data.background_survey.info if user_data.background_survey.info else []
            }
        else:
            background_survey = {
                "profession": 0,
                "is_student": False,
                "studied_lecture": 0,
                "living_place": 0,
                "info": []
            }
        
        # 평균 점수 초기화
        average_score = {
            "total_score": None,
            "comboset_score": None,
            "roleplaying_score": None,
            "unexpected_score": None
        }
        
        # 테스트 제한 설정
        limits = {
            "test_count": 0,
            "categorical_test_count": 0,
            "random_problem": 0,
            "script_count": 0
        }
        
        # 날짜 데이터 처리 - MongoDB에 저장 가능한 형식으로 변환
        target_exam_date = None
        if user_data.target_exam_date:
            # datetime으로 변환
            if isinstance(user_data.target_exam_date, date):
                target_exam_date = datetime.combine(user_data.target_exam_date, datetime.min.time())
            else:
                target_exam_date = user_data.target_exam_date.replace(tzinfo=None)
        
        # 새 사용자 생성 - 모든 필드가 MongoDB에 저장 가능한지 확인
        new_user = {
            "name": user_data.name,
            "auth_provider": user_data.auth_provider,
            "email": user_data.email,
            "provider_id": getattr(user_data, "provider_id", None),
            "profile_image": getattr(user_data, "profile_image", None),
            "current_opic_score": user_data.current_opic_score,
            "target_opic_score": user_data.target_opic_score,
            "target_exam_date": target_exam_date,
            "is_onboarded": getattr(user_data, "is_onboarded", False),
            "created_at": current_time,
            "updated_at": current_time,
            "background_survey": background_survey,
            "average_score": average_score,
            "limits": limits
        }
        
        # MongoDB에 사용자 추가
        print("Inserting user document:", new_user)  # 로깅 추가
        result = await db.users.insert_one(new_user)
        
        # 삽입된 ID로 전체 문서 검색
        user = await db.users.find_one({"_id": result.inserted_id})
        
        # 사용자가 생성되지 않은 경우 오류 발생
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="사용자 생성에 실패했습니다."
            )
        
        # MongoDB ObjectId를 문자열로 변환
        user["_id"] = str(user["_id"])
        
        return user
        
    except Exception as e:
        print(f"사용자 생성 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 생성 중 오류가 발생했습니다: {str(e)}"
        )



@router.get("/me", response_model=UserDetailResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db = Depends(get_mongodb)
):
    """
    현재 로그인한 사용자의 프로필 정보를 조회 (최근 7개의 테스트 정보 포함)
    토큰 인증 방식으로 사용자를 식별하여 별도의 user_id 파라미터가 필요하지 않습니다.
    """
    # 토큰에서 얻은 사용자 ID 활용
    user_id = str(current_user.id)
    
    # 최근 7개의 테스트 정보 조회
    test_info = await test_service.get_test_by_user_id(db, user_id)
    
    # 현재 사용자 정보를 딕셔너리로 변환
    user_dict = current_user.model_dump(by_alias=True)
    
    # 테스트 정보 추가
    if test_info:
        user_dict["test"] = test_info
    
    # 명시적으로 모델로 변환 후 리턴
    return UserDetailResponse.model_validate(user_dict)


@router.put("/", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user_info(
    user_data: UserUpdateSchema = Body(..., description="업데이트할 사용자 정보"), 
    current_user: User = Depends(get_current_user),
    db = Depends(get_mongodb)
):
    """
    현재 로그인한 사용자 정보를 업데이트합니다 (PUT 메서드 사용).
    """
    print(f"PUT /api/users/ 호출됨 - 사용자 정보 업데이트 요청: {user_data}")
    
    # 현재 인증된 사용자 ID 사용
    user_id = str(current_user.id)
    try:
        user_object_id = ObjectId(user_id)
    except Exception as e:
        print(f"ObjectId 변환 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 사용자 ID 형식입니다."
        )
    
    # 사용자 존재 여부 확인
    existing_user = await db.users.find_one({"_id": user_object_id})
    if not existing_user:
        print(f"사용자를 찾을 수 없음: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {user_id}인 사용자를 찾을 수 없습니다."
        )
    
    # 업데이트할 데이터 준비
    update_data = {}
    
    # 제공된 필드만 업데이트
    if user_data.target_opic_score is not None:
        update_data["target_opic_score"] = user_data.target_opic_score
        
    if user_data.current_opic_score is not None:
        update_data["current_opic_score"] = user_data.current_opic_score
        
    if user_data.target_exam_date is not None:
        # date 객체를 datetime 객체로 변환
        target_date = user_data.target_exam_date
        target_datetime = datetime.combine(target_date, datetime.min.time())
        update_data["target_exam_date"] = target_datetime

    # is_onboarded 필드 처리
    if user_data.is_onboarded is not None:
        update_data["is_onboarded"] = user_data.is_onboarded
        
    if user_data.background_survey is not None:
        # 기존 background_survey 가져오기
        existing_survey = existing_user.get("background_survey", {})
        
        # 새로운 데이터를 병합 (제공된 필드만 업데이트)
        survey_data = user_data.background_survey.model_dump() if hasattr(user_data.background_survey, 'model_dump') else user_data.background_survey
        
        # 기존 데이터와 새 데이터 병합
        merged_survey = {**existing_survey, **survey_data}
        update_data["background_survey"] = merged_survey
    
    # 업데이트 시간 추가
    update_data["updated_at"] = datetime.now()
    
    try:
        # 사용자 정보 업데이트
        print(f"사용자 정보 업데이트 시도: {update_data}")
        result = await db.users.update_one(
            {"_id": user_object_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            if result.matched_count > 0:
                print("사용자 정보가 이미 최신 상태입니다.")
            else:
                print(f"사용자를 찾을 수 없음: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="사용자를 찾을 수 없습니다."
                )
        else:
            print(f"사용자 정보 업데이트 성공: {result.modified_count}개 수정됨")
        
        # 업데이트된 사용자 정보 조회
        updated_user = await db.users.find_one({"_id": user_object_id})
        
        # MongoDB 문서를 API 응답 형식으로 변환
        response_data = dict(updated_user)
        response_data["id"] = str(updated_user["_id"])  # _id를 id로 변환
        del response_data["_id"]  # 원래의 _id 필드 제거
        
        return response_data
        
    except Exception as e:
        logger.error(f"사용자 정보 수정 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 정보 수정 중 오류가 발생했습니다: {str(e)}"
        )

@router.put("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user_info(
    user_data: UserUpdateSchema = Body(..., description="업데이트할 사용자 정보"), 
    current_user: User = Depends(get_current_user),
    db = Depends(get_mongodb)
):
    """
    현재 로그인한 사용자 정보를 업데이트합니다 (PUT 메서드 사용).
    """
    print(f"PUT /api/users/ 호출됨 - 사용자 정보 업데이트 요청: {user_data}")
    
    # 현재 인증된 사용자 ID 사용
    user_id = str(current_user.id)
    try:
        user_object_id = ObjectId(user_id)
    except Exception as e:
        print(f"ObjectId 변환 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 사용자 ID 형식입니다."
        )
    
    # 사용자 존재 여부 확인
    existing_user = await db.users.find_one({"_id": user_object_id})
    if not existing_user:
        print(f"사용자를 찾을 수 없음: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID {user_id}인 사용자를 찾을 수 없습니다."
        )
    
    # 업데이트할 데이터 준비
    update_data = {}
    
    # 제공된 필드만 업데이트
    if user_data.target_opic_score is not None:
        update_data["target_opic_score"] = user_data.target_opic_score
        
    if user_data.current_opic_score is not None:
        update_data["current_opic_score"] = user_data.current_opic_score
        
    if user_data.target_exam_date is not None:
        # date 객체를 datetime 객체로 변환
        target_date = user_data.target_exam_date
        target_datetime = datetime.combine(target_date, datetime.min.time())
        update_data["target_exam_date"] = target_datetime

    # is_onboarded 필드 처리
    if user_data.is_onboarded is not None:
        update_data["is_onboarded"] = user_data.is_onboarded
        
    if user_data.background_survey is not None:
        # 기존 background_survey 가져오기
        existing_survey = existing_user.get("background_survey", {})
        
        # 새로운 데이터를 병합 (제공된 필드만 업데이트)
        survey_data = user_data.background_survey.model_dump() if hasattr(user_data.background_survey, 'model_dump') else user_data.background_survey
        
        # 기존 데이터와 새 데이터 병합
        merged_survey = {**existing_survey, **survey_data}
        update_data["background_survey"] = merged_survey
    
    # 업데이트 시간 추가
    update_data["updated_at"] = datetime.now()
    
    try:
        # 사용자 정보 업데이트
        print(f"사용자 정보 업데이트 시도: {update_data}")
        result = await db.users.update_one(
            {"_id": user_object_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            if result.matched_count > 0:
                print("사용자 정보가 이미 최신 상태입니다.")
            else:
                print(f"사용자를 찾을 수 없음: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="사용자를 찾을 수 없습니다."
                )
        else:
            print(f"사용자 정보 업데이트 성공: {result.modified_count}개 수정됨")
        
        # 업데이트된 사용자 정보 조회
        updated_user = await db.users.find_one({"_id": user_object_id})
        
        # MongoDB 문서를 API 응답 형식으로 변환
        response_data = dict(updated_user)
        response_data["id"] = str(updated_user["_id"])  # _id를 id로 변환
        del response_data["_id"]  # 원래의 _id 필드 제거
        
        return response_data
        
    except Exception as e:
        logger.error(f"사용자 정보 수정 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 정보 수정 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(current_user: User = Depends(get_current_user)):
    """
    현재 로그인한 사용자 계정 삭제 엔드포인트
    """
    # 현재 인증된 사용자 ID 사용
    user_id = current_user.id
    
    try:
        # ObjectId로 변환
        oid = ObjectId(user_id)
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "유효하지 않은 사용자 ID 형식입니다."}
        )
    
    try:
        # 사용자 삭제
        deleted = await user_service.delete_user(oid)
        
        if not deleted:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": f"사용자를 찾을 수 없습니다."}
            )
        
        # 204 상태 코드로 응답 (No Content)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error(f"사용자 삭제 중 오류 발생: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"사용자 삭제 중 오류가 발생했습니다: {str(e)}"}
        )
