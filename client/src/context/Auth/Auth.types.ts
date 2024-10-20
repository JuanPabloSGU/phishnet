import { User } from "oidc-client-ts";

export type TAuth = {
  login(): Promise<void>;
  signout(): Promise<void>;
  authenticated: boolean | null;
  userInfo: User | null;
}
