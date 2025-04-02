import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from bson import ObjectId
import json
from core.config import settings  # 설정 모듈 가져오기
from api.deps import get_next_groq_key, get_next_gemini_key  # API 키 순환 함수 가져오기


# 대신 함수로 LLM을 초기화하는 함수 구현
def get_llama_llm():
    """Llama 모델 인스턴스를 반환하는 함수"""
    return ChatGroq(
        model="llama-3.3-70b-versatile", 
        temperature=0.3,
        api_key=get_next_groq_key()  # 순환 API 키 사용
    )

def get_gemini_llm():
    """Gemini 모델 인스턴스를 반환하는 함수"""
    return ChatGoogleGenerativeAI(
        model="gemini-pro", 
        temperature=0.3,
        api_key=get_next_gemini_key()  # 순환 API 키 사용
    )


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
    "AL": "일상적 대화 및 업무 관련 상황에서 완전히 참여 가능. 과거, 현재, 미래 시제를 사용하여 서술하고 묘사 가능.",
}

# 카테고리별 문제 가중치 설정
CATEGORY_WEIGHTS = {
    "self_introduction": 0,  # 자기소개
    "comboset": 0.3,           # 콤보셋
    "roleplaying": 0.35,        # 롤플레잉
    "unexpected": 0.35          # 돌발질문
}

# 오픽 평가 기준에 대한 상세 설명을 담은 프롬프트 템플릿
EVALUATION_PROMPT_TEMPLATE = """
당신은 OPIC(Oral Proficiency Interview-Computer) 시험의 전문 평가자입니다. 제시된 응답을 아래 기준에 따라 평가해 주세요.
피드백을 생성할 때는, 예상되는 등급보다 높은 등급의 레벨로 올라가기 위해서 어떤 것을 보완해야 하는지를 위주로 설명해주세요.
또한, 질문과 연관있는 답변을 하고 있는지 필수적으로 확인해서 평가해주세요.

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
   - AL: 일상적 대화 및 업무 관련 상황에서 완전히 참여 가능. 과거/현재/미래 시제 사용.

## 평가 영역:
1. 문단 구성력(Paragraph): 응답의 논리적 구성, 연결성, 일관성
2. 어휘력(Vocabulary): 어휘의 다양성, 적절성, 정확성
3. 발화량(Spoken Amount): 응답의 길이, 내용의 풍부함, 상세함

## 평가해야 할 항목:
1. OPIC 점수(레벨): 응답의 전반적인 언어 능력에 해당하는 레벨(NL부터 AL까지)
2. 문단 구성력 피드백: 응답의 논리적 구성에 대한 구체적인 피드백
3. 어휘력 피드백: 어휘 사용에 대한 구체적인 피드백. 문법을 잘 지키고 있는지도 판단한다.
4. 발화량 피드백: 응답의 양과 내용 풍부함에 대한 구체적인 피드백. 응답 중 단어와 단어, 문장과 문장 사이 발화를 하지 않은 시간이 너무 길지는 않은지, filler를 적절히 사용하고 있는지 확인한다.


평가 결과는 다음 JSON 형식으로 제공해 주세요:
```json
{
  "score": "레벨(예: IM2, IH, AL 등)",
  "feedback": {
    "paragraph": "문단 구성력에 대한 구체적인 피드백",
    "vocabulary": "어휘력에 대한 구체적인 피드백",
    "spoken_amount": "발화량에 대한 구체적인 피드백"
  }
}
```
"""

# 전체 테스트 종합 평가를 위한 프롬프트 템플릿
OVERALL_EVALUATION_PROMPT_TEMPLATE = """
당신은 OPIC(Oral Proficiency Interview-Computer) 시험의 전문 평가자입니다. 
아래 제시된 개별 문제 응답들을 종합적으로 평가하여 전체 테스트에 대한 종합 평가를 제공해 주세요.
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
   - 어휘력: 전반적인 어휘 사용 능력에 대한 피드백
   - 발화량: 전반적인 발화량과 내용의 풍부함에 대한 피드백

평가 결과는 다음 JSON 형식으로 제공해 주세요:
```json
{
  "test_score": {
    "total_score": "종합 레벨(예: IM2, IH, AL 등)",
    "comboset_score": "콤보셋 평균 레벨(예: IM2, IH, AL 등)",
    "roleplaying_score": "롤플레잉 평균 레벨(예: IM2, IH, AL 등)",
    "unexpected_score": "돌발질문 평균 레벨(예: IM2, IH, AL 등)"
  },
  "test_feedback": {
    "total_feedback": "전체 영어 구사력에 대한 종합적인 피드백",
    "paragraph": "전반적인 문단 구성 능력에 대한 피드백",
    "vocabulary": "전반적인 어휘 사용 능력에 대한 피드백",
    "spoken_amount": "전반적인 발화량과 내용의 풍부함에 대한 피드백"
  }
}
```
"""


class EvaluationResponseParser(JsonOutputParser):
    """문제 평가 결과 JSON 파서"""
    def parse(self, text):
        try:
            # JSON 블록 추출 시도
            json_str = extract_json_from_text(text)
            result = json.loads(json_str)
            
            # 필수 필드 확인 및 보정
            if "score" not in result:
                result["score"] = "IM2"  # 기본값
                
            if "feedback" not in result:
                result["feedback"] = {
                    "paragraph": "평가 데이터가 정확하게 생성되지 않았습니다.",
                    "vocabulary": "평가 데이터가 정확하게 생성되지 않았습니다.",
                    "spoken_amount": "평가 데이터가 정확하게 생성되지 않았습니다."
                }
            
            return result
        except Exception as e:
            print(f"응답 파싱 오류: {str(e)}")
            # 오류 시 기본값 반환
            return {
                "score": "IM2",
                "feedback": {
                    "paragraph": "응답 처리 중 오류가 발생했습니다.",
                    "vocabulary": "응답 처리 중 오류가 발생했습니다.",
                    "spoken_amount": "응답 처리 중 오류가 발생했습니다."
                }
            }
        

class OverallEvaluationResponseParser(JsonOutputParser):
    """종합 평가 결과 JSON 파서"""
    def parse(self, text):
        try:
            # JSON 블록 추출 시도
            json_str = extract_json_from_text(text)
            result = json.loads(json_str)
            
            # 필수 필드 확인 및 보정
            if "test_score" not in result:
                result["test_score"] = {
                    "total_score": "IM2",
                    "comboset_score": "IM2",
                    "roleplaying_score": "IM2",
                    "unexpected_score": "IM2"
                }
                
            if "test_feedback" not in result:
                result["test_feedback"] = {
                    "total_feedback": "종합 평가 데이터가 정확하게 생성되지 않았습니다.",
                    "paragraph": "종합 평가 데이터가 정확하게 생성되지 않았습니다.",
                    "vocabulary": "종합 평가 데이터가 정확하게 생성되지 않았습니다.",
                    "spoken_amount": "종합 평가 데이터가 정확하게 생성되지 않았습니다."
                }
            
            return result
        except Exception as e:
            print(f"종합 평가 응답 파싱 오류: {str(e)}")
            # 오류 시 기본값 반환
            return {
                "test_score": {
                    "total_score": "IM2",
                    "comboset_score": "IM2",
                    "roleplaying_score": "IM2",
                    "unexpected_score": "IM2"
                },
                "test_feedback": {
                    "total_feedback": "종합 평가 처리 중 오류가 발생했습니다.",
                    "paragraph": "종합 평가 처리 중 오류가 발생했습니다.",
                    "vocabulary": "종합 평가 처리 중 오류가 발생했습니다.",
                    "spoken_amount": "종합 평가 처리 중 오류가 발생했습니다."
                }
            }


# 각 문제 유형 분류 함수
def get_problem_type(problem_number: int, test_type_str: str) -> str:
    """
    문제 번호와 테스트 유형에 따라 문제 유형(자기소개/콤보셋/롤플레잉/돌발)을 결정하는 함수
    
    Args:
        problem_number: 문제 번호 (1부터 시작)
        test_type_str: 테스트 유형 문자열
        
    Returns:
        문제 유형 문자열: "self_introduction", "comboset", "roleplaying", "unexpected", "single" 중 하나
    """
    if test_type_str == "single":
        return "single"
    elif test_type_str == "category":
        # 카테고리 테스트에서는 기본적으로 콤보셋으로 처리
        return "comboset"
    elif test_type_str == "full_test":
        if problem_number == 1:
            return "self_introduction"
        elif 2 <= problem_number <= 10:
            return "comboset"
        elif 11 <= problem_number <= 13:
            return "roleplaying"
        else:  # 14~15
            return "unexpected"
    elif test_type_str == "half_test":
        if 1 <= problem_number <= 3:
            return "comboset"
        elif 4 <= problem_number <= 5:
            return "roleplaying"
        else:  # 6~7
            return "unexpected"
        
    # 알 수 없거나 지원되지 않는 테스트 유형의 경우 예외 발생
    raise ValueError(f"지원되지 않는 테스트 유형입니다: {test_type_str}")


# 개별 문제 응답 평가 함수
async def evaluate_problem_response(
    user_response: str, 
    problem_category: str,
    topic_category: str, 
    problem: str
) -> Dict[str, Any]:
    """
    사용자의 응답을 평가하여 점수와 피드백을 제공하는 함수 (최신 LangChain API 사용)
    
    Args:
        user_response: 사용자가 답변한 응답 텍스트
        problem_category: 문제 카테고리
        topic_category: 토픽 카테고리
        problem: 문제 내용
        
    Returns:
        평가 결과 딕셔너리: 점수와 피드백 정보 포함
    """
    try:
        # 평가 프롬프트 생성
        prompt = PromptTemplate(
            template=EVALUATION_PROMPT_TEMPLATE,
            input_variables=["user_response", "problem_category", "topic_category", "problem"]
        )
        
        # JSON 파서 생성
        parser = EvaluationResponseParser()
        
        # 매번 새로운 LLM 인스턴스 생성 (API 키 순환)
        llama_llm = get_llama_llm()
        gemini_llm = get_gemini_llm()

        # 최신 API 방식으로 체인 구성
        # chain = prompt | llama_llm | parser
        chain = prompt | gemini_llm | parser
        
        # 체인 실행
        result = await chain.ainvoke({
            "user_response": user_response,
            "problem_category": problem_category,
            "topic_category": topic_category,
            "problem": problem
        })
        
        return result
    except Exception as e:
        print(f"응답 평가 중 오류 발생: {str(e)}")
        # 오류 발생 시 기본 평가 결과 반환
        return {
            "score": "IM2",
            "feedback": {
                "paragraph": "평가 중 오류가 발생했습니다. 논리적 구성에 대한 평가를 완료하지 못했습니다.",
                "vocabulary": "평가 중 오류가 발생했습니다. 어휘 사용에 대한 평가를 완료하지 못했습니다.",
                "spoken_amount": "평가 중 오류가 발생했습니다. 발화량에 대한 평가를 완료하지 못했습니다."
            }
        }


# 전체 테스트 종합 평가 함수 - 최신 LangChain API 사용
async def evaluate_overall_test(
    test_data: Dict[str, Any],
    problem_details: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    전체 테스트의 종합 평가를 수행하는 함수 (최신 LangChain API 사용)
    
    Args:
        test_data: 테스트 정보 (test_type 등 포함)
        problem_details: 문제별 상세 정보 (응답 및 평가 결과 포함)
        
    Returns:
        종합 평가 결과 딕셔너리
    """
    try:
        # 테스트 유형 확인
        test_type = test_data.get("test_type", False)
        
        # 문제 유형별 카운트 및 응답 정보 초기화
        self_introduction_count = 0
        comboset_count = 0
        roleplaying_count = 0
        unexpected_count = 0
        
        self_introduction_responses = []
        comboset_responses = []
        roleplaying_responses = []
        unexpected_responses = []
        
        # 문제별 점수 데이터 추출 및 유형별 분류
        problem_responses_text = ""
        
        for problem_number, problem_data in problem_details.items():
            problem_number_int = int(problem_number)
            problem_type = get_problem_type(problem_number_int, test_type)
            
            response = problem_data.get("user_response", "")
            score = problem_data.get("score", "")
            problem_text = problem_data.get("problem", "")
            
            # 문제 유형별 카운트 및 응답 정보 수집
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
        
        # 유형별 평균 점수 계산 (문자열 레벨을 숫자로 변환 후 평균 계산)
        comboset_score = calculate_average_level([r["score"] for r in comboset_responses]) if comboset_responses else "N/A"
        roleplaying_score = calculate_average_level([r["score"] for r in roleplaying_responses]) if roleplaying_responses else "N/A"
        unexpected_score = calculate_average_level([r["score"] for r in unexpected_responses]) if unexpected_responses else "N/A"
        
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
        
        total_score = calculate_average_level(all_scores) if all_scores else "N/A"
        
        # 종합 평가 프롬프트 구성
        prompt = PromptTemplate(
            template=OVERALL_EVALUATION_PROMPT_TEMPLATE,
            input_variables=[
                "problem_responses", 
                "self_introduction_count", 
                "comboset_count", 
                "roleplaying_count", 
                "unexpected_count"
            ]
        )
        
        # JSON 파서 생성
        parser = OverallEvaluationResponseParser()
        
        # 매번 새로운 LLM 인스턴스 생성 (API 키 순환)
        llama_llm = get_llama_llm()
        gemini_llm = get_gemini_llm()

        # 최신 API 방식으로 체인 구성
        # chain = prompt | llama_llm | parser
        chain = prompt | gemini_llm | parser
        
        # 체인 실행
        result = await chain.ainvoke({
            "problem_responses": problem_responses_text,
            "self_introduction_count": self_introduction_count,
            "comboset_count": comboset_count,
            "roleplaying_count": roleplaying_count,
            "unexpected_count": unexpected_count
        })
        
        # 계산된 점수로 LLM 결과 보정 (LLM이 실수할 경우를 대비)
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
        
        return result
    except Exception as e:
        print(f"종합 평가 중 오류 발생: {str(e)}")
        # 오류 발생 시 기본 종합 평가 결과 반환
        return {
            "test_score": {
                "total_score": total_score if 'total_score' in locals() else "IM2",
                "comboset_score": comboset_score if 'comboset_score' in locals() else "IM2",
                "roleplaying_score": roleplaying_score if 'roleplaying_score' in locals() else "IM2",
                "unexpected_score": unexpected_score if 'unexpected_score' in locals() else "IM2"
            },
            "test_feedback": {
                "total_feedback": "평가 중 오류가 발생했습니다. 전체 영어 구사력에 대한 평가를 완료하지 못했습니다.",
                "paragraph": "전반적인 문단 구성 능력은 중간 수준입니다.",
                "vocabulary": "일상적인 어휘는 적절히 사용하고 있으나, 다양한 어휘 구사가 필요합니다.",
                "spoken_amount": "발화량은 적절하나 더 상세한 설명이 필요한 부분이 있습니다."
            }
        }

# 유틸리티 함수들

def extract_json_from_text(text: str) -> str:
    """텍스트에서 JSON 부분을 추출하는 함수"""
    
    # 1. 마크다운 코드 블록 확인 (```json ... ```)
    if "```json" in text and "```" in text:
        json_start = text.find("```json") + 7
        json_end = text.find("```", json_start)
        return text[json_start:json_end].strip()
    
    # 2. 일반 코드 블록 확인 (``` ... ```)
    if "```" in text:
        blocks = text.split("```")
        for block in blocks:
            if block.strip() and "{" in block and "}" in block:
                return block.strip()
    
    # 3. 중괄호로 시작하고 끝나는 블록 찾기 (중첩 중괄호 처리)
    json_start = text.find("{")
    if json_start != -1:
        count = 0
        for i in range(json_start, len(text)):
            if text[i] == "{":
                count += 1
            elif text[i] == "}":
                count -= 1
                if count == 0:
                    json_end = i + 1
                    return text[json_start:json_end]
    
    # 어떤 방법으로도 JSON을 찾지 못한 경우, 기본 JSON 반환
    return '{"score": "IM2", "feedback": {...}}' # 기본값


def calculate_average_level(levels: List[str]) -> str:
    """오픽 레벨 문자열 목록의 평균 레벨을 계산하는 함수"""
    
    # 레벨이 없으면 N/A 반환
    if not levels:
        return "N/A"
    
    # 레벨을 숫자로 변환
    level_values = []
    for level in levels:
        try:
            level_index = OPIC_LEVELS.index(level)
            level_values.append(level_index)
        except (ValueError, IndexError):
            # 유효하지 않은 레벨은 중간 레벨(IM2)로 처리
            level_values.append(OPIC_LEVELS.index("IM2"))
    
    # 평균 계산 및 가장 가까운 레벨 반환
    average_value = sum(level_values) / len(level_values)
    closest_index = round(average_value)
    
    # 인덱스 범위 확인
    if closest_index < 0:
        closest_index = 0
    elif closest_index >= len(OPIC_LEVELS):
        closest_index = len(OPIC_LEVELS) - 1
    
    return OPIC_LEVELS[closest_index]


