import styles from "./LevelChart.module.css";

type Props = {};

function LevelChart({}: Props) {
  return (
    <div className={styles["level-chart"]}>
      <h2>실력 향상 추이</h2>
      {/* 차트 자리 */}

      {/* 커스텀 범례 */}
      <div className={styles["chart-legend"]}>
        <div className={styles["legend-dot"]}></div>
        <p className={styles["legend-text"]}>모의고사 점수</p>
      </div>
    </div>
  );
}

export default LevelChart;
