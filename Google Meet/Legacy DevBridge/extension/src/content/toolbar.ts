import type { DevBridgeSection } from "../types/project";

export const TOOLBAR_HOST_ID = "legacy-devbridge-toolbar";

const toolbarSections: Array<{ label: string; section: DevBridgeSection }> = [
  { label: "Project", section: "Project" },
  { label: "Changes", section: "Changes" },
  { label: "Code Assistant", section: "Code Assistant" },
];

export function mountDevBridgeToolbar(onOpen: (section: DevBridgeSection) => void): HTMLElement {
  const existing = document.getElementById(TOOLBAR_HOST_ID);
  if (existing) return existing;

  const host = document.createElement("div");
  host.id = TOOLBAR_HOST_ID;
  host.setAttribute("data-devbridge-ui", "toolbar");
  const shadow = host.attachShadow({ mode: "open" });

  const style = document.createElement("style");
  style.textContent = `
    :host { all: initial; position: fixed; top: 72px; right: 18px; z-index: 2147483647; }
    .bar { display: flex; align-items: center; gap: 2px; padding: 4px; border: 1px solid #34445a; border-radius: 8px; color: #dfe8f3; background: #111925; box-shadow: 0 7px 24px rgba(0,0,0,.32); font: 12px/1.2 Arial, sans-serif; }
    .brand { display: flex; align-items: center; gap: 7px; padding: 0 9px 0 6px; color: #f1f5fa; font-weight: 700; letter-spacing: .06em; }
    .mark { display: grid; place-items: center; width: 22px; height: 22px; border-radius: 5px; color: #07111d; background: #66adff; font-size: 10px; }
    button { border: 0; border-radius: 5px; padding: 7px 9px; color: #aebdd0; background: transparent; cursor: pointer; font: inherit; }
    button:hover, button:focus-visible { color: #fff; background: #26364b; outline: none; }
    .open { color: #dcecff; background: #1d3856; }
  `;

  const bar = document.createElement("div");
  bar.className = "bar";
  bar.setAttribute("role", "toolbar");
  bar.setAttribute("aria-label", "Legacy DevBridge");

  const brand = document.createElement("span");
  brand.className = "brand";
  brand.innerHTML = '<span class="mark">DB</span><span>DEVBRIDGE</span>';
  bar.append(brand);

  for (const item of toolbarSections) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = item.label;
    button.setAttribute("aria-label", `Open DevBridge ${item.label}`);
    if (item.section === "Project") button.className = "open";
    button.addEventListener("click", () => onOpen(item.section));
    bar.append(button);
  }

  shadow.append(style, bar);
  document.documentElement.append(host);
  return host;
}
