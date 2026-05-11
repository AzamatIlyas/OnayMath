import { ApiError } from "../api";

export const getErrorMessage = (error: unknown, fallback = "Қате орын алды") => {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallback;
};
