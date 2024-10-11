import {
  ReactElement,
  ReactNode,
  useContext,
  useEffect,
  useState,
} from "react";
import { TAuth } from "./Auth.types";
import AuthContext from "./Auth.context";
import { createZitadelAuth, ZitadelConfig } from "@zitadel/react";
import { User } from "oidc-client-ts";

const useAuth: () => TAuth = () => useContext(AuthContext);

const AuthProvider: React.FC<{ children: ReactElement }> = (
  { children }: { children: ReactNode },
) => {

  const config: ZitadelConfig = {
    authority: "https://zitadel.databending.ca",
    client_id: "287272511991840275",
    redirect_uri: `${location.origin}/login/callback`,
    post_logout_redirect_uri: `${location.origin}/`,
  };

  const zitadel = createZitadelAuth(config);

  const [userInfo, setUserInfo] = useState<User | null>(null);
  const [authenticated, setAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    if (authenticated === null) {
      zitadel.userManager
        .signinRedirectCallback()
        .then((user: User) => {
          if (user) {
            setAuthenticated(true);
            setUserInfo(user);
          } else {
            setAuthenticated(false);
          }
        })
        .catch((error: any) => {
          setAuthenticated(false);
        });
    }
    if (authenticated === true && userInfo === null) {
      zitadel.userManager
        .getUser()
        .then((user) => {
          if (user) {
            setAuthenticated(true);
            setUserInfo(user);
          } else {
            setAuthenticated(false);
          }
        })
        .catch((error: any) => {
          setAuthenticated(false);
        });
    }
  }, [authenticated, zitadel.userManager, setAuthenticated]);

  useEffect(() => {
    zitadel.userManager.getUser().then((user) => {
      if (user) {
        setAuthenticated(true);
      } else {
        setAuthenticated(false);
      }
    });
  }, [zitadel]);
  return (
    <AuthContext.Provider
      value={{
        login: zitadel.authorize,
        signout: zitadel.signout,
        authenticated,
        userInfo,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export { AuthProvider, useAuth };
export default AuthContext;
