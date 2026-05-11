import type { ApiErrorPayload } from "./types";

const DEFAULT_BASE_URL = "https://onaymath.onrender.com/api";

const ACCESS_TOKEN_KEY = "onaymath_access_token";
const REFRESH_TOKEN_KEY = "onaymath_refresh_token";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() || DEFAULT_BASE_URL;

export class ApiError extends Error {
  public readonly status: number;
  public readonly code: string;
  public readonly details?: unknown;

  constructor(payload: { status: number; message: string; code: string; details?: unknown }) {
    super(payload.message);
    this.name = "ApiError";
    this.status = payload.status;
    this.code = payload.code;
    this.details = payload.details;
  }
}

export const tokenStorage = {
  getAccessToken() {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },
  getRefreshToken() {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },
  setTokens(tokens: { accessToken: string; refreshToken: string }) {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken);
  },
  setAccessToken(accessToken: string) {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  },
  clear() {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  auth?: boolean;
  retry?: boolean;
}

const parseJsonSafely = async (response: Response) => {
  const text = await response.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text) as unknown;
  } catch {
    return null;
  }
};

const doRefresh = async () => {
  const refreshToken = tokenStorage.getRefreshToken();
  if (!refreshToken) {
    return null;
  }

  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ refreshToken }),
  });

  if (!response.ok) {
    tokenStorage.clear();
    return null;
  }

  const data = (await response.json()) as { accessToken: string };
  tokenStorage.setAccessToken(data.accessToken);
  return data.accessToken;
};

export const apiRequest = async <T>(path: string, options: RequestOptions = {}): Promise<T> => {
  const { body, headers, auth = true, retry = true, ...rest } = options;
  const token = tokenStorage.getAccessToken();

  const requestHeaders = new Headers(headers);
  if (!requestHeaders.has("content-type") && body !== undefined) {
    requestHeaders.set("content-type", "application/json");
  }

  if (auth && token) {
    requestHeaders.set("authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: requestHeaders,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (response.status === 401 && auth && retry) {
    const refreshed = await doRefresh();
    if (refreshed) {
      return apiRequest<T>(path, { ...options, retry: false });
    }
  }

  if (!response.ok) {
    const maybePayload = (await parseJsonSafely(response)) as ApiErrorPayload | null;

    throw new ApiError({
      status: response.status,
      code: maybePayload?.code ?? "HTTP_ERROR",
      message: maybePayload?.error ?? `Request failed with status ${response.status}`,
      details: maybePayload?.details,
    });
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
};

export const apiConfig = {
  baseUrl: API_BASE_URL,
};
