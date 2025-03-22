from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# MongoDB는 SQLAlchemy와 달리 스키마가 자유롭지만,
# Pydantic을 사용하여 데이터 검증을 할 수 있습니다

class MongoDBModel(BaseModel):
    """MongoDB 문서의 기본 모델"""
    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class SampleDocument(MongoDBModel):
    """예시 MongoDB 문서 모델"""
    name: str
    description: Optional[str] = None
    tags: List[str] = []