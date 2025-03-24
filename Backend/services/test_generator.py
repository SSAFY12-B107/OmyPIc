# services/test_generator.py
import random
import logging
from typing import Dict, List, Any, Set, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase as Database
from bson import ObjectId
from models.test import TestModel, ProblemDetail

# 로깅 설정
logger = logging.getLogger(__name__)

async def generate_short_test(db: Database, test_data: TestModel, user_topics: List[str]):
    """
    7문제 테스트 생성 (콤보셋 3, 롤플레잉 2, 돌발 2)
    
    Args:
        db: MongoDB 데이터베이스
        test_data: 테스트 모델 인스턴스
        user_topics: 사용자 관심 주제 목록
    """
    problem_counter = 1
    used_topics = set()
    used_problem_ids = set()  # 문제 중복 방지를 위한 사용된 문제 ID 집합
    
    logger.info(f"7문제 테스트 생성 시작 - 사용자 주제: {user_topics}")
    
    # 1. 콤보셋 3문제 생성
    try:
        # 콤보셋 시작 문제 선택 (묘사 카테고리에서)
        first_combo_problem = await get_first_combo_problem(db, user_topics, used_topics, used_problem_ids)
        
        if first_combo_problem:
            logger.info(f"콤보셋 첫 문제 선택: {first_combo_problem.get('_id')} - {first_combo_problem.get('problem_category')}")
            
            test_data.problem_data[str(problem_counter)] = create_problem_detail(first_combo_problem)
            problem_counter += 1
            used_topic = first_combo_problem.get("topic_category")
            used_topics.add(used_topic)
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
        problem_counter += 3
    
    logger.info(f"롤플레이 문제 생성 시작 - 현재 문제 카운터: {problem_counter}")
    
    # 2. 롤플레잉 문제 생성 - 정확히 2문제만
    try:
        roleplay_count = 1  # 첫 번째 그룹만 선택
        roleplay_problems = await get_roleplay_problems(db, roleplay_count, used_problem_ids)
        logger.info(f"롤플레이 문제 그룹: {len(roleplay_problems)}개 선택")
        
        if roleplay_problems:
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
                        logger.info(f"롤플레이 연속 문제 추가: {next_problem.get('_id')}")
                    else:
                        logger.warning(f"롤플레이 두 번째 문제를 찾지 못함 (그룹 ID: {group_id})")
                        # 대체 문제 추가
                        await add_random_problems(db, test_data, problem_counter, 1, used_problem_ids)
                        problem_counter += 1
        else:
            logger.warning("롤플레이 문제를 찾지 못함. 대체 문제 추가")
            await add_random_problems(db, test_data, problem_counter, 2, used_problem_ids)
            problem_counter += 2
    
    except Exception as e:
        logger.error(f"롤플레이 문제 생성 중 오류: {str(e)}", exc_info=True)
        # 오류 발생 시 랜덤 문제로 대체
        await add_random_problems(db, test_data, problem_counter, 2, used_problem_ids)
        problem_counter += 2
    
    logger.info(f"돌발 문제 생성 시작 - 현재 문제 카운터: {problem_counter}")
    
    # 3. 돌발 2문제 생성 (롤플레잉 카테고리 제외, 동일 topic_category)
    try:
        unexpected_problems = await get_unexpected_problems(db, user_topics, 2, used_problem_ids)
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
            await add_random_problems(db, test_data, problem_counter, 2, used_problem_ids)
            problem_counter += 2
    
    except Exception as e:
        logger.error(f"돌발 문제 생성 중 오류: {str(e)}", exc_info=True)
        # 오류 발생 시 랜덤 문제로 대체
        await add_random_problems(db, test_data, problem_counter, 2, used_problem_ids)
        problem_counter += 2
    
    logger.info(f"테스트 생성 완료 - 총 문제 수: {len(test_data.problem_data)}, 고유 문제 수: {len(used_problem_ids)}")
    
    # 문제 번호 순서대로 로깅
    for num, prob in sorted(test_data.problem_data.items(), key=lambda x: int(x[0])):
        logger.info(f"문제 {num}: 카테고리 {prob.problem_category}, ID {prob.problem_id}")

async def generate_full_test(db: Database, test_data: TestModel, user_topics: List[str]):
    """
    15문제 테스트 생성 (자기소개 1, 콤보셋 9, 롤플레잉 3, 돌발 2)
    
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
        roleplay_problems = await get_roleplay_problems(db, 1, used_problem_ids)
        logger.info(f"롤플레잉 문제 그룹: {len(roleplay_problems)}개 선택")
        
        if roleplay_problems:
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
                        logger.info(f"롤플레이 두 번째 문제 추가: {second_problem.get('_id')}")
                        
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
                            logger.info(f"롤플레이 세 번째 문제 추가: {third_problem.get('_id')}")
                        else:
                            logger.warning(f"롤플레이 세 번째 문제를 찾지 못함 (그룹 ID: {group_id})")
                            await add_random_problems(db, test_data, problem_counter, 1, used_problem_ids)
                            problem_counter += 1
                    else:
                        logger.warning(f"롤플레이 두 번째 문제를 찾지 못함 (그룹 ID: {group_id})")
                        await add_random_problems(db, test_data, problem_counter, 2, used_problem_ids)
                        problem_counter += 2
        else:
            logger.warning("롤플레이 문제를 찾지 못함. 랜덤 문제 추가")
            await add_random_problems(db, test_data, problem_counter, 3, used_problem_ids)
            problem_counter += 3
    except Exception as e:
        logger.error(f"롤플레잉 문제 생성 중 오류: {str(e)}", exc_info=True)
        # 오류 발생 시 랜덤 문제로 대체
        await add_random_problems(db, test_data, problem_counter, 3, used_problem_ids)
        problem_counter += 3
    
    # 4. 돌발 2문제
    try:
        logger.info(f"돌발 문제 생성 시작 - 현재 문제 카운터: {problem_counter}")
        unexpected_problems = await get_unexpected_problems(db, user_topics, 2, used_problem_ids)
        logger.info(f"돌발 문제 {len(unexpected_problems)}개 선택")
        
        if unexpected_problems:
            for problem in unexpected_problems:
                test_data.problem_data[str(problem_counter)] = create_problem_detail(problem)
                problem_counter += 1
                used_problem_ids.add(str(problem.get('_id')))
                # 문제 topic_category 확인 로깅
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

async def get_first_combo_problem(
    db: Database, 
    user_topics: List[str], 
    used_topics: Set[str], 
    used_problem_ids: Set[str]
) -> Optional[Dict[str, Any]]:
    """
    콤보셋의 첫 번째 문제 가져오기 (주로 묘사 카테고리)
    
    Args:
        db: MongoDB 데이터베이스
        user_topics: 사용자 관심 주제 목록
        used_topics: 이미 사용된 주제 집합
        used_problem_ids: 이미 사용된 문제 ID 집합
        
    Returns:
        선택된 첫 번째 문제 또는 None
    """
    logger.info(f"콤보셋 시작 문제 검색 - 유저 주제: {user_topics}, 사용된 주제: {used_topics}")
    
    try:
        # 중복 방지를 위한 ObjectId 변환
        excluded_ids = [ObjectId(id) for id in used_problem_ids if ObjectId.is_valid(id)]
        
        # 기본 쿼리: '묘사' 카테고리의 문제 중 사용자 주제에 해당하고 아직 사용하지 않은 주제
        query = {
            "problem_category": "묘사",
            "topic_category": {"$in": user_topics, "$nin": list(used_topics) if used_topics else []},
            "$or": [
                {"problem_group_id": {"$exists": False}},
                {"problem_order": 1}
            ]
        }
        
        # 중복 방지 조건 추가
        if excluded_ids:
            query["_id"] = {"$nin": excluded_ids}
        
        # 조건에 맞는 문제 조회
        problems = await db.problems.find(query).to_list(length=10)
        logger.info(f"묘사 카테고리 검색 결과: {len(problems)}개 문제 발견")
        
        # 문제를 찾았으면 무작위로 하나 선택
        if problems:
            selected = random.choice(problems)
            logger.info(f"선택된 콤보셋 시작 문제: {selected.get('_id')} - 카테고리: {selected.get('problem_category')}")
            return selected
        
        # 사용자 주제를 제외한 문제 검색 (대체 검색)
        if not problems:
            logger.warning("사용자 주제에서 콤보셋 시작 문제를 찾지 못함. 전체 주제에서 검색")
            fallback_query = {
                "problem_category": "묘사",
                "topic_category": {"$nin": list(used_topics) if used_topics else []},
                "$or": [
                    {"problem_group_id": {"$exists": False}},
                    {"problem_order": 1}
                ]
            }
            
            if excluded_ids:
                fallback_query["_id"] = {"$nin": excluded_ids}
                
            fallback_problems = await db.problems.find(fallback_query).to_list(length=10)
            
            if fallback_problems:
                selected = random.choice(fallback_problems)
                logger.info(f"대체 검색으로 콤보셋 시작 문제 선택: {selected.get('_id')}")
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
        # 중복 방지를 위한 ObjectId 변환
        excluded_ids = [ObjectId(id) for id in used_problem_ids if ObjectId.is_valid(id)]
        
        # 같은 주제를 가진 비롤플레이 문제 쿼리
        query = {
            "problem_category": {"$ne": "롤플레이"},
            "topic_category": topic_category
        }
        
        # 중복 방지 조건 추가
        if excluded_ids:
            query["_id"] = {"$nin": excluded_ids}
        
        # 조건에 맞는 문제 조회
        problems = await db.problems.find(query).to_list(length=count * 2)
        
        # 필요한 수만큼 무작위로 선택
        if len(problems) >= count:
            selected_problems = random.sample(problems, count)
        else:
            # 부족한 경우 다른 주제에서 보완
            selected_problems = problems
            logger.warning(f"주제 '{topic_category}'에서 필요한 콤보 문제 수({count})가 부족함. {len(problems)}개만 선택")
            
            # 부족한 수만큼 다른 주제에서 추가 검색
            remaining_count = count - len(problems)
            if remaining_count > 0:
                fallback_query = {
                    "problem_category": {"$ne": "롤플레이"},
                    "topic_category": {"$ne": topic_category}
                }
                
                if excluded_ids:
                    excluded_ids.extend([ObjectId(p["_id"]) for p in selected_problems])
                    fallback_query["_id"] = {"$nin": excluded_ids}
                
                fallback_problems = await db.problems.find(fallback_query).limit(remaining_count).to_list(length=remaining_count)
                selected_problems.extend(fallback_problems)
                logger.info(f"콤보 문제 부족분 {len(fallback_problems)}개를 다른 주제에서 추가")
        
        return selected_problems
        
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
    
    Args:
        db: MongoDB 데이터베이스
        count: 필요한 그룹 수
        used_problem_ids: 이미 사용된 문제 ID 집합
        
    Returns:
        선택된 롤플레이 시작 문제 목록
    """
    try:
        logger.info(f"롤플레이 문제 검색 시작, 필요 개수: {count}")
        
        # 중복 방지를 위한 ObjectId 변환
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
        logger.info(f"롤플레이 시작 문제: {len(roleplay_starters)}개 발견")
        
        # 필요한 개수만큼 랜덤 선택
        if roleplay_starters:
            if len(roleplay_starters) >= count:
                return random.sample(roleplay_starters, count)
            else:
                logger.warning(f"롤플레이 문제 부족: 필요 {count}개, 발견 {len(roleplay_starters)}개")
                return roleplay_starters
        else:
            logger.warning("롤플레이 문제를 찾지 못했습니다")
            return []
            
    except Exception as e:
        logger.error(f"롤플레이 문제 검색 중 오류: {str(e)}", exc_info=True)
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
        
        # 중복 방지를 위한 ObjectId 변환
        excluded_ids = [ObjectId(id) for id in used_problem_ids if ObjectId.is_valid(id)]
        
        # 돌발 문제 기본 쿼리 - 롤플레이가 아닌 high_grade_kit 문제 또는 사용자 관심 영역 외 문제
        query = {
            "$or": [
                {"high_grade_kit": True},
                {"topic_category": {"$nin": user_topics if user_topics else []}}
            ],
            "problem_category": {"$ne": "롤플레이"}
        }
        
        # 중복 방지 조건 추가
        if excluded_ids:
            query["_id"] = {"$nin": excluded_ids}
        
        # 첫 번째 돌발 문제 선택
        first_problems = await db.problems.find(query).to_list(length=10)
        
        if not first_problems:
            logger.warning("돌발 문제를 찾지 못했습니다")
            return []
        
        # 첫 번째 문제 랜덤 선택
        first_problem = random.choice(first_problems)
        result = [first_problem]
        
        # 첫 번째 문제와 동일한 topic_category에서 나머지 문제 선택 (count-1개)
        if count > 1:
            topic_category = first_problem.get("topic_category")
            logger.info(f"선택된 돌발 문제 주제: {topic_category}")
            
            # 첫 번째 문제 ID를 제외 목록에 추가
            updated_excluded_ids = excluded_ids + [first_problem.get("_id")]
            
            # 같은 주제의 추가 문제 쿼리
            same_topic_query = {
                "topic_category": topic_category,
                "problem_category": {"$ne": "롤플레이"},
                "_id": {"$nin": updated_excluded_ids}
            }
            
            same_topic_problems = await db.problems.find(same_topic_query).to_list(length=(count - 1) * 3)
            
            # 같은 주제의 추가 문제가 있으면 선택
            if same_topic_problems:
                additional_problems = random.sample(same_topic_problems, min(count - 1, len(same_topic_problems)))
                result.extend(additional_problems)
                logger.info(f"같은 주제({topic_category})에서 추가 돌발 문제 {len(additional_problems)}개 선택")
            else:
                # 같은 주제의 문제가 없으면 다른 돌발 문제 선택
                logger.warning(f"주제({topic_category})에서 추가 문제를 찾지 못함, 다른 돌발 문제를 선택합니다")
                other_problems = await db.problems.find(query).to_list(length=(count - 1) * 3)
                
                if other_problems:
                    # 이미 선택된 문제 제외
                    other_problems = [p for p in other_problems if str(p["_id"]) != str(first_problem["_id"])]
                    if other_problems:
                        additional_problems = random.sample(other_problems, min(count - 1, len(other_problems)))
                        result.extend(additional_problems)
                        logger.info(f"다른 주제에서 추가 돌발 문제 {len(additional_problems)}개 선택")
        
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
        # 중복 방지를 위한 ObjectId 변환
        excluded_ids = [ObjectId(id) for id in used_problem_ids if ObjectId.is_valid(id)]
        
        # 사용되지 않은 문제 중에서 랜덤 선택
        query = {}
        if excluded_ids:
            query["_id"] = {"$nin": excluded_ids}
        
        random_problems = await db.problems.find(query).limit(count).to_list(length=count)
        
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

