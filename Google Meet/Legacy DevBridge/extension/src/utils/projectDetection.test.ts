import { describe, expect, test } from "vitest";
import { detectProjectContext, extractScriptId, normalizeProjectName } from "./projectDetection";

describe("Apps Script project detection", () => {
  test("extracts a project ID from the editor URL", () => {
    expect(extractScriptId(new URL("https://script.google.com/home/projects/1AbC_def-123/edit"))).toBe("1AbC_def-123");
  });

  test("rejects unrelated Google Script pages", () => {
    expect(extractScriptId(new URL("https://script.google.com/home/my"))).toBeNull();
  });

  test("normalizes the editor title", () => {
    expect(normalizeProjectName("ATLAS - Google Apps Script")).toBe("ATLAS");
  });

  test("creates a safe project context", () => {
    const context = detectProjectContext(
      "https://script.google.com/home/projects/1AbC_def-123/edit?folder=0",
      "ATLAS – Google Apps Script",
    );
    expect(context).toMatchObject({
      scriptId: "1AbC_def-123",
      name: "ATLAS",
      editorUrl: "https://script.google.com/home/projects/1AbC_def-123/edit",
    });
  });
});
