export interface ProjectContext {
  scriptId: string;
  name: string | null;
  editorUrl: string;
  detectedAt: string;
}

export type ProjectContextState =
  | { status: "loading" }
  | { status: "detected"; project: ProjectContext }
  | { status: "not-apps-script" }
  | { status: "unavailable"; message: string };

export type ExtensionMessage =
  | { type: "DEVBRIDGE_PROJECT_CONTEXT"; payload: ProjectContext }
  | { type: "DEVBRIDGE_GET_PROJECT_CONTEXT" }
  | { type: "DEVBRIDGE_PROJECT_CONTEXT_CHANGED"; payload: ProjectContext };
