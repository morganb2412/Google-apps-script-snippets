import type { OnboardingActions } from "../hooks/useOnboarding";
import type { OnboardingState } from "../types/onboarding";
import type { ProjectContext } from "../types/project";

export function OnboardingWizard({ state, actions, project }: { state: OnboardingState; actions: OnboardingActions; project: ProjectContext | null }) {
  if (state.status === "loading") return <div className="setup-card" role="status"><p>Loading DevBridge setup&hellip;</p></div>;
  if (state.status === "unavailable") return <div className="setup-card setup-card--warning"><p className="eyebrow">CONNECTION</p><h2>DevBridge API unavailable</h2><p className="muted">Start the local API or reconnect to the tenant service, then try again.</p><button className="secondary" onClick={() => void actions.retry()}>Retry connection</button></div>;
  if (state.setup.onboarding_completed) return null;

  const step = state.setup.next_step;
  const localMock = state.setup.connection_mode === "LOCAL_MOCK" || import.meta.env.DEV;
  const content = {
    GOOGLE: {
      title: "Connect your Google account",
      description: localMock
        ? "Local development records an explicit mock connection without creating a Google token."
        : "DevBridge opens Google in a separate tab. Access and refresh tokens remain server-side.",
      action: localMock ? "Connect Google (local mock)" : "Continue to Google",
      run: actions.connectGoogle,
      disabled: false,
    },
    GITHUB: { title: "Connect GitHub", description: "GitHub App connection is implemented in the next tracked milestone.", action: "Connect GitHub (local mock)", run: actions.connectGitHub, disabled: !import.meta.env.DEV },
    PROJECT: { title: project ? `Use ${project.name ?? "this Apps Script project"}` : "Open an Apps Script project", description: project ? "Confirm the project detected by the DevBridge toolbar." : "DevBridge needs an active Apps Script editor tab.", action: "Use detected project", run: actions.useProject, disabled: !project },
    REPOSITORY: { title: "Repository setup is next", description: "Repository creation and selection arrive in the GitHub integration milestones.", action: "Continue", run: actions.configureStandards, disabled: true },
    STANDARDS: { title: "Choose engineering standards", description: "Start with secure recommended defaults. These can be customized later.", action: "Use recommended standards", run: actions.configureStandards, disabled: false },
    COMPLETE: { title: "Setup foundation is ready", description: "Finish onboarding. Repository and AI readiness remain visible in Health.", action: "Finish setup", run: actions.complete, disabled: false },
  }[step];

  return <section className="setup-card" aria-label="DevBridge onboarding">
    <div className="setup-progress"><span className="setup-progress__fill" style={{ width: `${progress(step)}%` }} /></div>
    <p className="eyebrow">GUIDED SETUP{localMock ? " · LOCAL MOCK" : ""}</p>
    <h2>{content.title}</h2>
    <p className="muted">{content.description}</p>
    {state.error && <p className="setup-error" role="alert">{state.error}</p>}
    <button className="primary primary--active" disabled={content.disabled || state.busy} onClick={() => void content.run()}>{state.busy ? "Working…" : content.action}</button>
  </section>;
}

function progress(step: string): number {
  return ({ GOOGLE: 15, GITHUB: 35, PROJECT: 55, REPOSITORY: 65, STANDARDS: 80, COMPLETE: 100 } as Record<string, number>)[step] ?? 0;
}
