from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import StreamingResponse, RedirectResponse
from typing import Any, Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase as Database
from botocore.exceptions import NoCredentialsError

import io
import uuid
import boto3
import os
from bson import ObjectId
from gtts import gTTS
import random
from datetime import datetime

from core.config import settings

from models.test import TestModel, ProblemDetail

async def create_test(
    db: Database, 
    test_type: int, 
    user_id: str
) -> str:
    """
    테스트 생성 서비스 함수
    - test_type 0: 7문제 (콤보셋 3, 롤플레잉 2, 돌발 2)
    - test_type 1: 15문제 (자기소개 1, 콤보셋 9, 롤플레잉 3, 돌발 2)
    
    Returns:
        str: 생성된 테스트 ID (MongoDB ObjectId 문자열)
    """
    try:
        # 사용자 정보 가져오기
        user_object_id = ObjectId(user_id)
        user = await db.users.find_one({"_id": user_object_id})
        
        if not user:
            raise ValueError(f"사용자 ID {user_id}에 해당하는 사용자를 찾을 수 없습니다.")
        
        # 사용자의 배경 정보 가져오기 (background_survey.info)
        user_topics = user.get("background_survey", {}).get("info", [])
        
        # 테스트 생성 시작
        test_data = TestModel(
            test_type=bool(test_type),  # 0 -> False, 1 -> True
            problem_data={},
            user_id=str(user_object_id),
            test_date=datetime.now()
        )
        
        # 테스트 타입에 따라 문제 생성
        if test_type == 0:
            # 7문제 테스트 생성
            await generate_short_test(db, test_data, user_topics)
        else:
            # 15문제 테스트 생성
            await generate_full_test(db, test_data, user_topics)
        
        # Test 모델을 MongoDB에 저장하기 위해 변환
        data_to_insert = test_data.model_dump(by_alias=True)
        
        # _id 필드가 없거나 None일 경우 제거하여 MongoDB가 자동으로 생성하도록 함
        if "_id" in data_to_insert and data_to_insert["_id"] is None:
            del data_to_insert["_id"]
        
        # 문제 데이터가 비어있는지 확인
        if not data_to_insert.get("problem_data"):
            data_to_insert["problem_data"] = {}
        
        # MongoDB에 테스트 저장
        try:
            result = await db.tests.insert_one(data_to_insert)
            return str(result.inserted_id)
        except Exception as e:
            print(f"MongoDB 저장 중 오류: {str(e)}")
            raise
            
    except Exception as e:
        print(f"테스트 생성 중 오류: {str(e)}")
        raise



async def generate_short_test(db: Database, test_data: TestModel, user_topics: List[str]):
    """7문제 테스트 생성 (콤보셋 3, 롤플레잉 2, 돌발 2)"""
    problem_counter = 1
    used_topics = set()
    used_problem_ids = set()  # 문제 중복 방지를 위한 사용된 문제 ID 집합
    
    print(f"[DEBUG] 콤보셋 문제 생성 시작 - 사용자 주제: {user_topics}")
    
    # 1. 콤보셋 3문제 생성
    # 콤보셋 시작 문제 (묘사 카테고리에서 선택)
    first_combo_problem = await get_first_combo_problem(db, user_topics, used_topics, used_problem_ids)
    if first_combo_problem:
        print(f"[DEBUG] 콤보셋 첫 문제 선택됨: {first_combo_problem.get('_id')} - 카테고리: {first_combo_problem.get('problem_category')}")
        test_data.problem_data[str(problem_counter)] = create_problem_detail(first_combo_problem)
        problem_counter += 1
        used_topic = first_combo_problem.get("topic_category")
        used_topics.add(used_topic)
        used_problem_ids.add(str(first_combo_problem.get('_id')))
        
        # 콤보셋 나머지 2문제 (동일 topic_category에서 랜덤 선택)
        combo_problems = await get_combo_problems(db, used_topic, 2, used_problem_ids)
        print(f"[DEBUG] 콤보셋 추가 문제 {len(combo_problems)}개 선택됨")
        for problem in combo_problems:
            test_data.problem_data[str(problem_counter)] = create_problem_detail(problem)
            problem_counter += 1
            used_problem_ids.add(str(problem.get('_id')))
    else:
        print(f"[WARNING] 콤보셋 첫 문제를 찾지 못함!")
        # 콤보셋을 찾지 못한 경우 - 랜덤한 비롤플레이 문제 3개를 사용
        query = {
            "problem_category": {"$nin": ["롤플레이"]},
            "_id": {"$nin": [ObjectId(id) for id in used_problem_ids if ObjectId.is_valid(id)]}
        }
        random_problems = await db.problems.find(query).limit(3).to_list(length=3)
        for problem in random_problems:
            test_data.problem_data[str(problem_counter)] = create_problem_detail(problem)
            problem_counter += 1
            used_problem_ids.add(str(problem.get('_id')))
            print(f"[DEBUG] 대체 콤보셋 문제 추가: {problem.get('_id')} - {problem.get('problem_category')}")
    
    print(f"[DEBUG] 롤플레이 문제 생성 시작 - 현재 문제 카운터: {problem_counter}")
    
    # 2. 롤플레잉 문제 생성 - 정확히 2문제만
    roleplay_count = 1  # 첫 번째 그룹만 선택
    roleplay_problems = await get_roleplay_problems(db, roleplay_count, used_problem_ids)
    print(f"[DEBUG] 롤플레이 문제 그룹: {len(roleplay_problems)}개 선택됨")
    
    for problem in roleplay_problems:
        # 첫 번째 문제 추가
        test_data.problem_data[str(problem_counter)] = create_problem_detail(problem)
        problem_counter += 1
        used_problem_ids.add(str(problem.get('_id')))
        
        # 그룹 ID가 있으면 두 번째 문제만 추가 (총 2문제)
        if problem.get("problem_group_id"):
            group_id = problem.get("problem_group_id")
            query = {
                "problem_group_id": group_id,
                "problem_order": 2  # 정확히 두 번째 문제만
            }
            next_problem = await db.problems.find_one(query)
            
            if next_problem:
                test_data.problem_data[str(problem_counter)] = create_problem_detail(next_problem)
                problem_counter += 1
                used_problem_ids.add(str(next_problem.get('_id')))
                print(f"[DEBUG] 롤플레이 연속 문제 추가: {next_problem.get('_id')}")
            else:
                print(f"[WARNING] 롤플레이 두 번째 문제를 찾지 못함 (그룹 ID: {group_id})")
    
    print(f"[DEBUG] 돌발 문제 생성 시작 - 현재 문제 카운터: {problem_counter}")
    
    # 3. 돌발 2문제 생성 (롤플레잉 카테고리 제외, 동일 topic_category)
    unexpected_problems = await get_unexpected_problems(db, user_topics, 2, used_problem_ids)
    print(f"[DEBUG] 돌발 문제 {len(unexpected_problems)}개 선택됨")
    for problem in unexpected_problems:
        test_data.problem_data[str(problem_counter)] = create_problem_detail(problem)
        problem_counter += 1
        used_problem_ids.add(str(problem.get('_id')))
        # 문제 topic_category 확인 로깅
        topic = problem.get("topic_category", "없음")
        print(f"[DEBUG] 돌발 문제 추가: {problem.get('_id')} - 주제: {topic}")
    
    print(f"[DEBUG] 테스트 생성 완료 - 총 문제 수: {len(test_data.problem_data)}, 고유 문제 수: {len(used_problem_ids)}")
    # 결과 확인용
    for num, prob in sorted(test_data.problem_data.items(), key=lambda x: int(x[0])):
        print(f"[DEBUG] 문제 {num}: 카테고리 {prob.problem_category}, ID {prob.problem_id}")




async def generate_full_test(db: Database, test_data: TestModel, user_topics: List[str]):
    """15문제 테스트 생성 (자기소개 1, 콤보셋 9, 롤플레잉 3, 돌발 2)"""
    problem_counter = 1
    used_topics = set()  # 콤보 세트 간 중복 방지를 위한 사용된 주제 집합
    used_problem_ids = set()  # 문제 중복 방지를 위한 사용된 문제 ID 집합
    
    print(f"[DEBUG] 15문제 테스트 생성 시작 - 사용자 주제: {user_topics}")
    
    # 1. 자기소개 1문제
    intro_problem = await get_intro_problem(db)
    if intro_problem:
        print(f"[DEBUG] 자기소개 문제 선택됨: {intro_problem.get('_id')}")
        test_data.problem_data[str(problem_counter)] = create_problem_detail(intro_problem)
        problem_counter += 1
        used_problem_ids.add(str(intro_problem.get('_id')))
    else:
        print(f"[WARNING] 자기소개 문제를 찾지 못함!")
    
    # 2. 콤보셋 3세트(각 3문제) = 총 9문제
    for combo_set in range(3):
        print(f"[DEBUG] 콤보셋 {combo_set+1} 생성 시작")
        
        # 콤보셋 시작 문제 - 이전 콤보 세트와 다른 주제를 선택
        first_combo_problem = await get_first_combo_problem(db, user_topics, used_topics, used_problem_ids)
        if first_combo_problem:
            topic_category = first_combo_problem.get("topic_category")
            print(f"[DEBUG] 콤보셋 {combo_set+1} 첫 문제 선택됨: {first_combo_problem.get('_id')} - 주제: {topic_category}")
            test_data.problem_data[str(problem_counter)] = create_problem_detail(first_combo_problem)
            problem_counter += 1
            
            # 선택된 주제를 사용된 주제 집합에 추가 (다음 콤보 세트에서는 다른 주제를 선택하기 위함)
            used_topics.add(topic_category)
            used_problem_ids.add(str(first_combo_problem.get('_id')))
            
            # 콤보셋 나머지 2문제 (동일 topic_category에서 랜덤 선택)
            combo_problems = await get_combo_problems(db, topic_category, 2, used_problem_ids)
            print(f"[DEBUG] 콤보셋 {combo_set+1} 추가 문제 {len(combo_problems)}개 선택됨 - 주제: {topic_category}")
            for problem in combo_problems:
                test_data.problem_data[str(problem_counter)] = create_problem_detail(problem)
                problem_counter += 1
                used_problem_ids.add(str(problem.get('_id')))
        else:
            print(f"[WARNING] 콤보셋 {combo_set+1} 첫 문제를 찾지 못함!")
            # 콤보셋을 찾지 못한 경우 - 비롤플레이 문제 중에서 사용되지 않은 주제 찾기
            unused_topic_query = {
                "problem_category": {"$nin": ["롤플레이"]},
                "topic_category": {"$nin": list(used_topics)},
                "_id": {"$nin": [ObjectId(id) for id in used_problem_ids if ObjectId.is_valid(id)]}
            }
            alternative_problem = await db.problems.find_one(unused_topic_query)
            
            if alternative_problem:
                alt_topic = alternative_problem.get("topic_category")
                print(f"[DEBUG] 대체 콤보셋 주제 발견: {alt_topic}")
                
                # 첫 번째 문제 추가
                test_data.problem_data[str(problem_counter)] = create_problem_detail(alternative_problem)
                problem_counter += 1
                used_problem_ids.add(str(alternative_problem.get('_id')))
                used_topics.add(alt_topic)
                
                # 같은 주제의 추가 문제 2개 찾기
                same_topic_query = {
                    "problem_category": {"$nin": ["롤플레이"]},
                    "topic_category": alt_topic,
                    "_id": {"$nin": [ObjectId(id) for id in used_problem_ids if ObjectId.is_valid(id)]}
                }
                same_topic_problems = await db.problems.find(same_topic_query).limit(2).to_list(length=2)
                
                for problem in same_topic_problems:
                    test_data.problem_data[str(problem_counter)] = create_problem_detail(problem)
                    problem_counter += 1
                    used_problem_ids.add(str(problem.get('_id')))
                    print(f"[DEBUG] 대체 콤보셋 문제 추가: {problem.get('_id')} - 주제: {alt_topic}")
            else:
                # 완전히 다른 주제를 찾을 수 없는 경우 - 그냥 랜덤한 비롤플레이 문제 3개를 사용
                print(f"[WARNING] 대체 콤보셋 주제를 찾지 못함, 랜덤 문제 사용")
                random_query = {
                    "problem_category": {"$nin": ["롤플레이"]},
                    "_id": {"$nin": [ObjectId(id) for id in used_problem_ids if ObjectId.is_valid(id)]}
                }
                random_problems = await db.problems.find(random_query).limit(3).to_list(length=3)
                for problem in random_problems:
                    test_data.problem_data[str(problem_counter)] = create_problem_detail(problem)
                    problem_counter += 1
                    used_problem_ids.add(str(problem.get('_id')))
                    print(f"[DEBUG] 랜덤 대체 문제 추가: {problem.get('_id')} - 주제: {problem.get('topic_category')}")
    
    # 3. 롤플레잉 1세트(3문제)
    print(f"[DEBUG] 롤플레잉 문제 생성 시작 - 현재 문제 카운터: {problem_counter}")
    roleplay_problems = await get_roleplay_problems(db, 1, used_problem_ids)
    print(f"[DEBUG] 롤플레잉 문제 그룹: {len(roleplay_problems)}개 선택됨")
    
    for problem in roleplay_problems:
        # 첫 번째 문제 추가
        test_data.problem_data[str(problem_counter)] = create_problem_detail(problem)
        problem_counter += 1
        used_problem_ids.add(str(problem.get('_id')))
        
        # 그룹 ID가 있으면 두 번째와 세 번째 문제 추가 (총 3문제)
        if problem.get("problem_group_id"):
            group_id = problem.get("problem_group_id")
            
            # 두 번째 문제(order=2) 찾기
            query_2 = {
                "problem_group_id": group_id,
                "problem_order": 2
            }
            second_problem = await db.problems.find_one(query_2)
            
            if second_problem:
                test_data.problem_data[str(problem_counter)] = create_problem_detail(second_problem)
                problem_counter += 1
                used_problem_ids.add(str(second_problem.get('_id')))
                print(f"[DEBUG] 롤플레이 두 번째 문제 추가: {second_problem.get('_id')}")
                
                # 세 번째 문제(order=3) 찾기
                query_3 = {
                    "problem_group_id": group_id,
                    "problem_order": 3
                }
                third_problem = await db.problems.find_one(query_3)
                
                if third_problem:
                    test_data.problem_data[str(problem_counter)] = create_problem_detail(third_problem)
                    problem_counter += 1
                    used_problem_ids.add(str(third_problem.get('_id')))
                    print(f"[DEBUG] 롤플레이 세 번째 문제 추가: {third_problem.get('_id')}")
                else:
                    print(f"[WARNING] 롤플레이 세 번째 문제를 찾지 못함 (그룹 ID: {group_id})")
            else:
                print(f"[WARNING] 롤플레이 두 번째 문제를 찾지 못함 (그룹 ID: {group_id})")
    
    # 4. 돌발 2문제
    print(f"[DEBUG] 돌발 문제 생성 시작 - 현재 문제 카운터: {problem_counter}")
    unexpected_problems = await get_unexpected_problems(db, user_topics, 2, used_problem_ids)
    print(f"[DEBUG] 돌발 문제 {len(unexpected_problems)}개 선택됨")
    for problem in unexpected_problems:
        test_data.problem_data[str(problem_counter)] = create_problem_detail(problem)
        problem_counter += 1
        used_problem_ids.add(str(problem.get('_id')))
        # 문제 topic_category 확인 로깅
        topic = problem.get("topic_category", "없음")
        print(f"[DEBUG] 돌발 문제 추가: {problem.get('_id')} - 주제: {topic}")

    print(f"[DEBUG] 테스트 생성 완료 - 총 문제 수: {len(test_data.problem_data)}, 고유 문제 수: {len(used_problem_ids)}")
    # 결과 확인용
    for num, prob in sorted(test_data.problem_data.items(), key=lambda x: int(x[0])):
        print(f"[DEBUG] 문제 {num}: 카테고리 {prob.problem_category}, ID {prob.problem_id}")



async def get_first_combo_problem(db: Database, user_topics: List[str], used_topics: set, used_problem_ids: set) -> Dict:
    """콤보셋의 첫 번째 문제 가져오기 (주로 묘사 카테고리)"""
    print(f"[DEBUG] 콤보셋 시작 문제 검색 - 유저 주제: {user_topics}, 사용된 주제: {used_topics}")
    
    # 중복 방지를 위한 ObjectId 변환
    excluded_ids = [ObjectId(id) for id in used_problem_ids if ObjectId.is_valid(id)]
    
    query = {
        "problem_category": "묘사",
        "topic_category": {"$in": user_topics, "$nin": list(used_topics)},
        "$or": [
            {"problem_group_id": {"$exists": False}},
            {"problem_order": 1}
        ]
    }
    
    # 중복 방지 조건 추가
    if excluded_ids:
        query["_id"] = {"$nin": excluded_ids}
        
    problems = await db.problems.find(query).to_list(length=10)
    print(f"[DEBUG] 묘사 카테고리 검색 결과: {len(problems)}개 문제 발견")
    
    if problems:
        selected = random.choice(problems)
        print(f"[DEBUG] 선택된 콤보셋 시작 문제: {selected.get('_id')} - 카테고리: {selected.get('problem_category')}")
        return selected
    else:
        print("[ERROR] 콤보셋 시작 문제를 찾을 수 없음!")
        return None
    


async def get_combo_problems(db: Database, topic_category: str, count: int) -> List[Dict]:
    """특정 topic_category에서 추가 콤보 문제 가져오기"""
    query = {
        "problem_category": {"$ne": "롤플레이"},
        "topic_category": topic_category,
        "problem_order": {"$ne": 1}  # 첫 번째 문제가 아닌 경우만
    }
    problems = await db.problems.find(query).to_list(length=count * 2)
    return random.sample(problems, min(count, len(problems)))

async def get_roleplay_problems(db: Database, count: int, used_problem_ids: set = None) -> List[Dict]:
    """롤플레이 문제 가져오기 - 문제 그룹 단위로 선택"""
    print(f"[DEBUG] 롤플레이 문제 검색 시작, 필요 개수: {count}")
    
    # 중복 방지를 위한 ObjectId 변환
    excluded_ids = []
    if used_problem_ids:
        excluded_ids = [ObjectId(id) for id in used_problem_ids if ObjectId.is_valid(id)]
    
    # 롤플레이 첫 번째 문제(problem_order=1) 찾기
    query = {
        "problem_category": "롤플레이",
        "problem_order": 1
    }
    
    # 중복 방지 조건 추가
    if excluded_ids:
        query["_id"] = {"$nin": excluded_ids}
    
    # 롤플레이 시작 문제(order=1) 조회
    roleplay_starters = await db.problems.find(query).to_list(length=count * 3)
    print(f"[DEBUG] 롤플레이 시작 문제: {len(roleplay_starters)}개 발견")
    
    # 필요한 개수만큼 랜덤 선택
    if roleplay_starters:
        selected_starters = random.sample(roleplay_starters, min(count, len(roleplay_starters)))
        return selected_starters
    else:
        print("[DEBUG] 롤플레이 문제를 찾지 못했습니다")
        return []


async def get_unexpected_problems(db: Database, user_topics: List[str], count: int, used_problem_ids: set) -> List[Dict]:
    """돌발 문제 가져오기 (high_grade_kit=true 또는 사용자 관심 영역 외)"""
    print(f"[DEBUG] 돌발 문제 검색 시작, 필요 개수: {count}")
    
    # 중복 방지를 위한 ObjectId 변환
    excluded_ids = [ObjectId(id) for id in used_problem_ids if ObjectId.is_valid(id)]
    
    # 돌발 문제 기본 쿼리 - 롤플레이가 아닌 high_grade_kit 문제 또는 사용자 관심 영역 외 문제
    query = {
        "$or": [
            {"high_grade_kit": True},
            {"topic_category": {"$nin": user_topics}}
        ],
        "problem_category": {"$ne": "롤플레이"}  # 롤플레이가 아닌 문제만
    }
    
    # 중복 방지 조건 추가
    if excluded_ids:
        query["_id"] = {"$nin": excluded_ids}
    
    # 첫 번째 돌발 문제 선택
    first_problems = await db.problems.find(query).to_list(length=10)
    if not first_problems:
        print("[DEBUG] 돌발 문제를 찾지 못했습니다")
        return []
    
    # 첫 번째 문제 랜덤 선택
    first_problem = random.choice(first_problems)
    result = [first_problem]
    
    used_problem_ids.add(str(first_problem["_id"]))
    excluded_ids.append(ObjectId(first_problem["_id"]))
    
    # 첫 번째 문제와 동일한 topic_category에서 나머지 문제 선택
    if count > 1:
        topic_category = first_problem.get("topic_category")
        print(f"[DEBUG] 선택된 돌발 문제 주제: {topic_category}")
        
        # 같은 주제의 추가 문제 쿼리
        same_topic_query = {
            "topic_category": topic_category,
            "problem_category": {"$ne": "롤플레이"},
            "_id": {"$nin": excluded_ids}
        }
        
        same_topic_problems = await db.problems.find(same_topic_query).to_list(length=(count - 1) * 3)
        
        # 같은 주제의 추가 문제가 있으면 선택
        if same_topic_problems:
            additional_problems = random.sample(same_topic_problems, min(count - 1, len(same_topic_problems)))
            result.extend(additional_problems)
            print(f"[DEBUG] 같은 주제({topic_category})에서 추가 돌발 문제 {len(additional_problems)}개 선택됨")
        else:
            # 같은 주제의 문제가 없으면 다른 돌발 문제 선택
            print(f"[DEBUG] 주제({topic_category})에서 추가 문제를 찾지 못함, 다른 돌발 문제를 선택합니다")
            other_problems = await db.problems.find(query).to_list(length=(count - 1) * 3)
            if other_problems:
                # 이미 선택된 문제 제외
                other_problems = [p for p in other_problems if str(p["_id"]) != str(first_problem["_id"])]
                if other_problems:
                    additional_problems = random.sample(other_problems, min(count - 1, len(other_problems)))
                    result.extend(additional_problems)
                    print(f"[DEBUG] 다른 주제에서 추가 돌발 문제 {len(additional_problems)}개 선택됨")
    
    print(f"[DEBUG] 최종 선택된 돌발 문제: {len(result)}개")
    return result


async def get_intro_problem(db: Database) -> Dict:
    """자기소개 문제 가져오기"""
    query = {"topic_category": "자기소개"}
    problem = await db.problems.find_one(query)
    return problem

def create_problem_detail(problem: Dict) -> ProblemDetail:
    """문제 정보를 ProblemDetail 모델로 변환"""
        
    return ProblemDetail(
        problem_id=str(problem.get("_id")),
        problem_category=problem.get("problem_category", "기타"),
        topic_category=problem.get("topic_category", "기타"),
        problem=problem.get("content", "문제 내용 없음"),
        user_response=None,  # 사용자 응답은 아직 없음
        score=None,  # 점수는 아직 없음
        feedback=None  # 피드백은 아직 없음
    )


async def upload_audio_to_s3(audio_data, problem_id):
    """
    오디오 파일을 S3에 업로드하고 URL을 반환합니다.
    
    Args:
        audio_data (bytes): 업로드할 오디오 파일 데이터
        problem_id (str): 문제 ID
        
    Returns:
        str: S3에 업로드된 파일의 URL
    """
    try:
        # 파일명 생성 (문제 ID + 고유 식별자)
        file_name = f"problem_audio/{problem_id}/{uuid.uuid4()}.mp3"
        
        # S3에 업로드
        s3_client.put_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=file_name,
            Body=audio_data,
            ContentType='audio/mpeg'
        )
        
        # S3 URL 생성
        s3_url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{file_name}"
        
        return s3_url
    
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS 자격 증명을 찾을 수 없습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 업로드 중 오류가 발생했습니다: {str(e)}")