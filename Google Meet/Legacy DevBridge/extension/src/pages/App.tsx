import { useEffect, useState } from "react";
import { Navigation } from "../components/Navigation";
import { ProjectOverview } from "../components/ProjectOverview";
import { OnboardingWizard } from "../components/OnboardingWizard";
import { StatusBadge } from "../components/StatusBadge";
import { useApiHealth } from "../hooks/useApiHealth";
import { useProjectContext } from "../hooks/useProjectContext";
import { useOnboarding } from "../hooks/useOnboarding";
import type { Section } from "../types/navigation";
import type { ExtensionMessage } from "../types/project";

export function App() {
  const [active, setActive] = useState<Section>("Project");
  const apiState = useApiHealth();
  const projectState = useProjectContext();
  const detectedProject = projectState.status === "detected" ? projectState.project : null;
  const [onboardingState, onboardingActions] = useOnboarding(detectedProject);
  useEffect(() => {
    const navigate = (message: ExtensionMessage) => {
      if (message.type === "DEVBRIDGE_NAVIGATE") setActive(message.section);
    };
    chrome.runtime.onMessage.addListener(navigate);
    return () => chrome.runtime.onMessage.removeListener(navigate);
  }, []);
  return <main>
    <header><div><p className="eyebrow">LEGACY</p><h1>DEVBRIDGE</h1></div><StatusBadge label={apiState === "connected" ? "API connected" : apiState === "checking" ? "Checking API" : "API unavailable"} tone={apiState === "connected" ? "good" : apiState === "checking" ? "neutral" : "warning"} /></header>
    <Navigation active={active} onSelect={setActive} />
    <section className="panel">
      <p className="eyebrow">{active.toUpperCase()}</p>
      {active === "Project" ? <><OnboardingWizard state={onboardingState} actions={onboardingActions} project={detectedProject} /><ProjectOverview state={projectState} apiState={apiState} /></> : <><h2>{active} foundation ready</h2><p className="muted">This section is intentionally scaffolded for its planned milestone.</p></>}
    </section>
    <footer>Secure by design · Human approval required</footer>
  </main>;
}
