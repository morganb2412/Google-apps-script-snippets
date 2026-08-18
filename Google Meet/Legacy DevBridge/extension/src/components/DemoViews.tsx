import { useState } from "react";
import { demoApi } from "../services/apiClient";
import type { AgentResult, DemoWorkspace } from "../types/demo";
import type { Section } from "../types/navigation";

interface Actions { connect: () => Promise<void>; branch: (name: string) => Promise<void>; commit: (message: string) => Promise<void>; pullRequest: () => Promise<void> }

export function DemoView({ section, workspace, actions }: { section: Section; workspace: DemoWorkspace | null; actions: Actions }) {
  if (!workspace) return <div className="notice"><strong>Demo Workspace unavailable</strong><p>Start the local DevBridge API at 127.0.0.1:8000.</p></div>;
  if (section === "Repository") return <Repository workspace={workspace} actions={actions} />;
  if (section === "Changes") return <Changes workspace={workspace} />;
  if (section === "AI Engineer") return <Agent />;
  if (section === "Standards") return <Standards />;
  if (section === "Health") return <Health workspace={workspace} />;
  return null;
}

function Repository({ workspace, actions }: { workspace: DemoWorkspace; actions: Actions }) {
  return <><DemoLabel /><h2>Repository</h2><p className="repo-name">{workspace.repository ?? "No repository connected"}</p><p className="muted">Branch · {workspace.branch}</p>
    {!workspace.connected ? <button className="primary primary--active" onClick={() => void actions.connect()}>Create & Connect Demo Repository</button> : <div className="button-row"><button className="secondary" onClick={() => void actions.branch("feature/approval-workflow")}>Create feature branch</button><button className="secondary" onClick={() => void actions.commit("feat: improve approval workflow")}>Commit changes</button><button className="secondary" onClick={() => void actions.pullRequest()}>Create pull request</button></div>}
    {workspace.latest_commit && <p className="success-line">Latest commit · {workspace.latest_commit}</p>}{workspace.pull_request_url && <p className="success-line">Demo pull request · #1 ready for review</p>}</>;
}

function Changes({ workspace }: { workspace: DemoWorkspace }) {
  const [selected, setSelected] = useState(0); const change = workspace.changes[selected];
  return <><DemoLabel /><h2>Changes <span className="count">{workspace.changes.length}</span></h2><div className="changes-list">{workspace.changes.map((item, index) => <button key={item.path} onClick={() => setSelected(index)} className={index === selected ? "change change--active" : "change"}><span>{item.state === "CONFLICT" ? "!" : "+"}</span>{item.path}<small>{item.state}</small></button>)}</div>{change && <><p className="risk">Approval required · source will not be overwritten</p><pre className="diff">{change.diff}</pre></>}</>;
}

function Agent() {
  const [mode, setMode] = useState<"plan" | "review">("plan"); const [request, setRequest] = useState("Add Finance approval when the amount exceeds $25,000."); const [result, setResult] = useState<AgentResult | null>(null);
  return <><DemoLabel /><h2>AI Engineer</h2><div className="button-row"><button className={mode === "plan" ? "secondary selected" : "secondary"} onClick={() => setMode("plan")}>PLAN</button><button className={mode === "review" ? "secondary selected" : "secondary"} onClick={() => setMode("review")}>REVIEW</button></div><textarea value={request} onChange={(event) => setRequest(event.target.value)} /><button className="primary primary--active" onClick={() => void demoApi.agent(mode, request).then(setResult)}>Analyze Project</button>{result && <div className="agent-result"><h3>{result.title}</h3><p>{result.summary}</p><ol>{result.items.map((item) => <li key={item}>{item}</li>)}</ol><p className="fine-print">Files: {result.files_affected.join(", ")} · No OAuth changes detected.</p></div>}</>;
}

function Standards() { return <><DemoLabel /><h2>Standards</h2>{["V8 runtime required", "PropertiesService for configuration", "No hard-coded secrets", "JSDoc for public functions", "AI changes always require approval", "OAuth scope changes require review"].map((rule) => <p className="standard" key={rule}><span>✓</span>{rule}</p>)}</>; }
function Health({ workspace }: { workspace: DemoWorkspace }) { return <><DemoLabel /><h2>DevBridge Health</h2>{[["Apps Script", "Ready"], ["Repository", workspace.connected ? "Ready" : "Needs attention"], ["Synchronization", workspace.changes.length ? `${workspace.changes.length} changes` : "Up to date"], ["AI Engineer", "Demo ready"], ["Company Standards", "Ready"]].map(([key, value]) => <div className="health-row" key={key}><span>{key}</span><strong>{value}</strong></div>)}</>; }
function DemoLabel() { return <p className="demo-label">DEMO WORKSPACE · NO EXTERNAL WRITES</p>; }
