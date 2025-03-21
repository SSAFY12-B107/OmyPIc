import styles from './AverageGradeChart.module.css';
import { AverageScore } from '../../hooks/useHistory';

interface AverageGradeChartProps {
  averageScore?: AverageScore | null;
}


const AverageGradeChart: React.FC<AverageGradeChartProps> = ({ averageScore }) => {
  if (!averageScore) {
    console.log('averageScore',averageScore)
    return <div>데이터가 없습니다.</div>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.chartContainer}>
      <div>전체 평균: {averageScore.total_score}</div>
      <div>콤보셋: {averageScore.comboset_score}</div>
      <div>롤플레잉: {averageScore.roleplaying_score}</div>
      <div>돌발질문: {averageScore.unexpected_score}</div>
        </div>
      </div>

  );
}

export default AverageGradeChart;

