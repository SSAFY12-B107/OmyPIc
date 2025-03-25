"""
사용자 제한을 수동으로 초기화하기 위한 스크립트입니다.
이 스크립트는 테스트나 디버깅 목적으로 사용됩니다.
"""

import asyncio
import sys
import os

# 프로젝트 루트 디렉토리 추가 (실행 환경에 따라 경로 조정 필요)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.mongodb import connect_to_mongo, close_mongo_connection, get_collection
from core.config import settings

async def reset_limits_manually():
    """모든 사용자의 limits 값을 수동으로 초기화합니다."""
    try:
        # MongoDB 연결
        await connect_to_mongo()
        
        # users 컬렉션 가져오기
        users_collection = await get_collection("users")
        
        # 모든 사용자의 limits 필드 초기화
        result = await users_collection.update_many(
            {}, 
            {"$set": {
                "limits.test_count": 0,
                "limits.random_problem": 0, 
                "limits.script_count": 0
            }}
        )
        
        print(f"사용자 제한 초기화 완료: {result.modified_count}명의 사용자 정보가 업데이트되었습니다.")
        
        # MongoDB 연결 종료
        await close_mongo_connection()
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        
if __name__ == "__main__":
    # 비동기 함수 실행
    asyncio.run(reset_limits_manually())