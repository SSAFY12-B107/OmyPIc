import styles from "./NavigationButton.module.css";

interface NavigationButtonProps {
  type: "prev" | "next";
  onClick?: () => void;
}

const NavigationButton: React.FC<NavigationButtonProps> = ({ type, onClick }) => {
  const buttonTexts = {
    prev: "이전",
    next: "다음"
  };
  
  const buttonClasses = {
    prev: styles.frame,
    next: `${styles.frame} ${styles.frameNext}`
  };
  
  const textClasses = {
    prev: styles.textWrapper,
    next: `${styles.textWrapper} ${styles.textWrapperNext}`
  };
  
  return (
    <div className={buttonClasses[type]} onClick={onClick}>
      <span className={textClasses[type]}>{buttonTexts[type]}</span>
    </div>
  );
};

export default NavigationButton;