import { NavLink } from "react-router-dom";
import styles from "./Navbar.module.css";

type Props = {};

function Navbar({}: Props) {
  const tabs = [
    { to: "/test", label: "모의고사" },
    { to: "/", label: "홈" },
    { to: "/script", label: "스크립트" },
  ];

  return (
    <nav className={styles["nav-bar"]}>
      {tabs.map((tab, idx) => (
        <NavLink key={idx} to={tab.to}
        className={({ isActive }) => `${styles['nav-txt']} ${isActive ? styles['active'] : ''}`.trim()}>
          {tab.label}
        </NavLink>
      ))}
    </nav>
  );
}

export default Navbar;
