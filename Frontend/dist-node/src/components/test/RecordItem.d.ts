interface RecordItemProps {
    test_pk: string;
    date: string;
}
declare function RecordItem({ date, test_pk }: RecordItemProps): import("react").JSX.Element;
export default RecordItem;
