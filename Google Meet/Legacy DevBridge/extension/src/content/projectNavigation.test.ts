import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { watchProjectNavigation } from "./projectNavigation";

beforeEach(() => {
  vi.useFakeTimers();
  window.history.replaceState({}, "", "/home/projects/project-one/edit");
  document.title = "Project One - Google Apps Script";
});

afterEach(() => vi.useRealTimers());

test("detects Apps Script SPA URL changes that do not emit popstate", () => {
  const onChange = vi.fn();
  const stop = watchProjectNavigation(onChange, 100);
  window.history.pushState({}, "", "/home/projects/project-two/edit");
  vi.advanceTimersByTime(100);
  expect(onChange).toHaveBeenCalledTimes(1);
  stop();
});

test("detects title changes and cleanup stops observation", async () => {
  const onChange = vi.fn();
  const stop = watchProjectNavigation(onChange, 100);
  document.title = "Renamed Project - Google Apps Script";
  await vi.runAllTicks();
  expect(onChange).toHaveBeenCalled();

  stop();
  onChange.mockClear();
  window.history.pushState({}, "", "/home/projects/project-three/edit");
  vi.advanceTimersByTime(100);
  expect(onChange).not.toHaveBeenCalled();
});
