# services/test_generator.py
import random
import logging
from typing import Dict, List, Any, Set, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase as Database
from bson import ObjectId
from models.test import TestModel, ProblemDetail, TestTypeEnum
from datetime import datetime

# 로깅 설정
logger = logging.getLogger(__name__)

async def get_random_single_problem(
    db: Database,
    user_id: str
) -> Dict:
    """
    특정 problem_id를 가진 문제 하나만 조회하여 반환합니다. (테스트용)
    선택된 문제를 test 컬렉션에 저장합니다.
    
    Args:
        db: MongoDB 데이터베이스
        user_id: 사용자 ID
        
    Returns:
        Dict: 선택된 문제 정보 (SingleProblemResponse에 사용될 형식)
    """
    logger.info(f"테스트를 위한 고정 문제 선택 - 사용자: {user_id}")
    
    # 사용자 정보 가져오기
    user_object_id = ObjectId(user_id)
    user = await db.users.find_one({"_id": user_object_id})
    
    if not user:
        logger.error(f"사용자 ID {user_id}에 해당하는 사용자를 찾을 수 없습니다.")
        raise ValueError(f"사용자 ID {user_id}에 해당하는 사용자를 찾을 수 없습니다.")
    
    # 테스트용 고정 problem_id (실제 존재하는 ID로 변경해야 함)
    test_problem_id = "67d97ab2361f78766a3c466a"  # 실제 DB에 존재하는 ID로 교체하세요
    
    try:
        # 특정 ID로 문제 조회
        problem = await db.problems.find_one({"_id": ObjectId(test_problem_id)})
        
        if not problem:
            logger.error(f"테스트용 problem_id {test_problem_id}에 해당하는 문제를 찾을 수 없습니다.")
            # 대체 문제 가져오기 - 첫 번째 문제 선택
            problem = await db.problems.find_one()
            
            if not problem:
                logger.error("데이터베이스에 문제가 없습니다.")
                raise ValueError("테스트할 문제를 찾을 수 없습니다.")
        
        problem_id = str(problem["_id"])
        logger.info(f"테스트용 문제 선택됨: {problem_id}")

        # 테스트 데이터 생성
        test_data = TestModel(
            test_type=True,  # 기존 필드: 단일 문제는 Half로 간주
            test_type_str=TestTypeEnum.SINGLE_PROBLEM,  # 새 필드: 명시적으로 SINGLE_PROBLEM으로 설정
            problem_data={
                "1": create_problem_detail(problem)
            },
            user_id=user_id,
            test_date=datetime.now()
        )
        
        # Test 모델을 MongoDB에 저장하기 위해 변환
        data_to_insert = test_data.model_dump(by_alias=True)

        # _id 필드가 없거나 None일 경우 제거하여 MongoDB가 자동으로 생성하도록 함
        if "_id" in data_to_insert and data_to_insert["_id"] is None:
            del data_to_insert["_id"]
        
        # MongoDB에 테스트 저장
        result = await db.tests.insert_one(data_to_insert)
        test_id = str(result.inserted_id)
        logger.info(f"테스트용 문제 테스트 저장 완료 - ID: {test_id}")
        
        # 반환할 문제 데이터 구성
        response_data = {
            "test_id": test_id,
            "problem_id": problem_id,
            "problem_category": problem.get("problem_category", ""),
            "topic_category": problem.get("topic_category", ""),
            "content": problem.get("content", ""),
            "audio_s3_url": problem.get("audio_s3_url", None),
            "high_grade_kit": problem.get("high_grade_kit", False),
            "user_id": user_id
        }
        
        logger.info(f"테스트용 문제 반환 완료: {problem_id}, 카테고리: {problem.get('problem_category', '')}")
        return response_data
        
    except Exception as e:
        logger.error(f"테스트용 문제 조회 중 오류: {str(e)}")
        raise ValueError(f"테스트용 문제 조회 중 오류가 발생했습니다: {str(e)}")

# 원래 로직 (주석 처리)
"""
async def get_random_single_problem_original(
    db: Database,
    user_id: str
) -> Dict:
    logger.info(f"랜덤 단일 문제 선택 - 사용자: {user_id}")
    
    # 사용자 정보 가져오기
    user_object_id = ObjectId(user_id)
    user = await db.users.find_one({"_id": user_object_id})
    
    if not user:
        logger.error(f"사용자 ID {user_id}에 해당하는 사용자를 찾을 수 없습니다.")
        raise ValueError(f"사용자 ID {user_id}에 해당하는 사용자를 찾을 수 없습니다.")
    
    # 사용자의 배경 정보 가져오기
    user_topics = user.get("background_survey", {}).get("info", [])
    logger.info(f"사용자 관심 주제: {user_topics}")
    
    # 사용자 관심 주제가 있으면 해당 주제에서 우선 선택
    pipeline = []
    if user_topics:
        pipeline.append({
            "$match": {
                "topic_category": {"$in": user_topics}
            }
        })
    
    # 랜덤으로 하나의 문제 선택
    pipeline.extend([
        {"$sample": {"size": 1}}
    ])
    
    # 집계 쿼리 실행
    problems = await db.problems.aggregate(pipeline).to_list(length=1)
    
    # 문제가 없으면 모든 문제에서 랜덤으로 하나 선택
    if not problems:
        logger.info("관심 주제에 맞는 문제가 없어 전체 문제에서 랜덤 선택합니다")
        problems = await db.problems.aggregate([
            {"$sample": {"size": 1}}
        ]).to_list(length=1)
    
    # 선택된 문제가 있으면 반환
    if problems:
        problem = problems[0]
        problem_id = str(problem["_id"])

        # 테스트 데이터 생성
        test_data = TestModel(
            test_type=True,  # 기존 필드: 단일 문제는 Half로 간주
            test_type_str=TestTypeEnum.SINGLE_PROBLEM,  # 새 필드: 명시적으로 SINGLE_PROBLEM으로 설정
            problem_data={
                "1": create_problem_detail(problem)
            },
            user_id=user_id,
            test_date=datetime.now()
        )
        
        # Test 모델을 MongoDB에 저장하기 위해 변환
        data_to_insert = test_data.model_dump(by_alias=True)

        # _id 필드가 없거나 None일 경우 제거하여 MongoDB가 자동으로 생성하도록 함
        if "_id" in data_to_insert and data_to_insert["_id"] is None:
            del data_to_insert["_id"]
        
        # MongoDB에 테스트 저장
        try:
            result = await db.tests.insert_one(data_to_insert)
            test_id = str(result.inserted_id)
            logger.info(f"랜덤 단일 문제 테스트 저장 완료 - ID: {test_id}")
        except Exception as e:
            logger.error(f"테스트 저장 중 오류: {str(e)}")
            # 저장 실패해도 문제는 반환
        
        # 반환할 문제 데이터 구성
        response_data = {
            "test_id": str(result.inserted_id),  # 정확히 'test_id'로 키 지정
            "problem_id": problem_id,
            "problem_category": problem.get("problem_category", ""),
            "topic_category": problem.get("topic_category", ""),
            "content": problem.get("content", ""),
            "audio_s3_url": problem.get("audio_s3_url", None),
            "high_grade_kit": problem.get("high_grade_kit", False),
            "user_id": user_id
        }
        
        logger.info(f"랜덤 단일 문제 선택 완료: {problem_id}, 카테고리: {problem.get('problem_category', '')}")
        return response_data
    else:
        logger.warning("선택할 수 있는 문제가 없습니다.")
        raise ValueError("선택할 수 있는 문제가 없습니다.")
"""


async def generate_full_test(db: Database, test_data: TestModel, user_topics: List[str]):
    """
    15문제 테스트 생성 (자기소개 1, 콤보셋 9, 롤플레잉 3, 돌발 2)
    
    그룹 구성:
    - 1번: 자기소개
    - 2~4번: 동일 주제의 콤보셋 1
    - 5~7번: 동일 주제의 콤보셋 2
    - 8~10번: 동일 주제의 콤보셋 3
    - 11~13번: 롤플레잉 (순서 1,2,3)
    - 14~15번: 동일 주제의 돌발 문제
    
    Args:
        db: MongoDB 데이터베이스
        test_data: 테스트 모델 인스턴스
        user_topics: 사용자 관심 주제 목록
    """
    problem_counter = 1
    used_topics = set()  # 콤보 세트 간 중복 방지를 위한 사용된 주제 집합
    used_problem_ids = set()  # 문제 중복 방지를 위한 사용된 문제 ID 집합
    
    logger.info(f"15문제 테스트 생성 시작 - 사용자 주제: {user_topics}")
    
    # 1. 자기소개 1문제
    try:
        intro_problem = await get_intro_problem(db)
        if intro_problem:
            logger.info(f"자기소개 문제 선택: {intro_problem.get('_id')}")
            test_data.problem_data[str(problem_counter)] = create_problem_detail(intro_problem)
            problem_counter += 1
            used_problem_ids.add(str(intro_problem.get('_id')))
        else:
            logger.warning(f"자기소개 문제를 찾지 못함!")
            # 자기소개 문제가 없으면 랜덤 문제로 대체
            await add_random_problems(db, test_data, problem_counter, 1, used_problem_ids)
            problem_counter += 1
    except Exception as e:
        logger.error(f"자기소개 문제 생성 중 오류: {str(e)}", exc_info=True)
        # 오류 발생 시 랜덤 문제로 대체
        await add_random_problems(db, test_data, problem_counter, 1, used_problem_ids)
        problem_counter += 1
    
    # 2. 콤보셋 3세트(각 3문제) = 총 9문제
    for combo_set in range(3):
        try:
            logger.info(f"콤보셋 {combo_set+1} 생성 시작")
            
            # 콤보셋 시작 문제 - 이전 콤보 세트와 다른 주제를 선택
            first_combo_problem = await get_first_combo_problem(db, user_topics, used_topics, used_problem_ids)
            if first_combo_problem:
                topic_category = first_combo_problem.get("topic_category")
                logger.info(f"콤보셋 {combo_set+1} 첫 문제 선택: {first_combo_problem.get('_id')} - 주제: {topic_category}")
                
                test_data.problem_data[str(problem_counter)] = create_problem_detail(first_combo_problem)
                problem_counter += 1
                
                # 선택된 주제를 사용된 주제 집합에 추가 (다음 콤보 세트에서는 다른 주제를 선택하기 위함)
                used_topics.add(topic_category)
                used_problem_ids.add(str(first_combo_problem.get('_id')))
                
                # 콤보셋 나머지 2문제 (동일 topic_category에서 랜덤 선택)
                combo_problems = await get_combo_problems(db, topic_category, 2, used_problem_ids)
                logger.info(f"콤보셋 {combo_set+1} 추가 문제 {len(combo_problems)}개 선택 - 주제: {topic_category}")
                
                for problem in combo_problems:
                    test_data.problem_data[str(problem_counter)] = create_problem_detail(problem)
                    problem_counter += 1
                    used_problem_ids.add(str(problem.get('_id')))
            else:
                logger.warning(f"콤보셋 {combo_set+1} 첫 문제를 찾지 못함!")
                # 랜덤 문제 3개로 대체
                await add_random_problems(db, test_data, problem_counter, 3, used_problem_ids)
                problem_counter += 3
        except Exception as e:
            logger.error(f"콤보셋 {combo_set+1} 생성 중 오류: {str(e)}", exc_info=True)
            # 오류 발생 시 랜덤 문제로 대체
            await add_random_problems(db, test_data, problem_counter, 3, used_problem_ids)
            problem_counter += 3
    
    # 3. 롤플레잉 1세트(3문제)
    try:
        logger.info(f"롤플레잉 문제 생성 시작 - 현재 문제 카운터: {problem_counter}")
        roleplay_groups = await get_roleplay_problems(db, 1, used_problem_ids)
        logger.info(f"롤플레잉 문제 그룹: {len(roleplay_groups)}개 선택")
        
        if roleplay_groups and len(roleplay_groups) > 0:
            # 선택된 그룹의 3개 문제를 순서대로 추가
            group = roleplay_groups[0]
            
            for problem in group:
                test_data.problem_data[str(problem_counter)] = create_problem_detail(problem)
                problem_counter += 1
                used_problem_ids.add(str(problem.get('_id')))
                logger.info(f"롤플레이 문제 추가: 순서 {problem.get('problem_order')}, ID {problem.get('_id')}")
        else:
            logger.warning("롤플레이 문제를 찾지 못함. 랜덤 문제 추가")
            await add_random_problems(db, test_data, problem_counter, 3, used_problem_ids)
            problem_counter += 3
    except Exception as e:
        logger.error(f"롤플레잉 문제 생성 중 오류: {str(e)}", exc_info=True)
        # 오류 발생 시 랜덤 문제로 대체
        await add_random_problems(db, test_data, problem_counter, 3, used_problem_ids)
        problem_counter += 3
    
    # 4. 돌발 2문제 (동일 주제)
    try:
        logger.info(f"돌발 문제 생성 시작 - 현재 문제 카운터: {problem_counter}")
        
        # 랜덤 주제 선택
        random.seed(datetime.now().timestamp())
        
        # 단일 주제를 가진 돌발 문제 그룹 2개 찾기
        topic_unexpected_pipeline = [
            {"$match": {
                "problem_category": {"$ne": "롤플레이"},
                "$or": [
                    {"high_grade_kit": True},
                    {"topic_category": {"$nin": user_topics if user_topics else []}}
                ]
            }},
            {"$group": {
                "_id": "$topic_category",
                "count": {"$sum": 1}
            }},
            {"$match": {
                "count": {"$gte": 2}  # 최소 2개 이상 문제가 있는 주제
            }},
            {"$sample": {"size": 1}}  # 랜덤으로 하나의 주제 선택
        ]
        
        topic_groups = await db.problems.aggregate(topic_unexpected_pipeline).to_list(length=1)
        
        if topic_groups and len(topic_groups) > 0:
            selected_topic = topic_groups[0].get("_id")
            logger.info(f"돌발 문제용 주제 선택됨: {selected_topic}")
            
            # 선택된 주제에서 2개 문제 찾기
            topic_problems_pipeline = [
                {"$match": {
                    "topic_category": selected_topic,
                    "problem_category": {"$ne": "롤플레이"},
                    "_id": {"$nin": [ObjectId(id) for id in used_problem_ids if ObjectId.is_valid(id)]}
                }},
                {"$sample": {"size": 2}}
            ]
            
            unexpected_problems = await db.problems.aggregate(topic_problems_pipeline).to_list(length=2)
            
            if unexpected_problems and len(unexpected_problems) == 2:
                for problem in unexpected_problems:
                    test_data.problem_data[str(problem_counter)] = create_problem_detail(problem)
                    problem_counter += 1
                    used_problem_ids.add(str(problem.get('_id')))
                    logger.info(f"돌발 문제 추가: {problem.get('_id')} - 주제: {selected_topic}")
            else:
                # 기존 방식으로 대체 (주제 동일성 보장 못함)
                logger.warning(f"동일 주제의 돌발 문제 2개를 찾지 못함. 일반 방식으로 대체")
                unexpected_problems = await get_unexpected_problems(db, user_topics, 2, used_problem_ids)
                
                if unexpected_problems:
                    for problem in unexpected_problems:
                        test_data.problem_data[str(problem_counter)] = create_problem_detail(problem)
                        problem_counter += 1
                        used_problem_ids.add(str(problem.get('_id')))
                        topic = problem.get("topic_category", "없음")
                        logger.info(f"돌발 문제 추가: {problem.get('_id')} - 주제: {topic}")
                else:
                    logger.warning("돌발 문제를 찾지 못함. 랜덤 문제 추가")
                    await add_random_problems(db, test_data, problem_counter, 2, used_problem_ids)
                    problem_counter += 2
        else:
            # 기존 방식으로 대체 (주제 동일성 보장 못함)
            logger.warning(f"돌발 문제에 적합한 주제 그룹을 찾지 못함. 일반 방식으로 대체")
            unexpected_problems = await get_unexpected_problems(db, user_topics, 2, used_problem_ids)
            
            if unexpected_problems:
                for problem in unexpected_problems:
                    test_data.problem_data[str(problem_counter)] = create_problem_detail(problem)
                    problem_counter += 1
                    used_problem_ids.add(str(problem.get('_id')))
                    topic = problem.get("topic_category", "없음")
                    logger.info(f"돌발 문제 추가: {problem.get('_id')} - 주제: {topic}")
            else:
                logger.warning("돌발 문제를 찾지 못함. 랜덤 문제 추가")
                await add_random_problems(db, test_data, problem_counter, 2, used_problem_ids)
                problem_counter += 2
    except Exception as e:
        logger.error(f"돌발 문제 생성 중 오류: {str(e)}", exc_info=True)
        # 오류 발생 시 랜덤 문제로 대체
        await add_random_problems(db, test_data, problem_counter, 2, used_problem_ids)
        problem_counter += 2

    logger.info(f"테스트 생성 완료 - 총 문제 수: {len(test_data.problem_data)}, 고유 문제 수: {len(used_problem_ids)}")
    
    # 결과 확인용
    for num, prob in sorted(test_data.problem_data.items(), key=lambda x: int(x[0])):
        logger.info(f"문제 {num}: 카테고리 {prob.problem_category}, ID {prob.problem_id}")


async def generate_comboset_test(db: Database, test_data: TestModel, user_topics: List[str]):
    """
    콤보셋 3문제 테스트 생성
    
    Args:
        db: MongoDB 데이터베이스
        test_data: 테스트 모델 인스턴스
        user_topics: 사용자 관심 주제 목록
    """
    problem_counter = 1
    used_problem_ids = set()  # 문제 중복 방지를 위한 사용된 문제 ID 집합
    
    logger.info(f"콤보셋 3문제 테스트 생성 시작 - 사용자 주제: {user_topics}")
    
    # 콤보셋 시작 문제 선택 (묘사 카테고리에서)
    try:
        first_combo_problem = await get_first_combo_problem(db, user_topics, set(), used_problem_ids)
        
        if first_combo_problem:
            logger.info(f"콤보셋 첫 문제 선택: {first_combo_problem.get('_id')} - {first_combo_problem.get('problem_category')}")
            
            test_data.problem_data[str(problem_counter)] = create_problem_detail(first_combo_problem)
            problem_counter += 1
            used_topic = first_combo_problem.get("topic_category")
            used_problem_ids.add(str(first_combo_problem.get('_id')))
            
            # 콤보셋 나머지 2문제 (동일 topic_category에서 랜덤 선택)
            combo_problems = await get_combo_problems(db, used_topic, 2, used_problem_ids)
            logger.info(f"콤보셋 추가 문제 {len(combo_problems)}개 선택")
            
            for problem in combo_problems:
                test_data.problem_data[str(problem_counter)] = create_problem_detail(problem)
                problem_counter += 1
                used_problem_ids.add(str(problem.get('_id')))
        else:
            logger.warning(f"콤보셋 첫 문제를 찾지 못함. 대체 문제 선택")
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
                logger.info(f"대체 콤보셋 문제 추가: {problem.get('_id')} - {problem.get('problem_category')}")
    
    except Exception as e:
        logger.error(f"콤보셋 문제 생성 중 오류: {str(e)}", exc_info=True)
        # 오류 발생 시 랜덤 문제로 대체
        await add_random_problems(db, test_data, problem_counter, 3, used_problem_ids)
    
    logger.info(f"콤보셋 테스트 생성 완료 - 총 문제 수: {len(test_data.problem_data)}, 고유 문제 수: {len(used_problem_ids)}")
    
    # 문제 번호 순서대로 로깅
    for num, prob in sorted(test_data.problem_data.items(), key=lambda x: int(x[0])):
        logger.info(f"문제 {num}: 카테고리 {prob.problem_category}, ID {prob.problem_id}")

async def generate_roleplay_test(db: Database, test_data: TestModel, user_topics: List[str]):
    """
    롤플레잉 3문제 테스트 생성
    
    Args:
        db: MongoDB 데이터베이스
        test_data: 테스트 모델 인스턴스
        user_topics: 사용자 관심 주제 목록
    """
    problem_counter = 1
    used_problem_ids = set()  # 문제 중복 방지를 위한 사용된 문제 ID 집합
    
    logger.info(f"롤플레잉 테스트 생성 시작 - 사용자 주제: {user_topics}")
    
    try:
        # 한 개의 롤플레이 그룹 가져오기 (각 그룹은 3개의 문제로 구성)
        roleplay_groups = await get_roleplay_problems(db, 1, used_problem_ids)
        logger.info(f"롤플레이 문제 그룹: {len(roleplay_groups)}개 선택")
        
        if roleplay_groups and len(roleplay_groups) > 0:
            # 첫 번째 그룹의 문제들을 테스트에 추가
            group = roleplay_groups[0]
            
            for problem in group:
                test_data.problem_data[str(problem_counter)] = create_problem_detail(problem)
                problem_counter += 1
                used_problem_ids.add(str(problem.get('_id')))
                logger.info(f"롤플레이 문제 추가: 순서 {problem.get('problem_order')}, ID {problem.get('_id')}")
        else:
            # 완전한 그룹을 찾지 못한 경우, 랜덤 문제 3개로 대체
            logger.warning("완전한 롤플레이 그룹을 찾지 못함. 랜덤 문제 추가")
            await add_random_problems(db, test_data, problem_counter, 3, used_problem_ids)
    
    except Exception as e:
        logger.error(f"롤플레이 문제 생성 중 오류: {str(e)}", exc_info=True)
        # 오류 발생 시 랜덤 문제로 대체
        await add_random_problems(db, test_data, problem_counter, 3, used_problem_ids)
    
    logger.info(f"롤플레이 테스트 생성 완료 - 총 문제 수: {len(test_data.problem_data)}, 고유 문제 수: {len(used_problem_ids)}")
    
    # 문제 번호 순서대로 로깅
    for num, prob in sorted(test_data.problem_data.items(), key=lambda x: int(x[0])):
        logger.info(f"문제 {num}: 카테고리 {prob.problem_category}, ID {prob.problem_id}")

async def generate_unexpected_test(db: Database, test_data: TestModel, user_topics: List[str]):
    """
    돌발 3문제 테스트 생성
    
    Args:
        db: MongoDB 데이터베이스
        test_data: 테스트 모델 인스턴스
        user_topics: 사용자 관심 주제 목록
    """
    problem_counter = 1
    used_problem_ids = set()  # 문제 중복 방지를 위한 사용된 문제 ID 집합
    
    logger.info(f"돌발 테스트 생성 시작 - 사용자 주제: {user_topics}")
    
    try:
        unexpected_problems = await get_unexpected_problems(db, user_topics, 3, used_problem_ids)
        logger.info(f"돌발 문제 {len(unexpected_problems)}개 선택")
        
        if unexpected_problems:
            for problem in unexpected_problems:
                test_data.problem_data[str(problem_counter)] = create_problem_detail(problem)
                problem_counter += 1
                used_problem_ids.add(str(problem.get('_id')))
                topic = problem.get("topic_category", "없음")
                logger.info(f"돌발 문제 추가: {problem.get('_id')} - 주제: {topic}")
        else:
            logger.warning("돌발 문제를 찾지 못함. 대체 문제 추가")
            await add_random_problems(db, test_data, problem_counter, 3, used_problem_ids)
    
    except Exception as e:
        logger.error(f"돌발 문제 생성 중 오류: {str(e)}", exc_info=True)
        # 오류 발생 시 랜덤 문제로 대체
        await add_random_problems(db, test_data, problem_counter, 3, used_problem_ids)
    
    logger.info(f"돌발 테스트 생성 완료 - 총 문제 수: {len(test_data.problem_data)}, 고유 문제 수: {len(used_problem_ids)}")
    
    # 문제 번호 순서대로 로깅
    for num, prob in sorted(test_data.problem_data.items(), key=lambda x: int(x[0])):
        logger.info(f"문제 {num}: 카테고리 {prob.problem_category}, ID {prob.problem_id}")


async def get_intro_problem(db: Database) -> Optional[Dict[str, Any]]:
    """
    자기소개 문제를 데이터베이스에서 찾아 반환합니다.
    
    Args:
        db: MongoDB 데이터베이스
    
    Returns:
        Optional[Dict[str, Any]]: 자기소개 문제 데이터 또는 None
    """
    try:
        # 자기소개 문제 조회 조건
        query = {
            "problem_category": "자기소개",
            "high_grade_kit": {"$ne": True}  # 고급 문제 키트에 포함되지 않은 문제
        }
        
        # 문제 조회 (랜덤으로 1개 선택)
        cursor = db.problems.aggregate([
            {"$match": query},
            {"$sample": {"size": 1}}
        ])
        
        # 결과 추출
        problem = await cursor.to_list(length=1)
        
        if problem and len(problem) > 0:
            logger.info(f"자기소개 문제 찾음: {problem[0].get('_id')}")
            return problem[0]
        else:
            logger.warning("자기소개 문제를 찾지 못했습니다.")
            return None
            
    except Exception as e:
        logger.error(f"자기소개 문제 조회 중 오류 발생: {str(e)}", exc_info=True)
        return None


async def get_first_combo_problem(
    db: Database, 
    user_topics: List[str], 
    used_topics: Set[str], 
    used_problem_ids: Set[str]
) -> Optional[Dict[str, Any]]:
    """
    콤보셋의 첫 번째 문제 가져오기 (사용자 관심 주제에서 랜덤 선택)
    
    Args:
        db: MongoDB 데이터베이스
        user_topics: 사용자 관심 주제 목록
        used_topics: 이미 사용된 주제 집합
        used_problem_ids: 이미 사용된 문제 ID 집합
        
    Returns:
        선택된 첫 번째 문제 또는 None
    """
    logger.info(f"콤보셋 시작 문제 검색 - 유저 주제: {user_topics}, 사용된 주제: {used_topics}")
    
    # 현재 시간으로 랜덤 시드 설정
    random.seed(datetime.now().timestamp())
    
    try:
        # 중복 방지를 위한 ObjectId 변환
        excluded_ids = [ObjectId(id) for id in used_problem_ids if ObjectId.is_valid(id)]
        
        # 사용 가능한 주제 목록 생성 (used_topics에 없는 user_topics)
        available_topics = [topic for topic in user_topics if topic not in used_topics]
        
        # 관심 주제가 하나도 없거나 전부 사용된 경우 모든 주제 사용
        if not available_topics:
            logger.info("사용 가능한 관심 주제가 없습니다. 모든 주제에서 검색합니다.")
            pipeline = [
                {"$match": {
                    "topic_category": {"$nin": list(used_topics) if used_topics else []},
                    "problem_category": {"$ne": "롤플레이"}  # 롤플레이 제외
                }}
            ]
        else:
            # 사용 가능한 관심 주제에서 랜덤 선택
            pipeline = [
                {"$match": {
                    "topic_category": {"$in": available_topics},
                    "problem_category": {"$ne": "롤플레이"}  # 롤플레이 제외
                }}
            ]
        
        # 중복 방지 조건 추가
        if excluded_ids:
            pipeline[0]["$match"]["_id"] = {"$nin": excluded_ids}
        
        # 무작위 샘플링
        pipeline.append({"$sample": {"size": 1}})
        
        # 파이프라인 실행
        problems = await db.problems.aggregate(pipeline).to_list(length=1)
        
        if problems and len(problems) > 0:
            selected = problems[0]
            logger.info(f"선택된 콤보셋 첫 문제: {selected.get('_id')} - 주제: {selected.get('topic_category')}")
            return selected
        
        # 대체 검색 - 모든 주제에서 검색
        logger.warning("주제 제한 조건으로 문제를 찾지 못함. 모든 주제에서 검색합니다.")
        fallback_pipeline = [
            {"$match": {
                "problem_category": {"$ne": "롤플레이"}  # 롤플레이 제외
            }}
        ]
        
        if excluded_ids:
            fallback_pipeline[0]["$match"]["_id"] = {"$nin": excluded_ids}
            
        fallback_pipeline.append({"$sample": {"size": 1}})
        
        fallback_problems = await db.problems.aggregate(fallback_pipeline).to_list(length=1)
        
        if fallback_problems and len(fallback_problems) > 0:
            selected = fallback_problems[0]
            logger.info(f"대체 검색으로 콤보셋 첫 문제 선택: {selected.get('_id')}")
            return selected
        
        # 문제를 찾지 못한 경우
        logger.warning("콤보셋 시작 문제를 찾을 수 없음!")
        return None
        
    except Exception as e:
        logger.error(f"콤보셋 시작 문제 검색 중 오류: {str(e)}", exc_info=True)
        return None


async def get_combo_problems(
    db: Database, 
    topic_category: str, 
    count: int, 
    used_problem_ids: Set[str]
) -> List[Dict[str, Any]]:
    """
    특정 topic_category에서 추가 콤보 문제 가져오기
    
    Args:
        db: MongoDB 데이터베이스
        topic_category: 주제 카테고리
        count: 필요한 문제 수
        used_problem_ids: 이미 사용된 문제 ID 집합
        
    Returns:
        선택된 콤보 문제 목록
    """
    try:
        # 랜덤 시드 설정
        random.seed(datetime.now().timestamp())
        
        # 중복 방지를 위한 ObjectId 변환
        excluded_ids = [ObjectId(id) for id in used_problem_ids if ObjectId.is_valid(id)]
        
        # 주제 카테고리가 동일한 문제만 선택하는 파이프라인
        pipeline = [
            {"$match": {
                "problem_category": {"$ne": "롤플레이"},
                "topic_category": topic_category,  # 동일한 주제만 선택
            }}
        ]
        
        # 중복 방지 조건 추가
        if excluded_ids:
            pipeline[0]["$match"]["_id"] = {"$nin": excluded_ids}
        
        # 무작위 요소 추가 (쿼리 캐시 방지)
        import uuid
        random_value = str(uuid.uuid4())[:8]
        pipeline[0]["$match"]["__random"] = {"$exists": False}
        
        # 무작위 샘플링
        pipeline.append({"$sample": {"size": count}})
        
        # 파이프라인 실행
        filtered_problems = await db.problems.aggregate(pipeline).to_list(length=count)
        
        # 필요한 문제 수에 도달하지 못한 경우 (이 부분을 수정)
        if len(filtered_problems) < count:
            remaining_count = count - len(filtered_problems)
            logger.warning(f"주제 '{topic_category}'에서 필요한 콤보 문제 수({count})가 부족함. {len(filtered_problems)}개만 선택")
            
            # 추가 문제가 필요하면 동일 주제에서 모든 문제를 검색 (이미 선택된 문제 제외)
            additional_query = {
                "problem_category": {"$ne": "롤플레이"},
                "topic_category": topic_category,  # 여전히 동일 주제만 선택
            }
            
            # 이미 선택된 문제의 ID를 제외 목록에 추가
            additional_excluded_ids = [p.get('_id') for p in filtered_problems] + excluded_ids
            additional_query["_id"] = {"$nin": additional_excluded_ids}
            
            # 추가 문제 쿼리 실행 (find 사용)
            additional_problems = await db.problems.find(additional_query).to_list(length=remaining_count)
            filtered_problems.extend(additional_problems)
            
            # 그래도 부족하면 경고만 기록하고 진행 (다른 주제에서 보완하지 않음)
            if len(filtered_problems) < count:
                logger.warning(f"주제 '{topic_category}'에서 총 {len(filtered_problems)}개 문제만 찾을 수 있습니다. (요청: {count}개)")
        
        # 문제 순서 랜덤하게 섞기
        random.shuffle(filtered_problems)
        
        return filtered_problems
        
    except Exception as e:
        logger.error(f"콤보 문제 검색 중 오류: {str(e)}", exc_info=True)
        return []


async def get_roleplay_problems(
    db: Database, 
    count: int, 
    used_problem_ids: Set[str]
) -> List[Dict[str, Any]]:
    """
    롤플레이 문제 가져오기 - 문제 그룹 단위로 선택

    규칙:
    1. problem_category가 롤플레이인 문제 선택
    2. 롤플레이 문제는 1번부터 3번까지 순서가 있음
    3. 동일한 그룹의 롤플레이 문제는 동일한 problem_group_id를 가짐
    4. 그룹 ID를 먼저 랜덤하게 선택한 후, 해당 그룹 내 순서에 맞는 문제들을 가져옴
    
    Args:
        db: MongoDB 데이터베이스
        count: 필요한 그룹 수
        used_problem_ids: 이미 사용된 문제 ID 집합
        
    Returns:
        선택된 롤플레이 시작 문제 목록
    """
    try:
        logger.info(f"롤플레이 문제 그룹 검색 시작, 필요 그룹 수: {count}")
        
        # 현재 시간으로 랜덤 시드 설정
        random.seed(datetime.now().timestamp())
        
        # 중복 방지를 위한 ObjectId 변환
        excluded_ids = [ObjectId(id) for id in used_problem_ids if ObjectId.is_valid(id)]
        
        # 1. 롤플레이 문제의 고유 그룹 ID 목록 가져오기
        import uuid
        random_seed = str(uuid.uuid4())[:8]
        
        group_pipeline = [
            {"$match": {
                "problem_category": "롤플레이",
                "problem_order": 1,  # 첫 번째 문제만 그룹 선택에 사용
                "__seed": {"$exists": False}  # 캐시 방지용 (항상 True)
            }},
        ]
        
        # 중복 방지 조건 추가
        if excluded_ids:
            group_pipeline[0]["$match"]["_id"] = {"$nin": excluded_ids}
        
        # 그룹 ID 그룹화 및 랜덤 샘플링
        group_pipeline.extend([
            {"$group": {"_id": "$problem_group_id"}},
            {"$match": {"_id": {"$ne": None}}},  # null 그룹 ID 제외
            {"$sample": {"size": count * 2}}  # 필요한 수의 2배 가져오기
        ])
        
        group_results = await db.problems.aggregate(group_pipeline).to_list(length=count * 2)
        
        # 그룹 ID 목록 추출
        group_ids = [result["_id"] for result in group_results if result["_id"]]
        
        if not group_ids:
            logger.warning("롤플레이 그룹 ID를 찾지 못했습니다")
            return []
        
        # 그룹 ID 목록을 섞어서 랜덤성 더하기
        random.shuffle(group_ids)
        logger.info(f"롤플레이 그룹 후보: {len(group_ids)}개 그룹 ID")
        
        # 2. 각 그룹별로 문제 전체 가져오기
        all_groups = []
        
        for group_id in group_ids:
            # 그룹의 모든 문제 가져오기
            group_problems_pipeline = [
                {"$match": {
                    "problem_category": "롤플레이",
                    "problem_group_id": group_id
                }},
                {"$sort": {"problem_order": 1}}  # 문제 순서대로 정렬
            ]
            
            group_problems = await db.problems.aggregate(group_problems_pipeline).to_list(length=3)
            
            # 그룹에 3개의 문제가 있고, 순서가 1,2,3인지 확인
            if len(group_problems) == 3:
                # 문제 순서가 1,2,3인지 확인
                orders = [p.get("problem_order") for p in group_problems]
                if set(orders) == {1, 2, 3}:
                    # 순서대로 정렬
                    group_problems.sort(key=lambda p: p.get("problem_order", 0))
                    
                    # 첫 번째 문제 ID가 이미 사용된 ID인지 확인
                    first_problem_id = str(group_problems[0].get("_id"))
                    if first_problem_id not in used_problem_ids:
                        all_groups.append(group_problems)
                        logger.info(f"완전한 롤플레이 그룹 추가: 그룹 ID {group_id}")
                        
                        # 필요한 그룹 수에 도달하면 종료
                        if len(all_groups) >= count:
                            break
            else:
                logger.warning(f"불완전한 롤플레이 그룹 제외: 그룹 ID {group_id}, 문제 수 {len(group_problems)}")
        
        # 그룹을 최종 섞기 (추가 랜덤성)
        random.shuffle(all_groups)
        
        return all_groups[:count]  # 필요한 수만큼만 반환
    
    except Exception as e:
        logger.error(f"롤플레이 문제 그룹 검색 중 오류: {str(e)}", exc_info=True)
        return []


async def get_unexpected_problems(
    db: Database, 
    user_topics: List[str], 
    count: int, 
    used_problem_ids: Set[str]
) -> List[Dict[str, Any]]:
    """
    돌발 문제 가져오기 (high_grade_kit=true 또는 사용자 관심 영역 외)
    
    Args:
        db: MongoDB 데이터베이스
        user_topics: 사용자 관심 주제 목록
        count: 필요한 문제 수
        used_problem_ids: 이미 사용된 문제 ID 집합
        
    Returns:
        선택된 돌발 문제 목록
    """
    try:
        logger.info(f"돌발 문제 검색 시작, 필요 개수: {count}")
        
        # 시드 랜덤화
        random.seed(datetime.now().timestamp())
        
        # 중복 방지를 위한 ObjectId 변환
        excluded_ids = [ObjectId(id) for id in used_problem_ids if ObjectId.is_valid(id)]
        
        # 모든 돌발 문제 후보 찾기 (전체 개수를 더 많이 가져옴)
        pipeline = [
            {"$match": {
                "$or": [
                    {"high_grade_kit": True},
                    {"topic_category": {"$nin": user_topics if user_topics else []}}
                ],
                "problem_category": {"$ne": "롤플레이"}
            }}
        ]
        
        # 중복 방지 조건 추가
        if excluded_ids:
            pipeline[0]["$match"]["_id"] = {"$nin": excluded_ids}
        
        # 첫 단계에서 랜덤 샘플링 (더 많은 문제 샘플링)
        pipeline.append({"$sample": {"size": count * 3}})
        
        # 파이프라인 실행
        candidate_problems = await db.problems.aggregate(pipeline).to_list(length=None)
        
        if not candidate_problems:
            logger.warning("돌발 문제를 찾지 못했습니다")
            return []
        
        # 후보 문제를 섞어서 결과에 추가
        random.shuffle(candidate_problems)
        result = candidate_problems[:count]
        
        # 같은 주제의 문제가 너무 많으면 다양성을 높이기 위해 필터링
        topic_counts = {}
        for problem in result:
            topic = problem.get("topic_category", "기타")
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # 같은 주제의 문제가 2개 이상이고, 후보 문제가 충분히 있으면 교체
        if len(candidate_problems) > count and any(count > 1 for count in topic_counts.values()):
            # 주제 다양성을 위해 결과 재구성
            final_result = []
            used_topics = set()
            
            # 각 주제별로 최대 1개까지만 선택
            for problem in candidate_problems:
                topic = problem.get("topic_category", "기타")
                if topic not in used_topics:
                    final_result.append(problem)
                    used_topics.add(topic)
                    
                    if len(final_result) >= count:
                        break
            
            # 충분한 다양성을 얻지 못했으면 원래 결과 사용
            if len(final_result) >= count:
                result = final_result
        
        logger.info(f"최종 선택된 돌발 문제: {len(result)}개")
        return result
        
    except Exception as e:
        logger.error(f"돌발 문제 검색 중 오류: {str(e)}", exc_info=True)
        return []


async def add_random_problems(
    db: Database, 
    test_data: TestModel, 
    start_number: int, 
    count: int, 
    used_problem_ids: Set[str]
):
    """
    랜덤 문제를 추가하는 유틸리티 함수
    
    Args:
        db: MongoDB 데이터베이스
        test_data: 테스트 모델 인스턴스
        start_number: 시작 문제 번호
        count: 추가할 문제 수
        used_problem_ids: 이미 사용된 문제 ID 집합
    """
    try:
        # 랜덤 시드 설정
        random.seed(datetime.now().timestamp())
        
        # 중복 방지를 위한 ObjectId 변환
        excluded_ids = [ObjectId(id) for id in used_problem_ids if ObjectId.is_valid(id)]
        
        # 랜덤 변수 추가로 캐시 방지
        import uuid
        random_value = str(uuid.uuid4())
        
        # MongoDB 집계 파이프라인을 사용한 랜덤 선택
        pipeline = [
            {"$match": {"__random": {"$exists": False}}}  # 항상 true 조건이지만 쿼리 캐시 회피용
        ]
        
        # 중복 제외 조건 추가
        if excluded_ids:
            pipeline[0]["$match"]["_id"] = {"$nin": excluded_ids}
        
        # 먼저 대량 샘플링 후 필요한 만큼만 가져오기
        pipeline.append({"$sample": {"size": count * 3}})
        pipeline.append({"$limit": count})
        
        random_problems = await db.problems.aggregate(pipeline).to_list(length=count)
        
        # 충분한 문제를 찾지 못한 경우 대안으로 find 사용
        if len(random_problems) < count:
            logger.warning(f"집계 파이프라인으로 충분한 문제를 찾지 못함. find 메서드 사용")
            query = {}
            if excluded_ids:
                query["_id"] = {"$nin": excluded_ids}
            
            # 최대 100개 문제 가져와서 Python에서 랜덤 선택
            all_problems = await db.problems.find(query).to_list(length=100)
            
            # 중복 제거 (이미 선택된 문제 제외)
            selected_ids = {str(p.get("_id")) for p in random_problems}
            additional_problems = [
                p for p in all_problems 
                if str(p.get("_id")) not in selected_ids and str(p.get("_id")) not in used_problem_ids
            ]
            
            # 추가 문제 랜덤 선택
            if additional_problems:
                random.shuffle(additional_problems)
                additional_count = min(count - len(random_problems), len(additional_problems))
                random_problems.extend(additional_problems[:additional_count])
        
        # 문제가 없는 경우 처리
        if not random_problems:
            logger.error("랜덤 문제를 찾을 수 없습니다")
            return
            
        # 문제 추가
        for i, problem in enumerate(random_problems):
            problem_number = start_number + i
            test_data.problem_data[str(problem_number)] = create_problem_detail(problem)
            used_problem_ids.add(str(problem.get('_id')))
            logger.info(f"랜덤 문제 추가: 문제 번호 {problem_number}, ID {problem.get('_id')}")
            
    except Exception as e:
        logger.error(f"랜덤 문제 추가 중 오류: {str(e)}", exc_info=True)


def create_problem_detail(problem: Dict[str, Any]) -> ProblemDetail:
    """
    문제 정보를 ProblemDetail 모델로 변환
    
    Args:
        problem: 문제 데이터 딕셔너리
        
    Returns:
        변환된 ProblemDetail 객체
    """
    return ProblemDetail(
        problem_id=str(problem.get("_id")),
        problem_category=problem.get("problem_category", "기타"),
        topic_category=problem.get("topic_category", "기타"),
        problem=problem.get("content", "문제 내용 없음"),
        audio_s3_url=problem.get("audio_s3_url", "문제 내용 없음"),
        user_response=None,  # 사용자 응답은 아직 없음
        score=None,  # 점수는 아직 없음
        feedback=None,  # 피드백은 아직 없음
        processing_status="pending",  # 초기 상태
        processing_message="문제가 생성되었습니다."
    )

