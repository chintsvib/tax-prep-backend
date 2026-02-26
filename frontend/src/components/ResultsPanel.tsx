import { motion } from "framer-motion";
import type { RefundExplainerResponse } from "../api/types";
import ResultSummary from "./ResultSummary";
import WaterfallChart from "./WaterfallChart";
import styles from "./ResultsPanel.module.css";

interface ResultsPanelProps {
  result: RefundExplainerResponse;
  onClose: () => void;
}

export default function ResultsPanel({ result, onClose }: ResultsPanelProps) {
  return (
    <>
      <motion.div
        className={styles.backdrop}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      />
      <motion.div
        className={styles.panel}
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", damping: 30, stiffness: 300 }}
      >
        <div className={styles.panelHeader}>
          <button className={styles.closeBtn} onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path
                d="M15 5L5 15M5 5l10 10"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
            Back to form
          </button>
        </div>
        <div className={styles.panelBody}>
          <ResultSummary result={result} />
          <WaterfallChart drivers={result.drivers} />
        </div>
      </motion.div>
    </>
  );
}
