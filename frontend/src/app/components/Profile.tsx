import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Award, BookOpen, Flame, LogOut, Trophy } from "lucide-react";

import { usersApi } from "../api";
import type { UserWithStats } from "../api/users";
import { useAuth } from "../state/auth";
import { getErrorMessage } from "../utils/errors";
import { BottomNav } from "./HomeDashboard";

interface ProfileProps {
  onNavigate: (page: string) => void;
  onLogout: () => void;
}

export default function Profile({ onNavigate, onLogout }: ProfileProps) {
  const { user, logout } = useAuth();

  const [profile, setProfile] = useState<UserWithStats | null>(user);
  const [achievements, setAchievements] = useState<Array<{ id: string; title: string; description: string; iconUrl: string | null; xpReward: number }>>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const [me, earned] = await Promise.all([usersApi.getMe(), usersApi.getMyAchievements({ limit: 30 })]);
        if (!mounted) return;
        setProfile(me);
        setAchievements(earned.data.map((item) => item.achievement));
      } catch (err) {
        if (!mounted) return;
        setError(getErrorMessage(err, "Профильді жүктеу мүмкін болмады"));
      } finally {
        if (mounted) setIsLoading(false);
      }
    };

    void load();

    return () => {
      mounted = false;
    };
  }, []);

  const handleLogout = async () => {
    await logout();
    onLogout();
  };

  return (
    <div className="min-h-screen bg-background pb-20">
      <div className="bg-gradient-to-br from-[#6C3FE8] to-[#8B5CF6] text-white p-6 pb-12 rounded-b-[2.5rem]">
        <div className="text-center">
          <div className="w-24 h-24 rounded-3xl bg-white/20 mx-auto flex items-center justify-center text-5xl mb-3">👤</div>
          <h1 className="text-2xl" style={{ fontWeight: 800 }}>{profile?.name ?? "Пайдаланушы"}</h1>
          <p className="opacity-90 mt-1">{profile?.email ?? "-"}</p>
          <p className="opacity-90 mt-1">{profile?.grade ?? "-"}-сынып</p>
        </div>
      </div>

      <div className="p-6 -mt-6 space-y-4">
        {error && <div className="rounded-2xl border border-red-300 bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>}

        {isLoading ? (
          <div className="text-sm text-muted-foreground">Жүктелуде...</div>
        ) : (
          <>
            <div className="bg-white rounded-3xl border border-border p-5">
              <h2 className="text-lg mb-3" style={{ fontWeight: 700 }}>Статистика</h2>
              <div className="grid grid-cols-2 gap-3">
                <StatCard label="XP" value={String(profile?.stats.xpTotal ?? 0)} icon={<Trophy className="w-5 h-5 text-yellow-500" />} />
                <StatCard label="Серия" value={String(profile?.stats.streakDays ?? 0)} icon={<Flame className="w-5 h-5 text-orange-500" />} />
                <StatCard label="Сабақ" value={String(profile?.stats.lessonsDone ?? 0)} icon={<BookOpen className="w-5 h-5 text-blue-500" />} />
                <StatCard label="Квиз" value={String(profile?.stats.testsPassed ?? 0)} icon={<Award className="w-5 h-5 text-green-600" />} />
              </div>
            </div>

            <div className="bg-white rounded-3xl border border-border p-5">
              <h2 className="text-lg mb-3" style={{ fontWeight: 700 }}>Жетістіктер</h2>
              {achievements.length === 0 ? (
                <div className="text-sm text-muted-foreground">Әзірге жетістік жоқ</div>
              ) : (
                <div className="space-y-2">
                  {achievements.map((item) => (
                    <div key={item.id} className="p-3 rounded-xl bg-muted/40">
                      <div style={{ fontWeight: 700 }}>{item.title}</div>
                      <div className="text-sm text-muted-foreground">{item.description}</div>
                      <div className="text-xs text-muted-foreground mt-1">+{item.xpReward} XP</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button
              onClick={() => void handleLogout()}
              className="w-full bg-white border border-border rounded-2xl py-3 flex items-center justify-center gap-2 text-red-600"
              style={{ fontWeight: 700 }}
            >
              <LogOut className="w-4 h-4" />
              Шығу
            </button>
          </>
        )}
      </div>

      <BottomNav currentPage="profile" onNavigate={onNavigate} />
    </div>
  );
}

function StatCard({ label, value, icon }: { label: string; value: string; icon: ReactNode }) {
  return (
    <div className="bg-muted/40 rounded-2xl p-4">
      <div className="mb-2">{icon}</div>
      <div className="text-xl" style={{ fontWeight: 800 }}>{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}
