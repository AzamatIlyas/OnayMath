import { apiRequest } from "./http";
import type { LeaderboardResponse } from "./types";

export const leaderboardApi = {
  getLeaderboard(params?: { scope?: "class" | "school" | "city"; limit?: number }) {
    const query = new URLSearchParams();
    if (params?.scope) query.set("scope", params.scope);
    if (params?.limit) query.set("limit", String(params.limit));

    return apiRequest<LeaderboardResponse>(`/leaderboard/${query.toString() ? `?${query.toString()}` : ""}`, {
      method: "GET",
    });
  },
};
