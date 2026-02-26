import { useState, useEffect } from "react";
import { getLifeEvents } from "../api/client";
import type { TaxData, LifeEventPreset } from "../api/types";
import styles from "./LifeEvents.module.css";

// Maps event keys to the adjustments they make (mirrors backend LIFE_EVENTS)
const EVENT_ADJUSTMENTS: Record<
  string,
  (data: TaxData) => Partial<TaxData>
> = {
  got_married: () => ({ filing_status: "Married filing jointly" }),
  had_baby: (d) => ({ dependents_count: (d.dependents_count || 0) + 1 }),
  started_side_hustle: () => ({ schedule_1_income: 10000 }),
  bought_home: () => ({ total_deductions: 25000 }),
  maxed_401k: (d) => ({ wages: Math.max(0, (d.wages || 0) - 23500) }),
  contributed_ira: (d) => ({ wages: Math.max(0, (d.wages || 0) - 7000) }),
  contributed_hsa: (d) => ({ wages: Math.max(0, (d.wages || 0) - 4300) }),
  lost_job: (d) => ({
    wages: Math.round((d.wages || 0) * 0.5),
    w2_withholding: Math.round((d.w2_withholding || 0) * 0.5),
  }),
};

const EVENT_ICONS: Record<string, string> = {
  got_married: "\u2764",
  had_baby: "\uD83D\uDC76",
  started_side_hustle: "\uD83D\uDCBC",
  bought_home: "\uD83C\uDFE0",
  maxed_401k: "\uD83D\uDCB0",
  contributed_ira: "\uD83C\uDFE6",
  contributed_hsa: "\uD83C\uDFE5",
  lost_job: "\uD83D\uDCC9",
};

interface LifeEventsProps {
  data: TaxData;
  onChange: (data: TaxData) => void;
}

export default function LifeEvents({ data, onChange }: LifeEventsProps) {
  const [events, setEvents] = useState<LifeEventPreset[]>([]);
  const [active, setActive] = useState<Set<string>>(new Set());

  useEffect(() => {
    getLifeEvents().then(setEvents).catch(() => {});
  }, []);

  const toggle = (key: string) => {
    const next = new Set(active);
    const adjust = EVENT_ADJUSTMENTS[key];
    if (!adjust) return;

    if (next.has(key)) {
      next.delete(key);
    } else {
      next.add(key);
      const changes = adjust(data);
      onChange({ ...data, ...changes });
    }
    setActive(next);
  };

  if (!events.length) return null;

  return (
    <div className={styles.wrap}>
      <p className={styles.heading}>What changed this year?</p>
      <div className={styles.chips}>
        {events.map((ev) => (
          <button
            key={ev.key}
            type="button"
            className={`${styles.chip} ${
              active.has(ev.key) ? styles.chipActive : ""
            }`}
            onClick={() => toggle(ev.key)}
            title={ev.description}
          >
            <span className={styles.icon}>{EVENT_ICONS[ev.key]}</span>
            {ev.name}
          </button>
        ))}
      </div>
    </div>
  );
}
