import React from "react";
import { act, fireEvent, render, screen } from "@tests/test-utils.tsx";
import "@testing-library/jest-dom";
import Login from "./index";

test("loads and displays greeting", async () => {
  render(<Login />);

  fireEvent.click(screen.getByText("Login Now"));

  act(() => {

  })

});
