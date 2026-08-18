import type { DevBridgeSection } from "./project";

export const sections = ["Project", "Repository", "Changes", "Code Assistant", "Standards", "Health"] as const satisfies readonly DevBridgeSection[];
export type Section = DevBridgeSection;
