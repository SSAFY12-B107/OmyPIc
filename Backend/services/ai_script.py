import os
import logging
import traceback
from typing import Dict, List, Any

# 모든 imports 전에 로깅 설정
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# 로거 정의
logger = logging.getLogger("script_generator")

try:
    from langchain_groq import ChatGroq
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.chains import LLMChain
    from langchain.prompts import ChatPromptTemplate
    from langchain.prompts.chat import SystemMessagePromptTemplate, HumanMessagePromptTemplate
    from api.deps import get_next_groq_key, get_next_gemini_key
    from db.mongodb import get_mongodb, get_collection
except ImportError as e:
    logger.error(f"필수 모듈 임포트 실패: {str(e)}")

# 문제 유형과 질문 하드코딩
question_types = {
    "description": {
        "type": "묘사",
        "questions": [
            "지금 머릿속에 가장 먼저 떠오르는 이미지는 어떤 것인가요? 그 장면을 조금만 더 자세히 묘사해 주시겠어요?",
            "만약 친구나 가족에게 이 장소(또는 대상)를 소개한다면 어떤 부분을 가장 강조하고 싶은가요?",
            "그 대상이나 장소를 한 마디로 표현한다면 무엇이라고 표현할 수 있을까요? 이유도 알려주세요."
        ]
    },
    "past_experience": {
        "type": "과거 경험",
        "questions": [
            "그 상황이 발생했을 때의 당신의 첫 반응이나 감정은 무엇이었나요? 그때 가장 인상 깊었던 소리나 냄새, 느낌은 무엇이었나요?",
            "이 경험 이후 달라진 점이나 깨달은 점이 있다면 무엇인가요?",
            "당시 경험했던 일이 지금까지도 기억에 남아있는 특별한 이유는 무엇이라고 생각하나요?"
        ]
    },
    "routine": {
        "type": "루틴",
        "questions": [
            "보통 그런 활동을 할 때 어떤 감정을 느끼나요? 편안한지, 즐거운지, 아니면 피곤한가요? 그 이유는 무엇인가요?",
            "이 활동을 하면서 자주 사용하는 물건이나 꼭 필요한 물건이 있다면 무엇인가요?",
            "이 활동을 하기 전이나 후에 꼭 함께 하는 준비나 습관, 또는 특정한 절차가 있나요? 간단히 그 과정을 설명해 줄 수 있나요? 그 과정을 하는 이유는 무엇인가요?"
        ]
    },
    "comparison": {
        "type": "비교",
        "questions": [
            "첫 번째 대상(혹은 현재)에 대해 묘사해 주세요.",
            "두 번째 대상(혹은 과거)에 대해 묘사해 주세요.",
            "이러한 차이점이 당신에게 어떤 의미가 있나요? 어떤 점이 더 나은지, 혹은 여전히 아쉬운 점이 있다면 무엇인가요?"
        ]
    },
    "roleplaying": {
        "type": "롤플레이",
        "questions": [
            "이 상황에서 가장 먼저 확인해야 할 중요한 정보는 무엇인가요? 세 가지 이상 작성해주세요.",
            "상대방이 협조적이지 않거나 원하는 답을 주지 않을 경우, 어떻게 설득하거나 요청할 수 있을까요? 이 상황에서 선택할 수 있는 대안은 무엇이 있나요? 상대방이 거절할 경우, 어떤 추가 해결책을 제시할 수 있나요?",
            "이런 경험을 한 적이 있나요? 이 경험을 했을 때, 들었던 감정이 있었나요? 혹시 없더라도 비슷한 상황에서 어떻게 대처할지 생각해본 적 있나요?"
        ]
    }
}

# 카테고리를 질문 유형 키로 변환하는 함수
def get_question_type_key(category: str) -> str:
    """
    문제 카테고리를 질문 유형 키로 변환합니다.
    
    Args:
        category (str): 문제 카테고리
        
    Returns:
        str: 질문 유형 키
    """
    category_mapping = {
        "묘사": "description",
        "과거 경험": "past_experience",
        "루틴": "routine",
        "비교": "comparison",
        "롤플레이": "roleplaying"
    }
    
    return category_mapping.get(category)

# 테스트 목적의 기본 카테고리 제공 함수
def get_fallback_category(problem_pk: str) -> str:
    """
    DB 연결이 안될 경우를 대비한 기본 카테고리 제공 함수
    
    Args:
        problem_pk (str): 문제 ID
        
    Returns:
        str: 기본 카테고리
    """
    # 간단한 해시 기반 카테고리 결정 (실제 사용은 get_problem_category 함수 사용)
    if not problem_pk or len(problem_pk) < 1:
        return "묘사"  # 기본값
        
    first_char = problem_pk[0]
    if first_char in "0123":
        return "묘사"
    elif first_char in "456":
        return "과거 경험"
    elif first_char in "78":
        return "루틴" 
    elif first_char in "9a":
        return "비교"
    else:
        return "롤플레이"

# MongoDB에서 문제 카테고리를 가져오는 함수
async def get_problem_category(problem_pk: str) -> str:
    """
    MongoDB에서 problem_pk에 해당하는 문제의 카테고리를 가져옵니다.
    
    Args:
        problem_pk (str): 문제 ID
        
    Returns:
        str: 문제 카테고리
    """
    try:
        # MongoDB 연결
        db = await get_mongodb()
        
        # ObjectId로 변환 시도
        from bson import ObjectId
        try:
            # 먼저 ObjectId로 조회 시도
            problem_id = ObjectId(problem_pk)
            problem = await db["problems"].find_one({"_id": problem_id})
        except Exception:
            # ObjectId 변환 실패 시 문자열 그대로 조회 시도
            problem = await db["problems"].find_one({"_id": problem_pk})
        
        # 문제 정보 로깅
        if problem:
            logger.info(f"문제 정보 조회 성공: {problem_pk}")
        else:
            logger.error(f"문제 정보를 찾을 수 없습니다: {problem_pk}")
            return None
            
        # problem_category 필드 확인
        if "problem_category" not in problem:
            logger.error(f"문제에 카테고리 정보가 없습니다: {problem_pk}")
            return None
            
        return problem["problem_category"]
    except Exception as e:
        logger.error(f"문제 카테고리 조회 중 오류 발생: {str(e)}")
        # 디버깅을 위한 추가 정보 로깅
        logger.error(f"오류 상세 정보: {traceback.format_exc()}")
        return None

# MongoDB에서 문제 내용을 가져오는 함수
async def get_problem_content(problem_pk: str) -> Dict[str, Any]:
    """
    MongoDB에서 problem_pk에 해당하는 문제의 상세 내용을 가져옵니다.
    
    Args:
        problem_pk (str): 문제 ID
        
    Returns:
        Dict[str, Any]: 문제 상세 내용 (title, content, category 등)
    """
    try:
        # MongoDB 연결
        db = await get_mongodb()
        
        # ObjectId로 변환 시도
        from bson import ObjectId
        try:
            # 먼저 ObjectId로 조회 시도
            problem_id = ObjectId(problem_pk)
            problem = await db["problems"].find_one({"_id": problem_id})
        except Exception:
            # ObjectId 변환 실패 시 문자열 그대로 조회 시도
            problem = await db["problems"].find_one({"_id": problem_pk})
        
        # 문제 정보 로깅
        if problem:
            logger.info(f"문제 정보 조회 성공: {problem_pk}")
            logger.info(f"문제 상세 내용: {problem}")
            return problem
        else:
            logger.error(f"문제 정보를 찾을 수 없습니다: {problem_pk}")
            return None
            
    except Exception as e:
        logger.error(f"문제 상세 내용 조회 중 오류 발생: {str(e)}")
        # 디버깅을 위한 추가 정보 로깅
        logger.error(f"오류 상세 정보: {traceback.format_exc()}")
        return None

# Fallback 함수 - LLM이 사용 불가능한 경우 사용
def generate_fallback_follow_up_questions(answers: Dict[str, str]) -> List[str]:
    """
    LLM이 사용 불가능한 경우 간단한 꼬리질문을 생성하는 함수
    
    Args:
        answers (Dict[str, str]): 사용자 답변 (question1, question2, question3)
        
    Returns:
        List[str]: 생성된 꼬리질문 목록
    """
    follow_up_questions = []
    
    for i in range(3):
        question_key = f"question{i+1}"
        answer = answers.get(question_key, "")
        
        if not answer:
            continue
            
        # 답변 길이에 따른 꼬리질문 분기
        if len(answer) < 30:
            follow_up_questions.append(f"방금 말씀해 주신 내용에 대해 좀 더 자세히 설명해 주실 수 있을까요?")
        else:
            # 답변 길이에 따라 다양한 질문 패턴 사용
            if i == 0:
                follow_up_questions.append(f"방금 말씀하신 것 중에서 가장 중요하다고 생각하는 부분은 무엇인가요? 그 이유도 함께 알려주세요.")
            elif i == 1:
                follow_up_questions.append(f"그런 경험이 당신에게 어떤 의미가 있나요? 어떤 영향을 미쳤나요?")
            else:
                follow_up_questions.append(f"그 상황에서 다른 선택을 했다면 어떻게 달라졌을 것 같나요?")
    
    return follow_up_questions

async def generate_follow_up_questions(problem_pk: str, answers: Dict[str, str]) -> List[str]:
    """
    LangChain을 사용하여 사용자 답변에 대한 꼬리질문을 생성합니다.
    
    Args:
        problem_pk (str): 문제 ID
        answers (Dict[str, str]): 사용자 답변 (question1, question2, question3)
        
    Returns:
        List[str]: 생성된 꼬리질문 목록
    """
    try:
        # MongoDB에서 문제 카테고리 가져오기
        category = await get_problem_category(problem_pk)
        
        # DB 조회 실패 시 기본 카테고리 사용
        if not category:
            logger.warning(f"MongoDB에서 카테고리를 찾을 수 없어 기본값을 사용합니다: {problem_pk}")
            category = get_fallback_category(problem_pk)
            
        # 카테고리를 질문 유형 키로 변환
        type_key = get_question_type_key(category)
        if not type_key or type_key not in question_types:
            logger.error(f"지원되지 않는 문제 카테고리입니다: {category}")
            return ["지원되지 않는 질문 유형입니다."]
            
        question_type_data = question_types[type_key]
        
        # Groq 대신 Gemini-2.0 Flash 모델 사용
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        llm = ChatGoogleGenerativeAI(
            temperature=0.3,
            model="gemini-2.0-flash",  # Gemini-2.0 Flash 모델 사용
            google_api_key=get_next_gemini_key()  # Gemini API 키
        )
        
        # 질문 유형별 맞춤 프롬프트 템플릿
        type_specific_guidance = {
            "묘사": "상세한 시각적 요소나 감각적 정보를 더 이끌어내기 위한 질문을 제시하세요.",
            "과거 경험": "경험에서 느꼈던 감정이나 깨달음을 더 깊이 탐색할 수 있는 질문을 제시하세요.",
            "루틴": "이 활동의 의미나 중요성, 또는 개선점을 탐색하는 질문을 제시하세요.",
            "비교": "두 대상 간의 더 세밀한 차이점이나 유사점을 이끌어내는 질문을 제시하세요.",
            "롤플레잉": "상황에 대한 더 구체적인 접근 방법이나 전략을 이끌어내는 질문을 제시하세요."
        }
        
        follow_up_questions = []
        
        # 각 질문에 대한 꼬리질문 생성
        for i in range(3):
            question_key = f"question{i+1}"
            answer = answers.get(question_key, "")
            
            if not answer:
                continue
                
            original_question = question_type_data["questions"][i] if i < len(question_type_data["questions"]) else ""
            
            # 프롬프트 템플릿 수정
            system_template = f"""
            당신은 자연스러운 후속 질문을 생성하는 전문가입니다.
            
            질문 유형: {question_type_data["type"]}
            가이드라인: {type_specific_guidance.get(question_type_data["type"], "더 깊은 통찰이나 상세한 정보를 이끌어내는 질문을 제시하세요.")}
            
            다음 사항을 고려하여 질문을 생성하세요:
            1. 답변이 모호하거나 불충분한 경우: 구체적인 예시나 경험을 요청하세요
            2. 답변이 충분히 상세한 경우: 그 의미나 영향에 대해 더 깊이 생각해볼 수 있게 하세요
            3. 질문은 반드시 한국어로 작성하세요
            4. 자연스럽고 대화적인 어투를 사용하세요
            5. 친근하고 간결하게 작성하세요
            """
            
            human_template = f"""
            원래 질문: {original_question}
            사용자 답변: {answer}
            
            다음 조건을 만족하는 하나의 후속 질문을 생성하세요:
            1. 자연스러운 대화체로 작성
            2. 친근하고 간단한 표현 사용
            3. 더 깊은 생각이나 상세한 설명을 이끌어낼 수 있는 질문
            4. 반드시 한국어로 작성
            """
            
            chat_prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(system_template),
                HumanMessagePromptTemplate.from_template(human_template)
            ])
            
            # 꼬리질문 생성 - 최신 LangChain 방식 사용
            chain = chat_prompt | llm
            follow_up = await chain.ainvoke({
                "topic_type": question_type_data["type"],
                "problem_content": original_question,
                "answer": answer
            })
            
            # 결과 정리 (불필요한 따옴표나 공백 제거)
            if hasattr(follow_up, 'content'):
                follow_up = follow_up.content.strip().strip('"\'')
            else:
                follow_up = str(follow_up).strip().strip('"\'')
            follow_up_questions.append(follow_up)
            
        return follow_up_questions
        
    except Exception as e:
        logger.error(f"꼬리질문 생성 중 오류 발생: {str(e)}\n{traceback.format_exc()}")
        return [f"꼬리질문 생성 중 오류가 발생했습니다: {str(e)}"]

async def generate_opic_script(problem_pk: str, answers: Dict[str, Any]) -> str:
    """
    사용자 답변을 바탕으로 OPIc IH 수준의 영어 스크립트를 생성합니다.
    문제 내용을 직접 조회하여 사용합니다.
    
    Args:
        problem_pk (str): 문제 ID
        answers (Dict[str, Any]): 사용자 답변 
            {
                "type": "string", 
                "basic_answers": {"answer1": "string", "answer2": "string", "answer3": "string"}, 
                "custom_answers": {"answer1": "string", "answer2": "string", "answer3": "string"}
            }
        
    Returns:
        str: 생성된 OPIc IH 수준의 영어 스크립트
    """
    try:
        # MongoDB에서 문제 상세 내용 가져오기
        problem_data = await get_problem_content(problem_pk)
        
        if not problem_data:
            logger.error(f"문제 상세 내용을 찾을 수 없습니다: {problem_pk}")
            return "Script generation failed: Problem content not found."
        
        # 문제 카테고리 및 실제 문제 내용 추출
        category = problem_data.get("problem_category")
        problem_title = problem_data.get("title", "")
        problem_content = problem_data.get("content", "")
        
        logger.info(f"문제 제목: {problem_title}")
        logger.info(f"문제 내용: {problem_content}")
        
        # DB 조회 실패 시 기본 카테고리 사용
        if not category:
            logger.warning(f"MongoDB에서 카테고리를 찾을 수 없어 기본값을 사용합니다: {problem_pk}")
            category = get_fallback_category(problem_pk)
        
        logger.info(f"Using category: {category} for problem: {problem_pk}")
            
        # 카테고리를 질문 유형 키로 변환
        type_key = get_question_type_key(category)
        if not type_key or type_key not in question_types:
            logger.error(f"지원되지 않는 문제 카테고리입니다: {category}")
            return "Script generation failed: Unsupported question type."
            
        question_type_data = question_types[type_key]
        
        # LLM 모델 설정 (Groq LLM 사용)
        llm = ChatGroq(
            temperature=0.3,
            model_name="llama-3.3-70b-versatile",  # Groq에서 제공하는 Llama 모델
            api_key=get_next_groq_key()  # Groq API 키
        )
        
        # 답변 정리
        if not isinstance(answers, dict):
            logger.error("answers가 딕셔너리가 아닙니다.")
            return "Script generation failed: Invalid input format."
            
        # 기본 답변과 커스텀 답변 추출 및 타입 검사
        basic_answers = answers.get("basic_answers", {})
        custom_answers = answers.get("custom_answers", {})
        
        # 입력값 타입 체크 및 변환
        if not isinstance(basic_answers, dict):
            logger.warning("basic_answers가 딕셔너리가 아닙니다. 변환을 시도합니다.")
            try:
                basic_answers = dict(basic_answers)
            except:
                logger.error("basic_answers를 딕셔너리로 변환할 수 없습니다.")
                basic_answers = {}
                
        if not isinstance(custom_answers, dict):
            logger.warning("custom_answers가 딕셔너리가 아닙니다. 변환을 시도합니다.")
            try:
                custom_answers = dict(custom_answers)
            except:
                logger.error("custom_answers를 딕셔너리로 변환할 수 없습니다.")
                custom_answers = {}
        
        # 디버깅 로그 추가
        logger.info(f"Basic answers: {basic_answers}")
        logger.info(f"Custom answers: {custom_answers}")
        
        # 기본 질문 또는 문제에서 추출한 실제 질문 사용
        questions = []
        
        # 실제 문제 내용이 있으면 사용, 없으면 기본 질문 사용
        if problem_content:
            # 문제 내용을 줄 단위로 분할하여 질문 추출 시도
            content_lines = problem_content.split('\n')
            for line in content_lines:
                # 질문으로 보이는 줄 (물음표가 있거나 의문문 형태) 추가
                if '?' in line or line.strip().endswith('까요') or line.strip().endswith('나요'):
                    questions.append(line.strip())
            
            # 질문을 추출하지 못했거나 너무 적은 경우 기본 질문 추가
            if len(questions) < 3:
                logger.warning(f"문제에서 충분한 질문을 추출하지 못했습니다. 기본 질문 사용: {questions}")
                questions.extend(question_type_data["questions"][:3 - len(questions)])
        else:
            # 기본 질문 사용
            questions = question_type_data["questions"][:3]
        
        # 최대 3개 질문으로 제한
        questions = questions[:3]
        logger.info(f"사용할 질문 목록: {questions}")
        
        combined_info = []
        
        # 원래 질문과 기본 답변, 커스텀 답변 결합
        for i in range(1, 4):
            answer_key = f"answer{i}"
            
            if i <= len(questions):
                question = questions[i-1]
                
                # 안전하게 답변 추출
                basic_answer = basic_answers.get(answer_key, "")
                custom_answer = custom_answers.get(answer_key, "")
                
                # 디버깅 로그
                logger.info(f"Question {i}: {question}")
                logger.info(f"Basic answer {i}: {basic_answer}")
                logger.info(f"Custom answer {i}: {custom_answer}")
                
                # 우선순위: 커스텀 답변 > 기본 답변
                effective_answer = custom_answer if custom_answer else basic_answer
                
                if effective_answer:
                    combined_info.append({
                        "question": question,
                        "answer": effective_answer
                    })
        
        # 답변이 없는 경우 처리
        if not combined_info:
            logger.error("유효한 답변이 없습니다.")
            return "Script generation failed: No valid answers provided."
        
        # 유형별 안내 지침
        type_specific_guidance = {
            "묘사": "Use vivid, descriptive language. Include sensory details and personal impressions.",
            "과거 경험": "Share the experience in chronological order. Include feelings and reflections on the impact.",
            "루틴": "Describe the sequence of activities naturally. Include preferences and reasons for doing things in a certain way.",
            "비교": "Balance the comparison by discussing both similarities and differences. Share personal preferences with reasons.",
            "롤플레잉": "Take on the suggested role naturally. Use appropriate vocabulary and expressions for the situation."
        }
        
        # 스크립트 생성을 위한 프롬프트 템플릿 수정
        system_template = f"""
        You are an expert in generating natural, conversational English scripts for OPIc tests at the IH (Intermediate High) level.
        
        CRITICAL REQUIREMENTS:
        1. LENGTH CONSTRAINTS:
           - Generate EXACTLY 3 paragraphs
           - Each paragraph MUST have 2-3 sentences maximum
           - Total output MUST NOT exceed 9 sentences
        
        2. LANGUAGE: 
           - Output MUST be 100% in English
           - NO Korean or other languages allowed
           - Translate any Korean input into natural English
        
        3. Structure:
           - Each paragraph MUST start with a basic answer in <strong> tags
           - Follow with ONLY 1-2 supporting sentences
           - Use conversation fillers (like, you know, well)
           - Use contractions (I'm, don't, it's)
        
        4. Format:
        <div>
            <p>
            <strong>[Translated basic answer as a simple statement]</strong>
            [1-2 supporting sentences only]
            </p>
            <p>
            <strong>[Translated basic answer as a simple statement]</strong>
            [1-2 supporting sentences only]
            </p>
            <p>
            <strong>[Translated basic answer as a simple statement]</strong>
            [1-2 supporting sentences only]
            </p>
        </div>

        Remember: 
        - ANY non-English text is a critical error
        - Keep responses concise and focused
        - Never exceed the sentence limits
        """

        human_template = """
        Original problem: {problem_content}
        
        Here are the user's answers about {topic_type}:
        
        Basic Answers (translate to English and wrap in <strong> tags):
        {basic_answer_details}
        
        Custom Answers (translate to English for detailed explanations):
        {custom_answer_details}
        
        Requirements:
        1. Translate ALL Korean text to natural English
        2. Start each paragraph with a translated basic answer in <strong> tags
        3. Use casual, conversational English throughout
        4. Keep each paragraph SHORT (2-3 sentences maximum)
        5. Total response must not exceed 9 sentences
        6. Focus on the most important points only
        """

        # 답변 상세 정보 구성
        basic_answer_details = ""
        custom_answer_details = ""
        
        for i in range(1, 4):
            answer_key = f"answer{i}"
            if i <= len(questions):
                question = questions[i-1]
                basic_answer = basic_answers.get(answer_key, "")
                custom_answer = custom_answers.get(answer_key, "")
                
                if basic_answer:
                    basic_answer_details += f"Question {i}: {question}\nBasic Answer: {basic_answer}\n\n"
                if custom_answer:
                    custom_answer_details += f"Question {i}: {question}\nCustom Answer: {custom_answer}\n\n"

        # 프롬프트 템플릿 구성
        chat_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template(human_template)
        ])

        # Chain execution
        chain = chat_prompt | llm
        
        response = await chain.ainvoke({
            "topic_type": question_type_data["type"],
            "problem_content": problem_content,
            "basic_answer_details": basic_answer_details,
            "custom_answer_details": custom_answer_details
        })

        # LLM 응답에서 콘텐츠 추출
        if hasattr(response, 'content'):
            script = response.content.strip()
        else:
            script = str(response).strip()
            
        if not script:
            script = '<div class="opic-script"><p class="error">Script generation failed: Empty response from LLM.</p></div>'
    
        # 로그에 성공 메시지 및 스크립트 일부 기록
        logger.info(f"OPIc 스크립트 생성 성공 (처음 100자): {script[:100]}...")
        
        return script
        
    except Exception as e:
        error_msg = f"OPIc 스크립트 생성 중 오류 발생: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return f'<div class="opic-script"><p class="error">Script generation failed: {str(e)}</p></div>'


