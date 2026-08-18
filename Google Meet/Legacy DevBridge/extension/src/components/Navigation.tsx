import { sections, type Section } from "../types/navigation";

export function Navigation({ active, onSelect }: { active: Section; onSelect: (section: Section) => void }) {
  return <nav aria-label="DevBridge sections">{sections.map((section) => <button className={active === section ? "nav-item nav-item--active" : "nav-item"} key={section} onClick={() => onSelect(section)}>{section}</button>)}</nav>;
}
