import type { DevBridgeSection } from "./project";

export const sections = ["Project", "Repository", "Changes", "AI Engineer", "Standards", "Health"] as const satisfies readonly DevBridgeSection[];
export type Section = DevBridgeSection;
