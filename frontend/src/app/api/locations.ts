import { apiRequest } from "./http";
import type { City, PaginatedResponse, School } from "./types";

export const locationsApi = {
  getCities(params?: { cursor?: string; limit?: number }) {
    const query = new URLSearchParams();
    if (params?.cursor) query.set("cursor", params.cursor);
    if (params?.limit) query.set("limit", String(params.limit));

    return apiRequest<PaginatedResponse<City>>(`/locations/cities${query.toString() ? `?${query.toString()}` : ""}`, {
      method: "GET",
      auth: false,
    });
  },

  getSchoolsByCity(cityId: string, params?: { cursor?: string; limit?: number }) {
    const query = new URLSearchParams();
    if (params?.cursor) query.set("cursor", params.cursor);
    if (params?.limit) query.set("limit", String(params.limit));

    return apiRequest<PaginatedResponse<School>>(
      `/locations/cities/${cityId}/schools${query.toString() ? `?${query.toString()}` : ""}`,
      {
        method: "GET",
        auth: false,
      },
    );
  },
};
