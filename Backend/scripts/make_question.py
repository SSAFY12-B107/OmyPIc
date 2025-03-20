import pandas as pd
import json
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from bson import ObjectId

async def setup_mongodb():
    client = AsyncIOMotorClient("mongodb+srv://S12P22B107:tgXSWypINd@ssafy.ngivl.mongodb.net/S12P22B107?authSource=admin")
    db = client["S12P22B107"]
    return db

async def process_excel_and_save_questions(file_path):
    db = await setup_mongodb()
    
    # Excel 파일 읽기
    df = pd.read_excel(file_path)
    
    for idx, row in df.iterrows():
        problem_category = row.iloc[0]  # A열을 problem_category로 가정
        content_text = row.iloc[1]      # B열의 content 데이터
        
        try:
            # JSON 형식의 문자열로 되어 있는 경우
            if isinstance(content_text, str):
                # 작은따옴표를 큰따옴표로 변환 (JSON 형식에 맞춤)
                content_text = content_text.replace("'", '"')
                content_list = json.loads(content_text)
            else:
                content_list = []
        except json.JSONDecodeError:
            # JSON 파싱 오류 시 단일 문자열로 처리
            content_list = [content_text] if isinstance(content_text, str) else []
        
        question_data = {
            "problem_category": problem_category,
            "content": content_list
        }
        
        result = await db.questions.insert_one(question_data)
        print(f"질문 ID {result.inserted_id} 저장 완료: {problem_category}")
        print(f"  - 내용: {content_list}")

async def main():
    file_path = "C:/Users/SSAFY/Desktop/pjt2/data/question_data.xlsx"
    await process_excel_and_save_questions(file_path)

if __name__ == "__main__":
    asyncio.run(main())