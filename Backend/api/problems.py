from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from typing import Any, List, Dict, Optional, Union
from bson import ObjectId
from pymongo.database import Database

from db.mongodb import get_mongodb
from schemas.problem import ProblemResponse, ProblemDetailResponse, BasicQuestionResponse, ScriptUpdateRequest, ScriptResponse

router = APIRouter()

@router.get("/", response_model=Dict[str, Union[List[str], List[ProblemResponse]]], status_code=status.HTTP_200_OK)
async def get_problems_by_topics(
    skip: int = Query(0, description="건너뛸 문서 수"),
    limit: int = Query(10, description="각 토픽당 가져올 문서 수", ge=1, le=100),
    db: Database = Depends(get_mongodb)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    문제를 그룹별로 조회합니다
    - topic_group이 빈출/고난도인 경우: 해당 그룹으로 분류
    - topic_group이 null인 경우: problem_category 분류
    - skip: 건너뛸 문서 수
    - limit: 각 토픽당 가져올 최대 문서 수
    """
    # 결과 저장할 딕셔너리
    result = {}

    # 3. topic_group이 null인 문제를 problem_category별로 조회
    categories = [
        "주거", "해외여행", "여행", "음악감상", "술집/바에 가기", "영화보기", 
        "국내여행", "식당/카페 가기", "공연/콘서트보기", "집에서 보내는 휴가", 
        "걷기", "쇼핑하기", "하이킹, 트레킹", "해변 가기", "공원 가기", 
        "캠핑하기", "차 드라이브 하기", "요리하기", "헬스", 
        "혼자 노래 부르거나 합창하기", "자전거"
    ]

    result["카테고리"] = categories
    
    # 1. topic_group이 '빈출'인 문제 조회
    cursor_frequent = db.problems.find({"topic_group": "빈출"}).skip(skip).limit(limit)
    frequent_problems = await cursor_frequent.to_list(length=limit)
    
    # ObjectId를 문자열로 변환
    for problem in frequent_problems:
        problem["_id"] = str(problem["_id"])
    
    result["빈출"] = frequent_problems
    
    # 2. topic_group이 '고난도'인 문제 조회
    cursor_difficult = db.problems.find({"topic_group": "고난도"}).skip(skip).limit(limit)
    difficult_problems = await cursor_difficult.to_list(length=limit)
    
    # ObjectId를 문자열로 변환
    for problem in difficult_problems:
        problem["_id"] = str(problem["_id"])
    
    result["고난도"] = difficult_problems
    
    
    for category in categories:
        cursor = db.problems.find({
            "topic_category": category
        }).skip(skip).limit(limit)
        
        problems = await cursor.to_list(length=limit)
        
        # ObjectId를 문자열로 변환
        for problem in problems:
            problem["_id"] = str(problem["_id"])
        
        # 결과에 추가
        result[category] = problems
    
    return result


@router.get("/{problem_id}", response_model=ProblemDetailResponse, status_code=status.HTTP_200_OK)
async def get_problem_detail(
    problem_id: str = Path(..., description="조회할 문제 ID"),
    user_id: Optional[str] = Query(None, description="사용자 ID (제공 시 해당 사용자의 스크립트와 오답노트만 반환)"),
    db: Database = Depends(get_mongodb)
) -> ProblemDetailResponse:
    """
    문제 세부 정보 조회
    - problem_id: 조회할 문제 ID
    - user_id: (선택) 특정 사용자의 스크립트와 오답노트만 반환
    
    반환:
    - 문제 정보
    - 사용자 스크립트 (is_script=true)
    - 모의고사 오답노트 (is_script=false)
    """
    # 1. 문제 정보 조회
    try:
        problem = await db.problems.find_one({"_id": ObjectId(problem_id)})
        if not problem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID가 {problem_id}인 문제를 찾을 수 없습니다."
            )
        
        # ObjectId를 문자열로 변환
        problem["_id"] = str(problem["_id"])
        
        # 2. 스크립트 쿼리 구성
        scripts_query = {"problem_id": problem_id}
        
        # 특정 사용자의 스크립트만 조회하는 경우
        if user_id:
            scripts_query["user_id"] = user_id
        
        # 3. 사용자 스크립트 조회 (is_script=true)
        user_scripts_cursor = db.scripts.find({**scripts_query, "is_script": True}).sort("created_at", -1)
        user_scripts = await user_scripts_cursor.to_list(length=100)  # 최대 100개 조회
        
        # ObjectId를 문자열로 변환
        for script in user_scripts:
            script["_id"] = str(script["_id"])
        
        # 4. 모의고사 오답노트 조회 (is_script=false)
        test_notes_cursor = db.scripts.find({**scripts_query, "is_script": False}).sort("created_at", -1)
        test_notes = await test_notes_cursor.to_list(length=100)  # 최대 100개 조회
        
        # ObjectId를 문자열로 변환
        for note in test_notes:
            note["_id"] = str(note["_id"])
        
        # 5. 결과 반환
        return {
            "problem": problem,
            "user_scripts": user_scripts,
            "test_notes": test_notes
        }
        
    except Exception as e:
        # 유효하지 않은 ObjectId 형식 등의 오류 처리
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"문제 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{problem_pk}/basic-question", response_model=BasicQuestionResponse, status_code=status.HTTP_200_OK)
async def get_basic_questions(
    problem_pk: str = Path(..., description="조회할 문제 ID"),
    db: Database = Depends(get_mongodb)
) -> BasicQuestionResponse:
    """
    문제에 해당하는 스크립트 기본 질문 조회
    - problem_pk: 조회할 문제 ID
    
    반환:
    - 문제 정보
    - 해당 문제 카테고리에 맞는 기본 질문 목록
    """
    try:
        # 1. 문제 정보 조회
        problem = await db.problems.find_one({"_id": ObjectId(problem_pk)})
        if not problem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID가 {problem_pk}인 문제를 찾을 수 없습니다."
            )
        
        # ObjectId를 문자열로 변환
        problem["_id"] = str(problem["_id"])
        
        # 2. 문제 카테고리 추출
        problem_category = problem.get("problem_category")
        if not problem_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="문제에 카테고리 정보가 없습니다."
            )
        
        # 3. 해당 카테고리에 맞는 질문 조회
        question_doc = await db.questions.find_one({"problem_category": problem_category})
        if not question_doc:
            # 질문이 없는 경우 빈 리스트 반환
            return {
                "questions": []
            }
        
        # 4. 결과 반환
        return {
            "questions": question_doc.get("content", [])
        }
        
    except Exception as e:
        # 유효하지 않은 ObjectId 형식 등의 오류 처리
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"질문 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/{problem_pk}/custom-quesiton", response_model="", status_code=status.HTTP_201_CREATED)
async def make_custom_questions(
    db: Database = Depends(get_mongodb)
) -> Any:
    """
    스크립트 꼬리 질문 생성
    """
    pass

@router.post("/{problem_pk}/scripts", response_model="", status_code=status.HTTP_201_CREATED)
async def make_script(
    problem: None,
    db: Database = Depends(get_mongodb)
) -> Any:
    """
    스크립트 작성
    """
    pass

@router.patch("/scripts/{script_pk}", response_model=ScriptResponse, status_code=status.HTTP_200_OK)
async def update_script(
    script_pk: str = Path(..., description="수정할 스크립트 ID"),
    script_update: ScriptUpdateRequest = Body(...),
    db: Database = Depends(get_mongodb)
) -> Any:
    """
    스크립트 수정 - 스크립트 내용(content)만 수정 가능
    """
    try:
        # 스크립트 조회
        script = await db.scripts.find_one({"_id": ObjectId(script_pk)})
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID가 {script_pk}인 스크립트를 찾을 수 없습니다."
            )
        
        # 내용 업데이트
        update_result = await db.scripts.update_one(
            {"_id": ObjectId(script_pk)},
            {"$set": {"content": script_update.content}}
        )
        
        if update_result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_304_NOT_MODIFIED,
                detail="스크립트 내용이 변경되지 않았습니다."
            )
        
        # 업데이트된 스크립트 조회
        updated_script = await db.scripts.find_one({"_id": ObjectId(script_pk)})
        updated_script["_id"] = str(updated_script["_id"])
        
        return updated_script
        
    except Exception as e:
        if "ObjectId" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"유효하지 않은 스크립트 ID 형식입니다: {script_pk}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"스크립트 수정 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/scripts/{script_pk}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_script(
    script_pk: str = Path(..., description="삭제할 스크립트 ID"),
    db: Database = Depends(get_mongodb)
) -> None:
    """
    스크립트 삭제
    """
    try:
        # 스크립트 조회 (존재 여부 확인)
        script = await db.scripts.find_one({"_id": ObjectId(script_pk)})
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID가 {script_pk}인 스크립트를 찾을 수 없습니다."
            )
        
        # 스크립트 삭제
        delete_result = await db.scripts.delete_one({"_id": ObjectId(script_pk)})
        
        if delete_result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="스크립트 삭제에 실패했습니다."
            )
        
        # 204 No Content 상태 코드로 응답 (반환 데이터 없음)
        return None
        
    except Exception as e:
        if "ObjectId" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"유효하지 않은 스크립트 ID 형식입니다: {script_pk}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"스크립트 삭제 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/scripts/{script_pk}/listen", response_model="", status_code=status.HTTP_201_CREATED)
async def listen_script(
    script_pk: str = Path(..., description="조회할 문제 ID"),
    db: Database = Depends(get_mongodb)
) -> Any:
    """
    스크립트 발음 듣기
    """
    pass

@router.post("/scripts/{script_pk}/record", response_model="", status_code=status.HTTP_201_CREATED)
async def practice_script(
    script_pk: str = Path(..., description="조회할 문제 ID"),
    db: Database = Depends(get_mongodb)
) -> Any:
    """
    스크립트 발음 연습
    """
    pass
