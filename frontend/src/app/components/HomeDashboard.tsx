import { useEffect, useMemo, useState } from "react";
import { BookOpen, Home, Library, MessageCircle, Trophy, User, Flame, ChevronRight } from "lucide-react";

import { leaderboardApi, topicsApi } from "../api";
import type { LeaderboardEntry, TopicSummary } from "../api";
import { useAuth } from "../state/auth";
import { getErrorMessage } from "../utils/errors";

interface HomeDashboardProps {
  onNavigate: (page: string) => void;
  currentPage: string;
}

export default function HomeDashboard({ onNavigate, currentPage }: HomeDashboardProps) {
  const { user } = useAuth();

  const [topics, setTopics] = useState<TopicSummary[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const loadDashboard = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [topicsResponse, leaderboardResponse] = await Promise.all([
          topicsApi.getTopics({ grade: user?.grade, limit: 6 }),
          leaderboardApi.getLeaderboard({ scope: "class", limit: 5 }),
        ]);

        if (!mounted) return;
        setTopics(topicsResponse.data);
        setLeaderboard(leaderboardResponse.leaderboard);
      } catch (err) {
        if (!mounted) return;
        setError(getErrorMessage(err, "Failed to load dashboard"));
      } finally {
        if (mounted) setIsLoading(false);
      }
    };

    void loadDashboard();

    return () => {
      mounted = false;
    };
  }, [user?.grade]);

  const totalCompleted = useMemo(
    () => topics.reduce((acc, topic) => acc + topic.completedLessons, 0),
    [topics],
  );

  const topThree = leaderboard.slice(0, 3);

  return (
    <div className="min-h-screen bg-background pb-20">
      <div className="bg-gradient-to-br from-[#6C3FE8] to-[#8B5CF6] text-white p-6 rounded-b-3xl shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="text-sm opacity-80">Привет,</div>
            <div className="text-xl" style={{ fontWeight: 800 }}>{user?.name ?? "ученик"}</div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-white/20 px-3 py-2 rounded-xl border border-white/30">
              <Flame className="w-5 h-5 text-[#FF6B35]" />
              <span style={{ fontWeight: 700 }}>{user?.streakDays ?? 0}</span>
            </div>
            <div className="flex items-center gap-2 bg-white/20 px-3 py-2 rounded-xl border border-white/30">
              <Trophy className="w-5 h-5 text-[#FFD700]" />
              <span style={{ fontWeight: 700 }}>{user?.xpTotal ?? 0} XP</span>
            </div>
          </div>
        </div>
        <p className="opacity-90 text-sm">Завершено уроков: {totalCompleted}</p>
      </div>

      <div className="p-6 space-y-6">
        {error && <div className="rounded-2xl border border-red-300 bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>}

        <div className="bg-white rounded-3xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl" style={{ fontWeight: 700 }}>Продолжить обучение</h2>
            <button onClick={() => onNavigate("topics")} className="text-primary flex items-center gap-1" style={{ fontWeight: 700 }}>
              Все темы <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {isLoading ? (
            <div className="text-sm text-muted-foreground">Загрузка...</div>
          ) : topics.length === 0 ? (
            <div className="text-sm text-muted-foreground">Темы не найдены</div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {topics.map((topic) => (
                <button
                  key={topic.id}
                  onClick={() => onNavigate("topics")}
                  className="border border-border rounded-2xl p-4 text-left hover:border-primary transition-all"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div style={{ fontWeight: 700 }}>{topic.title}</div>
                    <span className="text-xs text-muted-foreground">{topic.progressPercent}%</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div className="h-full bg-primary rounded-full" style={{ width: `${topic.progressPercent}%` }} />
                  </div>
                  <div className="text-xs text-muted-foreground mt-2">
                    {topic.completedLessons}/{topic.totalLessons} уроков
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white rounded-3xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl" style={{ fontWeight: 700 }}>Лидеры класса</h2>
            <button onClick={() => onNavigate("leaderboard")} className="text-primary flex items-center gap-1" style={{ fontWeight: 700 }}>
              Рейтинг <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {isLoading ? (
            <div className="text-sm text-muted-foreground">Загрузка...</div>
          ) : topThree.length === 0 ? (
            <div className="text-sm text-muted-foreground">Пока данных нет</div>
          ) : (
            <div className="space-y-2">
              {topThree.map((item) => (
                <div key={item.user.id} className="flex items-center justify-between bg-muted/50 rounded-xl p-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center" style={{ fontWeight: 700 }}>
                      {item.rank}
                    </div>
                    <div>
                      <div style={{ fontWeight: 700 }}>{item.user.name}</div>
                      <div className="text-xs text-muted-foreground">{item.user.school?.name ?? "School"}</div>
                    </div>
                  </div>
                  <div style={{ fontWeight: 700 }}>{item.xp} XP</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <BottomNav currentPage={currentPage} onNavigate={onNavigate} />
    </div>
  );
}

function BottomNav({ currentPage, onNavigate }: { currentPage: string; onNavigate: (page: string) => void }) {
  const navItems = [
    { id: "home", icon: Home, label: "Главная" },
    { id: "topics", icon: BookOpen, label: "Темы" },
    { id: "books", icon: Library, label: "Книги" },
    { id: "ai", icon: MessageCircle, label: "AI" },
    { id: "profile", icon: User, label: "Профиль" },
  ];

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-border">
      <div className="flex items-center justify-around py-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`flex flex-col items-center gap-1 py-2 px-4 rounded-xl transition-all ${isActive ? "text-primary" : "text-muted-foreground"}`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-xs" style={{ fontWeight: isActive ? 700 : 500 }}>{item.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export { BottomNav };
