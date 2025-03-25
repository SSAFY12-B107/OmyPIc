interface ScriptBoxProps {
    userScript: Array<{
        _id: number;
        content: string;
    }>;
}
declare function ScriptBox({ userScript }: ScriptBoxProps): import("react").JSX.Element;
export default ScriptBox;
