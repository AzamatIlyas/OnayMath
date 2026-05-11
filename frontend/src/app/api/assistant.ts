import { apiRequest, apiConfig, ApiError } from "./http";
import type { ChatMessage } from "./types";

export interface ConversationItem {
  role: "user" | "assistant";
  content: string;
}

interface StreamParams {
  message: string;
  topicId?: string;
  conversationHistory: ConversationItem[];
  accessToken: string;
  onChunk: (chunk: string) => void;
  onError?: (message: string) => void;
}

const parseSseBuffer = (buffer: string) => {
  const events = buffer.split("\n\n");
  return {
    events: events.slice(0, -1),
    rest: events[events.length - 1] ?? "",
  };
};

const parseEventLine = (line: string) => {
  if (!line.startsWith("data:")) {
    return null;
  }

  const raw = line.replace(/^data:\s*/, "").trim();
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as { type: string; chunk?: string; error?: string };
  } catch {
    return null;
  }
};

export const assistantApi = {
  async streamChat(params: StreamParams) {
    const response = await fetch(`${apiConfig.baseUrl}/assistant/chat`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: `Bearer ${params.accessToken}`,
      },
      body: JSON.stringify({
        message: params.message,
        topicId: params.topicId,
        conversationHistory: params.conversationHistory,
      }),
    });

    if (!response.ok || !response.body) {
      throw new ApiError({
        status: response.status,
        code: "ASSISTANT_STREAM_ERROR",
        message: "Unable to stream assistant response",
      });
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const parsed = parseSseBuffer(buffer);
      buffer = parsed.rest;

      for (const event of parsed.events) {
        const lines = event.split("\n");
        for (const line of lines) {
          const item = parseEventLine(line);
          if (!item) {
            continue;
          }

          if (item.type === "chunk" && item.chunk) {
            params.onChunk(item.chunk);
          }

          if (item.type === "error") {
            params.onError?.(item.error ?? "Assistant error");
          }
        }
      }
    }
  },

  getHistory(limit = 50) {
    return apiRequest<{ data: ChatMessage[] }>(`/assistant/history?limit=${limit}`, {
      method: "GET",
    });
  },
};
