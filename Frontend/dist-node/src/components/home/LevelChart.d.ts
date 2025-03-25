interface TestResult {
    test_date: (string | null)[];
    test_score: (string | null)[];
}
interface LevelChartProps {
    testResult?: TestResult;
}
declare function LevelChart({ testResult }: LevelChartProps): import("react").JSX.Element;
export default LevelChart;
