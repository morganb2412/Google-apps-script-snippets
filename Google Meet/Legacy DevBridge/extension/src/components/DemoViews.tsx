import { useState } from "react";
import { demoApi } from "../services/apiClient";
import type { AssistantResponse, DemoWorkspace } from "../types/demo";
import type { Section } from "../types/navigation";

interface Actions {
  busy: boolean;
  connect: () => Promise<void>;
  branch: (name: string) => Promise<void>;
  commit: (message: string) => Promise<void>;
  pullRequest: () => Promise<void>;
}

export function DemoView({ section, workspace, actions }: { section: Section; workspace: DemoWorkspace | null; actions: Actions }) {
  if (!workspace) return <div className="notice"><strong>Demo Workspace unavailable</strong><p>Start the local DevBridge API at 127.0.0.1:8000.</p></div>;
  if (section === "Repository") return <Repository workspace={workspace} actions={actions} />;
  if (section === "Changes") return <Changes workspace={workspace} />;
  if (section === "Code Assistant") return <CodeAssistant />;
  if (section === "Standards") return <Standards />;
  if (section === "Health") return <Health workspace={workspace} />;
  return null;
}

function Repository({ workspace, actions }: { workspace: DemoWorkspace; actions: Actions }) {
  const onMain = workspace.branch === "main";
  return <><DemoLabel /><h2>Repository</h2><p className="repo-name">{workspace.repository ?? "No repository connected"}</p><p className="muted">Branch · {workspace.branch}</p>
    {!workspace.connected ? <button disabled={actions.busy} className="primary primary--active" onClick={() => void actions.connect()}>Create & Connect Demo Repository</button> : <><div className="workflow-steps"><span className="done">1 Connected</span><span className={!onMain ? "done" : ""}>2 Feature branch</span><span className={workspace.latest_commit ? "done" : ""}>3 Commit</span><span className={workspace.pull_request_url ? "done" : ""}>4 Pull request</span></div><div className="button-row"><button disabled={actions.busy || !onMain} className="secondary" onClick={() => void actions.branch("feature/approval-workflow")}>Create feature branch</button><button disabled={actions.busy || onMain || Boolean(workspace.latest_commit)} className="secondary" onClick={() => void actions.commit("feat: improve approval workflow")}>Commit approved changes</button><button disabled={actions.busy || !workspace.latest_commit || Boolean(workspace.pull_request_url)} className="secondary" onClick={() => void actions.pullRequest()}>Create pull request</button></div></>}
    {workspace.latest_commit && <p className="success-line">Latest commit · {workspace.latest_commit}</p>}{workspace.pull_request_url && <p className="success-line"><a href={workspace.pull_request_url} target="_blank" rel="noreferrer">Demo pull request · #1 ready for review</a></p>}{workspace.audit_events.length > 0 && <details><summary>Audit trail ({workspace.audit_events.length})</summary>{workspace.audit_events.map((event, index) => <p className="audit-event" key={`${event}-${index}`}>{event}</p>)}</details>}</>;
}

function Changes({ workspace }: { workspace: DemoWorkspace }) {
  const [selected, setSelected] = useState(0); const change = workspace.changes[selected];
  return <><DemoLabel /><h2>Changes <span className="count">{workspace.changes.length}</span></h2><div className="changes-list">{workspace.changes.map((item, index) => <button key={item.path} onClick={() => setSelected(index)} className={index === selected ? "change change--active" : "change"}><span>{item.state === "CONFLICT" ? "!" : "+"}</span>{item.path}<small>{item.state}</small></button>)}</div>{change && <><p className="risk">Approval required · source will not be overwritten</p><pre className="diff">{change.diff}</pre></>}</>;
}

function CodeAssistant() {
  const [request, setRequest] = useState("Analyze this project against our standards and fix the hard-coded Finance email.");
  const [conversation, setConversation] = useState<Array<{ role: "user" | "assistant"; text: string }>>([{ role: "assistant", text: "I’m your project-aware Code Assistant. I can explain code, check security and company standards, and prepare fixes for your approval." }]);
  const [result, setResult] = useState<AssistantResponse | null>(null);
  const send = async () => { const prompt = request.trim(); if (!prompt) return; setConversation((items) => [...items, { role: "user", text: prompt }]); setRequest(""); const response = await demoApi.chat(prompt); setResult(response); setConversation((items) => [...items, { role: "assistant", text: response.message }]); };
  const decide = async (approved: boolean) => { if (!result?.proposal) return; const response = await demoApi.decide(result.proposal.proposal_id, approved); setResult(response); setConversation((items) => [...items, { role: "assistant", text: response.message }]); };
  return <><DemoLabel /><h2>Code Assistant</h2><p className="muted">Conversational project help · security and standards aware · changes require approval</p><div className="conversation">{conversation.map((message, index) => <div key={`${message.role}-${index}`} className={`message message--${message.role}`}><strong>{message.role === "user" ? "You" : "DevBridge"}</strong><p>{message.text}</p></div>)}</div><textarea aria-label="Message Code Assistant" value={request} onChange={(event) => setRequest(event.target.value)} placeholder="Ask about the project or request a fix…" /><button className="primary primary--active" onClick={() => void send()}>Send</button>{result?.findings.length ? <div className="findings"><h3>Standards & security findings</h3>{result.findings.map((finding) => <p key={finding}>{finding}</p>)}</div> : null}{result?.proposal && <div className="proposal"><div className="proposal-head"><strong>Proposed change</strong><span>{result.proposal.risk_level} RISK</span></div><p>{result.proposal.file} · {result.proposal.operation}</p><p className="muted">{result.proposal.explanation}</p><pre className="diff">{result.proposal.diff}</pre><p className="fine-print">Original hash: {result.proposal.original_hash.slice(0, 16)}… · Status: {result.proposal.status}</p>{result.proposal.status === "PENDING_APPROVAL" && <div className="button-row"><button className="primary primary--active" onClick={() => void decide(true)}>Approve demo change</button><button className="secondary" onClick={() => void decide(false)}>Reject</button></div>}</div>}</>;
}

function Standards() { return <><DemoLabel /><h2>Standards</h2>{["V8 runtime required", "PropertiesService for configuration", "No hard-coded secrets", "JSDoc for public functions", "AI changes always require approval", "OAuth scope changes require review"].map((rule) => <p className="standard" key={rule}><span>✓</span>{rule}</p>)}</>; }
function Health({ workspace }: { workspace: DemoWorkspace }) { return <><DemoLabel /><h2>DevBridge Health</h2>{[["Apps Script", "Ready"], ["Repository", workspace.connected ? "Ready" : "Needs attention"], ["Synchronization", workspace.changes.length ? `${workspace.changes.length} changes` : "Up to date"], ["Code Assistant", "Demo ready"], ["Company Standards", "Ready"]].map(([key, value]) => <div className="health-row" key={key}><span>{key}</span><strong>{value}</strong></div>)}</>; }
function DemoLabel() { return <p className="demo-label">DEMO WORKSPACE · NO EXTERNAL WRITES</p>; }
