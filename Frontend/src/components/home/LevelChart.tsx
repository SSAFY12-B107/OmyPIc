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
    const levels = ['IL이하', 'IM1', 'IM2', 'IM3', 'IH', 'AL', ''];
    // 유효한 레벨 정의 (NH이하보다 높은 레벨들)
    const validLevels = ['IM1', 'IM2', 'IM3', 'IH', 'AL'];
    
    // 정렬된 인덱스를 저장할 변수
    let sortedIndices: number[] = [];
  
    // 테스트 데이터 가공
    const formatLabels = () => {
      if (!testResult || !testResult.test_date) return [];
      
      // 날짜와 인덱스를 함께 저장
      const datesWithIndices = testResult.test_date.map((dateStr, index) => {
        if (!dateStr) return { date: new Date(0), formatted: '', index };
        
        try {
          const date = new Date(dateStr);
          if (isNaN(date.getTime())) return { date: new Date(0), formatted: '', index };
          
          // 한국 시간으로 변환 (+9시간)
          const koreaDate = new Date(date.getTime() + 9 * 60 * 60 * 1000);
          
          return {
            date: koreaDate, // 정렬을 위해 한국 시간 기준 저장
            rawDate: koreaDate, // 포맷팅에 사용할 날짜 저장
            index
          };
        } catch (e) {
          console.error("Invalid date format:", dateStr);
          return { date: new Date(0), rawDate: new Date(0), formatted: '', index };
        }
      }).filter(item => item.date.getTime() > 0);
      
      // 날짜 오름차순 정렬 (과거 → 최근)
      datesWithIndices.sort((a, b) => a.date.getTime() - b.date.getTime());
      
      // 정렬된 인덱스 저장
      sortedIndices = datesWithIndices.map(item => item.index);
      
      // 정렬 후 포맷팅 적용
      return datesWithIndices.map(item => {
        if (!item.rawDate) return '';
        
        const date = item.rawDate;
        const month = date.getMonth() + 1;
        const day = date.getDate();
        const hour = date.getHours();
        
        return `${month}/${day}\n${hour}시`;
      });
    };
    
    const formatData = () => {
      if (!testResult || !testResult.test_score) return [];
      
      // 정렬된 인덱스가 비어있으면 formatLabels 호출
      if (sortedIndices.length === 0) {
        formatLabels();
      }
      
      // 정렬된 인덱스 순서에 맞게 점수 데이터 재구성
      return sortedIndices.map(index => {
        const score = testResult.test_score[index];
        
        if (!score) return 0;
        
        if (!validLevels.includes(score)) {
          return 0;
        }
        
        const levelIndex = levels.indexOf(score);
        return levelIndex >= 0 ? levelIndex : 0;
      });
    };
    
    // 차트 데이터
    const data: LevelChartData = {
      labels: formatLabels(),
      datasets: [{
        label: '실전 연습 점수',
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
    aspectRatio: 1.8,
    plugins: {
      legend: {
        display: false, // 기본 범례 숨김
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            return levels[context.raw as number]; // 툴팁에도 레벨 이름 표시
          }
        }
      }
    },
    scales: {
      y: {
        min: -0.5,
        max: levels.length - 1,
        ticks: {
          callback: function(value) {
            return levels[value as number]; // Y축에 레벨 이름 표시
          },
          stepSize: 1
        },
        grid: {
          border: {
            display: false  // 그리드 테두리를 숨김
          }
        } as any
      },
      x: {
        grid: {
          display: false,
        },
        offset: true  // 이 설정이 각 데이터 포인트를 tickmark 사이에 배치
      }
    }
  };

  return (
    <div className={styles["level-chart"]}>
      <h2>실력 향상 추이</h2>
      <div className={styles["chart-box"]}>
        <Line data={data} options={options} />
      </div>

      {/* 커스텀 범례 */}
      <div className={styles["chart-legend"]}>
        <div className={styles["legend-dot"]}></div>
        <p className={styles["legend-text"]}>실전 연습 점수</p>
      </div>
    </div>
  );
}

export default LevelChart;