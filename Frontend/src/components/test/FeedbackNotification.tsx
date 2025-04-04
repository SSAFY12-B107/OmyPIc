
import styles from './FeedbackNotification.module.css';

interface FeedbackNotificationProps {
  visible: boolean;
  onClose: () => void;
}

function FeedbackNotification({ visible, onClose }: FeedbackNotificationProps) {
  if (!visible) return null;

  return (
    <div className={styles.notificationContainer}>
      {/* 아래 방향 화살표 SVG */}
      <svg 
        className={styles.arrow} 
        width="40" 
        height="40" 
        viewBox="0 0 40 40" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect width="40" height="40" rx="20" fill="#845ADF" fillOpacity="0.1" />
        <path 
          d="M20 28C19.7348 28 19.4804 27.8946 19.2929 27.7071L12.2929 20.7071C11.9024 20.3166 11.9024 19.6834 12.2929 19.2929C12.6834 18.9024 13.3166 18.9024 13.7071 19.2929L20 25.5858L26.2929 19.2929C26.6834 18.9024 27.3166 18.9024 27.7071 19.2929C28.0976 19.6834 28.0976 20.3166 27.7071 20.7071L20.7071 27.7071C20.5196 27.8946 20.2652 28 20 28Z" 
          fill="#845ADF" 
        />
      </svg>
      
      {/* 알림 메시지 박스 */}
      <div className={styles.messageBox}>
        {/* 닫기 버튼 */}
        <button className={styles.closeButton} onClick={onClose}>
          <svg 
            width="24" 
            height="24" 
            viewBox="0 0 24 24" 
            fill="none" 
            xmlns="http://www.w3.org/2000/svg"
          >
            <path 
              d="M18 6L6 18M6 6L18 18" 
              stroke="#845ADF" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            />
          </svg>
        </button>
        
        {/* 메시지 내용 */}
        <div className={styles.messageContent}>
          <p className={styles.title}>피드백 준비 중</p>
          <p className={styles.description}>
            아래 기록에서 피드백을 확인해보세요! 평가가 완료되면 보라색 테두리가 사라져요!
          </p>
        </div>
      </div>
    </div>
  );
}

export default FeedbackNotification;