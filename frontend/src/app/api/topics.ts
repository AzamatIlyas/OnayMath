import { apiRequest } from "./http";
import type { PaginatedResponse, TopicDetail, TopicSummary } from "./types";

export const topicsApi = {
  getTopics(params?: { grade?: number; cursor?: string; limit?: number }) {
    const query = new URLSearchParams();
    if (params?.grade) query.set("grade", String(params.grade));
    if (params?.cursor) query.set("cursor", params.cursor);
    if (params?.limit) query.set("limit", String(params.limit));

    return apiRequest<PaginatedResponse<TopicSummary>>(`/topics/${query.toString() ? `?${query.toString()}` : ""}`, {
      method: "GET",
    });
  },

  getTopicById(topicId: string) {
    return apiRequest<TopicDetail>(`/topics/${topicId}`, { method: "GET" });
  },
};
