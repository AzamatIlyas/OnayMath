import { apiRequest } from "./http";
import type { PaginatedResponse, User } from "./types";

export interface UserStats {
  xpTotal: number;
  streakDays: number;
  lessonsDone: number;
  testsPassed: number;
}

export interface UserWithStats extends User {
  city: {
    id: string;
    name: string;
    region: string;
  } | null;
  school: {
    id: string;
    name: string;
    address: string | null;
  } | null;
  stats: UserStats;
}

export const usersApi = {
  getMe() {
    return apiRequest<UserWithStats>("/users/me", { method: "GET" });
  },

  updateMe(payload: { name?: string; avatarUrl?: string; grade?: number }) {
    return apiRequest<User>("/users/me", {
      method: "PATCH",
      body: payload,
    });
  },

  getMyAchievements(params?: { cursor?: string; limit?: number }) {
    const query = new URLSearchParams();
    if (params?.cursor) query.set("cursor", params.cursor);
    if (params?.limit) query.set("limit", String(params.limit));

    return apiRequest<
      PaginatedResponse<{
        id: string;
        unlockedAt: string;
        achievement: {
          id: string;
          title: string;
          description: string;
          iconUrl: string | null;
          xpReward: number;
        };
      }>
    >(`/users/me/achievements${query.toString() ? `?${query.toString()}` : ""}`, {
      method: "GET",
    });
  },

  getMyStats() {
    return apiRequest<UserStats>("/users/me/stats", { method: "GET" });
  },
};
