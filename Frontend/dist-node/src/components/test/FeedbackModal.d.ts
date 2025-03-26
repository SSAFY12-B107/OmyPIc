interface FeedbackModalProps {
    isOpen: boolean;
    onClose: () => void;
    data: {
        feedback: {
            paragraph: string;
            spoken_amount: string;
            vocabulary: string;
        };
        score: string;
    } | null;
    isLoading: boolean;
}
declare const FeedbackModal: React.FC<FeedbackModalProps>;
export default FeedbackModal;
