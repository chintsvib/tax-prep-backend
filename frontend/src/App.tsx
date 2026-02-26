import { useState, useCallback } from "react";
import { AnimatePresence } from "framer-motion";
import { AuthProvider } from "./context/AuthContext";
import Header from "./components/Header";
import AuthModal from "./components/AuthModal";
import TaxForm from "./components/TaxForm";
import ExampleScenarios from "./components/ExampleScenarios";
import ResultsPanel from "./components/ResultsPanel";
import Disclaimer from "./components/Disclaimer";
import { explainRefundChange } from "./api/client";
import type { TaxData, RefundExplainerResponse } from "./api/types";
import { DEFAULT_TAX_DATA } from "./api/types";
import styles from "./App.module.css";

function AppInner() {
  const [showAuth, setShowAuth] = useState(false);
  const [priorData, setPriorData] = useState<TaxData>({
    ...DEFAULT_TAX_DATA,
    tax_year: new Date().getFullYear() - 2,
  });
  const [currentData, setCurrentData] = useState<TaxData>({
    ...DEFAULT_TAX_DATA,
    tax_year: new Date().getFullYear() - 1,
  });
  const [result, setResult] = useState<RefundExplainerResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await explainRefundChange({
        prior_data: priorData,
        current_data: currentData,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }, [priorData, currentData]);

  return (
    <div className={styles.app}>
      <Header onLoginClick={() => setShowAuth(true)} />

      <main className={styles.main}>
        <div className={styles.hero}>
          <h2 className={styles.heroTitle}>
            Why did your <span className={styles.heroAccent}>refund</span>{" "}
            change?
          </h2>
          <p className={styles.heroSub}>
            Enter two years of tax data. We'll show you exactly what changed and
            why — in 60 seconds.
          </p>
        </div>

        {import.meta.env.DEV && (
          <ExampleScenarios
            onLoad={(prior, current) => {
              setPriorData(prior);
              setCurrentData(current);
            }}
          />
        )}

        <TaxForm
          priorData={priorData}
          currentData={currentData}
          onPriorChange={setPriorData}
          onCurrentChange={setCurrentData}
          onSubmit={handleSubmit}
          loading={loading}
        />

        {error && (
          <p style={{ color: "#c93a2a", textAlign: "center", marginTop: 24 }}>
            {error}
          </p>
        )}
      </main>

      <Disclaimer />

      <AnimatePresence>
        {showAuth && <AuthModal onClose={() => setShowAuth(false)} />}
      </AnimatePresence>

      <AnimatePresence>
        {result && (
          <ResultsPanel result={result} onClose={() => setResult(null)} />
        )}
      </AnimatePresence>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppInner />
    </AuthProvider>
  );
}
