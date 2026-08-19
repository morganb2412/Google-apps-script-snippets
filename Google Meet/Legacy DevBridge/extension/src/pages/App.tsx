import { useEffect, useState } from "react";
import { Navigation } from "../components/Navigation";
import { ProjectOverview } from "../components/ProjectOverview";
import { OnboardingWizard } from "../components/OnboardingWizard";
import { DemoView } from "../components/DemoViews";
import { StatusBadge } from "../components/StatusBadge";
import { SectionErrorBoundary } from "../components/SectionErrorBoundary";
import { useApiHealth } from "../hooks/useApiHealth";
import { useProjectContext } from "../hooks/useProjectContext";
import { useOnboarding } from "../hooks/useOnboarding";
import { useDemoWorkspace } from "../hooks/useDemoWorkspace";
import type { Section } from "../types/navigation";
import type { ExtensionMessage } from "../types/project";

export function App() {
  const [active, setActive] = useState<Section>("Project");
  const apiState = useApiHealth();
  const projectState = useProjectContext();
  const detectedProject = projectState.status === "detected" ? projectState.project : null;
  const [onboardingState, onboardingActions] = useOnboarding(detectedProject);
  const demo = useDemoWorkspace();
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
      {active === "Project" ? <><OnboardingWizard state={onboardingState} actions={onboardingActions} project={detectedProject} /><ProjectOverview state={projectState} apiState={apiState} /></> : <SectionErrorBoundary section={active}><DemoView section={active} workspace={demo.workspace} actions={demo} />{demo.error && <p className="action-error" role="alert">{demo.error}</p>}</SectionErrorBoundary>}
    </section>
    <footer>Code Assistant &middot; Standards checked &middot; Human approval required</footer>
  </main>;
}
