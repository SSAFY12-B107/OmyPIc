// NavigationButton.tsx
import styles from './NavigationButton.module.css';

type Props = {
  type: 'prev' | 'next';
  onClick: () => void;
  disabled?: boolean;
  label?: string; // 추가: 커스텀 레이블
};

function NavigationButton({ type, onClick, disabled = false, label }: Props) {
  // 기본 레이블 설정
  const buttonLabel = label || (type === 'prev' ? '이전' : '다음');
  
  return (
    <button 
      className={`${styles.frame} ${type === 'next' ? styles.frameNext : ''}`}
      onClick={onClick}
      disabled={disabled}
    >
      <span className={`${styles.textWrapper} ${type === 'next' ? styles.textWrapperNext : ''}`}>
        {buttonLabel}
      </span>
    </button>
  );
}

export default NavigationButton;