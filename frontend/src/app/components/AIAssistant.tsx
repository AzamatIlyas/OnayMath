import { useEffect, useMemo, useRef, useState } from "react";
import { Send, Sparkles } from "lucide-react";

import { assistantApi, tokenStorage } from "../api";
import { getErrorMessage } from "../utils/errors";
import { BottomNav } from "./HomeDashboard";

interface AIAssistantProps {
  onNavigate: (page: string) => void;
  topicId?: string | null;
}

interface UiMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
}

export default function AIAssistant({ onNavigate, topicId }: AIAssistantProps) {
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let mounted = true;

    const loadHistory = async () => {
      setIsLoadingHistory(true);
      setError(null);

      try {
        const response = await assistantApi.getHistory(50);
        if (!mounted) return;

        const history = [...response.data]
          .reverse()
          .map((item) => ({
            id: item.id,
            role: item.role === "USER" ? "user" : "assistant",
            content: item.content,
            createdAt: item.createdAt,
          }));

        setMessages(history);
      } catch (err) {
        if (!mounted) return;
        setError(getErrorMessage(err, "Чат тарихын жүктеу мүмкін болмады"));
      } finally {
        if (mounted) setIsLoadingHistory(false);
      }
    };

    void loadHistory();

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  const conversationHistory = useMemo(
    () =>
      messages.slice(-20).map((message) => ({
        role: message.role,
        content: message.content,
      })),
    [messages],
  );

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || isStreaming) return;

    const accessToken = tokenStorage.getAccessToken();
    if (!accessToken) {
      setError("Сессия аяқталды. Қайта кіріңіз.");
      return;
    }

    setError(null);

    const userMessage: UiMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      createdAt: new Date().toISOString(),
    };

    const assistantMessageId = crypto.randomUUID();
    const assistantMessage: UiMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      createdAt: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setInput("");
    setIsStreaming(true);

    try {
      await assistantApi.streamChat({
        message: text,
        topicId: topicId ?? undefined,
        conversationHistory,
        accessToken,
        onChunk: (chunk) => {
          setMessages((prev) =>
            prev.map((item) =>
              item.id === assistantMessageId ? { ...item, content: `${item.content}${chunk}` } : item,
            ),
          );
        },
        onError: (streamError) => {
          setError(streamError);
        },
      });
    } catch (err) {
      setError(getErrorMessage(err, "Ассистент жауабын алу мүмкін болмады"));
      setMessages((prev) => prev.filter((item) => item.id !== assistantMessageId));
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col pb-20">
      <div className="bg-gradient-to-br from-[#6C3FE8] to-[#8B5CF6] text-white p-6 shadow-lg">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center text-2xl">🤖</div>
          <div className="flex-1">
            <h1 className="text-2xl" style={{ fontWeight: 800 }}>OnayBot</h1>
            <p className="text-sm opacity-90">Математика бойынша AI-көмекші</p>
          </div>
          <Sparkles className="w-5 h-5" />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {error && <div className="rounded-2xl border border-red-300 bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>}

        {isLoadingHistory ? (
          <div className="text-sm text-muted-foreground">Тарих жүктелуде...</div>
        ) : messages.length === 0 ? (
          <div className="bg-white border border-border rounded-2xl p-4 text-sm text-muted-foreground">
            Сұрақ қойыңыз, мен тақырыпты қадамдап түсіндіріп беремін.
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] rounded-2xl p-4 ${message.role === "user" ? "bg-primary text-white" : "bg-white border border-border"}`}>
                <div className="whitespace-pre-wrap">{message.content || (isStreaming ? "..." : "")}</div>
                <div className={`text-xs mt-2 ${message.role === "user" ? "text-white/70" : "text-muted-foreground"}`}>
                  {new Date(message.createdAt).toLocaleTimeString("kk-KZ", { hour: "2-digit", minute: "2-digit" })}
                </div>
              </div>
            </div>
          ))
        )}

        <div ref={endRef} />
      </div>

      <div className="p-4 bg-white border-t border-border">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                void sendMessage();
              }
            }}
            placeholder="Сұрағыңызды жазыңыз..."
            className="flex-1 px-4 py-3 border border-border rounded-2xl focus:outline-none focus:border-primary"
          />
          <button
            onClick={() => void sendMessage()}
            disabled={!input.trim() || isStreaming}
            className="px-4 py-3 bg-primary text-white rounded-2xl disabled:opacity-50"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>

      <BottomNav currentPage="ai" onNavigate={onNavigate} />
    </div>
  );
}
