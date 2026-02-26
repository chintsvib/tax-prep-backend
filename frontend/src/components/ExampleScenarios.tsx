import type { TaxData } from "../api/types";
import styles from "./ExampleScenarios.module.css";

interface Scenario {
  name: string;
  description: string;
  prior: Partial<TaxData>;
  current: Partial<TaxData>;
}

const SCENARIOS: Scenario[] = [
  {
    name: "Got married + had a baby",
    description: "Single → MFJ, added dependent, wages up",
    prior: { tax_year: 2023, filing_status: "Single", wages: 75000, w2_withholding: 11000, dependents_count: 0 },
    current: { tax_year: 2024, filing_status: "Married filing jointly", wages: 85000, w2_withholding: 12500, dependents_count: 1 },
  },
  {
    name: "Big raise, same withholding",
    description: "Wages jumped $30k but forgot to update W-4",
    prior: { tax_year: 2023, filing_status: "Single", wages: 70000, w2_withholding: 10500 },
    current: { tax_year: 2024, filing_status: "Single", wages: 100000, w2_withholding: 10500 },
  },
  {
    name: "Started freelancing",
    description: "W-2 employee added $25k side income",
    prior: { tax_year: 2023, filing_status: "Single", wages: 80000, w2_withholding: 12000 },
    current: { tax_year: 2024, filing_status: "Single", wages: 80000, w2_withholding: 12000, schedule_1_income: 25000, estimated_tax_payments: 3000 },
  },
  {
    name: "Bought a house",
    description: "Switched from standard to itemized deductions",
    prior: { tax_year: 2023, filing_status: "Married filing jointly", wages: 120000, w2_withholding: 18000 },
    current: { tax_year: 2024, filing_status: "Married filing jointly", wages: 125000, w2_withholding: 18500, total_deductions: 35000 },
  },
  {
    name: "Maxed 401k + HSA",
    description: "Reduced taxable wages with retirement + health savings",
    prior: { tax_year: 2023, filing_status: "Single", wages: 95000, w2_withholding: 14000 },
    current: { tax_year: 2024, filing_status: "Single", wages: 67200, w2_withholding: 14000 },
  },
  {
    name: "Investment income spike",
    description: "Added interest, dividends, and capital gains",
    prior: { tax_year: 2023, filing_status: "Single", wages: 90000, w2_withholding: 13500 },
    current: { tax_year: 2024, filing_status: "Single", wages: 90000, w2_withholding: 13500, taxable_interest: 2500, ordinary_dividends: 3000, capital_gain_or_loss: 15000 },
  },
  {
    name: "Lost job mid-year",
    description: "Wages and withholding cut in half",
    prior: { tax_year: 2023, filing_status: "Single", wages: 85000, w2_withholding: 12750 },
    current: { tax_year: 2024, filing_status: "Single", wages: 42500, w2_withholding: 6375 },
  },
  {
    name: "Divorce",
    description: "MFJ → Single, lost dependent, wages similar",
    prior: { tax_year: 2023, filing_status: "Married filing jointly", wages: 110000, w2_withholding: 16000, dependents_count: 2 },
    current: { tax_year: 2024, filing_status: "Single", wages: 110000, w2_withholding: 16000, dependents_count: 0 },
  },
  {
    name: "New parent, Head of Household",
    description: "Single → HOH with child + CTC",
    prior: { tax_year: 2023, filing_status: "Single", wages: 65000, w2_withholding: 9000, dependents_count: 0 },
    current: { tax_year: 2024, filing_status: "Head of household", wages: 68000, w2_withholding: 9500, dependents_count: 1, child_tax_credit: 2200 },
  },
  {
    name: "Full-time freelancer",
    description: "All W-2 income replaced by Schedule C + SE tax",
    prior: { tax_year: 2023, filing_status: "Single", wages: 90000, w2_withholding: 13500 },
    current: { tax_year: 2024, filing_status: "Single", wages: 0, w2_withholding: 0, schedule_1_income: 95000, self_employment_tax: 13430, estimated_tax_payments: 15000, qbi_deduction: 19000 },
  },
  {
    name: "Stock market loss",
    description: "Capital loss offset some income",
    prior: { tax_year: 2023, filing_status: "Married filing jointly", wages: 150000, w2_withholding: 25000, capital_gain_or_loss: 8000 },
    current: { tax_year: 2024, filing_status: "Married filing jointly", wages: 150000, w2_withholding: 25000, capital_gain_or_loss: -3000 },
  },
  {
    name: "Second child",
    description: "Same income, added another dependent + CTC",
    prior: { tax_year: 2023, filing_status: "Married filing jointly", wages: 100000, w2_withholding: 15000, dependents_count: 1, child_tax_credit: 2200 },
    current: { tax_year: 2024, filing_status: "Married filing jointly", wages: 102000, w2_withholding: 15300, dependents_count: 2, child_tax_credit: 4400 },
  },
  {
    name: "High earner, underwithholding",
    description: "Bonus pushed income up, not enough withheld",
    prior: { tax_year: 2023, filing_status: "Single", wages: 180000, w2_withholding: 35000 },
    current: { tax_year: 2024, filing_status: "Single", wages: 250000, w2_withholding: 40000, schedule_2_total: 2250 },
  },
  {
    name: "IRA + charitable deductions",
    description: "Traditional IRA contribution + large charity donation",
    prior: { tax_year: 2023, filing_status: "Single", wages: 85000, w2_withholding: 12000 },
    current: { tax_year: 2024, filing_status: "Single", wages: 78000, w2_withholding: 12000, total_deductions: 22000 },
  },
  {
    name: "1099 contractor, no estimated payments",
    description: "Forgot to pay quarterly taxes on side gig",
    prior: { tax_year: 2023, filing_status: "Single", wages: 60000, w2_withholding: 8500 },
    current: { tax_year: 2024, filing_status: "Single", wages: 60000, w2_withholding: 8500, schedule_1_income: 40000, withholding_1099: 0, estimated_tax_payments: 0 },
  },
  {
    name: "Multi-income family",
    description: "Both spouses working, interest + dividends",
    prior: { tax_year: 2023, filing_status: "Married filing jointly", wages: 140000, w2_withholding: 21000, taxable_interest: 500, ordinary_dividends: 1000, dependents_count: 1 },
    current: { tax_year: 2024, filing_status: "Married filing jointly", wages: 160000, w2_withholding: 24000, taxable_interest: 1200, ordinary_dividends: 2500, dependents_count: 2, child_tax_credit: 4400 },
  },
  {
    name: "Filing status only change",
    description: "Same income, switched Single → HOH",
    prior: { tax_year: 2023, filing_status: "Single", wages: 70000, w2_withholding: 10000, dependents_count: 1 },
    current: { tax_year: 2024, filing_status: "Head of household", wages: 70000, w2_withholding: 10000, dependents_count: 1 },
  },
  {
    name: "Everything changed",
    description: "New job, married, baby, bought house, investments",
    prior: { tax_year: 2023, filing_status: "Single", wages: 65000, w2_withholding: 9500, dependents_count: 0 },
    current: { tax_year: 2024, filing_status: "Married filing jointly", wages: 110000, w2_withholding: 16000, dependents_count: 1, child_tax_credit: 2200, total_deductions: 30000, taxable_interest: 800, ordinary_dividends: 1500, capital_gain_or_loss: 5000 },
  },
  {
    name: "Retired mid-year",
    description: "Half year wages, added 1099 pension + interest",
    prior: { tax_year: 2023, filing_status: "Married filing jointly", wages: 120000, w2_withholding: 18000 },
    current: { tax_year: 2024, filing_status: "Married filing jointly", wages: 60000, w2_withholding: 9000, other_income: 30000, withholding_1099: 4500, taxable_interest: 5000, ordinary_dividends: 3000 },
  },
  {
    name: "Same everything (control test)",
    description: "Nothing changed — should show $0 difference",
    prior: { tax_year: 2023, filing_status: "Single", wages: 75000, w2_withholding: 11000 },
    current: { tax_year: 2024, filing_status: "Single", wages: 75000, w2_withholding: 11000 },
  },
];

const DEFAULTS: TaxData = {
  tax_year: 2024,
  filing_status: "Single",
  wages: 0,
  schedule_1_income: 0,
  w2_withholding: 0,
  schedule_3_total: 0,
  total_deductions: null,
  deduction_type: "Standard",
  dependents_count: 0,
  child_tax_credit: 0,
  other_income: 0,
  taxable_interest: 0,
  ordinary_dividends: 0,
  capital_gain_or_loss: 0,
  self_employment_tax: 0,
  qbi_deduction: 0,
  schedule_2_total: 0,
  estimated_tax_payments: 0,
  withholding_1099: 0,
};

interface ExampleScenariosProps {
  onLoad: (prior: TaxData, current: TaxData) => void;
}

export default function ExampleScenarios({ onLoad }: ExampleScenariosProps) {
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const idx = parseInt(e.target.value);
    if (isNaN(idx)) return;
    const s = SCENARIOS[idx];
    onLoad(
      { ...DEFAULTS, ...s.prior } as TaxData,
      { ...DEFAULTS, ...s.current } as TaxData
    );
  };

  return (
    <div className={styles.wrap}>
      <select className={styles.select} onChange={handleChange} defaultValue="">
        <option value="" disabled>
          Load an example scenario...
        </option>
        {SCENARIOS.map((s, i) => (
          <option key={i} value={i}>
            {s.name} — {s.description}
          </option>
        ))}
      </select>
    </div>
  );
}
