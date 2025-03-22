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

interface TestResult {
  test_date: (string | null)[];
  test_score: (string | null)[];
}

interface LevelChartProps {
  testResult?: TestResult;
}

function LevelChart({ testResult }: LevelChartProps) {
    // 레벨 정의
    const levels = ['IL', 'IM1', 'IM2', 'IM3', 'IH', 'AL', ''];
  
    // 테스트 데이터 가공
    const formatLabels = () => {
      if (!testResult || !testResult.test_date) return [];
      
      return testResult.test_date.map(dateStr => {
        if (!dateStr) return '';
        
        // ISO 날짜 포맷을 "M/D h시" 형식으로 변환
        try {
          const date = new Date(dateStr);
          if (isNaN(date.getTime())) return '';
          
          const month = date.getMonth() + 1;
          const day = date.getDate();
          const hour = date.getHours();
          
          return `${month}/${day}\n${hour}시`;
        } catch (e) {
          console.error("Invalid date format:", dateStr);
          return '';
        }
      }).filter(date => date !== ''); // 빈 문자열 필터링
    };
    
    const formatData = () => {
      if (!testResult || !testResult.test_score) return [];
      
      return testResult.test_score.map(score => {
        if (!score) return 0;
        const levelIndex = levels.indexOf(score);
        return levelIndex >= 0 ? levelIndex : 0;
      });
    };
    
    // 차트 데이터
    const data: LevelChartData = {
      labels: formatLabels(),
      datasets: [{
        label: '모의고사 점수',
        data: formatData(),
        borderColor: '#8A63D2',
        backgroundColor: '#8A63D2',
        tension: 0,
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
        },
        offset: true,  // 이 설정이 각 데이터 포인트를 tickmark 사이에 배치
      // 첫 번째 데이터 포인트가 y축에서 떨어지도록 왼쪽 패딩 추가
      // afterFit: function(scaleInstance) {
      //   scaleInstance.paddingLeft = 1;  // y축에서 10px 떨어지게 설정
      // }
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
