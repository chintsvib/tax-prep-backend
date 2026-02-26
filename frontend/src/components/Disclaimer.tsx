import styles from "./Disclaimer.module.css";

export default function Disclaimer() {
  return (
    <footer className={styles.footer}>
      <p className={styles.text}>
        For educational purposes only. Not tax advice. Consult a qualified tax
        professional before making financial decisions.
      </p>
    </footer>
  );
}
