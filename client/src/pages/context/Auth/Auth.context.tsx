import { createContext } from "react";

import { TAuth } from "./Auth.types";

const AuthContext: React.Context<TAuth> = createContext<TAuth>({
});

export default AuthContext;
