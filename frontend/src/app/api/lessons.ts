import { apiRequest } from "./http";
import type { Lesson } from "./types";

export const lessonsApi = {
  getLesson(lessonId: string) {
    return apiRequest<Lesson>(`/lessons/${lessonId}`, { method: "GET" });
  },

  completeLesson(lessonId: string) {
    return apiRequest<{ success: boolean; xpEarned: number }>(`/lessons/${lessonId}/complete`, {
      method: "POST",
    });
  },
};
