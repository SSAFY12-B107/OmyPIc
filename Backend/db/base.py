# 베이스 클래스 임포트
from db.base_class import Base

# 모든 모델 가져오기 (Alembic에서 필요)
from models.user import UserModel, SocialAccount  # noqa
# 다른 모델들도 필요하면 여기에 import