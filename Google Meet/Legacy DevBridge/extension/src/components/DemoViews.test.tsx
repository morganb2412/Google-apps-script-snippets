import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { DemoView } from "./DemoViews";
import type { DemoWorkspace } from "../types/demo";

test("repository remains usable with an older workspace response", () => {
  const workspace = {
    mode: "DEMO",
    project_name: "ATLAS",
    script_id: "demo",
    repository: "acme/atlas",
    branch: "main",
    branches: ["main"],
    connected: true,
    changes: [],
    latest_commit: null,
    pull_request_url: null,
    updated_at: new Date().toISOString(),
  } satisfies DemoWorkspace;

  render(<DemoView section="Repository" workspace={workspace} actions={{ busy: false, connect: vi.fn(), branch: vi.fn(), commit: vi.fn(), pullRequest: vi.fn() }} />);
  expect(screen.getByRole("heading", { name: "Repository" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Create feature branch" })).toBeEnabled();
});
