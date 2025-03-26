from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from db.mongodb import get_collection
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

async def reset_user_limits():
    """매일 오전 12:00에 모든 사용자의 limits 필드 값을 0으로 초기화합니다."""
    try:
        users_collection = await get_collection("users")
        
        # 모든 사용자의 limits 필드를 초기화
        result = await users_collection.update_many(
            {}, 
            {"$set": {
                "limits.test_count": 0,
                "limits.random_problem": 0,
                "limits.script_count": 0
            }}
        )
        
        logger.info(f"사용자 제한 초기화 완료: {result.modified_count}명의 사용자 정보가 업데이트되었습니다.")
    except Exception as e:
        logger.error(f"사용자 제한 초기화 중 오류 발생: {str(e)}")

def setup_scheduler():
    """스케줄러를 설정하고 시작합니다."""
    scheduler = AsyncIOScheduler()
    
    # 매일 오전 12:00에 실행되는 작업 추가
    scheduler.add_job(
        reset_user_limits,
        CronTrigger(hour=0, minute=0),  # 매일 오전 12시 정각
        id="reset_user_limits",
        name="사용자 제한 초기화",
        replace_existing=True
    )
    
    return scheduler