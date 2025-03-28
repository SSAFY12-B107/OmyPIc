import logging
from typing import Dict, List, Any
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

from api.deps import get_next_groq_key, get_next_gemini_key

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
당신은 OPIC(Oral Proficiency Interview-Computer) 시험의 전문 평가자입니다. 제시된 응답을 아래 기준에 따라 **한국어로** 평가해 주세요.
피드백을 생성할 때는, 예상되는 등급보다 높은 등급의 레벨로 올라가기 위해서 어떤 것을 보완해야 하는지를 위주로 설명해주세요.
또한, 질문과 연관있는 답변을 하고 있는지 필수적으로 확인해서 피드백해주세요.

## 중요: 의미 없는 응답 감지
가장 먼저, 응답이 의미가 있는지 확인하세요. "에베베베", "아아아", "음음음" 등과 같이 실제 단어가 아니거나 의미 없는 소리의 나열, 또는 질문과 전혀 관련 없는 무의미한 응답인 경우 즉시 최하 점수인 "NL"을 부여하세요.
이런 응답에 대해서는 이유를 설명하는 간단한 피드백만 제공하세요.

## 평가할 응답:
"{user_response}"

## 문제 유형 및 내용:
- 문제 카테고리: {problem_category}
- 토픽 카테고리: {topic_category}
- 문제: {problem}

## OPIC 레벨 기준:
1. Novice(초급): 
   - NL/NM/NH: 기본적인 개인 정보를 표현하고 알고 있는 단어나 구문으로 소통. 제한된 어휘와 정확성.

2. Intermediate(중급):
   - IL: 일상적인 소재에서 간단한 문장으로 대화 가능하나 유지하기 어려움.
   - IM1: 일상 주제에 대해 기본적인 문장으로 소통 가능. 짧은 대화 유지 가능하나 언어 정확성 부족.
   - IM2: 일상적인 주제에서 단문 구조로 소통 가능. 대화 유지 능력 향상, 어휘 다양성 증가.
   - IM3: 자주 사용하는 구조와 어휘를 활용하여 명료하게 소통. 다른 언어의 영향 감소.
   - IH: 대부분의 상황에서 문장 수준의 언어 사용. 개인적 주제와 사회적 맥락에서 소통 가능.

3. Advanced(고급):
   - AL: "일상적 대화 및 업무 관련 상황에서 완전히 참여 가능. 과거, 현재, 미래 시제를 사용하여 서술하고 묘사 가능하며, 문단 단위의 논리적인 답변 생성 가능"

## 평가 영역:
1. 문단 구성력(Paragraph): 응답의 논리적 구성, 연결성, 일관성
2. 어휘력(Vocabulary): 어휘의 다양성, 적절성, 정확성
3. 발화량(Spoken Amount): 응답의 길이, 내용의 풍부함, 상세함

## 평가해야 할 항목:
1. OPIC 점수(레벨): 응답의 전반적인 언어 능력에 해당하는 레벨(NL부터 AL까지)
2. 문단 구성력 피드백: 응답의 논리적 구성에 대한 구체적인 피드백
3. 어휘력 피드백: 어휘 사용에 대한 구체적인 피드백. 문법을 잘 지키고 있는지도 판단해서 피드백한다.
4. 발화량 피드백: 응답의 양과 내용 풍부함에 대한 구체적인 피드백. 응답 중 단어와 단어, 문장과 문장 사이 발화를 하지 않은 시간이 너무 길지는 않은지, filler를 적절히 사용하고 있는지 확인한다.

중요: 피드백을 작성할 때는 다음 사항을 지켜주세요.
1. 문단 구분이 필요한 경우 <br><br>를 사용하세요.
2. 중요한 포인트는 <b>강조할 내용</b> 형식으로 볼드 처리하세요.
3. 피드백은 가독성이 좋게 작성해주세요.

평가 결과는 반드시 다음 JSON 형식만으로 제공해 주세요:
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
당신은 OPIC(Oral Proficiency Interview-Computer) 시험의 전문 평가자입니다. 
아래 제시된 개별 문제 응답들을 종합적으로 평가하여 전체 테스트에 대한 종합 평가를 **한국어로** 제공해 주세요.
평가를 할 때는, 예상되는 등급보다 높은 등급의 레벨로 올라가기 위해서 어떤 것을 보완해야 하는지를 위주로 설명해주세요.
또한, 질문과 연관있는 답변을 하고 있는지 필수적으로 확인해서 평가해주세요.

## 문제별 응답 및 평가 결과:
{problem_responses}

## 테스트 구성:
- 자기소개: {self_introduction_count}문제
- 콤보셋: {comboset_count}문제
- 롤플레잉: {roleplaying_count}문제
- 돌발질문: {unexpected_count}문제

## 평가해야 할 항목:
1. 종합 OPIC 점수: 전체 응답을 종합한 최종 OPIC 레벨
2. 영역별 점수:
   - 콤보셋 점수: 콤보셋 문제들의 평균 레벨
   - 롤플레잉 점수: 롤플레잉 문제들의 평균 레벨
   - 돌발질문 점수: 돌발질문 문제들의 평균 레벨
3. 종합 피드백:
   - 전체 피드백: 응시자의 전반적인 영어 구사력에 대한 종합적인 피드백
   - 문단 구성력: 전반적인 문단 구성 능력에 대한 피드백
   - 어휘력: 전반적인 어휘 사용 능력 및 문법 준수 여부에 대한 피드백.
   - 발화량: 전반적인 발화량과 내용의 풍부함에 대한 피드백

중요: 피드백을 작성할 때는 다음 사항을 지켜주세요.
1. 문단 구분이 필요한 경우 <br><br>를 사용하세요.
2. 중요한 포인트는 <b>강조할 내용</b> 형식으로 볼드 처리하세요.
3. 피드백은 가독성이 좋게 작성해주세요.
   
평가 결과는 반드시 다음 JSON 형식만으로 제공해 주세요:
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
                problem_type = self._get_problem_type(problem_number_int, test_type)
                
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
    
    def _get_problem_type(self, problem_number: int, test_type: bool) -> str:
        """
        문제 번호와 테스트 유형에 따라 문제 유형 결정
        
        Args:
            problem_number: 문제 번호 (1부터 시작)
            test_type: 테스트 유형(True: Full, False: Half)
            
        Returns:
            문제 유형 문자열
        """
        if test_type:  # Full 테스트
            if problem_number == 1:
                return "self_introduction"
            elif 2 <= problem_number <= 10:
                return "comboset"
            elif 11 <= problem_number <= 13:
                return "roleplaying"
            else:  # 14~15
                return "unexpected"
        else:  # Half 테스트
            if 1 <= problem_number <= 3:
                return "comboset"
            elif 4 <= problem_number <= 5:
                return "roleplaying"
            else:  # 6~7
                return "unexpected"
    

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