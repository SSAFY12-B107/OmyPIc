import styles from "./Survey.module.css";
import Tip from "../../components/survey/Tip";
import GeneralSurvey from '../../components/survey/GeneralSurvey';

const Survey = () => {
    return (
        <div className={styles.surveyContainer}>
            <div className={styles.header}>
                <h1 className={styles.title}>Background Survey</h1>
            </div>

            <div className={styles.content}>
                <Tip type="workExperience" />
            </div>

            <div className={styles.choice}>
                <GeneralSurvey questionNumber="1" questionText="현재 직장 혹은 학교에서 무엇을 하고 있습니까?" choices={[
                    { id: 1, text: "사업/회사", recommended: true },
                    { id: 2, text: "재택근무/재택사업", recommended: true },
                    { id: 3, text: "교사/교육자", recommended: false },
                    { id: 4, text: "군복무", recommended: false },
                    { id: 5, text: "일 경험 없음", recommended: false },
                ]}/>
            </div>
        </div>
    );
};

export default Survey;