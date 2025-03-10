from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta

# SQLAlchemy 베이스 클래스 설정
Base: DeclarativeMeta = declarative_base()

# 모든 모델 가져오기 (Alembic에서 필요)
from models.user import UserModel, SocialAccount  # noqa