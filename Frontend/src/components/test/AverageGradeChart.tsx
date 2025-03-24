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
  if (!score) return 0;

  const scoreMap: { [key: string]: number } = {
    AL: 100,
    IH: 80,
    IM3: 60,
    IM2: 40,
    IM1: 20,
    IL: 0,
  };
  return scoreMap[score] || 0;
};

const AverageGradeChart: React.FC<AverageGradeChartProps> = ({
  averageScore,
}) => {
  // 차트 옵션 설정
  const options = {
    responsive: true,
    maintainAspectRatio: false,

    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: function (context: any) {
            const value = context.raw;
            console.log(value, value);
            const gradeMap: { [key: number]: string } = {
              100: "AL",
              80: "IH",
              60: "IM3",
              40: "IM2",
              20: "IM1",
              0: "IL",
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
          callback: function (value: number) {
            const labelMap: { [key: number]: string } = {
              0: "IL",
              20: "IM1",
              40: "IM2",
              60: "IM3",
              80: "IH",
              100: "AL",
            };
            return labelMap[value] || "";
          },
        },
        grid: { drawBorder: false },
      },
      x: { grid: { display: false } },
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

  return (
    <div className={styles.container}>
      <div className={styles.chartContainer}>
          <Bar options={options} data={chartData} />

      </div>
    </div>
  );
};

export default AverageGradeChart;
