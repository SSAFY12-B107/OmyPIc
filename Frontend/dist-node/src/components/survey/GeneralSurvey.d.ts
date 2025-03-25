type Choice = {
    id: number | string;
    text: string;
    recommended?: boolean;
};
type Props = {
    questionNumber: string;
    questionText: string;
    choices: Choice[];
    selected?: number | string | null;
    onSelect?: (value: number | string) => void;
    hasError?: boolean;
};
declare function GeneralSurvey({ questionNumber, questionText, choices, selected, onSelect, hasError }: Props): import("react").JSX.Element;
export default GeneralSurvey;
