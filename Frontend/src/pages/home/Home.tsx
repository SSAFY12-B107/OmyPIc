import styles from './Home.module.css'
import CharacterChange from '../../components/home/CharacterChange';
import LevelChart from '../../components/home/LevelChart'
import Navbar from '../../components/common/Navbar';

function Home() {
  return (
    <div className={styles['home']}>
      {/* 메인화면 header */}
      <header className={styles['home-header']}>
      <h1 className={styles['logo-txt']}>OmyPIc</h1>
      <div className={styles['user-info']}>
        <p>Hello, [username]!</p>
        <img src="" alt="" className={styles['user-img']} />
      </div>
    </header>

    <div className={styles['home-body']}>
      {/* 레벨 박스 */}
      <div className={styles['level-box']}>
        <div className={styles['my-level']}>
          <p className={styles['level']}>[IM2]</p>
          <p className={styles['level-title']}>현재 레벨</p>
        </div>
        <div className={styles['hope-level']}>
          <p className={styles['level']}>[IH]</p>
          <p className={styles['level-title']}>희망 레벨</p>
        </div>
      </div>

      {/* 시험 날짜 박스 */}
      <div className={styles['test-date-box']}>
        <div className={styles['date-info']}>
          <div className={styles['date-title']}>
            <p>내 OPIc 시험</p>
            <div className={styles['date-icon-box']}>
              [아이콘]
            </div>
          </div>
          <div className={styles['test-date']}>[시험 일자]</div>
        </div>
        <div className={styles['d-day']}>D-[남은 날짜]</div>
      </div>

        {/* 캐릭터 박스 */}
        <CharacterChange />

        {/* 실력 향상 추이 그래프 */}
        <LevelChart />

        {/* 네브바 */}
        <Navbar />
      </div>
    </div>
  )
}

export default Home