export type UserRole = "STUDENT" | "TEACHER" | "ADMIN";

export interface ApiErrorPayload {
  error: string;
  code: string;
  details?: unknown;
}

export interface City {
  id: string;
  name: string;
  region: string;
}

export interface School {
  id: string;
  name: string;
  cityId: string;
  address: string | null;
}

export interface User {
  id: string;
  email: string;
  name: string;
  avatarUrl: string | null;
  cityId: string | null;
  schoolId: string | null;
  grade: number;
  xpTotal: number;
  streakDays: number;
  lastActiveAt: string | null;
  role: UserRole;
  emailVerified?: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export interface TopicSummary {
  id: string;
  title: string;
  description: string | null;
  grade: number;
  order: number;
  iconUrl: string | null;
  isPublished: boolean;
  progressPercent: number;
  completedLessons: number;
  totalLessons: number;
}

export interface TopicLesson {
  id: string;
  title: string;
  order: number;
  durationMinutes: number;
  progress: {
    status: "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED";
    score: number;
    xpEarned: number;
    completedAt: string | null;
  };
}

export interface TopicDetail {
  id: string;
  title: string;
  description: string | null;
  grade: number;
  order: number;
  iconUrl: string | null;
  isPublished: boolean;
  progressPercent: number;
  lessons: TopicLesson[];
}

export interface Lesson {
  id: string;
  topicId: string;
  title: string;
  content: unknown;
  order: number;
  durationMinutes: number;
  progress: {
    status: "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED";
    score: number;
    xpEarned: number;
    completedAt: string | null;
  };
}

export interface QuizQuestion {
  id: string;
  text: string;
  options: string[];
}

export interface QuizSubmitResult {
  score: number;
  maxScore: number;
  xpEarned: number;
  stars: number;
  correctAnswers: Array<{
    questionId: string;
    selectedIndex: number;
    correctIndex: number;
    isCorrect: boolean;
    explanation: string;
  }>;
  explanations: Array<{
    questionId: string;
    explanation: string;
  }>;
}

export interface LeaderboardEntry {
  rank: number;
  xp: number;
  user: {
    id: string;
    name: string;
    avatarUrl: string | null;
    grade: number;
    xpTotal: number;
    school: {
      id: string;
      name: string;
    } | null;
    city: {
      id: string;
      name: string;
    } | null;
  };
}

export interface LeaderboardResponse {
  scope: "class" | "school" | "city";
  leaderboard: LeaderboardEntry[];
  currentUser: LeaderboardEntry | null;
}

export interface Book {
  id: string;
  title: string;
  grade: number;
  coverUrl: string | null;
  fileUrl: string;
  author: string | null;
  publishedYear: number | null;
  chapters: unknown;
  createdAt: string;
  updatedAt: string;
  signedFileUrl?: string;
}

export interface ChatMessage {
  id: string;
  role: "USER" | "ASSISTANT";
  content: string;
  topicContext: string | null;
  createdAt: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  nextCursor: string | null;
}
