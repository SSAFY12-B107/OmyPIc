import styles from './LoadingSpinner.module.css'

function LoadingSpinner() {
  return (
    <div className={styles.loadingContainer}>
      <div className={styles.spinner}></div>
    </div>
  );
}

export default LoadingSpinner;
