import styles from "./LevelChart.module.css";
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
  ChartData
} from 'chart.js';

// Chart.js 등록
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

// Chart.js 타입 정의
type LevelChartData = ChartData<'line', number[], string>;
type LevelChartOptions = ChartOptions<'line'>;

type Props = {};

function LevelChart({}: Props) {
  // 레벨 정의
  const levels = ['IL', 'IM1', 'IM2', 'IM3', 'IH', 'AL'];
  
  // 차트 데이터
  const data: LevelChartData = {
    labels: ['3/1', '3/3', '3/5', '3/7', '3/8'],
    datasets: [{
      label: '모의고사 점수',
      data: [0, 0, 1, 2, 2], // 인덱스로 레벨 표시 (0=IL, 1=IM1, ...)
      borderColor: '#8A63D2',
      backgroundColor: '#8A63D2',
      tension: 0, // 직선으로 설정
      pointRadius: 5,
      pointBackgroundColor: 'white',
      pointBorderColor: '#8A63D2',
      pointBorderWidth: 2,
    }]
  };
  
  // 차트 옵션
  const options: LevelChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        display: false, // 기본 범례 숨김
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            return levels[context.raw]; // 툴팁에도 레벨 이름 표시
          }
        }
      }
    },
    scales: {
      y: {
        min: 0,
        max: levels.length - 1,
        ticks: {
          callback: function(value) {
            return levels[value]; // Y축에 레벨 이름 표시
          },
          stepSize: 1
        },
        grid: {
          drawBorder: false,
        }
      },
      x: {
        grid: {
          display: false,
        }
      }
    }
  };

  return (
    <div className={styles["level-chart"]}>
      <h2>실력 향상 추이</h2>
      <Line data={data} options={options} />

      {/* 커스텀 범례 */}
      <div className={styles["chart-legend"]}>
        <div className={styles["legend-dot"]}></div>
        <p className={styles["legend-text"]}>모의고사 점수</p>
      </div>
    </div>
  );
}

export default LevelChart;
