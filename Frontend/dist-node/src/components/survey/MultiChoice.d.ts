type ChoiceItem = {
    id: string | number;
    text: string;
    recommended: boolean;
};
type Props = {
    questionNumber: string;
    questionText: string;
    choices: ChoiceItem[];
    minSelect?: number;
    selected?: (string | number)[];
    onSelect?: (selected: (string | number)[]) => void;
    totalSelected?: number;
    requiredTotal?: number;
};
declare function MultiChoice({ questionNumber, questionText, choices, minSelect, selected, onSelect, totalSelected, }: Props): import("react").JSX.Element;
export default MultiChoice;
