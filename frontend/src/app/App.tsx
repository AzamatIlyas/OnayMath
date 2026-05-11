import { useEffect, useState } from "react";

import AIAssistant from "./components/AIAssistant";
import Books from "./components/Books";
import HomeDashboard from "./components/HomeDashboard";
import Leaderboard from "./components/Leaderboard";
import LessonQuiz from "./components/LessonQuiz";
import Onboarding from "./components/Onboarding";
import Profile from "./components/Profile";
import TopicsPage from "./components/TopicsPage";
import { AuthProvider, useAuth } from "./state/auth";

type Page = "home" | "topics" | "lesson" | "leaderboard" | "books" | "ai" | "profile";

function AppShell() {
  const { isReady, isAuthenticated } = useAuth();

  const [currentPage, setCurrentPage] = useState<Page>("home");
  const [selectedLessonId, setSelectedLessonId] = useState<string | null>(null);
  const [selectedTopicId, setSelectedTopicId] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      setCurrentPage("home");
      setSelectedLessonId(null);
      setSelectedTopicId(null);
    }
  }, [isAuthenticated]);

  if (!isReady) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="text-sm text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Onboarding onComplete={() => setCurrentPage("home")} />;
  }

  return (
    <div className="size-full bg-background overflow-auto">
      {currentPage === "home" && <HomeDashboard onNavigate={(page) => setCurrentPage(page as Page)} currentPage="home" />}

      {currentPage === "topics" && (
        <TopicsPage
          onNavigate={(page) => setCurrentPage(page as Page)}
          onStartLesson={(lessonId, topicId) => {
            setSelectedLessonId(lessonId);
            setSelectedTopicId(topicId);
            setCurrentPage("lesson");
          }}
        />
      )}

      {currentPage === "lesson" && selectedLessonId && (
        <LessonQuiz
          lessonId={selectedLessonId}
          onClose={() => setCurrentPage("topics")}
          onComplete={() => setCurrentPage("home")}
        />
      )}

      {currentPage === "leaderboard" && <Leaderboard onNavigate={(page) => setCurrentPage(page as Page)} />}
      {currentPage === "books" && <Books onNavigate={(page) => setCurrentPage(page as Page)} />}
      {currentPage === "ai" && <AIAssistant onNavigate={(page) => setCurrentPage(page as Page)} topicId={selectedTopicId} />}
      {currentPage === "profile" && <Profile onNavigate={(page) => setCurrentPage(page as Page)} onLogout={() => setCurrentPage("home")} />}
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  );
}
