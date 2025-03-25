export type IntroType = "first" | "second" | "third";
interface Props {
    type: IntroType;
}
declare function Introduction({ type }: Props): import("react").JSX.Element;
export default Introduction;
