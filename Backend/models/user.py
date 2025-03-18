from datetime import datetime
from typing import Dict, Optional, List, Any
from datetime import date

class User:
    """
    MongoDB 사용자 모델
    """
    @staticmethod
    def create_user_document(
        user_id: int,
        name: str,
        auth_provider: str = "local",
        current_opic_score: Optional[str] = None,
        target_opic_score: Optional[str] = None,
        target_exam_date: Optional[date] = None,
        is_onboarded: bool = False,
        profession: Optional[int] = None,
        is_student: Optional[bool] = None,
        studied_lecture: Optional[int] = None,
        living_place: Optional[int] = None,
        info: Optional[List[str]] = None
    ) -> Dict:
        """
        새 사용자 문서 생성
        """
        now = datetime.now()
        
        return {
            "user_id": user_id,
            "name": name,
            "auth_provider": auth_provider,
            "current_opic_score": current_opic_score,
            "target_opic_score": target_opic_score,
            "target_exam_date": target_exam_date,
            "is_onboarded": is_onboarded,
            "created_at": now,
            "background_survey": {
                "profession": profession,
                "is_student": is_student,
                "studied_lecture": studied_lecture,
                "living_place": living_place,
                "info": info or []  # info를 background_survey 하위로 이동, 기본값은 빈 리스트
            }
        }