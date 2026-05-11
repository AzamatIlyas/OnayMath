import { useEffect, useMemo, useState } from "react";
import { Crown, Trophy } from "lucide-react";

import { leaderboardApi } from "../api";
import type { LeaderboardEntry } from "../api";
import { getErrorMessage } from "../utils/errors";
import { BottomNav } from "./HomeDashboard";

interface LeaderboardProps {
  onNavigate: (page: string) => void;
}

export default function Leaderboard({ onNavigate }: LeaderboardProps) {
  const [scope, setScope] = useState<"class" | "school" | "city">("class");
  const [items, setItems] = useState<LeaderboardEntry[]>([]);
  const [currentUser, setCurrentUser] = useState<LeaderboardEntry | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await leaderboardApi.getLeaderboard({ scope, limit: 50 });
        if (!mounted) return;
        setItems(response.leaderboard);
        setCurrentUser(response.currentUser);
      } catch (err) {
        if (!mounted) return;
        setError(getErrorMessage(err, "Рейтингті жүктеу мүмкін болмады"));
      } finally {
        if (mounted) setIsLoading(false);
      }
    };

    void load();

    return () => {
      mounted = false;
    };
  }, [scope]);

  const topThree = useMemo(() => items.slice(0, 3), [items]);

  return (
    <div className="min-h-screen bg-background pb-20">
      <div className="bg-gradient-to-br from-[#6C3FE8] to-[#8B5CF6] text-white p-6 rounded-b-3xl shadow-lg">
        <div className="text-center mb-5">
          <Trophy className="w-10 h-10 mx-auto mb-2" />
          <h1 className="text-3xl" style={{ fontWeight: 800 }}>Көшбасшылар кестесі</h1>
        </div>

        <div className="flex gap-2 bg-white/10 rounded-2xl p-1">
          {(["class", "school", "city"] as const).map((key) => (
            <button
              key={key}
              onClick={() => setScope(key)}
              className={`flex-1 py-2 rounded-xl ${scope === key ? "bg-white text-primary" : "text-white"}`}
              style={{ fontWeight: 700 }}
            >
              {key === "class" ? "Сынып" : key === "school" ? "Мектеп" : "Қала"}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6 space-y-4">
        {error && <div className="rounded-2xl border border-red-300 bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>}

        {isLoading ? (
          <div className="text-sm text-muted-foreground">Жүктелуде...</div>
        ) : (
          <>
            {topThree.length > 0 && (
              <div className="bg-white rounded-3xl p-5 shadow-sm">
                <div className="text-center text-sm text-muted-foreground mb-3">Топ 3</div>
                <div className="space-y-2">
                  {topThree.map((entry, idx) => (
                    <div key={entry.user.id} className="flex items-center justify-between bg-muted/50 rounded-xl p-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center" style={{ fontWeight: 700 }}>
                          {entry.rank}
                        </div>
                        <div>
                          <div style={{ fontWeight: 700 }} className="flex items-center gap-2">
                            {idx === 0 && <Crown className="w-4 h-4 text-yellow-500" />}
                            {entry.user.name}
                          </div>
                          <div className="text-xs text-muted-foreground">{entry.user.school?.name ?? "Мектеп"}</div>
                        </div>
                      </div>
                      <div style={{ fontWeight: 700 }}>{entry.xp} XP</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="bg-white rounded-3xl p-5 shadow-sm">
              <h2 className="text-lg mb-3" style={{ fontWeight: 700 }}>Барлық қатысушы</h2>
              <div className="space-y-2">
                {items.map((entry) => (
                  <div
                    key={entry.user.id}
                    className={`flex items-center justify-between p-3 rounded-xl ${currentUser?.user.id === entry.user.id ? "bg-primary/10 border border-primary" : "bg-muted/40"}`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center" style={{ fontWeight: 700 }}>{entry.rank}</div>
                      <div>
                        <div style={{ fontWeight: 700 }}>{entry.user.name}</div>
                        <div className="text-xs text-muted-foreground">{entry.user.city?.name ?? "Қала"}</div>
                      </div>
                    </div>
                    <div style={{ fontWeight: 700 }}>{entry.xp} XP</div>
                  </div>
                ))}
              </div>

              {currentUser && !items.some((item) => item.user.id === currentUser.user.id) && (
                <div className="mt-4 p-3 rounded-xl border border-primary bg-primary/5 text-sm">
                  Сіздің орныңыз: <span style={{ fontWeight: 700 }}>#{currentUser.rank}</span>, XP: <span style={{ fontWeight: 700 }}>{currentUser.xp}</span>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      <BottomNav currentPage="leaderboard" onNavigate={onNavigate} />
    </div>
  );
}
