interface TestTypeButtonProps {
    title: string;
    description: string;
    onClick: () => void;
    isLoading: boolean;
}
declare function TestTypeButton({ title, description, onClick, isLoading }: TestTypeButtonProps): import("react").JSX.Element;
export default TestTypeButton;
