import logging
from typing import Dict, List, Any
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

from api.deps import get_next_groq_key, get_next_gemini_key

import time

# 로깅 설정
logger = logging.getLogger(__name__)

# 오픽 레벨 정의
OPIC_LEVELS = [
    "NL", "NM", "NH",  # Novice
    "IL", "IM1", "IM2", "IM3", "IH",  # Intermediate
    "AL"  # Advanced
]

# 평가 기준에 대한 상세 설명
LEVEL_DESCRIPTIONS = {
    # Novice 레벨
    "NL": "기본 어휘와 간단한 문장만 사용. 개인적이고 일상적인 주제에 대해서만 제한적으로 대화 가능.",
    "NM": "기본적인 개인 정보를 표현하고 제한된 어휘와 간단한 문장으로 소통 가능.",
    "NH": "알고 있는 단어나 구문, 간단한 문장으로 자신을 표현 가능. 제한된 어휘와 정확성.",
    
    # Intermediate 레벨
    "IL": "일상적인 소재에서 간단한 문장으로 대화 가능. 대화에 참여는 가능하지만 유지하기 어려움.",
    "IM1": "일상 주제에 대해 기본적인 문장으로 소통 가능. 짧은 대화 유지 가능하나 언어 정확성 부족.",
    "IM2": "일상적인 주제에서 문장과 단문 구조로 소통 가능. 대화 유지 능력이 향상되고 어휘 다양성 증가.",
    "IM3": "자주 사용하는 구조와 어휘를 활용하여 명료하게 소통 가능하며, 다른 언어의 영향 감소.",
    "IH": "대부분의 상황에서 문장 수준의 언어 사용 가능. 개인적 주제와 사회적 맥락에서 소통 가능하며, 문장 또는 문장 연결 수준의 답변 생성 가능.",
    
    # Advanced 레벨
    "AL": "일상적 대화 및 업무 관련 상황에서 완전히 참여 가능. 과거, 현재, 미래 시제를 사용하여 서술하고 묘사 가능하며, 문단 단위의 논리적인 답변 생성 가능",
}

# 오픽 평가 기준에 대한 상세 설명을 담은 프롬프트 템플릿
EVALUATION_PROMPT_TEMPLATE = """
당신은 OPIC(Oral Proficiency Interview-Computer) Speaking 평가 기준에 따라 수험자의 발화를 평가하는 전문 평가자입니다.

---

## 중요 지침
- 제시된 응답을 아래 기준에 따라 **한국어로** 평가해 주세요.
- 피드백을 생성할 때는, <b>예상되는 등급보다 높은 레벨로 올라가기 위해서 어떤 것을 보완해야 하는지</b>를 위주로 설명해주세요.
- 반드시 <b>질문과 연관 있는 응답인지 확인</b>해서 평가해주세요.

---

## 중요: 의미 없는 응답 감지
먼저 응답이 의미 있는 발화인지 확인하세요.

- "에베베베", "아아아", "음음음", "ㅋㅋㅋ" 등 실제 단어가 아니거나 무의미한 소리의 반복만 있는 경우 → <b>"즉시 NL 점수"</b>를 부여하세요.  
  이 경우에는 <b>간단한 이유만 피드백</b>으로 작성하세요. 예: "실제 발화가 없어 의미를 파악할 수 없습니다."

- 문장은 되었지만 질문과 **전혀 관련 없는 응답**이라면 → <b>가능한 등급을 매긴 후</b>,  
  피드백에 <b>“질문과 관련 없는 응답이었습니다”</b>를 반드시 포함해 주세요.

---

## 점수 판단 기준: ACTFL Speaking Proficiency (FACT)
다음 네 가지 기준에 따라 수험자의 말하기 능력을 분석하여 최종 등급을 판단해 주세요:

1. <b>Functions</b>: 수험자가 어떤 말하기 기능(묘사, 설명, 질문, 의견 진술 등)을 지속적으로 수행할 수 있는지
2. <b>Accuracy</b>: 문법, 어휘, 발음, 억양의 정확성과 자연스러움
3. <b>Context and Content</b>: 어떤 주제나 상황에서 효과적으로 의사소통할 수 있는지
4. <b>Text Type</b>: 단어, 문장, 문단 등 발화 길이와 복잡성

---

## 등급 정의 (ACTFL 기준)

- <b>NL</b>: 단어나 문장을 거의 생성하지 못하며, 무의미한 소리를 반복하거나 질문과 전혀 관련 없는 말
- <b>NM</b>: 인사, 이름 말하기, 나이 등 아주 기본적인 표현만 가능
- <b>NH</b>: 제한된 주제에 대해 단순 문장으로 대답 가능하나, 반복적이고 형식적
- <b>IL</b>: 일상적 주제에 대해 간단한 문장으로 대화 가능하지만 지속성은 부족
- <b>IM1</b>: 간단한 질문과 응답이 가능하며 문장이 연결되기 시작함
- <b>IM2</b>: 다양한 일상 주제에 대해 문장과 단문 수준으로 소통 가능
- <b>IM3</b>: 대부분의 상황에서 명확하게 소통 가능, 오류는 있지만 의사소통엔 큰 지장 없음
- <b>IH</b>: 복잡한 문장을 사용하고 문단 수준 연결 가능, 다양한 맥락에서도 대체로 성공적으로 말함
- <b>AL</b>: 과거-현재-미래 시제를 자유롭게 사용하고 문단 단위의 설명/묘사 가능. 논리적 구조를 갖춘 응답 가능

---

## 피드백 구성 (무조건 HTML 형식으로)
다음 항목별로 피드백을 제공합니다. <b>피드백은 반드시 HTML 형식으로 작성</b>해야 하며, 다음 항목을 포함해야 합니다:

- <b>paragraph</b>: 문단 구성력 (논리적 연결과 구조적 완성도)
- <b>vocabulary</b>: 어휘력 및 정확성 (문법 포함)
- <b>spoken_amount</b>: 발화량 및 풍부함 (응답 길이, filler 사용 여부 등)

1. 문단 구분이 필요한 경우 <br><br>를 사용하세요.
2. 중요한 포인트는 <b>강조할 내용</b> 형식으로 볼드 처리하세요.
3. 피드백은 가독성이 좋게 작성해주세요.
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
  "score": "레벨(예: IM2, IH, AL 등)",
  "feedback": {{
    "paragraph": "HTML 형식의 문단 구성력 피드백(예: <b>강조</b> 태그 사용 가능, <br><br>로 문단 구분)",
    "vocabulary": "HTML 형식의 어휘력 피드백(예: <b>강조</b> 태그 사용 가능, <br><br>로 문단 구분)",
    "spoken_amount": "HTML 형식의 발화량 피드백(예: <b>강조</b> 태그 사용 가능, <br><br>로 문단 구분)"
  }}
}}
"""

# 전체 테스트 종합 평가를 위한 프롬프트 템플릿 - 수정됨
OVERALL_EVALUATION_PROMPT_TEMPLATE = """
당신은 OPIC(Oral Proficiency Interview-Computer) Speaking 평가 기준에 따라 수험자의 전체 테스트 결과를 종합적으로 평가하는 전문 평가자입니다.

---

## 평가 지침

- 모든 응답을 종합해 **ACTFL Proficiency Guidelines 2024 (Speaking 기준)**에 따라 전체 점수를 판단해 주세요.
- **Functions, Accuracy, Context and Content, Text Type** 네 가지 기준(FACT)을 기반으로 레벨을 결정해 주세요.
- 각 유형(콤보셋, 롤플레잉, 돌발질문)의 평균 점수도 포함해 주세요.
- 모든 피드백은 <b>HTML 형식</b>으로 작성되어야 합니다.
- 피드백 작성 시 <b>“다음 등급으로 올라가기 위해 보완할 점”</b> 위주로 작성하세요.
- <b>질문과 관련 없는 응답이 있는 경우 반드시 지적</b>해 주세요.

---

## ACTFL Speaking 등급 정의

- <b>NL</b>: 단어나 문장을 거의 생성하지 못함. 무의미한 소리 반복.
- <b>NM</b>: 기본 인사, 이름, 나이 등 단편적 표현만 가능
- <b>NH</b>: 익숙한 주제에 대해 단문으로 대화 가능하나 확장 어려움
- <b>IL</b>: 단순 문장으로 일상 주제 대화 가능하나 유지 어려움
- <b>IM1</b>: 짧은 문장을 연결하여 대화 가능. 일관성은 부족
- <b>IM2</b>: 문장 단위로 일관되게 말함. 어휘와 정확성 증가
- <b>IM3</b>: 대부분 상황에서 명확히 의사 표현 가능. 오류는 있으나 방해되지 않음
- <b>IH</b>: 다양한 문장 구조와 시제 사용 가능. 문단 단위 말하기 시도
- <b>AL</b>: 과거-현재-미래 서술 가능. 구조적 문단 표현. 추상적 주제 일부 가능

---

## 문제별 응답 및 평가 결과:
{problem_responses}

## 테스트 구성:
- 자기소개: {self_introduction_count}문제
- 콤보셋: {comboset_count}문제
- 롤플레잉: {roleplaying_count}문제
- 돌발질문: {unexpected_count}문제

---

## 결과는 반드시 다음 JSON 형식으로 출력하세요.  
<b>모든 피드백은 HTML 형식으로 작성되어야 하며, <b>문단 단위 구분은 <code><br><br></code>를 사용하고 중요한 표현은 <code><b>강조</b></code> 처리</b> 해야 합니다.</b>

```json
{{
  "test_score": {{
    "total_score": "종합 레벨(예: IM2, IH, AL 등)",
    "comboset_score": "콤보셋 평균 레벨(예: IM2, IH, AL 등)",
    "roleplaying_score": "롤플레잉 평균 레벨(예: IM2, IH, AL 등)",
    "unexpected_score": "돌발질문 평균 레벨(예: IM2, IH, AL 등)"
  }},
  "test_feedback": {{
    "total_feedback": "HTML 형식의 전체 영어 구사력 피드백(예: <b>강조</b> 태그 사용 가능, <br><br>로 문단 구분)",
    "paragraph": "HTML 형식의 문단 구성력 피드백(예: <b>강조</b> 태그 사용 가능, <br><br>로 문단 구분)",
    "vocabulary": "HTML 형식의 어휘력 피드백(예: <b>강조</b> 태그 사용 가능, <br><br>로 문단 구분)",
    "spoken_amount": "HTML 형식의 발화량 피드백(예: <b>강조</b> 태그 사용 가능, <br><br>로 문단 구분)"
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

    @track_time_async(LLM_API_DURATION, {"model": "gemini-1.5-pro", "operation": "evaluate_response"})
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
    


    @track_time_async(LLM_API_DURATION, {"model": "gemini-1.5-pro", "operation": "evaluate_overall_test"})
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


    def evaluate_response_sync(self, user_response, problem_category, topic_category, problem):
        """
        사용자 응답 평가를 동기적으로 수행하는 메소드
        
        Celery 작업에서 호출할 때 사용됩니다.
        
        Args:
            user_response: 사용자 응답 텍스트
            problem_category: 문제 카테고리 (self_introduction, comboset, roleplaying, unexpected)
            topic_category: 주제 카테고리
            problem: 문제 내용
        
        Returns:
            평가 결과 딕셔너리 (score와 feedback 포함)
        """
        import asyncio
        
        # 비동기 함수를 동기적으로 실행하기 위한 새 이벤트 루프 생성
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # evaluate_response 메소드가 비동기 메소드라고 가정
            result = loop.run_until_complete(self.evaluate_response(
                user_response=user_response,
                problem_category=problem_category,
                topic_category=topic_category,
                problem=problem
            ))
            return result
        except Exception as e:
            logger.error(f"응답 평가 동기 실행 중 오류 발생: {str(e)}", exc_info=True)
            # 오류 발생 시 기본 평가 결과 반환
            return {
                "score": "N/A",
                "feedback": {
                    "paragraph": f"평가 중 오류가 발생했습니다: {str(e)}",
                    "vocabulary": "평가를 완료할 수 없습니다.",
                    "spoken_amount": "평가를 완료할 수 없습니다."
                }
            }
        finally:
            # 이벤트 루프 종료
            loop.close()


