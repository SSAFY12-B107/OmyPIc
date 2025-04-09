import { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import styles from "./Home.module.css";
// import CharacterChange from "@/components/home/CharacterChange";
import LevelChart from "@/components/home/LevelChart";
import Navbar from "@/components/common/Navbar";
import { useTestDate } from '@/hooks/useTestDate';
import { useGetUserInfo, useLogout } from '@/hooks/useUserInfo';
import LoadingSpinner from "@/components/common/LoadingSpinner";

function Home() {
  // 사용자 정보 가져오기
  const { data: userInfo, isLoading: userInfoIsLoading, error } = useGetUserInfo();
  const today = new Date();
  const [testDateIso, setTestDateIso] = useState(`${today}`);

  // 로그아웃 로직
  const { mutate: logout } = useLogout();
  console.log(userInfo)

  // 데이터가 로딩되면 상태 업데이트
  useEffect(() => {
    if (userInfo?.target_exam_date) {
      setTestDateIso(userInfo.target_exam_date);
    }
  }, [userInfo]);

  // 시험일 계산
  const { formattedDate, dday } = useTestDate(testDateIso);

  // 로딩 상태 처리
  if (userInfoIsLoading) {
    return <div className={styles["loading"]}><LoadingSpinner/></div>;
  }

  // 에러 상태 처리
  if (error) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className={styles["home"]}>
      {/* 메인화면 header */}
      <header className={styles["home-header-box"]}>
        <div className={styles["home-header"]}>
          <h1 className={styles["logo-txt"]}>OmyPIc</h1>
          <button className={styles["logout-btn"]} onClick={() => logout()} aria-label="로그아웃">
            <svg
              aria-hidden="true"
              xmlns="http://www.w3.org/2000/svg"
              width="18"
              height="18"
              viewBox="0 0 18 18"
              fill="none"
            >
              <path
                d="M2 18C1.45 18 0.979333 17.8043 0.588 17.413C0.196667 17.0217 0.000666667 16.5507 0 16V2C0 1.45 0.196 0.979333 0.588 0.588C0.98 0.196667 1.45067 0.000666667 2 0H8C8.28333 0 8.521 0.0960001 8.713 0.288C8.905 0.48 9.00067 0.717333 9 1C8.99933 1.28267 8.90333 1.52033 8.712 1.713C8.52067 1.90567 8.28333 2.00133 8 2H2V16H8C8.28333 16 8.521 16.096 8.713 16.288C8.905 16.48 9.00067 16.7173 9 17C8.99933 17.2827 8.90333 17.5203 8.712 17.713C8.52067 17.9057 8.28333 18.0013 8 18H2ZM14.175 10H7C6.71667 10 6.47933 9.904 6.288 9.712C6.09667 9.52 6.00067 9.28267 6 9C5.99933 8.71733 6.09533 8.48 6.288 8.288C6.48067 8.096 6.718 8 7 8H14.175L12.3 6.125C12.1167 5.94167 12.025 5.71667 12.025 5.45C12.025 5.18333 12.1167 4.95 12.3 4.75C12.4833 4.55 12.7167 4.44567 13 4.437C13.2833 4.42833 13.525 4.52433 13.725 4.725L17.3 8.3C17.5 8.5 17.6 8.73333 17.6 9C17.6 9.26667 17.5 9.5 17.3 9.7L13.725 13.275C13.525 13.475 13.2877 13.571 13.013 13.563C12.7383 13.555 12.5007 13.4507 12.3 13.25C12.1167 13.05 12.0293 12.8127 12.038 12.538C12.0467 12.2633 12.1423 12.034 12.325 11.85L14.175 10Z"
                fill="white"
              />
            </svg>
          </button>
        </div>
        <div className={styles["user-info"]}>
          <p>Hello, {userInfo?.name}!</p>
          {/* <img src="" alt="" /> */}
          {/* user-img 없는 경우 */}
          <div className={styles["basic-img"]} role="img" aria-label="사용자 기본 프로필 이미지">
            <svg
              aria-hidden="true"
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
            >
              <path
                fillRule="evenodd"
                clipRule="evenodd"
                d="M10 1.04166C8.95018 1.04166 7.94336 1.4587 7.20103 2.20103C6.4587 2.94336 6.04166 3.95018 6.04166 5C6.04166 6.04981 6.4587 7.05663 7.20103 7.79896C7.94336 8.54129 8.95018 8.95833 10 8.95833C11.0498 8.95833 12.0566 8.54129 12.799 7.79896C13.5413 7.05663 13.9583 6.04981 13.9583 5C13.9583 3.95018 13.5413 2.94336 12.799 2.20103C12.0566 1.4587 11.0498 1.04166 10 1.04166ZM7.29166 5C7.29166 4.2817 7.577 3.59283 8.08492 3.08492C8.59283 2.57701 9.2817 2.29166 10 2.29166C10.7183 2.29166 11.4072 2.57701 11.9151 3.08492C12.423 3.59283 12.7083 4.2817 12.7083 5C12.7083 5.71829 12.423 6.40717 11.9151 6.91508C11.4072 7.42299 10.7183 7.70833 10 7.70833C9.2817 7.70833 8.59283 7.42299 8.08492 6.91508C7.577 6.40717 7.29166 5.71829 7.29166 5ZM10 10.2083C8.0725 10.2083 6.29583 10.6467 4.98 11.3867C3.68333 12.1167 2.70833 13.2217 2.70833 14.5833V14.6683C2.7075 15.6367 2.70666 16.8517 3.7725 17.72C4.29666 18.1467 5.03083 18.4508 6.0225 18.6508C7.01583 18.8525 8.31166 18.9583 10 18.9583C11.6883 18.9583 12.9833 18.8525 13.9783 18.6508C14.97 18.4508 15.7033 18.1467 16.2283 17.72C17.2942 16.8517 17.2925 15.6367 17.2917 14.6683V14.5833C17.2917 13.2217 16.3167 12.1167 15.0208 11.3867C13.7042 10.6467 11.9283 10.2083 10 10.2083ZM3.95833 14.5833C3.95833 13.8742 4.47666 13.1042 5.5925 12.4767C6.68916 11.86 8.24583 11.4583 10.0008 11.4583C11.7542 11.4583 13.3108 11.86 14.4075 12.4767C15.5242 13.1042 16.0417 13.8742 16.0417 14.5833C16.0417 15.6733 16.0083 16.2867 15.4383 16.75C15.13 17.0017 14.6133 17.2475 13.73 17.4258C12.8492 17.6042 11.645 17.7083 10 17.7083C8.355 17.7083 7.15 17.6042 6.27 17.4258C5.38666 17.2475 4.87 17.0017 4.56166 16.7508C3.99166 16.2867 3.95833 15.6733 3.95833 14.5833Z"
                fill="white"
              />
            </svg>
          </div>
        </div>
      </header>

      <div className={styles["home-body"]}>
        {/* 레벨 박스 */}
        <div className={`${styles["home-box"]} ${styles["level-box"]}`}>
          <div className={styles["my-level"]}>
            <p className={styles["level"]}>{userInfo?.current_opic_score || '-'}</p>
            <p className={styles["level-title"]}>현재 레벨</p>
          </div>
          <div className={styles["hope-level"]}>
            <p className={styles["level"]}>{userInfo?.target_opic_score || '-'}</p>
            <p className={styles["level-title"]}>희망 레벨</p>
          </div>
        </div>

        {/* 시험 날짜 박스 */}
        <div className={`${styles["home-box"]} ${styles["test-date-box"]}`}>
          <div className={styles["date-info"]}>
            <div className={styles["date-title"]}>
              <p>내 OPIc 시험</p>
              <div className={styles['calendar']}>
                <svg
                  aria-hidden="true"
                  xmlns="http://www.w3.org/2000/svg"
                  width="17"
                  height="17"
                  viewBox="0 0 17 17"
                  fill="none"
                >
                  <path
                    d="M3.77419 14.1129C3.46461 14.1129 3.20632 14.0094 2.99933 13.8024C2.79234 13.5954 2.68862 13.3371 2.68817 13.0276V4.44556C2.68817 4.13642 2.79189 3.87836 2.99933 3.67137C3.20676 3.46438 3.46505 3.36066 3.77419 3.36021H4.96304V1.86156H5.68683V3.36021H10.4946V1.86156H11.1667V3.36021H12.3555C12.6647 3.36021 12.9229 3.46393 13.1304 3.67137C13.3378 3.87881 13.4413 4.13709 13.4409 4.44623V13.0276C13.4409 13.3367 13.3374 13.595 13.1304 13.8024C12.9234 14.0099 12.6649 14.1133 12.3548 14.1129H3.77419ZM3.77419 13.4409H12.3555C12.4586 13.4409 12.5533 13.3978 12.6398 13.3118C12.7263 13.2258 12.7693 13.1308 12.7688 13.0269V7.13441H3.36021V13.0276C3.36021 13.1306 3.40323 13.2254 3.48925 13.3118C3.57527 13.3983 3.67003 13.4413 3.77352 13.4409"
                    fill="#8A8A8A"
                  />
                </svg>
              </div>
            </div>
            <div className={styles["test-date"]}>
              {formattedDate}
            </div>
          </div>
          <div className={styles["d-day"]}>{dday === 0 ? "D-Day" : dday > 0 ? `D-${dday}` : `D+${Math.abs(dday)}`}</div>
        </div>

        {/* 캐릭터 박스 */}
        {/* <CharacterChange /> */}

        {/* 실력 향상 추이 그래프 */}
        <LevelChart testResult={userInfo?.test} />
      </div>

      {/* 네브바 */}
      <Navbar />
    </div>
  );
}

export default Home;
