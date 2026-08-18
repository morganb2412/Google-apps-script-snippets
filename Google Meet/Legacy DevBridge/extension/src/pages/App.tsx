import { useState } from "react";
import { Navigation } from "../components/Navigation";
import { StatusBadge } from "../components/StatusBadge";
import { useApiHealth } from "../hooks/useApiHealth";
import type { Section } from "../types/navigation";

export function App() {
  const [active, setActive] = useState<Section>("Project");
  const apiState = useApiHealth();
  return <main>
    <header><div><p className="eyebrow">LEGACY</p><h1>DEVBRIDGE</h1></div><StatusBadge label={apiState === "connected" ? "API connected" : apiState === "checking" ? "Checking API" : "API unavailable"} tone={apiState === "connected" ? "good" : apiState === "checking" ? "neutral" : "warning"} /></header>
    <Navigation active={active} onSelect={setActive} />
    <section className="panel">
      <p className="eyebrow">{active.toUpperCase()}</p>
      <h2>{active === "Project" ? "Open an Apps Script project" : `${active} foundation ready`}</h2>
      <p className="muted">{active === "Project" ? "Project detection arrives in Milestone 2. No credentials are stored in this extension." : "This section is intentionally scaffolded for its planned milestone."}</p>
      {active === "Project" && <button className="primary" disabled>Waiting for Apps Script</button>}
    </section>
    <footer>Secure by design · Human approval required</footer>
  </main>;
}
