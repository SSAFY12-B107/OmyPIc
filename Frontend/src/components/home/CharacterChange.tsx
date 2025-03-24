import styles from './CharacterChange.module.css'
import opigi from '@/assets/images/opigi.png'

type Props = {}

function CharacterChange({}: Props) {
  return (
    <div className={styles['character-change']}>
      <p>[학습의지가 불타서 행복해!]</p>
      <img src={opigi} alt="opigi-img" />
    </div>
  )
}

export default CharacterChange