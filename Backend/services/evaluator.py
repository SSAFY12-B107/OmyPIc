import logging
from typing import Dict, List, Any
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from api.deps import handle_api_error, get_next_gemini_key

import time

# 로깅 설정
import logging # Assuming you have logging imported

logger = logging.getLogger(__name__)

# 오픽 레벨 정의 (ACTFL 매핑 고려)
OPIC_LEVELS = [
    "NL", "NM", "NH",  # Novice Low, Mid, High
    "IL",  # Intermediate Low
    "IM1", "IM2", "IM3", # Intermediate Mid (varying strength)
    "IH",  # Intermediate High
    "AL"  # Advanced (likely Low/Mid within ACTFL Advanced)
]

# ACTFL 2024 Speaking 기준 요약 (OPIC 레벨 매핑 포함)
ACTFL_LEVEL_DESCRIPTIONS_SUMMARY = {
    "NH": "Novice High: 주로 암기한 표현 확장 사용. 현재 시제 위주 짧고 불완전한 문장. 간단한 생존 관련 대화 가능. 때때로 문장 생성 시도 (Intermediate Low 수준 보임).",
    "IL": "Intermediate Low: 제한된 수의 간단한 소통 과제 수행. 예측 가능한 생존 관련 주제(개인 정보, 음식 주문 등)에서 창의적 언어 사용 시작. 짧은 문장 조합/재조합. 주로 반응적이며 질문에 어려움. 망설임, 반복, 자가 수정 잦음.",
    "IM": "Intermediate Mid (IM1-IM3 포괄): 다양한 비복잡성 소통 과제 수행. 예측 가능한 교환(일상 활동, 관심사, 필요 등) 참여. 기본적인 필요 충족 위한 질문 가능. 문장 연결 시작. 오류 있으나 대체로 이해 가능. IM1/2/3은 이 Mid 레벨 내에서의 일관성, 유창성, 정확성 차이 반영.",
    "IH": "Intermediate High: 익숙한 일상 업무/상황에서 자신감 있게 대화. 개인 관심/능력 분야 정보 교환. 어휘/통제력 향상. Advanced 수준 과제(주요 시제 사용한 서술/묘사, 문단 길이 발화) 수행 가능하나, **일관되게 유지하지 못하고** 때때로 오류/붕괴(breakdown) 발생.",
    "AL": "Advanced Low/Mid: 다양한 소통 과제 처리. 대부분 비공식 및 일부 공식 대화 참여(업무, 시사, 개인 관심사 등). 주요 시제(과거, 현재, 미래) 사용하여 서술/묘사. 사실 보고, 간단한 권고, 명확한 설명 가능. **문단 길이의 연결된 발화**. 예상치 못한 상황 대처. 명확성, 정확성 갖춘 구체적 언어 사용."
    # Superior/Distinguished는 일반적인 OPIC 범위 넘어서므로 생략
}


# 오픽 평가 기준에 대한 상세 설명을 담은 프롬프트 템플릿
EVALUATION_PROMPT_TEMPLATE = """
당신은 **ACTFL Proficiency Guidelines 2024 (Speaking)** 기준에 능통한 OPIC(Oral Proficiency Interview-Computer) 전문 평가자입니다.
수험자의 발화를 아래 기준에 따라 **정확하게 평가**하고, OPIC 등급(NH, IL, IM1-3, IH, AL)을 부여하세요.

---

## 중요 지침
- 제시된 응답을 아래 **ACTFL 2024 Speaking 기준 (FACT)** 과 **세부 등급 설명**에 따라 **한국어로** 평가해 주세요.
- 피드백 생성 시, <b>현재 등급의 강점과 함께, 다음 등급(예: IM3 -> IH, IH -> AL)으로 올라가기 위해 보완해야 할 점</b>을 구체적으로 설명해주세요.
- 반드시 <b>질문과 연관 있는 응답인지 확인</b>하여 평가에 반영하세요.

---

## 중요: 의미 없는 응답 감지
먼저 응답이 의미 있는 발화인지 확인하세요.

- "에베베베", "아아아", "음음음", "ㅋㅋㅋ" 등 실제 단어가 아니거나 무의미한 소리의 반복만 있는 경우 → <b>"즉시 NL 점수"</b>를 부여하고, 간단한 이유만 피드백으로 작성하세요. (예: "실제 발화 내용이 없어 평가가 불가능합니다.")

- 문장은 구성되었으나 질문과 **전혀 관련 없는 응답**이라면 → <b>ACTFL 기준에 따라 가능한 등급을 신중히 매긴 후</b>, 피드백에 <b>“질문과 관련 없는 응답이었습니다.”</b>를 반드시 포함해 주세요. 관련 없는 응답은 Functions와 Context/Content 측면에서 감점 요인이 될 수 있습니다.

---

## 점수 판단 기준: ACTFL Speaking Proficiency Guidelines 2024 (FACT)
다음 네 가지 기준을 종합적으로 분석하여 OPIC 등급을 결정합니다.

1.  <b>Functions & Tasks (F)</b>: 수험자가 언어로 **무엇을 할 수 있는가?** (예: 정보 제공, 질문, 묘사, 서술, 의견 제시, 상황 대처 등). 등급을 나누는 **가장 중요한 기준**입니다.
2.  <b>Accuracy (A)</b>: 언어적 특징(문법, 구문, 어휘, 발음, 강세/억양, 사회문화적 지식 등)을 얼마나 정확하게 사용하는가?
3.  <b>Context & Content (C)</b>: 어떤 상황(Context)과 주제(Content) 범위 내에서 의사소통이 가능한가? (예: 개인적, 사회적, 직업적, 추상적)
4.  <b>Text Type (T)</b>: 어느 정도 길이와 복잡성(단어, 구, 문장, 연결된 문장, 문단, 다문단)의 발화를 생성하는가?

---

## ACTFL 2024 기반 OPIC 등급별 세부 기준:
- **NH (Novice High)**: {{ACTFL_LEVEL_DESCRIPTIONS_SUMMARY[NH]}}
- **IL (Intermediate Low)**: {{ACTFL_LEVEL_DESCRIPTIONS_SUMMARY[IL]}}
- **IM1-IM3 (Intermediate Mid)**: {{ACTFL_LEVEL_DESCRIPTIONS_SUMMARY[IM]}} (IM1: Mid의 초기 단계, IM2: Mid의 안정적 단계, IM3: Mid의 상위 단계로, IH 수준에 근접하나 아직 도달하지 못함)
- **IH (Intermediate High)**: {{ACTFL_LEVEL_DESCRIPTIONS_SUMMARY[IH]}} (**핵심: Advanced 기능(시제 사용 서술/묘사, 문단 길이 발화)을 시도하고 일부 성공하지만, 일관되게 유지하지 못함**)
- **AL (Advanced Low/Mid)**: {{ACTFL_LEVEL_DESCRIPTIONS_SUMMARY[AL]}} (**핵심: Advanced 기능을 일관되게 수행하며 문단 길이 발화 가능**)

---

## 피드백 구성 (반드시 HTML 형식)
다음 항목별로 피드백을 제공합니다. **피드백은 반드시 HTML 형식으로 작성**하며, 다음 항목을 포함합니다:

-   <b>paragraph (Text Type & Cohesion)</b>: 발화의 길이, 문장 연결성, 문단 구성 능력 (논리적 흐름, 구조적 완성도).
-   <b>vocabulary & accuracy (Accuracy & Content)</b>: 어휘의 다양성, 정확성, 적절성 및 문법/구문 정확성.
-   <b>delivery (Accuracy & Functions)</b>: 발음, 강세, 억양의 명확성 및 유창성(끊김, filler 사용). 전반적인 의사 전달 능력.

1. 문단 구분이 필요한 경우 `<br><br>`를 사용하세요.
2. 중요한 포인트는 `<b>강조할 내용</b>` 형식으로 볼드 처리하세요.
3. 피드백은 가독성이 좋게 작성하고, **다음 등급으로 나아가기 위한 구체적인 조언**을 포함하세요.

---

## Few-shot 예시 (ACTFL 기준 적용):
아래 예시들은 각 레벨별 특징을 보여줍니다. 수험자의 응답을 FACT 기준에 맞춰 분석하고 가장 유사한 수준의 등급을 판단하세요.

### IM1 예시 (Intermediate Mid - Low):
"Yes, that's right. I live in a high-rise apartment building in Gumi. There are so many apartment buildings in Gumi. I live on the top floor, so I have a great view. and um... There are a living room, two rooms, a kitchen, and a balcony in my apartment."
*   **분석:** 단순 정보 나열 (Function). 짧고 분리된 문장 (Text Type). 기본 어휘 (Accuracy). 개인적이고 구체적인 주제 (Context). IL보다는 창의적이나 연결성 부족.

### IM2 예시 (Intermediate Mid - Solid):
"Yes, that's right. I live in a high-rise apartment building in Gumi. There are so many apartment buildings in Gumi. I live on the top floor, so I have a great view. and um... There are a living room, two rooms, a kitchen, and a balcony in my apartment. And you know, Even though it's a small house, it can be spacious if you style your home. So I styled my home, and I'm very satisfied with my apartment."
*   **분석:** 이유/결과 추가 (Function 향상). 문장 연결 시도 (Text Type). 감정 표현 (Function). 어휘 약간 확장 (Accuracy). IM1보다 길고 약간 더 복잡.

### IM3 예시 (Intermediate Mid - High):
"Yes, I live in a high-rise apartment in Gumi. It's located near downtown and has great access to public transportation. My apartment is on the top floor, so I can enjoy the city view every night. It's quite spacious, with a living room, two bedrooms, a kitchen, and a balcony. I decorated it with warm-toned furniture, and I feel comfortable and relaxed whenever I stay at home."
*   **분석:** 묘사 구체화 (Function). 연결된 문장들 (Text Type). 더 나은 어휘 선택 (Accuracy). 일관성 있고 유창함 증가 (Accuracy). IH에 가까우나 아직 Advanced 기능(복잡한 시제, 문단 구조) 부족.

### IH 예시 (Intermediate High):
"Let's see, when it comes to my favorite furniture in my house... Um... you know, It's definitely, my sofa in the living room. I almost spend my time on the sofa when I stay at home. This sofa is, you know, perfect for having a relax. Especially after work when I am worn out. It's made of natural leather, and it is ash gray. That's a totally nice texture and a nice color. So this sofa is making the living room atmosphere just so comfortable. Of course, the sofa itself is also comfortable. I love watching TV and, you know, playing games with my PlayStation 4 on that sofa. So what I'm trying to say is that my favorite piece of furniture in my house is the sofa. Is this enough to answer?"
*   **분석:** **문단 길이 발화 시도** (Text Type). 이유/사례 상세 설명 (Function - Advanced 시도). 현재 시제 위주지만 과거 경험(worn out) 언급. 연결성 좋음. 하지만 **Advanced 수준의 서술/묘사(과거/미래 시제 활용)나 복잡한 구조를 일관되게 유지하지는 못함.** AL로 가기엔 부족.

### AL 예시 (Advanced Low/Mid):
"I had one very crazy experience. One time I was having a picnic with my friend. These guys were playing a game of baseball near us. This is common for, um, people who go to the park. We didn't mind that they were close to us, but then a baseball hit my head! One guy tried to catch it but he missed the ball. It went past him and hit my head! I don't know how hard they threw that ball, but I was in excruciating pain. Everyone was staring at me and I just wanted to hide. The guy said sorry, but… I was so embarrassed! My friend would not stop laughing at me. That made the situation, umm, even worse. I wanted to go home and never come back. I can't stand this story, but that was my crazy experience."
*   **분석:** **과거 시제 일관된 사용 및 사건 서술** (Function - Advanced). **문단 길이의 연결된 발화** (Text Type). 감정 묘사 (Function). 예상치 못한 상황 설명. 명확하고 이해하기 쉬움 (Accuracy). Advanced 수준의 기능을 **일관되게** 보여줌.

---

## 수험자의 응답:
"{user_response}"

## 문항 정보:
- 문제 카테고리: {problem_category}
- 토픽 카테고리: {topic_category}
- 문제: {problem}

---

## 평가 결과는 반드시 다음 JSON 형식만으로 제공해 주세요:
```json
{{
  "score": "OPIC 레벨 (예: IM2, IH, AL 등)",
  "feedback": {{
    "paragraph": "HTML 형식의 Text Type & Cohesion 피드백",
    "vocabulary": "HTML 형식의 Accuracy & Content 피드백",
    "delivery": "HTML 형식의 Accuracy & Functions (전달력) 피드백"
  }}
}}
"""

# 전체 테스트 종합 평가를 위한 프롬프트 템플릿 - 수정됨
OVERALL_EVALUATION_PROMPT_TEMPLATE = """
당신은 **ACTFL Proficiency Guidelines 2024 (Speaking)** 기준에 따라 수험자의 전체 OPIC 테스트 결과를 종합적으로 평가하는 전문 평가자입니다.

---

## 평가 지침

-   제시된 모든 문제별 응답과 평가 결과를 종합하여 **ACTFL 2024 Speaking 기준 (FACT)** 에 따라 전체 OPIC 등급(NH ~ AL)을 결정해 주세요.
-   **Functions, Accuracy, Context and Content, Text Type (FACT)** 네 가지 기준을 **일관되게** 보여주는 최고 등급을 최종 등급으로 판단합니다. 특정 문제에서 더 높은 등급의 특징을 보이더라도, 전체적으로 **지속적인(sustained)** 능력을 보여주지 못하면 해당 등급을 부여할 수 없습니다.
-   각 문제 유형(콤보셋, 롤플레잉, 돌발질문)별 평균적인 수행 능력 수준도 평가에 참고하여 점수를 제시하세요.
-   모든 피드백은 <b>HTML 형식</b>으로 작성되어야 합니다.
-   종합 피드백 작성 시, 수험자의 전반적인 강점을 언급하고, <b>“다음 등급으로 올라가기 위해 보완해야 할 점”</b>을 FACT 기준에 맞춰 구체적으로 제시하세요.
-   테스트 중 <b>질문과 관련 없는 응답이 있었다면 반드시 종합 피드백에서 지적</b>해 주세요.

---

## ACTFL 2024 Speaking 등급 정의 (OPIC 적용 요약):

-   <b>Novice (NL, NM, NH)</b>: 단어, 구, 암기된 문장 위주. 제한적 소통.
-   <b>Intermediate Low (IL)</b>: 기본적인 생존 요구 관련 창의적 문장 생성 시작. 짧고 단순하며, 오류 많고 망설임.
-   <b>Intermediate Mid (IM1, IM2, IM3)</b>: 예측 가능한 일상 주제 관련 문장 단위 소통. 문장 연결 시도. 자신감/어휘/정확성 증가. IM3는 IH에 근접.
-   <b>Intermediate High (IH)</b>: **Advanced 수준 기능(시제 활용 서술/묘사, 문단 단위 발화) 수행 가능**하나, **일관성 부족 및 오류/붕괴 발생**. Advanced 수준을 지속하지 못함.
-   <b>Advanced Low/Mid (AL)</b>: **Advanced 수준 기능(시제 활용 서술/묘사, 문단 단위 발화, 상황 대처)을 일관되게 수행**. 연결성, 명확성, 정확성 갖춤. OPIC의 AL은 주로 ACTFL Advanced Low/Mid에 해당.
-   <b>Superior & Distinguished</b>: OPIC 범위 초과. 추상적 토론, 가설 설정, 설득, 전문적 주제 등.

---

## 문제별 응답 및 평가 결과 요약:
{problem_responses}

## 테스트 구성:
-   자기소개: {self_introduction_count}문제
-   콤보셋: {comboset_count}문제
-   롤플레잉: {roleplaying_count}문제
-   돌발질문: {unexpected_count}문제

---

## 결과는 반드시 다음 JSON 형식으로 출력하세요.
<b>모든 피드백은 HTML 형식으로 작성되어야 하며, 문단 구분은 `<br><br>`, 중요 표현은 `<b>강조</b>` 처리해야 합니다.</b>

```json
{{
  "test_score": {{
    "total_score": "최종 종합 OPIC 레벨 (예: IM2, IH, AL 등)",
    "comboset_score": "콤보셋 평균 수행 레벨 (예: IM2, IH, AL 등)",
    "roleplaying_score": "롤플레잉 평균 수행 레벨 (예: IM2, IH, AL 등)",
    "unexpected_score": "돌발질문 평균 수행 레벨 (예: IM2, IH, AL 등)"
  }},
  "test_feedback": {{
    "total_feedback": "HTML 형식의 전체적인 강점 및 다음 등급을 위한 종합 피드백",
    "paragraph": "HTML 형식의 Text Type & Cohesion 종합 피드백",
    "vocabulary": "HTML 형식의 Accuracy & Content 종합 피드백",
    "delivery": "HTML 형식의 Accuracy & Functions (전달력) 종합 피드백"
  }}
}}
"""


from core.metrics import LLM_API_DURATION, track_time_async, track_problem_evaluation_time

class ResponseEvaluator:
    """OPIC 응답 평가 클래스"""
    
    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        """
        평가기 초기화
        
        Args:
            model_name: 사용할 LLM 모델 이름
        """
        self.model_name = model_name
        
        # 프롬프트 템플릿 및 파서 초기화
        self.evaluation_prompt = PromptTemplate(
            template=EVALUATION_PROMPT_TEMPLATE,
            input_variables=["user_response", "problem_category", "topic_category", "problem"]
        )
        
        self.overall_prompt = PromptTemplate(
            template=OVERALL_EVALUATION_PROMPT_TEMPLATE,
            input_variables=[
                "problem_responses", 
                "self_introduction_count", 
                "comboset_count", 
                "roleplaying_count", 
                "unexpected_count"
            ]
        )
        
        # JSON 파서
        self.evaluation_parser = JsonOutputParser()
        self.overall_parser = JsonOutputParser()
    
    def _get_llm(self):
        """
        API 키 순환을 적용한 LLM 인스턴스 반환
        """
        # Groq 모델 사용
        # api_key = get_next_groq_key()
        
        # return ChatGroq(
        #     model=self.model_name,
        #     temperature=0.3,
        #     api_key=api_key
        # )

        api_key = get_next_gemini_key()
    
        if not api_key:
            logger.error("유효한 Gemini API 키를 찾을 수 없습니다.")
            raise ValueError("Gemini API 키가 설정되지 않았습니다.")
        
        logger.info(f"Gemini LLM 초기화 중 - 모델: gemini-1.5-pro")
        
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0.3,
            google_api_key=api_key,
            convert_system_message_to_human=True
        )

    @track_time_async(LLM_API_DURATION, {"provider": "google", "model": "gemini-1.5-pro", "operation": "evaluate_response"})
    async def evaluate_response(
        self, 
        user_response: str, 
        problem_category: str,
        topic_category: str, 
        problem: str
    ) -> Dict[str, Any]:
        """
        사용자 응답을 평가하여 점수와 피드백 제공
        
        Args:
            user_response: 사용자 응답 텍스트
            problem_category: 문제 카테고리
            topic_category: 토픽 카테고리
            problem: 문제 내용
            
        Returns:
            평가 결과 딕셔너리
        """
        start_time = time.time()
        status = "success"

        try:
            logger.info(f"응답 평가 시작 - 문제 카테고리: {problem_category}, 토픽: {topic_category}")
            
            # 응답이 너무 짧으면 즉시 낮은 점수 반환
            if len(user_response.split()) < 5:
                logger.warning(f"응답이 너무 짧음: '{user_response}'")
                return {
                    "score": "NL",
                    "feedback": {
                        "paragraph": "응답이 너무 짧아 평가할 수 없습니다. 최소 한 문장 이상의 응답이 필요합니다.",
                        "vocabulary": "응답이 너무 짧아 어휘력을 평가할 수 없습니다.",
                        "spoken_amount": "발화량이 매우 부족합니다. 질문에 대해 충분한 길이로 답변해야 합니다."
                    }
                }
            
            # API 키 순환을 적용한 LLM 인스턴스 생성
            llm = self._get_llm()
            
            # 최신 API 방식으로 체인 구성
            chain = self.evaluation_prompt | llm | self.evaluation_parser
            
            # 체인 실행
            result = await chain.ainvoke({
                "user_response": user_response,
                "problem_category": problem_category,
                "topic_category": topic_category,
                "problem": problem
            })
            
            # 결과 유효성 검증 및 보정
            result = self._validate_and_fix_evaluation(result)
            
            logger.info(f"응답 평가 완료 - 점수: {result.get('score', 'N/A')}")
            return result
            
        except Exception as e:
            status = "error"
            logger.error(f"응답 평가 중 오류 발생: {str(e)}", exc_info=True)
            # 오류 발생 시 점수를 제공하지 않고 오류 정보만 반환
            return {
                "score": "ERROR",  # 점수를 제공하지 않고 ERROR 표시
                "feedback": {
                    "paragraph": f"평가 중 오류가 발생했습니다: {str(e)}. 논리적 구성에 대한 평가를 완료하지 못했습니다.",
                    "vocabulary": "평가 중 오류가 발생했습니다. 어휘 사용에 대한 평가를 완료하지 못했습니다.",
                    "spoken_amount": "평가 중 오류가 발생했습니다. 발화량에 대한 평가를 완료하지 못했습니다."
                },
                "error": True  # 평가 오류 플래그 추가
            }
        finally:
            # 평가 시간 측정 추가
            duration = time.time() - start_time
            track_problem_evaluation_time(problem_category, duration, status)
    


    @track_time_async(LLM_API_DURATION, {"provider": "google", "model": "gemini-1.5-pro", "operation": "evaluate_overall_test"})
    async def evaluate_overall_test(
        self,
        test_data: Dict[str, Any],
        problem_details: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        전체 테스트의 종합 평가 수행
        
        Args:
            test_data: 테스트 정보
            problem_details: 문제별 상세 정보 및 평가 결과
            
        Returns:
            종합 평가 결과 딕셔너리
        """
        try:
            logger.info(f"전체 테스트 종합 평가 시작 - 문제 수: {len(problem_details)}")
            
            # 테스트 유형 확인
            test_type = test_data.get("test_type", False)
            
            # 문제 유형별 카운트 및 분류
            self_introduction_count, comboset_count, roleplaying_count, unexpected_count = 0, 0, 0, 0
            
            self_introduction_responses = []
            comboset_responses = []
            roleplaying_responses = []
            unexpected_responses = []
            
            # 문제별 응답 텍스트 구성 및 유형별 분류
            problem_responses_text = ""
            
            for problem_number, problem_data in problem_details.items():
                problem_number_int = int(problem_number)
                problem_type = self._get_problem_type(problem_number_int, test_data)
                
                response = problem_data.get("user_response", "")
                score = problem_data.get("score", "")
                if score == "ERROR" or "error" in problem_data:
                    score = "N/A"  # 오류가 발생한 문제는 점수를 N/A로 표시
                problem_text = problem_data.get("problem", "")
                
                # 문제 유형별 카운트 및 응답 정보 수집 - 오류가 아닌 응답만 처리
                if score != "N/A":  # 오류가 발생하지 않은 경우에만 평가에 포함
                    if problem_type == "self_introduction":
                        self_introduction_count += 1
                        self_introduction_responses.append({"response": response, "score": score})
                    elif problem_type == "comboset":
                        comboset_count += 1
                        comboset_responses.append({"response": response, "score": score})
                    elif problem_type == "roleplaying":
                        roleplaying_count += 1
                        roleplaying_responses.append({"response": response, "score": score})
                    elif problem_type == "unexpected":
                        unexpected_count += 1
                        unexpected_responses.append({"response": response, "score": score})
                
                # 종합 평가를 위한 문제별 응답 텍스트 구성
                problem_responses_text += f"### 문제 {problem_number} ({problem_type}):\n"
                problem_responses_text += f"- 문제: {problem_text}\n"
                problem_responses_text += f"- 응답: {response}\n"
                problem_responses_text += f"- 점수: {score}\n\n"
            
            # 유형별 평균 점수 계산
            comboset_score = self._calculate_average_level([r["score"] for r in comboset_responses]) if comboset_responses else "N/A"
            roleplaying_score = self._calculate_average_level([r["score"] for r in roleplaying_responses]) if roleplaying_responses else "N/A"
            unexpected_score = self._calculate_average_level([r["score"] for r in unexpected_responses]) if unexpected_responses else "N/A"
            
            # 전체 점수 계산 (가중치 적용)
            all_scores = []
            if self_introduction_responses:
                all_scores.extend([r["score"] for r in self_introduction_responses])
            if comboset_responses:
                all_scores.extend([r["score"] for r in comboset_responses])
            if roleplaying_responses:
                all_scores.extend([r["score"] for r in roleplaying_responses])
            if unexpected_responses:
                all_scores.extend([r["score"] for r in unexpected_responses])
            
            total_score = self._calculate_average_level(all_scores) if all_scores else "N/A"
            
            # API 키 순환을 적용한 LLM 인스턴스 생성
            llm = self._get_llm()
            
            # 종합 평가 체인 구성 및 실행
            chain = self.overall_prompt | llm | self.overall_parser
            
            result = await chain.ainvoke({
                "problem_responses": problem_responses_text,
                "self_introduction_count": self_introduction_count,
                "comboset_count": comboset_count,
                "roleplaying_count": roleplaying_count,
                "unexpected_count": unexpected_count
            })
            
            # 계산된 점수로 결과 보정
            if "test_score" in result:
                result["test_score"]["total_score"] = total_score
                result["test_score"]["comboset_score"] = comboset_score
                result["test_score"]["roleplaying_score"] = roleplaying_score
                result["test_score"]["unexpected_score"] = unexpected_score
            else:
                result["test_score"] = {
                    "total_score": total_score,
                    "comboset_score": comboset_score,
                    "roleplaying_score": roleplaying_score,
                    "unexpected_score": unexpected_score
                }
            
            logger.info(f"전체 테스트 종합 평가 완료 - 총점: {total_score}")
            return result
            
        except Exception as e:
            logger.error(f"종합 평가 중 오류 발생: {str(e)}", exc_info=True)
            # 오류 발생 시 계산된 값 사용, 없으면 "N/A" 반환
            return {
                "test_score": {
                    "total_score": total_score if 'total_score' in locals() else "N/A",
                    "comboset_score": comboset_score if 'comboset_score' in locals() else "N/A",
                    "roleplaying_score": roleplaying_score if 'roleplaying_score' in locals() else "N/A",
                    "unexpected_score": unexpected_score if 'unexpected_score' in locals() else "N/A"
                },
                "test_feedback": {
                    "total_feedback": f"평가 중 오류가 발생했습니다: {str(e)}. 전체 영어 구사력에 대한 평가를 완료하지 못했습니다.",
                    "paragraph": "평가 중 오류가 발생했습니다. 문단 구성력에 대한 종합 평가를 제공할 수 없습니다.",
                    "vocabulary": "평가 중 오류가 발생했습니다. 어휘력에 대한 종합 평가를 제공할 수 없습니다.",
                    "spoken_amount": "평가 중 오류가 발생했습니다. 발화량에 대한 종합 평가를 제공할 수 없습니다."
                }
            }
    


    def _get_problem_type(self, problem_number: int, test_data: Dict[str, Any]) -> str:
        """
        문제 번호와 테스트 정보에 따라 문제 유형 결정
        
        Args:
            problem_number: 문제 번호 (1부터 시작)
            test_data: 테스트 정보 딕셔너리
            
        Returns:
            문제 유형 문자열
        """
        # test_data가 None이거나 유효하지 않은 경우
        if not test_data:
            logger.error(f"유효하지 않은 test_data: {test_data}")
            raise ValueError("유효한 test_data가 필요합니다.")

        # test_type_str 우선 확인
        test_type_str = test_data.get("test_type_str")
        if test_type_str:
            logger.info(f"test_type_str로 문제 유형 결정: {test_type_str}")
            if test_type_str == "single":
                return "single"
            elif test_type_str == "category":  # 수정: category로 변경
                problem_data = test_data.get("problem_data", {})
                if str(problem_number) in problem_data:
                    problem_category = problem_data[str(problem_number)].get("problem_category", "").lower()
                    logger.info(f"유형별 테스트 문제 카테고리: {problem_category}")
                    if "롤플레이" in problem_category or "roleplay" in problem_category:
                        return "roleplaying"
                    elif "콤보셋" in problem_category or "comboset" in problem_category:
                        return "comboset"
                    elif "자기소개" in problem_category or "introduction" in problem_category:
                        return "self_introduction"
                    elif "돌발" in problem_category or "unexpected" in problem_category:
                        return "unexpected"
                return "comboset"  # 기본값
            elif test_type_str == "full_test":
                if problem_number == 1:
                    return "self_introduction"
                elif 2 <= problem_number <= 10:
                    return "comboset"
                elif 11 <= problem_number <= 13:
                    return "roleplaying"
                else:  # 14~15
                    return "unexpected"
        
        # test_type (bool) 필드 확인
        test_type = test_data.get("test_type")
        logger.info(f"test_type으로 문제 유형 결정: {test_type}")
        
        if test_type is True:  # Half 테스트
            if len(test_data.get("problem_data", {})) == 1:
                return "single"
            elif 1 <= problem_number <= 3:
                return "comboset"
            elif 4 <= problem_number <= 5:
                return "roleplaying"
            else:
                return "unexpected"
        elif test_type is False:  # Full 테스트
            if problem_number == 1:
                return "self_introduction"
            elif 2 <= problem_number <= 10:
                return "comboset"
            elif 11 <= problem_number <= 13:
                return "roleplaying"
            else:  # 14~15
                return "unexpected"
        
        # 모든 분기에서 해당되지 않는 경우
        logger.error(f"문제 유형을 결정할 수 없습니다. test_data: {test_data}")
        raise ValueError(f"문제 유형을 결정할 수 없습니다. test_data: {test_data}")
    
    def _calculate_average_level(self, levels: List[str]) -> str:
        """
        오픽 레벨 문자열 목록의 평균 레벨 계산
        
        Args:
            levels: 오픽 레벨 문자열 목록
            
        Returns:
            평균 레벨 문자열
        """
        # 레벨이 없으면 N/A 반환
        if not levels:
            return "N/A"
        
        # 오류가 있는 평가 결과는 제외
        valid_levels = [level for level in levels if level != "ERROR" and level in OPIC_LEVELS]
        
        # 유효한 레벨이 없으면 N/A 반환
        if not valid_levels:
            return "N/A"
        
        # 레벨을 숫자로 변환
        level_values = []
        for level in levels:
            try:
                level_index = OPIC_LEVELS.index(level)
                level_values.append(level_index)
            except (ValueError, IndexError):
                # 유효하지 않은 레벨은 건너뛰기
                continue
        
        # 변환된 값이 없으면 N/A 반환
        if not level_values:
            return "N/A"

        # 평균 계산 및 가장 가까운 레벨 반환
        average_value = sum(level_values) / len(level_values)
        closest_index = round(average_value)
        
        # 인덱스 범위 확인
        if closest_index < 0:
            closest_index = 0
        elif closest_index >= len(OPIC_LEVELS):
            closest_index = len(OPIC_LEVELS) - 1
        
        return OPIC_LEVELS[closest_index]
    
    def _validate_and_fix_evaluation(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        평가 결과의 유효성을 검증하고 필요시 보정
        
        Args:
            result: LLM에서 반환된 평가 결과
            
        Returns:
            검증 및 보정된 평가 결과
        """
        # 결과가 없거나 필수 필드가 없는 경우 기본값 설정
        if not result or not isinstance(result, dict):
            logger.warning("평가 결과가 유효하지 않습니다. 기본값으로 설정합니다.")
            result = {}
        
        # 점수 필드 검증 및 보정
        if "score" not in result or not result["score"] or result["score"] not in OPIC_LEVELS:
            result["score"] = "NL"  # 오류가 아닌 경우에는 최하 점수인 NL 부여
            logger.warning(f"유효하지 않은 점수를 'NL'로 대체합니다.")
        
        # 피드백 필드 검증 및 보정
        if "feedback" not in result or not isinstance(result["feedback"], dict):
            result["feedback"] = {}
            logger.warning("피드백 필드가 유효하지 않습니다. 새로 생성합니다.")
        
        # 피드백 세부 항목 검증 및 보정
        feedback_fields = ["paragraph", "vocabulary", "spoken_amount"]
        for field in feedback_fields:
            if field not in result["feedback"] or not result["feedback"][field]:
                default_msg = f"{field} 평가 정보가 누락되어 기본값으로 설정되었습니다."
                result["feedback"][field] = default_msg
                logger.warning(f"피드백 항목 '{field}'가 없거나 유효하지 않습니다.")
        
        return result
    
    
    def evaluate_overall_test_sync(self, test_data, problem_details):
        """
        전체 테스트의 종합 평가를 동기적으로 수행하는 메소드
        Celery 작업에서 호출할 때 사용됩니다.
        """
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                self.evaluate_overall_test(test_data, problem_details)
            )
            return result
        except Exception as e:
            logger.error(f"종합 평가 동기 실행 중 오류 발생: {str(e)}", exc_info=True)
            return {
                "test_score": {
                    "total_score": "N/A",
                    "comboset_score": "N/A",
                    "roleplaying_score": "N/A",
                    "unexpected_score": "N/A"
                },
                "test_feedback": {
                    "total_feedback": f"평가 실행 중 오류가 발생했습니다: {str(e)}",
                    "paragraph": "문단 구성력에 대한 평가를 제공할 수 없습니다.",
                    "vocabulary": "어휘력에 대한 평가를 제공할 수 없습니다.",
                    "spoken_amount": "발화량에 대한 평가를 제공할 수 없습니다."
                }
            }
        finally:
            loop.close()


    # def evaluate_response_sync(self, user_response, problem_category, topic_category, problem):
    #     """
    #     사용자 응답 평가를 동기적으로 수행하는 메소드
        
    #     Celery 작업에서 호출할 때 사용됩니다.
        
    #     Args:
    #         user_response: 사용자 응답 텍스트
    #         problem_category: 문제 카테고리 (self_introduction, comboset, roleplaying, unexpected)
    #         topic_category: 주제 카테고리
    #         problem: 문제 내용
        
    #     Returns:
    #         평가 결과 딕셔너리 (score와 feedback 포함)
    #     """
    #     import asyncio
        
    #     # 비동기 함수를 동기적으로 실행하기 위한 새 이벤트 루프 생성
    #     loop = asyncio.new_event_loop()
    #     asyncio.set_event_loop(loop)
        
    #     try:
    #         # evaluate_response 메소드가 비동기 메소드라고 가정
    #         result = loop.run_until_complete(self.evaluate_response(
    #             user_response=user_response,
    #             problem_category=problem_category,
    #             topic_category=topic_category,
    #             problem=problem
    #         ))
    #         return result
    #     except Exception as e:
    #         logger.error(f"응답 평가 동기 실행 중 오류 발생: {str(e)}", exc_info=True)
    #         # 오류 발생 시 기본 평가 결과 반환
    #         return {
    #             "score": "N/A",
    #             "feedback": {
    #                 "paragraph": f"평가 중 오류가 발생했습니다: {str(e)}",
    #                 "vocabulary": "평가를 완료할 수 없습니다.",
    #                 "spoken_amount": "평가를 완료할 수 없습니다."
    #             }
    #         }
    #     finally:
    #         # 이벤트 루프 종료
    #         loop.close()

    def evaluate_response_sync(self, user_response, problem_category, topic_category, problem):
        """
        사용자 응답 평가 실행
        
        Args:
            user_response: 사용자 음성 응답 텍스트
            problem_category: 문제 카테고리 (예: 일상생활, 과거 경험)
            topic_category: 주제 카테고리 (예: 여행, 음식)
            problem: 문제 내용
            
        Returns:
            평가 결과 사전
        """
        logger.info(f"응답 평가 시작 - 문제 카테고리: {problem_category}, 토픽: {topic_category}")
        
        # 10번 재시도 루프
        retry_count = 0
        max_retries = 10
        
        while retry_count < max_retries:
            try:
                # LLM 초기화
                llm = self._get_llm()
                current_key = None
                
                # 현재 키 추출
                if hasattr(llm, 'google_api_key'):
                    current_key = llm.google_api_key
                
                # 프롬프트 포맷
                evaluation_chain = (
                    self.evaluation_prompt 
                    | llm 
                    | self.evaluation_parser
                )
                
                # 평가 실행
                result = evaluation_chain.invoke({
                    "user_response": user_response,
                    "problem_category": problem_category,
                    "topic_category": topic_category,
                    "problem": problem
                })
                
                return result
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e).lower()
                
                # 현재 사용 중인 키가 있으면 오류 처리
                if current_key and ("quota" in error_msg or "rate limit" in error_msg or "exceeded" in error_msg):
                    handle_api_error(current_key, error_msg)
                
                logger.warning(f"평가 중 오류 발생 ({retry_count}/{max_retries}): {str(e)}")
                
                if retry_count >= max_retries:
                    logger.error(f"최대 재시도 횟수에 도달했습니다: {str(e)}")
                    raise ValueError(f"응답 평가 중 오류가 발생했습니다: {str(e)}")
                
                # 다음 시도 전에 잠시 대기
                time.sleep(2)


