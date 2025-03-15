import React from "react";
import styles from "./ProfilePage.module.css";

interface ProfilePageProps {
  // You can add props here if needed
}

export const ProfilePage: React.FC<ProfilePageProps> = () => {
  return (
    <div className={styles.screen}>
      <div className={styles.container}>
        <div className={styles.header}>
          <div className={styles.headerBackground} />
          <div className={styles.headerTitle}>회원정보 입력</div>
          {/* 이미지 임시 제거 */}
        </div>

        <div className={styles.desiredGradeLabel}>희망 등급</div>
        <div className={styles.testDateLabel}>시험 예정일</div>
        <div className={styles.privacyAgreementLabel}>개인정보 동의서</div>

        <div className={styles.checkGroup}>
          <div className={styles.checkItem}>
            {/* 아이콘 임시 제거 */}
            <div className={styles.checkCircle}>✓</div>
          </div>
        </div>

        <div className={styles.checkGroup}>
          <div className={styles.checkItem}>
            {/* 아이콘 임시 제거 */}
            <div className={styles.checkCircle}>✓</div>
          </div>
        </div>

        <div className={styles.checkGroup}>
          <div className={styles.checkItem}>
            {/* 아이콘 임시 제거 */}
            <div className={styles.checkCircle}>✓</div>
          </div>
        </div>

        <div className={styles.checkGroup}>
          <div className={styles.checkItem}>
            {/* 아이콘 임시 제거 */}
            <div className={styles.checkCircle}>✓</div>
          </div>
        </div>

        <div className={styles.currentGradeLabel}>현재 등급</div>

        <div className={styles.privacyAgreementContainer}>
          <div className={styles.agreementFrame}>
            <div className={styles.agreementCheckbox}>
              <p className={styles.agreementText}>위 개인정보 수집 및 이용에 동의합니다.</p>
              {/* 아이콘 임시 제거 */}
              <div className={styles.checkboxIcon}>□</div>
            </div>
            {/* 이미지 임시 제거 */}
          </div>

          <p className={styles.privacyPolicyText}>
            <span className={styles.policyTitle}>
              개인정보 수집 및 이용 동의 (필수)
              <br />
            </span>
            <span className={styles.policyContent}>
              (주)오마이픽은 서비스 제공을 위해 아래와 같이 개인정보를 수집 및
              이용합니다. 동의를 거부할 권리가 있으며, 동의 거부 시 서비스
              이용이 제한됩니다.
              <br />
              수집 목적: 서비스 제공 및 계정 관리
            </span>
          </p>
        </div>

        <div className={styles.currentGradeSelector}>
          <div className={styles.selectorLabel}>현재 등급을 선택하세요.</div>
          {/* 아이콘 임시 제거 */}
          <div className={styles.dropdownIcon}>▼</div>
        </div>

        <div className={styles.testDateSelector}>
          <div className={styles.dateLabel}>연도-월-일</div>
          {/* 아이콘 임시 제거 */}
          <div className={styles.calendarIcon}>📅</div>
        </div>

        <div className={styles.desiredGradeSelector}>
          <div className={styles.selectorGroup}>
            <div className={styles.selectorLabel}>희망하는 등급을 선택하세요.</div>
          </div>
          {/* 아이콘 임시 제거 */}
          <div className={styles.dropdownIcon}>▼</div>
        </div>

        <div className={styles.nextButton}>
          <div className={styles.buttonText}>다음</div>
          {/* 이미지 임시 제거 */}
          <span className={styles.nextArrow}>→</span>
        </div>

        <div className={styles.prevButton}>
          <div className={styles.buttonText}>이전</div>
          {/* 이미지 임시 제거 */}
          <span className={styles.prevArrow}>←</span>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;