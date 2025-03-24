from typing import Any, Annotated
from pydantic import GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from bson import ObjectId

# Pydantic V2 방식으로 ObjectId 처리하기
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> Any:
        from pydantic_core import core_schema
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ]),
        ])
    
    @classmethod
    def validate(cls, value):
        if not ObjectId.is_valid(value):
            raise ValueError("유효하지 않은 ObjectId입니다")
        return ObjectId(value)
    
    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: Any, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {"type": "string"}