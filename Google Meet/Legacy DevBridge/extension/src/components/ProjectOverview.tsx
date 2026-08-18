import type { ApiState } from "../hooks/useApiHealth";
import type { ProjectContextState } from "../types/project";
import { StatusBadge } from "./StatusBadge";

export function ProjectOverview({ state, apiState }: { state: ProjectContextState; apiState: ApiState }) {
  if (state.status === "loading") return <p className="muted">Detecting the active Apps Script project…</p>;
  if (state.status === "unavailable") return <div className="notice notice--warning"><strong>Project detection needs attention</strong><p>{state.message}</p></div>;
  if (state.status === "not-apps-script") return <div className="notice"><strong>Open an Apps Script project</strong><p>DevBridge recognizes projects opened at script.google.com.</p></div>;
  const { project } = state;
  return <>
    <div className="project-heading"><div><p className="eyebrow">ACTIVE PROJECT</p><h2>{project.name ?? "Apps Script Project"}</h2></div><StatusBadge label="Detected" tone="good" /></div>
    <dl className="project-grid">
      <div><dt>Apps Script</dt><dd>Connected to editor</dd></div>
      <div><dt>Project ID</dt><dd className="project-id" title={project.scriptId}>{project.scriptId}</dd></div>
      <div><dt>Repository</dt><dd>Not connected</dd></div>
      <div><dt>Backend</dt><dd>{apiState === "connected" ? "Available" : apiState === "checking" ? "Checking" : "Local API unavailable"}</dd></div>
    </dl>
    <button className="primary primary--active">Add to GitHub</button>
    <p className="fine-print">Repository connection begins in a later milestone. This button currently previews readiness only.</p>
  </>;
}
