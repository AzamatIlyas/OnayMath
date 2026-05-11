import { apiRequest } from "./http";
import type { QuizQuestion, QuizSubmitResult } from "./types";

export const quizzesApi = {
  getQuestions(lessonId: string) {
    return apiRequest<{ lessonId: string; questions: QuizQuestion[] }>(`/quizzes/${lessonId}/questions`, {
      method: "GET",
    });
  },

  submit(lessonId: string, answers: number[]) {
    return apiRequest<QuizSubmitResult>(`/quizzes/${lessonId}/submit`, {
      method: "POST",
      body: { answers },
    });
  },
};
