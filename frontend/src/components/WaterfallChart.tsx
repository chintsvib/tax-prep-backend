import { useState } from "react";
import { motion } from "framer-motion";
import type { RefundChangeDriver } from "../api/types";
import styles from "./WaterfallChart.module.css";

const CATEGORY_COLORS: Record<string, string> = {
  income: "#3b82f6",
  deduction: "#8b5cf6",
  tax: "#ef4444",
  credit: "#16a34a",
  payment: "#d97706",
  structural: "#64748b",
  interaction: "#a855f7",
};

function fmt(n: number): string {
  const sign = n >= 0 ? "+" : "-";
  return `${sign}$${Math.abs(n).toLocaleString("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })}`;
}

interface WaterfallChartProps {
  drivers: RefundChangeDriver[];
}

export default function WaterfallChart({ drivers }: WaterfallChartProps) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  if (!drivers.length) return null;

  const maxImpact = Math.max(...drivers.map((d) => Math.abs(d.impact_on_balance)));

  return (
    <motion.div
      className={styles.wrap}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3, delay: 0.2 }}
    >
      <h4 className={styles.sectionTitle}>What drove the change</h4>

      <div className={styles.chart}>
        {drivers.map((driver, i) => {
          const pct = maxImpact > 0
            ? (Math.abs(driver.impact_on_balance) / maxImpact) * 100
            : 0;
          const isPositive = driver.direction === "increased_refund";
          const isExpanded = expandedIdx === i;
          const catColor = CATEGORY_COLORS[driver.category] || "#94a3b8";

          return (
            <motion.div
              key={driver.field}
              className={styles.row}
              initial={{ opacity: 0, x: isPositive ? 20 : -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: 0.15 * i }}
              onClick={() => setExpandedIdx(isExpanded ? null : i)}
            >
              <div className={styles.rowHeader}>
                <div className={styles.labelGroup}>
                  <span
                    className={styles.catDot}
                    style={{ background: catColor }}
                  />
                  <span className={styles.driverLabel}>{driver.label}</span>
                  <span className={styles.category}>{driver.category}</span>
                </div>
                <span
                  className={`${styles.amount} ${
                    isPositive ? styles.amountPos : styles.amountNeg
                  }`}
                >
                  {fmt(driver.impact_on_balance)}
                </span>
              </div>

              <div className={styles.barTrack}>
                <motion.div
                  className={`${styles.bar} ${
                    isPositive ? styles.barPos : styles.barNeg
                  }`}
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.max(pct, 3)}%` }}
                  transition={{
                    duration: 0.6,
                    delay: 0.15 * i,
                    ease: "easeOut",
                  }}
                  style={{
                    [isPositive ? "marginLeft" : "marginRight"]: "auto",
                  }}
                />
              </div>

              {isExpanded && (
                <motion.div
                  className={styles.explanation}
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  transition={{ duration: 0.2 }}
                >
                  <p>{driver.explanation}</p>
                  {typeof driver.prior_value === "number" &&
                    typeof driver.current_value === "number" && (
                      <p className={styles.values}>
                        ${driver.prior_value.toLocaleString()} &rarr; $
                        {driver.current_value.toLocaleString()}
                      </p>
                    )}
                </motion.div>
              )}
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
}
