import React from "react";
import { AverageScore } from "@/hooks/useHistory";
interface AverageGradeChartProps {
    averageScore: AverageScore | null | undefined;
}
declare const AverageGradeChart: React.FC<AverageGradeChartProps>;
export default AverageGradeChart;
