type Props = {
    type: 'prev' | 'next';
    onClick: () => void;
    disabled?: boolean;
    label?: string;
};
declare function NavigationButton({ type, onClick, disabled, label }: Props): import("react").JSX.Element;
export default NavigationButton;
