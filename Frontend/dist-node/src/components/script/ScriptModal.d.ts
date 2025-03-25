interface Props {
    isGenerating: boolean;
    onClose: () => void;
    scriptContent: string;
    detailPagePath: string;
    problemId: string;
    currentAnswers: string[];
}
declare function ScriptModal({ isGenerating, onClose, scriptContent, detailPagePath, problemId, currentAnswers, }: Props): import("react").JSX.Element;
export default ScriptModal;
