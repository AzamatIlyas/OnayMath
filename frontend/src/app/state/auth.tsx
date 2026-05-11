import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { authApi, tokenStorage, usersApi } from "../api";
import type { LoginPayload, RegisterPayload } from "../api/auth";
import type { UserWithStats } from "../api/users";

interface AuthContextValue {
  user: UserWithStats | null;
  isReady: boolean;
  isAuthenticated: boolean;
  setUser: (user: UserWithStats | null) => void;
  refreshMe: () => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  login: (payload: LoginPayload) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserWithStats | null>(null);
  const [isReady, setIsReady] = useState(false);

  const refreshMe = useCallback(async () => {
    const me = await usersApi.getMe();
    setUser(me);
  }, []);

  const bootstrap = useCallback(async () => {
    const access = tokenStorage.getAccessToken();
    if (!access) {
      setUser(null);
      setIsReady(true);
      return;
    }

    try {
      await refreshMe();
    } catch {
      tokenStorage.clear();
      setUser(null);
    } finally {
      setIsReady(true);
    }
  }, [refreshMe]);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  const register = useCallback(
    async (payload: RegisterPayload) => {
      const response = await authApi.register(payload);
      tokenStorage.setTokens({
        accessToken: response.accessToken,
        refreshToken: response.refreshToken,
      });
      await refreshMe();
    },
    [refreshMe],
  );

  const login = useCallback(
    async (payload: LoginPayload) => {
      const response = await authApi.login(payload);
      tokenStorage.setTokens({
        accessToken: response.accessToken,
        refreshToken: response.refreshToken,
      });
      await refreshMe();
    },
    [refreshMe],
  );

  const logout = useCallback(async () => {
    const refreshToken = tokenStorage.getRefreshToken();

    try {
      if (refreshToken) {
        await authApi.logout(refreshToken);
      }
    } finally {
      tokenStorage.clear();
      setUser(null);
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isReady,
      isAuthenticated: Boolean(user),
      setUser,
      refreshMe,
      register,
      login,
      logout,
    }),
    [user, isReady, refreshMe, register, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
};
