import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { ProjectOverview } from "./ProjectOverview";

test("renders a detected Apps Script project", () => {
  render(<ProjectOverview apiState="connected" state={{ status: "detected", project: {
    scriptId: "1AbC_def-123",
    name: "ATLAS",
    editorUrl: "https://script.google.com/home/projects/1AbC_def-123/edit",
    detectedAt: "2026-08-18T00:00:00Z",
  } }} />);
  expect(screen.getByRole("heading", { name: "ATLAS" })).toBeInTheDocument();
  expect(screen.getByText("1AbC_def-123")).toBeInTheDocument();
  expect(screen.getByText("Available")).toBeInTheDocument();
});
