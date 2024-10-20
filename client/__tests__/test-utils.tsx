import React, { ReactElement } from "react";
import { render, RenderOptions } from "@testing-library/react";
import { BrowserRouter, MemoryRouter, Router, RouterProvider } from "react-router-dom";
import { MantineProvider } from "@mantine/core";
import { AuthProvider } from "../src/context/Auth";
import { createMemoryHistory } from "history";

const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const history = createMemoryHistory();

  return (
    <MantineProvider>
      <AuthProvider>
        <BrowserRouter>
          {children}
        </BrowserRouter>
      </AuthProvider>
    </MantineProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, "wrapper">,
) => render(ui, { wrapper: AllTheProviders, ...options });

export * from "@testing-library/react";
export { customRender as render };
