import { ApiError } from "../api";

export const getErrorMessage = (error: unknown, fallback = "Something went wrong") => {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallback;
};
