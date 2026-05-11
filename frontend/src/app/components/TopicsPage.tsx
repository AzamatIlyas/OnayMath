import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, ChevronDown, ChevronUp, Play } from "lucide-react";

import { topicsApi } from "../api";
import type { TopicDetail, TopicSummary } from "../api";
import { useAuth } from "../state/auth";
import { getErrorMessage } from "../utils/errors";
import { BottomNav } from "./HomeDashboard";

interface TopicsPageProps {
  onNavigate: (page: string) => void;
  onStartLesson: (lessonId: string, topicId: string) => void;
}

export default function TopicsPage({ onNavigate, onStartLesson }: TopicsPageProps) {
  const { user } = useAuth();

  const [filter, setFilter] = useState<"all" | "in-progress" | "completed">("all");
  const [topics, setTopics] = useState<TopicSummary[]>([]);
  const [topicDetails, setTopicDetails] = useState<Record<string, TopicDetail>>({});
  const [expandedTopicId, setExpandedTopicId] = useState<string | null>(null);
  const [loadingTopicId, setLoadingTopicId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const loadTopics = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await topicsApi.getTopics({ grade: user?.grade, limit: 50 });
        if (!mounted) return;
        setTopics(response.data);
      } catch (err) {
        if (!mounted) return;
        setError(getErrorMessage(err, "Тақырыптарды жүктеу мүмкін болмады"));
      } finally {
        if (mounted) setIsLoading(false);
      }
    };

    void loadTopics();

    return () => {
      mounted = false;
    };
  }, [user?.grade]);

  const filteredTopics = useMemo(() => {
    return topics.filter((topic) => {
      if (filter === "all") return true;
      if (filter === "in-progress") return topic.progressPercent > 0 && topic.progressPercent < 100;
      if (filter === "completed") return topic.progressPercent === 100;
      return true;
    });
  }, [topics, filter]);

  const handleToggleTopic = async (topicId: string) => {
    if (expandedTopicId === topicId) {
      setExpandedTopicId(null);
      return;
    }

    setExpandedTopicId(topicId);

    if (topicDetails[topicId]) {
      return;
    }

    setLoadingTopicId(topicId);
    try {
      const detail = await topicsApi.getTopicById(topicId);
      setTopicDetails((prev) => ({ ...prev, [topicId]: detail }));
    } catch (err) {
      setError(getErrorMessage(err, "Тақырып сабақтарын жүктеу мүмкін болмады"));
    } finally {
      setLoadingTopicId(null);
    }
  };

  return (
    <div className="min-h-screen bg-background pb-20">
      <div className="bg-white border-b border-border sticky top-0 z-10">
        <div className="p-6">
          <h1 className="text-2xl mb-2" style={{ fontWeight: 800 }}>Математика тақырыптары</h1>
          <p className="text-sm text-muted-foreground">{user?.grade ?? "-"}-сынып, оқу бағдарламасы</p>

          <div className="flex gap-2 mt-4">
            <button
              onClick={() => setFilter("all")}
              className={`px-4 py-2 rounded-xl transition-all ${filter === "all" ? "bg-primary text-white" : "bg-muted text-muted-foreground"}`}
              style={{ fontWeight: 700 }}
            >
              Барлығы
            </button>
            <button
              onClick={() => setFilter("in-progress")}
              className={`px-4 py-2 rounded-xl transition-all ${filter === "in-progress" ? "bg-primary text-white" : "bg-muted text-muted-foreground"}`}
              style={{ fontWeight: 700 }}
            >
              Орындалып жатыр
            </button>
            <button
              onClick={() => setFilter("completed")}
              className={`px-4 py-2 rounded-xl transition-all ${filter === "completed" ? "bg-primary text-white" : "bg-muted text-muted-foreground"}`}
              style={{ fontWeight: 700 }}
            >
              Аяқталған
            </button>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-4">
        {error && <div className="rounded-2xl border border-red-300 bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>}

        {isLoading ? (
          <div className="text-sm text-muted-foreground">Жүктелуде...</div>
        ) : filteredTopics.length === 0 ? (
          <div className="text-sm text-muted-foreground">Тақырыптар табылмады</div>
        ) : (
          filteredTopics.map((topic) => {
            const isExpanded = expandedTopicId === topic.id;
            const detail = topicDetails[topic.id];

            return (
              <div key={topic.id} className="bg-white rounded-3xl shadow-sm border border-border">
                <button className="w-full p-5 flex items-center gap-4" onClick={() => void handleToggleTopic(topic.id)}>
                  <div className="flex-1 text-left">
                    <div className="flex items-center justify-between">
                      <h3 style={{ fontWeight: 800 }}>{topic.title}</h3>
                      <span className="text-sm text-muted-foreground">{topic.progressPercent}%</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden mt-2">
                      <div className="h-full bg-primary rounded-full" style={{ width: `${topic.progressPercent}%` }} />
                    </div>
                    <div className="text-xs text-muted-foreground mt-2">
                      {topic.completedLessons}/{topic.totalLessons} сабақ
                    </div>
                  </div>

                  {isExpanded ? <ChevronUp className="w-5 h-5 text-muted-foreground" /> : <ChevronDown className="w-5 h-5 text-muted-foreground" />}
                </button>

                {isExpanded && (
                  <div className="border-t border-border px-5 py-4 space-y-2">
                    {loadingTopicId === topic.id && <div className="text-sm text-muted-foreground">Сабақтар жүктелуде...</div>}

                    {detail?.lessons.map((lesson) => (
                      <button
                        key={lesson.id}
                        onClick={() => onStartLesson(lesson.id, topic.id)}
                        className="w-full flex items-center gap-3 p-3 bg-muted/50 hover:bg-muted rounded-2xl"
                      >
                        {lesson.progress.status === "COMPLETED" ? (
                          <CheckCircle2 className="w-5 h-5 text-green-600" />
                        ) : (
                          <Play className="w-5 h-5 text-primary" />
                        )}
                        <div className="flex-1 text-left">
                          <div style={{ fontWeight: 700 }}>{lesson.title}</div>
                          <div className="text-xs text-muted-foreground">{lesson.durationMinutes} мин</div>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      <BottomNav currentPage="topics" onNavigate={onNavigate} />
    </div>
  );
}
