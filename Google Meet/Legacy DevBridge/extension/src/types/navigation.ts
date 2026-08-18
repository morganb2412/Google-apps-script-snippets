export const sections = ["Project", "Repository", "Changes", "AI Engineer", "Standards", "Health"] as const;
export type Section = (typeof sections)[number];
