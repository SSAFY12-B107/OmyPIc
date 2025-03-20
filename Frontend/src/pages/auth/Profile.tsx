import React, { useState } from "react";
import styles from "./Profile.module.css";
import NavigationButton from "../../components/common/NavigationButton";
import { useNavigate } from "react-router-dom";

function ProfilePage() {
  const navigate = useNavigate();

  // 폼 데이터 상태 관리
  const [formData, setFormData] = useState({
    wishGrade: "",
    currentGrade: "",
    examDate: "",
    agreeToTerms: false
  });

  // 입력값 변경 처리
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const {name, value, type} = e.target as HTMLInputElement;

    if(type === "checkbox") {
      const {checked} = e.target as HTMLInputElement;
      setFormData({
        ...formData,
        [name]: checked
      });
    } else {
      setFormData({
        ...formData,
        [name]: value
      });
    }
  };

  const handlePrev = () => {
    navigate(-1);
    console.log("이전 버튼 클릭");
  };

  const handleNext = () => {
    if(!formData.wishGrade || !formData.currentGrade || !formData.examDate || !formData.agreeToTerms) {
      alert("모든 항목을 입력해주세요.");
      console.log("다음 버튼 클릭");
      return;
    }
  };
  navigate("/auth/survey", {state: {profileData: formData}});

  localStorage.setItem("profileData", JSON.stringify(formData));
  navigate("/auth/survey");
  console.log("다음 버튼 클릭");


  return (
    <div className={styles["profile-container"]}>
      {/* 공통 헤더 */}

      {/* 희망 등급 선택 */}
      <div className={styles["form-group"]}>
        <div className={styles["form-label"]}>
          <label>희망 등급</label>
        </div>
        <select 
          name="wishGrade" 
          className={styles.select}
          defaultValue=""
        >
          <option value="" disabled>희망하는 등급을 선택하세요.</option>
          <option value="AL">AL</option>
          <option value="IH">IH</option>
          <option value="IM3">IM3</option>
          <option value="IM2">IM2</option>
          <option value="IM1">IM1</option>
          <option value="IL">IL</option>
        </select>
      </div>  

      {/* 현재 등급 선택 */}
      <div className={styles["form-group"]}>
        <div className={styles["form-label"]}>
          <label>현재 등급</label>
        </div>
        <select 
          name="currentGrade" 
          className={styles.select}
          defaultValue=""
        >
          <option value="" disabled>현재 등급을 선택하세요.</option>
          <option value="AL">AL</option>
          <option value="IH">IH</option>
          <option value="IM3">IM3</option>
          <option value="IM2">IM2</option>
          <option value="IM1">IM1</option>
          <option value="IL">IL</option>
        </select>
      </div>

      {/* 시험 예정일 입력 */}
      <div className={styles["form-group"]}>
        <div className={styles["form-label"]}>
          <label>시험 예정일</label>
        </div>
        <div className={styles["date-input-container"]}>
        <input 
          type="date" 
          name="examDate" 
          className={styles["date-input"]}
        />
        </div>
      </div>

      {/* 개인정보 동의서 */}
      <div className={styles["form-group"]}>
        <div className={styles["form-label"]}>
          <label>개인정보 동의서</label>
        </div>
        <div className={styles["terms-container"]}>
          <div className={styles["terms-content"]}>
            <p>개인정보 수집 및 이용 동의 (필수)</p>
            <p>(주)오마이픽은 서비스 제공을 위해 아래와 같이 개인정보를 수집 및 이용합니다. 동의를 거부할 권리가 있으며, 동의 거부 시 서비스 이용이 제한됩니다.</p>
            <p className={styles["terms-detail"]}>* 수집 목적: 서비스 제공 및 계정 관리</p>
          </div>
          <div className={styles["checkbox-container"]}>
            <input 
              type="checkbox" 
              id="agreeToTerms" 
              name="agreeToTerms" 
              className={styles.checkbox}
            />
            <label htmlFor="agreeToTerms" className={styles["checkbox-label"]}>
              위 개인정보 수집 및 이용에 동의합니다.
            </label>
          </div>
        </div>
      </div>

      {/* 이전, 다음 버튼 */}
      <div className={styles["button-group"]}>
        <NavigationButton 
          type="prev" 
          onClick={handlePrev}
        />
        <NavigationButton 
          type="next" 
          onClick={handleNext}
        />
      </div>
    </div>
  );
}

export default ProfilePage;