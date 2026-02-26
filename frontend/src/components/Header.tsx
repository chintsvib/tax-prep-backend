import { useAuth } from "../context/AuthContext";
import styles from "./Header.module.css";

interface HeaderProps {
  onLoginClick: () => void;
}

export default function Header({ onLoginClick }: HeaderProps) {
  const { isAuthenticated, email, logout } = useAuth();

  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <h1 className={styles.logo}>RefundLens</h1>
        <span className={styles.tagline}>
          Find out why your refund changed in 60 seconds.
        </span>
      </div>
      <div className={styles.auth}>
        {isAuthenticated ? (
          <>
            <span className={styles.email}>{email}</span>
            <button className={styles.authBtn} onClick={logout}>
              Sign Out
            </button>
          </>
        ) : (
          <button className={styles.authBtn} onClick={onLoginClick}>
            Sign In
          </button>
        )}
      </div>
    </header>
  );
}
