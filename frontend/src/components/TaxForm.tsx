import { useState } from "react";
import type { TaxData, FilingStatus } from "../api/types";
import LifeEvents from "./LifeEvents";
import styles from "./TaxForm.module.css";

const FILING_STATUSES: { value: FilingStatus; short: string }[] = [
  { value: "Single", short: "Single" },
  { value: "Married filing jointly", short: "MFJ" },
  { value: "Head of household", short: "HOH" },
  { value: "Married filing separately", short: "MFS" },
];

interface TaxFormProps {
  priorData: TaxData;
  currentData: TaxData;
  onPriorChange: (data: TaxData) => void;
  onCurrentChange: (data: TaxData) => void;
  onSubmit: () => void;
  loading: boolean;
}

function CurrencyInput({
  value,
  onChange,
  label,
  hint,
  allowNegative,
}: {
  value: number;
  onChange: (v: number) => void;
  label: string;
  hint?: string;
  allowNegative?: boolean;
}) {
  return (
    <div className={styles.field}>
      <label className={styles.label}>
        {label}
        {hint && <span className={styles.hint}>{hint}</span>}
      </label>
      <div className={styles.inputWrap}>
        <span className={styles.prefix}>$</span>
        <input
          type="number"
          className={styles.input}
          value={value || ""}
          onChange={(e) => {
            const v = parseFloat(e.target.value) || 0;
            onChange(allowNegative ? v : Math.max(0, v));
          }}
          placeholder="0"
          min={allowNegative ? undefined : 0}
        />
      </div>
    </div>
  );
}

function YearColumn({
  title,
  data,
  onChange,
  showLifeEvents,
}: {
  title: string;
  data: TaxData;
  onChange: (data: TaxData) => void;
  showLifeEvents?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);

  const update = <K extends keyof TaxData>(key: K, value: TaxData[K]) => {
    onChange({ ...data, [key]: value });
  };

  return (
    <div className={styles.column}>
      <div className={styles.columnHeader}>
        <h3 className={styles.columnTitle}>{title}</h3>
        <select
          className={styles.yearSelect}
          value={data.tax_year}
          onChange={(e) => update("tax_year", parseInt(e.target.value))}
        >
          {Array.from({ length: 6 }, (_, i) => {
            const y = new Date().getFullYear() - 1 - i;
            return (
              <option key={y} value={y}>
                {y}
              </option>
            );
          })}
        </select>
      </div>

      <div className={styles.filingStatus}>
        <label className={styles.label}>Filing Status</label>
        <div className={styles.statusGroup}>
          {FILING_STATUSES.map((fs) => (
            <button
              key={fs.value}
              type="button"
              className={`${styles.statusBtn} ${
                data.filing_status === fs.value ? styles.statusActive : ""
              }`}
              onClick={() => update("filing_status", fs.value)}
            >
              {fs.short}
            </button>
          ))}
        </div>
      </div>

      <CurrencyInput
        label="W-2 Wages"
        hint="W-2 Box 1"
        value={data.wages}
        onChange={(v) => update("wages", v)}
      />
      <CurrencyInput
        label="W-2 Withholding"
        hint="W-2 Box 2"
        value={data.w2_withholding}
        onChange={(v) => update("w2_withholding", v)}
      />

      <div className={styles.field}>
        <label className={styles.label}>Dependents</label>
        <input
          type="number"
          className={styles.input}
          value={data.dependents_count || ""}
          onChange={(e) =>
            update("dependents_count", Math.max(0, parseInt(e.target.value) || 0))
          }
          placeholder="0"
          min={0}
        />
      </div>

      <button
        type="button"
        className={styles.expandBtn}
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? "Hide advanced fields" : "Show more fields"}
        <span className={expanded ? styles.arrowUp : styles.arrowDown} />
      </button>

      {expanded && (
        <div className={styles.advanced}>
          <CurrencyInput
            label="Self-Employment Income"
            hint="Schedule C, line 31"
            value={data.schedule_1_income}
            onChange={(v) => update("schedule_1_income", v)}
          />
          <CurrencyInput
            label="Other Income"
            hint="1040 line 8"
            value={data.other_income}
            onChange={(v) => update("other_income", v)}
          />
          <CurrencyInput
            label="Taxable Interest"
            hint="1099-INT Box 1"
            value={data.taxable_interest}
            onChange={(v) => update("taxable_interest", v)}
          />
          <CurrencyInput
            label="Ordinary Dividends"
            hint="1099-DIV Box 1a"
            value={data.ordinary_dividends}
            onChange={(v) => update("ordinary_dividends", v)}
          />
          <CurrencyInput
            label="Capital Gains / Losses"
            hint="1040 line 7"
            value={data.capital_gain_or_loss}
            onChange={(v) => update("capital_gain_or_loss", v)}
            allowNegative
          />
          <CurrencyInput
            label="Total Deductions (leave blank for standard)"
            hint="1040 line 12"
            value={data.total_deductions ?? 0}
            onChange={(v) => update("total_deductions", v || null)}
          />
          <CurrencyInput
            label="QBI Deduction"
            hint="1040 line 13"
            value={data.qbi_deduction}
            onChange={(v) => update("qbi_deduction", v)}
          />
          <CurrencyInput
            label="Child Tax Credit"
            hint="1040 line 19"
            value={data.child_tax_credit}
            onChange={(v) => update("child_tax_credit", v)}
          />
          <CurrencyInput
            label="Schedule 3 Credits"
            hint="Schedule 3, line 8"
            value={data.schedule_3_total}
            onChange={(v) => update("schedule_3_total", v)}
          />
          <CurrencyInput
            label="1099 Withholding"
            hint="1099 Box 4"
            value={data.withholding_1099}
            onChange={(v) => update("withholding_1099", v)}
          />
          <CurrencyInput
            label="Estimated Tax Payments"
            hint="1040 line 26"
            value={data.estimated_tax_payments}
            onChange={(v) => update("estimated_tax_payments", v)}
          />
          <CurrencyInput
            label="Self-Employment Tax"
            hint="Schedule SE, line 12"
            value={data.self_employment_tax}
            onChange={(v) => update("self_employment_tax", v)}
          />
          <CurrencyInput
            label="Schedule 2 Additional Taxes"
            hint="Schedule 2, line 21"
            value={data.schedule_2_total}
            onChange={(v) => update("schedule_2_total", v)}
          />
        </div>
      )}

      {showLifeEvents && (
        <LifeEvents data={data} onChange={onChange} />
      )}
    </div>
  );
}

export default function TaxForm({
  priorData,
  currentData,
  onPriorChange,
  onCurrentChange,
  onSubmit,
  loading,
}: TaxFormProps) {
  return (
    <div className={styles.formWrap}>
      <div className={styles.columns}>
        <YearColumn
          title="Last Year"
          data={priorData}
          onChange={onPriorChange}
        />
        <div className={styles.divider} />
        <YearColumn
          title="This Year"
          data={currentData}
          onChange={onCurrentChange}
          showLifeEvents
        />
      </div>
      <button
        className={styles.submitBtn}
        onClick={onSubmit}
        disabled={loading}
      >
        {loading ? "Analyzing..." : "Show Me Why"}
      </button>
    </div>
  );
}
