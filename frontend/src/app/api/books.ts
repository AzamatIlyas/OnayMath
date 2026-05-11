import { apiRequest } from "./http";
import type { Book, PaginatedResponse } from "./types";

export const booksApi = {
  getBooks(params?: { grade?: number; cursor?: string; limit?: number }) {
    const query = new URLSearchParams();
    if (params?.grade) query.set("grade", String(params.grade));
    if (params?.cursor) query.set("cursor", params.cursor);
    if (params?.limit) query.set("limit", String(params.limit));

    return apiRequest<PaginatedResponse<Book>>(`/books/${query.toString() ? `?${query.toString()}` : ""}`, {
      method: "GET",
    });
  },

  getBookById(bookId: string) {
    return apiRequest<Book & { signedFileUrl: string }>(`/books/${bookId}`, { method: "GET" });
  },
};
