import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { Navigation } from "./Navigation";

test("selects a navigation section", () => {
  const onSelect = vi.fn();
  render(<Navigation active="Project" onSelect={onSelect} />);
  fireEvent.click(screen.getByRole("button", { name: "Changes" }));
  expect(onSelect).toHaveBeenCalledWith("Changes");
});
