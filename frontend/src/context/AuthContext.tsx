import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import * as api from "../api/client";

interface AuthState {
  token: string | null;
  email: string | null;
  userId: number | null;
}

interface AuthContextValue extends AuthState {
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(() => {
    const token = localStorage.getItem("token");
    const email = localStorage.getItem("user_email");
    const userId = localStorage.getItem("user_id");
    return {
      token,
      email,
      userId: userId ? Number(userId) : null,
    };
  });

  const handleAuth = useCallback(
    (res: { access_token: string; email: string; user_id: number }) => {
      localStorage.setItem("token", res.access_token);
      localStorage.setItem("user_email", res.email);
      localStorage.setItem("user_id", String(res.user_id));
      setState({
        token: res.access_token,
        email: res.email,
        userId: res.user_id,
      });
    },
    []
  );

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await api.login(email, password);
      handleAuth(res);
    },
    [handleAuth]
  );

  const signup = useCallback(
    async (email: string, password: string, fullName: string) => {
      const res = await api.signup(email, password, fullName);
      handleAuth(res);
    },
    [handleAuth]
  );

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("user_email");
    localStorage.removeItem("user_id");
    setState({ token: null, email: null, userId: null });
  }, []);

  return (
    <AuthContext.Provider
      value={{ ...state, isAuthenticated: !!state.token, login, signup, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
