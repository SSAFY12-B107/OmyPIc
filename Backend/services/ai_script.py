from langchain_groq import ChatGroq
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain.prompts.chat import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from typing import Dict, List, Any
import os
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

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
        "type": "롤플레잉",
        "questions": [
            "이 상황에서 가장 먼저 확인해야 할 중요한 정보는 무엇인가요? 세 가지 이상 작성해주세요.",
            "상대방이 협조적이지 않거나 원하는 답을 주지 않을 경우, 어떻게 설득하거나 요청할 수 있을까요? 이 상황에서 선택할 수 있는 대안은 무엇이 있나요? 상대방이 거절할 경우, 어떤 추가 해결책을 제시할 수 있나요?",
            "이런 경험을 한 적이 있나요? 이 경험을 했을 때, 들었던 감정이 있었나요? 혹시 없더라도 비슷한 상황에서 어떻게 대처할지 생각해본 적 있나요?"
        ]
    }
}

# ObjectID에서 질문 유형 결정하는 함수
def get_question_type_from_problem_pk(problem_pk: str) -> str:
    """
    problem_pk(ObjectID)를 기반으로 문제 유형을 결정합니다.
    
    Args:
        problem_pk (str): 문제 ID
        
    Returns:
        str: 결정된 질문 유형 키 (description, past_experience 등)
    """
    types = list(question_types.keys())
    index = int(problem_pk[0], 16) % len(types)
    return types[index]

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
        # 질문 유형 결정
        type_key = get_question_type_from_problem_pk(problem_pk)
        question_type_data = question_types.get(type_key)
        
        if not question_type_data:
            logger.error(f"문제 유형을 찾을 수 없습니다: {type_key}")
            return ["질문 유형을 결정할 수 없습니다."]
        
        # LLM 모델 설정 (Groq LLM 사용)
        llm = ChatGroq(
            temperature=0.3,
            model_name="llama-3.3-70b-versatile",  # Groq에서 제공하는 Llama 모델
            api_key="GROQ API"  # Groq API 키
            ##Warining #아직까지 직접입력을 넣어줘야함!
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
            
            # 프롬프트 템플릿 구성
            system_template = f"""
            당신은 심층적인 대화를 이끌어내는 전문가입니다. 
            사용자의 답변을 분석하고 더 깊은 통찰이나 상세한 정보를 이끌어낼 수 있는 후속 질문을 생성해주세요.
            
            질문 유형: {question_type_data["type"]}
            가이드라인: {type_specific_guidance.get(question_type_data["type"], "더 깊은 통찰이나 상세한 정보를 이끌어내는 질문을 제시하세요.")}
            
            답변이 모호하거나 불충분한 경우, 구체적인 예시나 경험을 요청하는 질문을 생성하세요.
            답변이 충분히 상세하다면, 그 의미나 영향에 대해 더 깊이 생각해볼 수 있는 질문을 생성하세요.
            
            한국어로 자연스럽고 대화적인 하나의 후속 질문만 생성하세요. 친근하고 간결하게 작성하세요.
            """
            
            human_template = f"""
            원래 질문: {original_question}
            사용자 답변: {answer}
            
            위 답변에 대한 적절한 후속 질문을 생성해주세요.
            """
            
            chat_prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(system_template),
                HumanMessagePromptTemplate.from_template(human_template)
            ])
            
            # 꼬리질문 생성
            chain = LLMChain(llm=llm, prompt=chat_prompt)
            follow_up = await chain.arun({})
            
            # 결과 정리 (불필요한 따옴표나 공백 제거)
            follow_up = follow_up.strip().strip('"\'')
            follow_up_questions.append(follow_up)
            
        return follow_up_questions
        
    except Exception as e:
        logger.error(f"꼬리질문 생성 중 오류 발생: {str(e)}")
        return [f"꼬리질문 생성 중 오류가 발생했습니다: {str(e)}"]

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

async def generate_opic_script(problem_pk: str, answers: Dict[str, Any]) -> str:
    """
    사용자 답변을 바탕으로 OPIc IH 수준의 영어 스크립트를 생성합니다.
    
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
        # 질문 유형 결정
        type_key = get_question_type_from_problem_pk(problem_pk)
        question_type_data = question_types.get(type_key)
        
        if not question_type_data:
            logger.error(f"문제 유형을 찾을 수 없습니다: {type_key}")
            return "Script generation failed: Question type could not be determined."
        
        # LLM 모델 설정 (Groq LLM 사용)
        llm = ChatGroq(
            temperature=0.7,  # 창의성을 위해 약간 높임
            model_name="llama-3.3-70b-versatile",  # Groq에서 제공하는 Llama 모델
            api_key="GROQ API"  # Groq API 키
        )
        
        # 답변 정리 - QuestionAnswers 객체에서 필드를 직접 접근
        basic_answers = answers["basic_answers"]
        custom_answers = answers.get("custom_answers", {})
        
        questions = question_type_data["questions"]
        combined_info = []
        
        # 원래 질문과 기본 답변, 커스텀 답변 결합
        for i in range(1, 4):
            answer_key = f"answer{i}"
            
            if i <= len(questions):
                question = questions[i-1]
                
                # 객체에서 속성으로 직접 접근
                try:
                    # 먼저 딕셔너리인지 확인
                    if isinstance(basic_answers, dict):
                        basic_answer = basic_answers.get(answer_key, "")
                    else:
                        # 그렇지 않으면 속성으로 접근
                        basic_answer = getattr(basic_answers, answer_key, "")
                        
                    if isinstance(custom_answers, dict):
                        custom_answer = custom_answers.get(answer_key, "")
                    else:
                        custom_answer = getattr(custom_answers, answer_key, "")
                except AttributeError:
                    logger.warning(f"답변 접근 오류: {answer_key}")
                    basic_answer = ""
                    custom_answer = ""
                
                if basic_answer or custom_answer:
                    combined_info.append({
                        "question": question,
                        "basic_answer": basic_answer,
                        "custom_answer": custom_answer
                    })
        
        # 답변이 없는 경우 처리
        if not combined_info:
            return "Script generation failed: No answers provided."
        
        # 유형별 안내 지침
        type_specific_guidance = {
            "묘사": "Use vivid, descriptive language. Include sensory details and personal impressions.",
            "과거 경험": "Share the experience in chronological order. Include feelings and reflections on the impact.",
            "루틴": "Describe the sequence of activities naturally. Include preferences and reasons for doing things in a certain way.",
            "비교": "Balance the comparison by discussing both similarities and differences. Share personal preferences with reasons.",
            "롤플레잉": "Take on the suggested role naturally. Use appropriate vocabulary and expressions for the situation."
        }
        
        # 프롬프트 템플릿 구성
        system_template = f"""
        You are an expert in generating natural, conversational English scripts for OPIc tests at the IH (Intermediate High) level.
        
        Topic type: {question_type_data["type"]}
        Guidance: {type_specific_guidance.get(question_type_data["type"], "Create a natural, conversational response that demonstrates paragraph-level discourse.")}
        
        Follow these requirements exactly:
        1. Generate a 1-1.5 minute spoken script (7-9 sentences total).
        2. Use conversational language with natural discourse markers (well, you know, actually, anyway, etc.).
        3. Include a mix of simple and complex sentences.
        4. Use appropriate transitions between ideas.
        5. Include personal opinions, feelings, or reflections.
        6. Maintain coherent paragraph-level discourse.
        7. Avoid overly formal language - this should sound natural when spoken.
        8. Include 1-2 hesitations or self-corrections to sound natural (like "um", "I mean", etc.).
        
        The final output should ONLY be the English script - do not include any explanations, introductions, or annotations.
        """
        
        human_template = """
        Here are the user's Korean answers to questions about {topic_type}:
        
        {answer_details}
        
        Create a natural, conversational English script at the OPIc IH level that integrates these ideas into a coherent response.
        The script should be 7-9 sentences long (1-1.5 minutes when spoken).
        """
        
        # 답변 상세 정보 구성
        answer_details = ""
        for item in combined_info:
            answer_text = item["custom_answer"] if item["custom_answer"] else item["basic_answer"]
            answer_details += f"Question: {item['question']}\nAnswer: {answer_text}\n\n"
        
        chat_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template(human_template)
        ])
        
        # 스크립트 생성
        chain = LLMChain(llm=llm, prompt=chat_prompt)
        script = await chain.arun({
            "topic_type": question_type_data["type"],
            "answer_details": answer_details
        })
        
        # 결과 정리
        script = script.strip()
        return script
        
    except Exception as e:
        logger.error(f"OPIc 스크립트 생성 중 오류 발생: {str(e)}")
        return f"Script generation failed: Error occurred during generation: {str(e)}"