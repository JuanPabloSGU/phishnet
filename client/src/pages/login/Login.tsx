import "@mantine/core/styles.css";
import { Authentication } from "./components/Authentication";
import { HeaderSimple } from "../../components/HeaderSimple";
import { Container } from "@mantine/core";
import { FooterSimple } from "../../components/FooterSimple";
import { createZitadelAuth, ZitadelConfig } from "@zitadel/react";
import { useEffect, useState } from "react";

function Login() {
  const config: ZitadelConfig = {
    authority: "https://zitadel.databending.ca",
    client_id: "287272511991840275",
  };

  const zitadel = createZitadelAuth(config);

  function login() {
    zitadel.authorize();
  }

  function signout() {
    zitadel.signout();
  }


  return (
    <>
      <HeaderSimple />
      <Container>
        <Authentication  />
      </Container>
      <FooterSimple />
    </>
  );
}

export default Login;
