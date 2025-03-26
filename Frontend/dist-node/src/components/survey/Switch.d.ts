type Props = {
    onPrev?: () => void;
    onNext?: () => void;
    step?: number;
    pageId?: number;
};
declare function Switch({ onPrev, onNext, step, pageId }: Props): import("react").JSX.Element;
export default Switch;
