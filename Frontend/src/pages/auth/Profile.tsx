import React, { useState, useEffect } from "react";
import styles from "./Profile.module.css";
import NavigationButton from "@/components/common/NavigationButton";
import { useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { RootState } from "../../store"; // Redux 스토어 타입
import { setProfileField, setProfileData } from "../../store/authSlice";
import { useUser } from "../../hooks/useUser"; // useUser 훅 추가

function ProfilePage() {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  
  // Redux에서 profileData 가져오기
  const { profileData } = useSelector((state: RootState) => state.auth);
  
  // useUser 훅 사용
  const { saveProfile, isSubmitting } = useUser();
  
  // 로컬 폼 상태 관리 (Redux와 별개로)
  const [formData, setFormData] = useState({
    wishGrade: profileData.wishGrade || "",
    currentGrade: profileData.currentGrade || "",
    examDate: profileData.examDate || "",
    agreeToTerms: false
  });
  
  // 에러 상태 관리
  const [errors, setErrors] = useState<Record<string, string>>({});

  // 인증 상태 확인
  useEffect(() => {
    const accessToken = sessionStorage.getItem('access_token');
    if (!accessToken) {
      navigate('/auth/login');
    }
  }, [navigate]);

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
      
      // Redux 스토어에도 업데이트 (체크박스 제외)
      if (name === 'wishGrade' || name === 'currentGrade' || name === 'examDate') {
        dispatch(setProfileField({ 
          field: name as keyof typeof profileData, 
          value 
        }));
      }
    }
  };

  // 폼 유효성 검증
  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.wishGrade) {
      newErrors.wishGrade = "희망 등급을 선택해주세요.";
    }
    
    if (!formData.currentGrade) {
      newErrors.currentGrade = "현재 등급을 선택해주세요.";
    }
    
    if (!formData.examDate) {
      newErrors.examDate = "시험 예정일을 입력해주세요.";
    } else {
      // 날짜 유효성 검증
      const selectedDate = new Date(formData.examDate);
      const today = new Date();
      
      if (selectedDate < today) {
        newErrors.examDate = "시험 예정일은 오늘 이후 날짜여야 합니다.";
      }
    }
    
    if (!formData.agreeToTerms) {
      newErrors.agreeToTerms = "개인정보 수집 및 이용에 동의해주세요.";
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handlePrev = () => {
    navigate(-1);
    console.log("이전 버튼 클릭");
  };

  const handleNext = () => {
    if (!validateForm()) {
      return;
    }
    
    // 프로필 데이터를 Redux에만 저장하고 API 호출은 하지 않음
    dispatch(setProfileData({
      wishGrade: formData.wishGrade,
      currentGrade: formData.currentGrade,
      examDate: formData.examDate
    }));
    
    // localStorage에도 저장 (선택적)
    localStorage.setItem("profileData", JSON.stringify({
      wishGrade: formData.wishGrade,
      currentGrade: formData.currentGrade,
      examDate: formData.examDate
    }));
    
    // 서베이 페이지로 이동
    navigate("/auth/survey");
  };

  return (
    <div className={styles["profile-container"]}>
      {/* 희망 등급 선택 */}
      <div className={styles["form-group"]}>
        <div className={styles["form-label"]}>
          <label>희망 등급</label>
        </div>
        <select 
          name="wishGrade" 
          className={`${styles.select} ${errors.wishGrade ? styles.error : ''}`}
          value={formData.wishGrade}
          onChange={handleInputChange}
          style={{ color: formData.wishGrade ? '#000000' : '#A3A3A3' }}
        >
          <option value="" disabled>희망하는 등급을 선택하세요.</option>
          <option value="AL">AL</option>
          <option value="IH">IH</option>
          <option value="IM3">IM3</option>
          <option value="IM2">IM2</option>
          <option value="IM1">IM1</option>
          <option value="IL">IL</option>
        </select>
        {errors.wishGrade && <p className={styles.errorText}>{errors.wishGrade}</p>}
      </div>  

      {/* 현재 등급 선택 */}
      <div className={styles["form-group"]}>
        <div className={styles["form-label"]}>
          <label>현재 등급</label>
        </div>
        <select 
          name="currentGrade" 
          className={`${styles.select} ${errors.currentGrade ? styles.error : ''}`}
          value={formData.currentGrade}
          onChange={handleInputChange}
          style={{ color: formData.currentGrade ? '#000000' : '#A3A3A3' }}
        >
          <option value="" disabled>현재 등급을 선택하세요.</option>
          <option value="AL">AL</option>
          <option value="IH">IH</option>
          <option value="IM3">IM3</option>
          <option value="IM2">IM2</option>
          <option value="IM1">IM1</option>
          <option value="IL">IL</option>
        </select>
        {errors.currentGrade && <p className={styles.errorText}>{errors.currentGrade}</p>}
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
            className={`${styles["date-input"]} ${errors.examDate ? styles.error : ''}`}
            value={formData.examDate}
            onChange={handleInputChange}
          />
        </div>
        {errors.examDate && <p className={styles.errorText}>{errors.examDate}</p>}
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
            <p className={styles["terms-detail"]}>* 수집 목적 : 서비스 제공 및 계정 관리</p>
          </div>
          <div className={`${styles["checkbox-container"]} ${errors.agreeToTerms ? styles.error : ''}`}>
            <input 
              type="checkbox" 
              id="agreeToTerms" 
              name="agreeToTerms" 
              className={styles.checkbox}
              checked={formData.agreeToTerms}
              onChange={handleInputChange}
            />
            <label htmlFor="agreeToTerms" className={styles["checkbox-label"]}>
              위 개인정보 수집 및 이용에 동의합니다.
            </label>
          </div>
          {errors.agreeToTerms && <p className={styles.errorText}>{errors.agreeToTerms}</p>}
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
          disabled={isSubmitting}
          label={isSubmitting ? "저장 중..." : "다음"}
        />
      </div>
    </div>
  );
}

export default ProfilePage;