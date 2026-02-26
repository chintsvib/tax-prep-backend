import { motion } from "framer-motion";
import type { RefundExplainerResponse } from "../api/types";
import styles from "./ResultSummary.module.css";

function fmt(amount: number): string {
  return Math.abs(amount).toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
}

function balanceLabel(amount: number, type: string): string {
  if (type === "refund") return `${fmt(amount)} refund`;
  return `${fmt(amount)} owed`;
}

interface ResultSummaryProps {
  result: RefundExplainerResponse;
}

export default function ResultSummary({ result }: ResultSummaryProps) {
  const isIncrease = result.total_change_direction === "increased_refund";
  const changeAbs = Math.abs(result.total_change);

  let headline: string;
  if (result.total_change === 0) {
    headline = "Your tax outcome stayed the same";
  } else if (isIncrease) {
    if (result.current_balance_type === "refund") {
      headline = `Your refund increased by ${fmt(changeAbs)}`;
    } else {
      headline = `You owe ${fmt(changeAbs)} less this year`;
    }
  } else {
    if (result.current_balance_type === "owed") {
      headline = `You owe ${fmt(changeAbs)} more this year`;
    } else {
      headline = `Your refund decreased by ${fmt(changeAbs)}`;
    }
  }

  return (
    <motion.div
      className={styles.wrap}
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      <h3
        className={`${styles.headline} ${
          isIncrease ? styles.positive : styles.negative
        }`}
      >
        {headline}
      </h3>

      <div className={styles.comparison}>
        <div className={styles.yearBox}>
          <span className={styles.yearLabel}>{result.prior_year}</span>
          <span className={styles.yearAmount}>
            {balanceLabel(result.prior_balance, result.prior_balance_type)}
          </span>
        </div>
        <div className={styles.arrow}>
          <svg width="32" height="16" viewBox="0 0 32 16" fill="none">
            <path
              d="M0 8h28m0 0l-6-6m6 6l-6 6"
              stroke="#b0aaa2"
              strokeWidth="1.5"
            />
          </svg>
        </div>
        <div className={styles.yearBox}>
          <span className={styles.yearLabel}>{result.current_year}</span>
          <span className={styles.yearAmount}>
            {balanceLabel(result.current_balance, result.current_balance_type)}
          </span>
        </div>
      </div>

      {result.ai_summary && (
        <div className={styles.aiCallout}>
          <span className={styles.aiLabel}>AI Summary</span>
          <ul className={styles.aiList}>
            {result.ai_summary
              .split(/(?<=\.)\s+/)
              .filter((s) => s.trim())
              .map((sentence, i) => (
                <li key={i}>{sentence.trim()}</li>
              ))}
          </ul>
        </div>
      )}
    </motion.div>
  );
}
