import { useEffect } from "react";
import { Link } from "react-router-dom";
import { useInView } from "react-intersection-observer";
import styles from "./ScriptList.module.css";
import opigi from "../../assets/images/opigi.png";
import QuestionBox from "../../components/script/QuestionBox";
import { useGetProblems } from "../../hooks/useProblems";
import LoadingSpinner from "../../components/common/LoadingSpinner";

type Props = {
  category?: string; // 선택된 카테고리
};

function ScriptList({ category = "빈출 문제" }: Props) {
  // Intersection Observer 설정
  const { ref, inView } = useInView({
    // 요소의 20%만 보여도 감지 (기본값 0)
    threshold: 0.2,
    // 뷰포트 하단에서 200px 전에 미리 감지
    rootMargin: "0px 0px 200px 0px",
  });

  // 문제 목록 데이터 가져오기
  const {
    data,
    fetchNextPage, // 다음 페이지 로드 함수
    hasNextPage, // 더 로드할 페이지가 있는지 여부
    isFetchingNextPage, // 다음 페이지 로딩 중인지 여부
    isLoading,
    error,
  } = useGetProblems(category);

  // 스크롤 감지 시 다음 페이지 로드
  useEffect(() => {
    let timeoutId: NodeJS.Timeout;

    if (inView && hasNextPage && !isFetchingNextPage) {
      timeoutId = setTimeout(() => {
        fetchNextPage();
      }, 300); // 300ms 디바운스 : 연속적인 API 호출 방지
    }

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [inView, fetchNextPage, hasNextPage, isFetchingNextPage]);

  return (
    <div className={styles["script-list-container"]}>
      {/* 공통 헤더 */}

      {/* 질문 선택 멘트 */}
      <div className={styles["selection-title"]}>
        <p>
          <span>{category}</span>을 선택하셨네요!
          <br />
          무슨 질문으로 대화를 나눌까요?
        </p>
        <img src={opigi} alt="opigi-img" />
      </div>

      {/* 질문 리스트 */}
      <div className={styles["question-list"]}>
        {isLoading ? (
          <LoadingSpinner />
        ) : error ? (
          <div>오류가 발생했습니다.</div>
        ) : (
          <>
            {/* 모든 페이지의 문제들을 flat하게 렌더링 */}
            {data?.pages.map((page, pageIndex) => (
              <div key={pageIndex}>
                {page.map((problem, problemIndex) => {
                  // 마지막 페이지의 마지막 아이템에 ref 연결
                  const isLastPage = pageIndex === data.pages.length - 1;
                  const isLastItem = problemIndex === page.length - 1;
                  const shouldAttachRef = isLastPage && isLastItem;

                  return (
                    <div key={problem.id} ref={shouldAttachRef ? ref : null}>
                      <Link to={"scripts/${category}/${problemId}"}>
                        <QuestionBox
                          title={`Q${pageIndex * 10 + problemIndex + 1}`}
                          content={problem.content}
                        />
                      </Link>
                    </div>
                  );
                })}
              </div>
            ))}

            {/* 로딩 스피너 (페치 중일 때만 표시) */}
            {isFetchingNextPage && <LoadingSpinner />}

            {/* 비어있는 요소 - 더 이상 불러올 데이터가 없을 때 */}
            {/* {!hasNextPage && data?.pages[0]?.length > 0 && (
              <div style={{ height: '10px' }}></div> // 간격 유지를 위한 빈 요소
            )} */}
          </>
        )}
      </div>
    </div>
  );
}

export default ScriptList;
