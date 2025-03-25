import React from "react";
import styles from "./AverageGradeChart.module.css";
import { AverageScore } from "@/hooks/useHistory";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions
} from "chart.js";
import { Bar } from "react-chartjs-2";

// Chart.js 등록
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface AverageGradeChartProps {
  averageScore: AverageScore | null | undefined;
}

// 점수 변환 함수 (등급 → 숫자)
const scoreToNumber = (score: string | null | undefined): number => {
  
  console.log('score',score)
  if (!score) return 0;

  const scoreMap: { [key: string]: number } = {
    AL: 100,
    IH: 80,
    IM3: 60,
    IM2: 40,
    IM1: 20,
    IL: 10,
    NH : 10,
    NM : 10,
    NL :10 
  };
  const result = scoreMap[score] || 0;
  // console.log(`scoreToNumber 변환: ${score} -> ${result}`);
  return result;
};

const AverageGradeChart: React.FC<AverageGradeChartProps> = ({
  averageScore,
}) => {
  // 차트 옵션 설정
  const options: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,

    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: function (context: any) {
            const value = context.raw;
            const gradeMap: { [key: number]: string } = {
              100: "AL",
              80: "IH",
              60: "IM3",
              40: "IM2",
              20: "IM1",
              10: "IL 이하",
            };
            return `등급: ${gradeMap[value] || ""}`;
          },
        },
      },
    },
    scales: {
      y: {
        min: 0,
        max: 100,
        ticks: {
          stepSize: 20,
          callback: function(tickValue: string | number) {
            const value = Number(tickValue);
            const labelMap: { [key: number]: string } = {
              10: "IL 이하",
              20: "IM1",
              40: "IM2",
              60: "IM3",
              80: "IH",
              100: "AL",
            };
            return labelMap[value] || "";
          },
        },
        grid: {
        },
        border: {
          display: false
        }
      },
      x: { 
        grid: { 
          display: false,
        },
        border: {
          display: false
        }
      }
    },
  };

  // 차트 데이터 구성
  const chartData = {
    labels: ["콤보셋", "롤플레잉", "돌발질문", "종합"],
    datasets: [
      {
        data: [
          scoreToNumber(averageScore?.comboset_score),
          scoreToNumber(averageScore?.roleplaying_score),
          scoreToNumber(averageScore?.unexpected_score),
          scoreToNumber(averageScore?.total_score),
        ],
        backgroundColor: [
          "rgba(132, 90, 223, 0.7)",
          "rgba(170, 130, 255, 0.7)",
          "rgba(100, 80, 170, 0.7)",
          "rgba(255, 150, 170, 0.7)",
        ],
        borderColor: [
          "rgba(132, 90, 223, 1)",
          "rgba(170, 130, 255, 1)",
          "rgba(100, 80, 170, 1)",
          "rgba(255, 150, 170, 1)",
        ],
        borderWidth: 1,
        borderRadius: 8,
        maxBarThickness: 40,
      },
    ],
  };

  // console.log('average_score 전달받음', averageScore)
  // console.log('chartData',chartData.datasets)
  return (
    <div className={styles.container}>
      <div className={styles.chartContainer}>
        {!averageScore ? (
          <div className={styles.emptyData}>첫 시험에 도전해보세요!🐧🐟</div>
        ) : (
          <Bar options={options} data={chartData} />
        )}
      </div>
    </div>
  );
};

export default AverageGradeChart;