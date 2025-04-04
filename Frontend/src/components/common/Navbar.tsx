import { NavLink } from "react-router-dom";
import styles from "./Navbar.module.css";

type Props = {};

function Navbar({}: Props) {
  const tabs = [
    { to: "/tests", label: "실전 연습" },
    { to: "/scripts", label: "스크립트" },
    { to: "/home", label: "마이페이지" },
  ];

  return (
    <nav className={styles["nav-bar"]}>
      {tabs.map((tab, idx) => (
        <NavLink
          key={idx}
          to={tab.to}
          className={({ isActive }) =>
            `${styles["nav-txt"]} ${isActive ? styles["active"] : ""}`.trim()
          }
        >
          {tab.label}
        </NavLink>
      ))}
    </nav>
  );
}

export default Navbar;
