# Backend/api/deps.py
from fastapi import Depends, HTTPException, status, Cookie, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db.mongodb import get_mongodb
from motor.motor_asyncio import AsyncIOMotorDatabase as Database
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime

import jwt
from models.user import User
from typing import Dict, Any
from services import auth as auth_service
from itertools import cycle
from core.config import settings
import logging
from redis import Redis
import time
import asyncio

redis_client = Redis.from_url(settings.REDIS_URL)

# 전역 변수로 미리 선언
_gemini_key_cycle = None
_groq_key_cycle = None

# API 키 관리를 위한 Lock 객체
_api_key_lock = asyncio.Lock()


# 로거 설정
logger = logging.getLogger(__name__)

# HTTP Bearer 토큰 인증 객체 생성
security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_mongodb)
) -> User:
    """
    프론트엔드에서 전달받은 액세스 토큰으로 현재 사용자 정보를 가져오는 의존성 함수
    """    
    try:
        # 토큰 검증
        payload = jwt.decode(
            credentials.credentials, 
            settings.JWT_SECRET_KEY,
            algorithms=settings.JWT_ALGORITHM
        )
        
        logger.info(f"JWT 페이로드: {payload}")
        
        user_id = payload.get("sub")
        logger.info(f"추출된 사용자 ID: {user_id}, 타입: {type(user_id)}")
        
        if user_id is None:
            logger.warning("토큰에 사용자 ID(sub)가 없습니다")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 인증 정보",
                headers={
                    "WWW-Authenticate": "Bearer",
                    "X-Error-Type": "invalid_payload"  # 오류 유형 식별자
                },
            )
        
        try:
            logger.info(f"ObjectId 변환 시도: {user_id}")
            user_object_id = ObjectId(user_id)
            logger.info(f"ObjectId 변환 성공: {user_id}")
        except Exception as e:
            logger.error(f"ObjectId 변환 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 사용자 ID 형식",
                headers={
                    "WWW-Authenticate": "Bearer",
                    "X-Error-Type": "invalid_user_id_format"  # 오류 유형 식별자
                },
            )
            
        # 사용자 조회
        user = await db.users.find_one({"_id": user_object_id})
        if user is None:
            logger.warning(f"사용자를 찾을 수 없음: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,  # 404 사용
                detail="사용자를 찾을 수 없습니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"User.from_mongo 메서드로 사용자 객체 생성")
        user_obj = User.from_mongo(user)
        logger.info(f"사용자 인증 완료: {user.get('name', '알 수 없음')}")
        return user_obj
        
    except jwt.ExpiredSignatureError:
        # 토큰 만료 처리 - 특별한 헤더로 구분
        logger.warning("JWT 토큰이 만료되었습니다")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 토큰이 만료되었습니다. 리프레시 토큰을 사용하여 갱신하세요.",
            headers={
                "WWW-Authenticate": "Bearer",
                "X-Error-Type": "token_expired"  # 명확한 오류 유형 식별자
            },
        )
    except jwt.InvalidTokenError:
        logger.error("JWT 토큰 검증 실패")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 토큰입니다",
            headers={
                "WWW-Authenticate": "Bearer",
                "X-Error-Type": "invalid_token"  # 오류 유형 식별자
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"인증 과정에서 예상치 못한 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="인증 처리 중 오류가 발생했습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    

async def get_current_user_for_multipart(
    request: Request,
    db: Database = Depends(get_mongodb)
) -> User:
    """파일 업로드 요청에서 사용자 인증을 처리합니다."""
    try:
        # 헤더에서 Authorization 토큰 추출 시도
        auth_header = request.headers.get("Authorization")
        if auth_header:
            # Bearer 토큰 추출
            try:
                scheme, token = auth_header.split()
                if scheme.lower() != "bearer":
                    raise HTTPException(status_code=401, detail="Bearer 형식의 토큰이 필요합니다")
                
                # 토큰 검증
                payload = jwt.decode(
                    token, settings.JWT_SECRET_KEY, algorithms=settings.JWT_ALGORITHM
                )
                user_id = payload.get("sub")
                
                if not user_id:
                    raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")
                
                # 사용자 조회
                user = await db.users.find_one({"_id": ObjectId(user_id)})
                if not user:
                    raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
                
                return User.from_mongo(user)
            except ValueError:
                # Authorization 헤더가 "Bearer 토큰" 형식이 아닌 경우
                raise HTTPException(status_code=401, detail="잘못된 인증 형식입니다")
            except jwt.InvalidTokenError:
                # 토큰 검증 실패
                raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")
        
        # 폼 데이터에서 user_id 추출 시도
        form = await request.form()
        if "user_id" not in form:
            raise HTTPException(status_code=401, detail="인증 정보가 필요합니다")
        
        user_id = form.get("user_id")
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="유효하지 않은 사용자 ID 형식입니다")
        
        # 사용자 조회
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        return User.from_mongo(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"인증 처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=401, detail="인증에 실패했습니다")




async def get_next_gemini_key_async():
    """비동기 버전의 API 키 가져오기 함수"""
    async with _api_key_lock:
        return get_next_gemini_key()

def get_next_gemini_key():
    """다음 Gemini API 키를 반환합니다. Redis 기반 블랙리스트를 통해 할당량 초과된 키 관리."""
    global _gemini_key_cycle
    
    # 모든 키 가져오기
    gemini_keys = settings.gemini_api_keys()
    if not gemini_keys:
        logger.warning("Gemini API 키가 설정되지 않았습니다.")
        return ""
    
    # 초기화가 필요하면 초기화
    if _gemini_key_cycle is None:
        _gemini_key_cycle = cycle(gemini_keys)
    
    # 현재 시간
    current_time = time.time()
    
    # 모든 키 확인 (최대 한 바퀴)
    keys_checked = 0
    total_keys = len(gemini_keys)
    
    while keys_checked < total_keys:
        keys_checked += 1
        key = next(_gemini_key_cycle)
        
        try:
            # Redis에서 블랙리스트 체크
            blacklist_key = f"key_blacklist:gemini:{key}"
            blacklist_until = redis_client.get(blacklist_key)
            
            if blacklist_until:
                blacklist_until = float(blacklist_until)
                if current_time < blacklist_until:
                    # 아직 블랙리스트 시간이 지나지 않음
                    time_left = int(blacklist_until - current_time)
                    logger.debug(f"키 {key[:8]}...는 블랙리스트에 있음 (남은 시간: {time_left}초)")
                    continue
                else:
                    # 블랙리스트 시간 경과, 블랙리스트에서 제거
                    redis_client.delete(blacklist_key)
                    logger.info(f"키 {key[:8]}...의 블랙리스트 시간이 만료되어 다시 사용합니다.")
            
            # 사용량 제한 확인 (선택 사항)
            usage_key = f"key_usage:gemini:{key}"
            usage_count = int(redis_client.get(usage_key) or 0)
            
            # 사용량이 일정 수준 이상이면 다른 키 사용 (선택적으로 적용)
            if usage_count >= 40:  # 시간당 40회로 제한
                logger.debug(f"키 {key[:8]}...의 사용량이 많아 다른 키 시도 (사용량: {usage_count})")
                continue
                
            # 사용 가능한 키 발견
            # 사용량 카운터 증가
            redis_client.incr(usage_key)
            redis_client.expire(usage_key, 3600)  # 1시간 후 리셋
            
            logger.info(f"Gemini API 키 사용: {key[:8]}... (사용량: {usage_count + 1})")
            return key
            
        except Exception as e:
            logger.error(f"Redis에서 키 블랙리스트 확인 중 오류: {str(e)}")
            # Redis 오류 시 그냥 키 반환
            return key
    
    # 모든 키가 블랙리스트에 있는 경우, 블랙리스트 시간이 가장 적게 남은 키 선택
    logger.warning("모든 Gemini API 키가 블랙리스트에 있습니다. 가장 빨리 해제될 키를 선택합니다.")
    
    try:
        earliest_release = float('inf')
        earliest_key = None
        
        for key in gemini_keys:
            blacklist_key = f"key_blacklist:gemini:{key}"
            blacklist_until = redis_client.get(blacklist_key)
            
            if blacklist_until:
                blacklist_until = float(blacklist_until)
                time_left = blacklist_until - current_time
                
                if time_left < earliest_release:
                    earliest_release = time_left
                    earliest_key = key
        
        if earliest_key:
            logger.warning(f"모든 키가 블랙리스트에 있어 {earliest_key[:8]}... 키를 강제로 선택합니다. (블랙리스트 해제까지 {int(earliest_release)}초)")
            return earliest_key
    except Exception as e:
        logger.error(f"최적 키 선택 중 오류: {str(e)}")
    
    # 어떤 키든 반환
    return gemini_keys[0]  # 첫 번째 키 반환

def handle_api_error(key, error_message):
    """API 오류 발생 시 키를 Redis 블랙리스트에 추가"""
    try:
        # 할당량 초과 여부 확인 (더 많은 키워드 추가)
        quota_terms = ["quota", "rate limit", "exceeded", "resource", "429", "limit"]
        quota_exceeded = any(term in error_message.lower() for term in quota_terms)
        
        if quota_exceeded:
            # 할당량 초과 시 30분 동안 블랙리스트에 추가
            blacklist_until = time.time() + 1800  # 30분
            redis_client.set(f"key_blacklist:gemini:{key}", blacklist_until)
            logger.warning(f"Gemini API 키 {key[:8]}...를 할당량 초과로 30분간 블랙리스트에 추가했습니다.")
            
            # 키 개수 로깅
            active_keys = 0
            total_keys = len(settings.gemini_api_keys())
            
            for k in settings.gemini_api_keys():
                if not redis_client.exists(f"key_blacklist:gemini:{k}"):
                    active_keys += 1
            
            logger.warning(f"현재 사용 가능한 키: {active_keys}/{total_keys}")
            
            return True
        return False
    except Exception as e:
        logger.error(f"API 오류 처리 중 예외 발생: {str(e)}")
        return False


        

# API 키 순환자 초기화
# _gemini_key_cycle = None
# _groq_key_cycle = None

# def _init_key_cycles():
#     global _gemini_key_cycle, _groq_key_cycle
    
#     # 메서드 호출하여 실제 리스트 받기
#     gemini_keys = settings.gemini_api_keys()  # 메서드 호출 추가
#     groq_keys = settings.groq_api_keys()      # 메서드 호출 추가
    
#     # 순환자 생성
#     _gemini_key_cycle = cycle(gemini_keys) if gemini_keys else None
#     _groq_key_cycle = cycle(groq_keys) if groq_keys else None

# 초기화는 필요할 때만 - Redis 키 관리 실패 시 폴백으로 사용
# _init_key_cycles()

# Redis 클라이언트 초기화

# def get_next_gemini_key():
#     """다음 Gemini API 키를 반환합니다. Redis 기반 구현."""
#     try:
#         # 모든 키 가져오기
#         keys = settings.gemini_api_keys()
#         if not keys:
#             logger.warning("Gemini API 키가 설정되지 않았습니다.")
#             return ""
        
#         # 가장 적게 사용된 키 선택
#         min_usage_key = None
#         min_usage_count = float('inf')
        
#         for key in keys:
#             # 키 사용량 확인 (Redis에서)
#             usage_count = int(redis_client.get(f"key_usage:gemini:{key}") or 0)
            
#             if usage_count < min_usage_count:
#                 min_usage_count = usage_count
#                 min_usage_key = key
        
#         # 선택된 키 사용량 증가
#         if min_usage_key:
#             redis_client.incr(f"key_usage:gemini:{min_usage_key}")
#             # 만료 시간 설정 (1시간 후 리셋)
#             redis_client.expire(f"key_usage:gemini:{min_usage_key}", 3600)
            
#             # 키 사용 로그
#             logger.debug(f"Gemini API 키 사용: {min_usage_key[:8]}... (사용량: {min_usage_count+1})")
#             return min_usage_key
            
#     except Exception as e:
#         logger.error(f"Redis에서 Gemini API 키 관리 중 오류: {str(e)}")
#         # Redis 오류 시 기존 방식으로 폴백
#         if _gemini_key_cycle is None:
#             _init_key_cycles()
#         return next(_gemini_key_cycle) if _gemini_key_cycle else ""
    
#     # 예상치 못한 경우를 대비한 폴백
#     if _gemini_key_cycle is None:
#         _init_key_cycles()
#     return next(_gemini_key_cycle) if _gemini_key_cycle else ""

def get_next_groq_key():
    """다음 Groq API 키를 반환합니다. Redis 기반 구현."""
    try:
        # 모든 키 가져오기
        keys = settings.groq_api_keys()
        if not keys:
            logger.warning("Groq API 키가 설정되지 않았습니다.")
            return ""
        
        # 가장 적게 사용된 키 선택
        min_usage_key = None
        min_usage_count = float('inf')
        
        for key in keys:
            # 키 사용량 확인 (Redis에서)
            usage_count = int(redis_client.get(f"key_usage:groq:{key}") or 0)
            
            if usage_count < min_usage_count:
                min_usage_count = usage_count
                min_usage_key = key
        
        # 선택된 키 사용량 증가
        if min_usage_key:
            redis_client.incr(f"key_usage:groq:{min_usage_key}")
            # 만료 시간 설정 (1시간 후 리셋)
            redis_client.expire(f"key_usage:groq:{min_usage_key}", 3600)
            
            # 키 사용 로그
            logger.debug(f"Groq API 키 사용: {min_usage_key[:8]}... (사용량: {min_usage_count+1})")
            return min_usage_key
            
    except Exception as e:
        logger.error(f"Redis에서 Groq API 키 관리 중 오류: {str(e)}")
        # Redis 오류 시 기존 방식으로 폴백
        if _groq_key_cycle is None:
            _init_key_cycles()
        return next(_groq_key_cycle) if _groq_key_cycle else ""
    
    # 예상치 못한 경우를 대비한 폴백
    if _groq_key_cycle is None:
        _init_key_cycles()
    return next(_groq_key_cycle) if _groq_key_cycle else ""