import React from "react";
import ReactDOM from "react-dom/client";
import "@mantine/core/styles.css";

import {
  Container,
  createTheme,
  MantineColorsTuple,
  MantineProvider,
} from "@mantine/core";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Contact from "./pages/Contact";
import About from "./pages/About";
import Login from "./pages/Login";
import Callback from "./pages/Login/Callback";
import { AuthProvider } from "./context/Auth";
import Header from "@layout/Header";
import Footer from "@layout/Footer";
import Home from "@pages/Home";

const colours: MantineColorsTuple = [
  "#f3edff",
  "#e0d7fa",
  "#beabf0",
  "#9a7ce6",
  "#7c56de",
  "#683dd9",
  "#5f2fd8",
  "#4f23c0",
  "#451eac",
  "#3a1899",
];

const theme = createTheme({
  colors: {
    colours,
  },
});

const router = [
  {
    path: "/",
    element: <Home />,
  },
  {
    path: "/contact",
    element: <Contact />,
  },
  {
    path: "/about",
    element: <About />,
  },
  {
    path: "/login",
    element: <Login />,
  },
  {
    path: "/login/callback",
    element: <Callback />,
  },
];

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <MantineProvider theme={theme}>
      <BrowserRouter>
        <AuthProvider>
          <>
            <Header />
            <Container>
              <Routes>
                {router.map((route) => (
                  <Route
                    key={route.path}
                    path={route.path}
                    element={route.element}
                  />
                ))}
              </Routes>
            </Container>
            <Footer />
          </>
        </AuthProvider>
      </BrowserRouter>
    </MantineProvider>
  </React.StrictMode>,
);
