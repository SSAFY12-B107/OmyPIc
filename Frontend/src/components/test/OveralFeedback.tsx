import styles from "./OveralFeedback.module.css";
import { MultipleFeedback } from "@/hooks/useFeedBack";
// import {
//   Chart as ChartJS,
//   RadialLinearScale,
//   PointElement,
//   LineElement,
//   Filler,
//   Tooltip,
//   Legend,
// } from "chart.js";
// import { Radar } from "react-chartjs-2";

// ChartJS.register(
//   RadialLinearScale,
//   PointElement,
//   LineElement,
//   Filler,
//   Tooltip,
//   Legend
// );

interface OveralFeedbackProps {
  testFeedback?: MultipleFeedback | null;
}

// // 레벨 값을 숫자로 변환하는 함수
// const getLevelValue = (level: string): number => {
//   const levelMap: { [key: string]: number } = {
//     NL: 1,
//     NM: 2,
//     NH: 3,
//     IL: 4,
//     IM1: 5,
//     IM2: 6,
//     IM3: 7,
//     IH: 8,
//     AL: 9,
//   };

//   return levelMap[level] || 0;
// };

function OveralFeedback({ testFeedback }: OveralFeedbackProps) {
  if (!testFeedback) {
    return (
      <div className={styles.noFeedback}>
        피드백을 불러오고 있어요! 
      </div>
    );
  }

  // // 피드백에서 직접 레벨 정보 사용
  // const skillData = [
  //   { name: "문단 구성", level: testFeedback.paragraph }, // 예시 데이터, 실제 데이터로 변경 필요
  //   { name: "어휘력", level: testFeedback.vocabulary }, // 예시 데이터, 실제 데이터로 변경 필요
  //   { name: "발화량", level: testFeedback.spoken_amount }, // 예시 데이터, 실제 데이터로 변경 필요
  // ];
  // console.log("skillddata", skillData);
  // console.log("testfeedack", testFeedback);

  // // 차트 데이터 설정
  // const chartData = {
  //   labels: skillData.map((item) => item.name),
  //   datasets: [
  //     {
  //       label: "언어 능력 레벨",
  //       data: skillData.map((item) => getLevelValue(item.level)),
  //       backgroundColor: "rgba(75, 192, 192, 0.3)",
  //       borderColor: "rgba(75, 192, 192, 1)",
  //       borderWidth: 2,
  //       pointBackgroundColor: "rgba(75, 192, 192, 1)",
  //       pointBorderColor: "#fff",
  //       pointHoverBackgroundColor: "#fff",
  //       pointHoverBorderColor: "rgba(75, 192, 192, 1)",
  //       pointRadius: 5,
  //       pointHoverRadius: 7,
  //     },
  //   ],
  // };

  // // 차트 옵션 설정
  // const chartOptions = {
  //   scales: {
  //     r: {
  //       angleLines: {
  //         display: true,
  //         color: "rgba(0, 0, 0, 0.1)",
  //       },
  //       min: 0,
  //       max: 9,
  //       ticks: {
  //         stepSize: 1,
  //         display: false, // 눈금 숫자 표시 안함
  //         backdropColor: "transparent",
  //       },
  //       grid: {
  //         circular: true,
  //         color: "rgba(0, 0, 0, 0.1)",
  //       },
  //       pointLabels: {
  //         font: {
  //           size: 16,
  //           weight: "bold",
  //         },
  //         color: "#333",
  //         padding: 20,
  //       },
  //     },
  //   },
  //   plugins: {
  //     tooltip: {
  //       enabled: true,
  //       callbacks: {
  //         label: function (context: any) {
  //           const index = context.dataIndex;
  //           const level = skillData[index].level;
  //           return `${level}`;
  //         },
  //       },
  //       displayColors: false,
  //       backgroundColor: "rgba(0, 0, 0, 0.7)",
  //       padding: 10,
  //       titleFont: {
  //         size: 14,
  //       },
  //       bodyFont: {
  //         size: 14,
  //         weight: "bold",
  //       },
  //     },
  //     legend: {
  //       display: false,
  //     },
  //     // 데이터 포인트에 레벨 라벨 표시
  //     datalabels: {
  //       display: true,
  //       color: "#333",
  //       align: "end",
  //       anchor: "end",
  //       offset: 10,
  //       font: {
  //         size: 14,
  //         weight: "bold",
  //       },
  //       formatter: function (value: any, context: any) {
  //         return skillData[context.dataIndex].level;
  //       },
  //     },
  //   },
  //   maintainAspectRatio: false,
  //   layout: {
  //     padding: {
  //       top: 20,
  //       right: 20,
  //       bottom: 20,
  //       left: 20,
  //     },
  //   },
  //   elements: {
  //     line: {
  //       tension: 0.4, // 선을 더 부드럽게
  //     },
  //   },
  // };

  return (
    <div>
      <div className={styles.feedbackCard}>
        <div className={styles.feedbackHeader}>
          <div className={styles.iconCircle}>
            <div className={styles.personIcon}>👤</div>
          </div>
          <span className={styles.feedbackTitle}>종합 피드백</span>
        </div>
        <p
          className={styles.feedbackContent}
          dangerouslySetInnerHTML={{ __html: testFeedback.total_feedback }}
        />

        {/* <div className={styles.chartContainer}>
          <h3 className={styles.chartTitle}>영역별 평가</h3>
          <div className={styles.radarChart}>
            <Radar data={chartData} options={chartOptions} />
          </div>

          {/* 각 꼭짓점 별 레벨 표시 */}
          {/* <div className={styles.levelLabels}>
            {skillData.map((item) => (
              <div key={item.name} className={styles.levelItem}>
                <span className={styles.levelName}>{item.name}:</span>
                <span className={styles.levelValue}>{item.level}</span>
              </div>
            ))}
          </div>
        </div>  */}
      </div>
    </div>
  );
}

export default OveralFeedback;
