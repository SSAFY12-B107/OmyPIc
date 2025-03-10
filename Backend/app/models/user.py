from sqlalchemy import Column, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from fastapi_users.db import SQLAlchemyUserDatabase

from db.base import Base

class UserModel(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"
    
    name = Column(String(length=100), nullable=False)
    current_opic_score = Column(String(length=10), nullable=True)  # 현재 오픽 성적 (AL, IH, IM3 등)
    target_opic_score = Column(String(length=10), nullable=True)  # 희망 오픽 성적
    target_exam_date = Column(Date, nullable=True)  # 희망 시험 일자
    expected_opic_score = Column(String(length=10), nullable=True)  # 예상 오픽 성적
    auth_provider = Column(String(length=20), nullable=False)  # 'kakao', 'google' 등
    is_onboarded = Column(Boolean, default=False)  # 초기 설문 완료 여부

class SocialAccount(Base):
    __tablename__ = "social_accounts"
    
    id = Column(String, primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(20), nullable=False)  # 'kakao', 'google' 등
    social_id = Column(String(length=100), nullable=False)
    social_email = Column(String(length=320), nullable=False)  # 소셜 계정 이메일
    
    user = relationship("UserModel", backref="social_accounts")