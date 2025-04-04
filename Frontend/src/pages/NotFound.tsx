import { Link } from 'react-router-dom';
import styles from './NotFound.module.css';
import NotFoundImage from '../assets/images/notfound.png';

type Props = {}

function NotFound({}: Props) {
  return (
    <div className={styles.container}>
      <div className={styles.content}>
        <img 
          src={NotFoundImage} 
          alt="404 Not Found" 
          className={styles.image} 
        />
        <Link to="/" className={styles.link}>
          홈으로 돌아가기
        </Link>
      </div>
    </div>
  )
}

export default NotFound