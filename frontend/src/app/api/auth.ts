import { apiRequest } from "./http";
import type { User } from "./types";

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
  cityId: string;
  schoolId: string;
  grade: number;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface AuthResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
}

export const authApi = {
  register(payload: RegisterPayload) {
    return apiRequest<AuthResponse>("/auth/register", {
      method: "POST",
      body: payload,
      auth: false,
    });
  },

  login(payload: LoginPayload) {
    return apiRequest<AuthResponse>("/auth/login", {
      method: "POST",
      body: payload,
      auth: false,
    });
  },

  refresh(refreshToken: string) {
    return apiRequest<{ accessToken: string }>("/auth/refresh", {
      method: "POST",
      body: { refreshToken },
      auth: false,
    });
  },

  logout(refreshToken: string) {
    return apiRequest<{ success: boolean }>("/auth/logout", {
      method: "POST",
      body: { refreshToken },
      auth: false,
    });
  },
};
