import { useEffect, useMemo, useState } from "react";
import { ChevronRight, Star, Trophy, X } from "lucide-react";

import { lessonsApi, quizzesApi } from "../api";
import type { Lesson, QuizQuestion, QuizSubmitResult } from "../api";
import { getErrorMessage } from "../utils/errors";

interface LessonQuizProps {
  lessonId: string;
  onComplete: () => void;
  onClose: () => void;
}

type Screen = "lesson" | "quiz" | "result";

type LessonTasks =
  | string[]
  | {
      basic?: string[];
      medium?: string[];
      advanced?: string[];
    };

type LessonContentView = {
  overview?: string;
  objectives: string[];
  theory?: string;
  algorithm: string[];
  formula?: string;
  example?: string;
  exampleSteps: string[];
  check?: string;
  mistakes: string[];
  tasks: LessonTasks;
  summary?: string;
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null;

const toStringArray = (value: unknown): string[] => {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
};

const toLessonContent = (content: unknown): LessonContentView => {
  if (!isRecord(content)) {
    return {
      objectives: [],
      algorithm: [],
      exampleSteps: [],
      mistakes: [],
      tasks: [],
    };
  }

  const tasksRaw = content.tasks;
  const tasks: LessonTasks =
    Array.isArray(tasksRaw) || !isRecord(tasksRaw)
      ? toStringArray(tasksRaw)
      : {
          basic: toStringArray(tasksRaw.basic),
          medium: toStringArray(tasksRaw.medium),
          advanced: toStringArray(tasksRaw.advanced),
        };

  return {
    overview: typeof content.overview === "string" ? content.overview : undefined,
    objectives: toStringArray(content.objectives),
    theory: typeof content.theory === "string" ? content.theory : undefined,
    algorithm: toStringArray(content.algorithm),
    formula: typeof content.formula === "string" ? content.formula : undefined,
    example: typeof content.example === "string" ? content.example : undefined,
    exampleSteps: toStringArray(content.exampleSteps),
    check: typeof content.check === "string" ? content.check : undefined,
    mistakes: toStringArray(content.commonMistakes ?? content.mistakes),
    tasks,
    summary: typeof content.summary === "string" ? content.summary : undefined,
  };
};

export default function LessonQuiz({ lessonId, onComplete, onClose }: LessonQuizProps) {
  const [screen, setScreen] = useState<Screen>("lesson");
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [answers, setAnswers] = useState<number[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [result, setResult] = useState<QuizSubmitResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const loadLesson = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await lessonsApi.getLesson(lessonId);
        if (!mounted) return;
        setLesson(response);
      } catch (err) {
        if (!mounted) return;
        setError(getErrorMessage(err, "Сабақты жүктеу мүмкін болмады"));
      } finally {
        if (mounted) setIsLoading(false);
      }
    };

    void loadLesson();

    return () => {
      mounted = false;
    };
  }, [lessonId]);

  const activeQuestion = questions[currentQuestion] ?? null;

  const selectedCount = useMemo(
    () => answers.filter((item) => typeof item === "number").length,
    [answers],
  );
  const lessonContent = useMemo(() => toLessonContent(lesson?.content), [lesson?.content]);

  const handleStartQuiz = async () => {
    setError(null);
    setIsLoading(true);

    try {
      await lessonsApi.completeLesson(lessonId);
      const response = await quizzesApi.getQuestions(lessonId);
      setQuestions(response.questions);
      setAnswers(new Array(response.questions.length).fill(-1));
      setCurrentQuestion(0);
      setScreen("quiz");
    } catch (err) {
      setError(getErrorMessage(err, "Квизді бастау мүмкін болмады"));
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnswerSelect = (optionIndex: number) => {
    setAnswers((prev) => {
      const next = [...prev];
      next[currentQuestion] = optionIndex;
      return next;
    });
  };

  const handleNextQuestion = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion((prev) => prev + 1);
    }
  };

  const handleSubmit = async () => {
    if (answers.some((answer) => answer < 0)) {
      setError("Барлық сұраққа жауап беріңіз");
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      const response = await quizzesApi.submit(lessonId, answers);
      setResult(response);
      setScreen("result");
    } catch (err) {
      setError(getErrorMessage(err, "Квиз нәтижесін жіберу мүмкін болмады"));
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading && !lesson) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="text-sm text-muted-foreground">Жүктелуде...</div>
      </div>
    );
  }

  if (screen === "lesson") {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <div className="bg-white border-b border-border p-4 flex items-center justify-between">
          <button onClick={onClose} className="p-2 rounded-xl hover:bg-muted"><X className="w-5 h-5" /></button>
          <h2 style={{ fontWeight: 700 }}>{lesson?.title ?? "Сабақ"}</h2>
          <div className="w-9" />
        </div>

        <div className="flex-1 p-6 space-y-4">
          {error && <div className="rounded-2xl border border-red-300 bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>}

          <div className="bg-white rounded-3xl border border-border p-5">
            <div className="text-sm text-muted-foreground mb-2">Ұзақтығы: {lesson?.durationMinutes ?? 0} мин</div>
            <h3 className="text-xl mb-3" style={{ fontWeight: 800 }}>{lesson?.title}</h3>
            <div className="space-y-4 text-sm text-foreground">
              {lessonContent.overview && (
                <section className="rounded-2xl bg-muted/40 p-4">
                  <h4 className="mb-2 font-semibold">Сабақ туралы</h4>
                  <p className="leading-relaxed text-muted-foreground">{lessonContent.overview}</p>
                </section>
              )}

              {lessonContent.objectives.length > 0 && (
                <section>
                  <h4 className="mb-2 font-semibold">Не үйренесіз</h4>
                  <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
                    {lessonContent.objectives.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </section>
              )}

              {lessonContent.theory && (
                <section>
                  <h4 className="mb-2 font-semibold">Теория</h4>
                  <p className="leading-relaxed text-muted-foreground whitespace-pre-wrap">{lessonContent.theory}</p>
                </section>
              )}

              {lessonContent.formula && (
                <section className="rounded-2xl border border-primary/20 bg-primary/5 p-4">
                  <h4 className="mb-1 font-semibold">Негізгі формула / ереже</h4>
                  <p className="font-mono text-[13px] leading-relaxed">{lessonContent.formula}</p>
                </section>
              )}

              {lessonContent.algorithm.length > 0 && (
                <section>
                  <h4 className="mb-2 font-semibold">Шешу алгоритмі</h4>
                  <ol className="list-decimal pl-5 space-y-1 text-muted-foreground">
                    {lessonContent.algorithm.map((step, index) => (
                      <li key={index}>{step}</li>
                    ))}
                  </ol>
                </section>
              )}

              {(lessonContent.example || lessonContent.exampleSteps.length > 0 || lessonContent.check) && (
                <section className="rounded-2xl border border-border p-4">
                  <h4 className="mb-2 font-semibold">Мысалды талдау</h4>
                  {lessonContent.example && <p className="mb-2 text-muted-foreground">{lessonContent.example}</p>}
                  {lessonContent.exampleSteps.length > 0 && (
                    <ol className="list-decimal pl-5 space-y-1 text-muted-foreground">
                      {lessonContent.exampleSteps.map((step, index) => (
                        <li key={index}>{step}</li>
                      ))}
                    </ol>
                  )}
                  {lessonContent.check && (
                    <p className="mt-2 text-muted-foreground">
                      <strong>Тексеру:</strong> {lessonContent.check}
                    </p>
                  )}
                </section>
              )}

              {lessonContent.mistakes.length > 0 && (
                <section>
                  <h4 className="mb-2 font-semibold">Жиі қателер</h4>
                  <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
                    {lessonContent.mistakes.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </section>
              )}

              {Array.isArray(lessonContent.tasks) ? (
                lessonContent.tasks.length > 0 && (
                  <section>
                    <h4 className="mb-2 font-semibold">Тапсырмалар</h4>
                    <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
                      {lessonContent.tasks.map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  </section>
                )
              ) : (
                <section>
                  <h4 className="mb-2 font-semibold">Тапсырмалар</h4>
                  <div className="space-y-3 text-muted-foreground">
                    {toStringArray(lessonContent.tasks.basic).length > 0 && (
                      <div>
                        <div className="font-medium text-foreground mb-1">Базалық деңгей</div>
                        <ul className="list-disc pl-5 space-y-1">
                          {toStringArray(lessonContent.tasks.basic).map((item, index) => (
                            <li key={index}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {toStringArray(lessonContent.tasks.medium).length > 0 && (
                      <div>
                        <div className="font-medium text-foreground mb-1">Орта деңгей</div>
                        <ul className="list-disc pl-5 space-y-1">
                          {toStringArray(lessonContent.tasks.medium).map((item, index) => (
                            <li key={index}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {toStringArray(lessonContent.tasks.advanced).length > 0 && (
                      <div>
                        <div className="font-medium text-foreground mb-1">Күрделі деңгей</div>
                        <ul className="list-disc pl-5 space-y-1">
                          {toStringArray(lessonContent.tasks.advanced).map((item, index) => (
                            <li key={index}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </section>
              )}

              {lessonContent.summary && (
                <section className="rounded-2xl bg-emerald-50 border border-emerald-100 p-4">
                  <h4 className="mb-1 font-semibold text-emerald-900">Қорытынды</h4>
                  <p className="text-emerald-900/80">{lessonContent.summary}</p>
                </section>
              )}
            </div>
          </div>
        </div>

        <div className="p-6 bg-white border-t border-border">
          <button
            onClick={() => void handleStartQuiz()}
            disabled={isLoading}
            className="w-full bg-primary text-white py-3 rounded-2xl flex items-center justify-center gap-2 disabled:opacity-50"
            style={{ fontWeight: 700 }}
          >
            {isLoading ? "Жүктелуде..." : "Квизді бастау"}
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    );
  }

  if (screen === "quiz" && activeQuestion) {
    const currentAnswer = answers[currentQuestion];

    return (
      <div className="min-h-screen bg-background flex flex-col">
        <div className="bg-white border-b border-border p-4">
          <div className="flex items-center justify-between mb-3">
            <button onClick={onClose} className="p-2 rounded-xl hover:bg-muted"><X className="w-5 h-5" /></button>
            <div className="text-sm text-muted-foreground">{currentQuestion + 1}/{questions.length}</div>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div className="h-full bg-primary rounded-full" style={{ width: `${((currentQuestion + 1) / questions.length) * 100}%` }} />
          </div>
        </div>

        <div className="flex-1 p-6 space-y-4">
          {error && <div className="rounded-2xl border border-red-300 bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>}

          <div className="bg-white rounded-3xl border border-border p-5">
            <div className="text-sm text-muted-foreground mb-2">Сұрақ {currentQuestion + 1}</div>
            <h3 className="text-xl" style={{ fontWeight: 800 }}>{activeQuestion.text}</h3>
          </div>

          <div className="space-y-2">
            {activeQuestion.options.map((option, idx) => (
              <button
                key={idx}
                onClick={() => handleAnswerSelect(idx)}
                className={`w-full p-4 rounded-2xl border text-left ${currentAnswer === idx ? "border-primary bg-primary/5" : "border-border bg-white"}`}
                style={{ fontWeight: 600 }}
              >
                {option}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6 bg-white border-t border-border">
          {currentQuestion < questions.length - 1 ? (
            <button
              onClick={handleNextQuestion}
              disabled={currentAnswer < 0}
              className="w-full bg-primary text-white py-3 rounded-2xl disabled:opacity-50"
              style={{ fontWeight: 700 }}
            >
              Келесі сұрақ
            </button>
          ) : (
            <button
              onClick={() => void handleSubmit()}
              disabled={selectedCount !== questions.length || isSubmitting}
              className="w-full bg-primary text-white py-3 rounded-2xl disabled:opacity-50"
              style={{ fontWeight: 700 }}
            >
              {isSubmitting ? "Тексерілуде..." : "Квизді аяқтау"}
            </button>
          )}
        </div>
      </div>
    );
  }

  const stars = result?.stars ?? 0;
  const passed = result?.passed ?? false;
  const passingScorePercent = result?.passingScorePercent ?? 60;

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#6C3FE8] to-[#8B5CF6] flex items-center justify-center p-6 text-white">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="w-24 h-24 bg-white/20 rounded-full mx-auto flex items-center justify-center">
          <Trophy className="w-12 h-12" />
        </div>

        <div>
          <h1 className="text-3xl" style={{ fontWeight: 800 }}>Квиз аяқталды</h1>
          <p className="opacity-90 mt-1">
            {passed ? "Жарайсың! Сабақ өтті." : `Өту үшін кемінде ${passingScorePercent}% керек. Қайта тапсырып көріңіз.`}
          </p>
        </div>

        <div className="bg-white/10 rounded-3xl p-5">
          <div className="flex justify-center gap-2 mb-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <Star key={index} className={`w-10 h-10 ${index < stars ? "fill-yellow-400 text-yellow-400" : "text-white/40"}`} />
            ))}
          </div>

          <div className="text-2xl" style={{ fontWeight: 800 }}>{result?.score ?? 0}/{result?.maxScore ?? 0}</div>
          <div className="text-sm opacity-90 mt-1">{result?.scorePercent ?? 0}%</div>
          <div className="text-lg mt-1">+{result?.xpEarned ?? 0} XP</div>
        </div>

        <button
          onClick={passed ? onComplete : () => void handleStartQuiz()}
          className="w-full bg-[#FF6B35] text-white py-3 rounded-2xl"
          style={{ fontWeight: 700 }}
        >
          {passed ? "Жалғастыру" : "Қайта тапсыру"}
        </button>
      </div>
    </div>
  );
}
