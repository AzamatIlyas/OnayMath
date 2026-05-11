import { useEffect, useMemo, useState } from "react";
import { BookOpen, Download, FileText } from "lucide-react";

import { booksApi } from "../api";
import type { Book } from "../api";
import { useAuth } from "../state/auth";
import { getErrorMessage } from "../utils/errors";
import { BottomNav } from "./HomeDashboard";

interface BooksProps {
  onNavigate: (page: string) => void;
}

export default function Books({ onNavigate }: BooksProps) {
  const { user } = useAuth();

  const [books, setBooks] = useState<Book[]>([]);
  const [selectedGrade, setSelectedGrade] = useState<number | null>(user?.grade ?? null);
  const [selectedBook, setSelectedBook] = useState<(Book & { signedFileUrl?: string }) | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isBookLoading, setIsBookLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const loadBooks = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await booksApi.getBooks({ limit: 100 });
        if (!mounted) return;
        setBooks(response.data);
      } catch (err) {
        if (!mounted) return;
        setError(getErrorMessage(err, "Кітаптарды жүктеу мүмкін болмады"));
      } finally {
        if (mounted) setIsLoading(false);
      }
    };

    void loadBooks();

    return () => {
      mounted = false;
    };
  }, []);

  const grades = useMemo(
    () => [...new Set(books.map((book) => book.grade))].sort((a, b) => a - b),
    [books],
  );

  const filteredBooks = useMemo(() => {
    if (!selectedGrade) return books;
    return books.filter((book) => book.grade === selectedGrade);
  }, [books, selectedGrade]);

  const openBook = async (book: Book) => {
    setError(null);
    setIsBookLoading(true);
    try {
      const detail = await booksApi.getBookById(book.id);
      setSelectedBook(detail);
    } catch (err) {
      setError(getErrorMessage(err, "Кітап мәліметін жүктеу мүмкін болмады"));
    } finally {
      setIsBookLoading(false);
    }
  };

  if (selectedBook) {
    const chapters = Array.isArray(selectedBook.chapters) ? selectedBook.chapters : [];

    return (
      <div className="min-h-screen bg-background pb-20">
        <div className="bg-white border-b border-border sticky top-0 z-10 p-4">
          <button onClick={() => setSelectedBook(null)} className="text-primary" style={{ fontWeight: 700 }}>
            ← Артқа
          </button>
        </div>

        <div className="p-6 space-y-4">
          {error && <div className="rounded-2xl border border-red-300 bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>}

          <div className="bg-white rounded-3xl border border-border p-5">
            <h1 className="text-2xl" style={{ fontWeight: 800 }}>{selectedBook.title}</h1>
            <p className="text-sm text-muted-foreground mt-1">{selectedBook.grade}-сынып</p>
            <p className="text-sm text-muted-foreground">{selectedBook.author ?? "Белгісіз автор"}</p>

            <div className="flex gap-3 mt-4">
              <button
                onClick={() => {
                  if (selectedBook.signedFileUrl) {
                    window.open(selectedBook.signedFileUrl, "_blank", "noopener,noreferrer");
                  }
                }}
                className="flex-1 bg-primary text-white py-3 rounded-2xl flex items-center justify-center gap-2"
                style={{ fontWeight: 700 }}
              >
                <BookOpen className="w-4 h-4" /> Ашу
              </button>
              <button
                onClick={() => {
                  if (selectedBook.signedFileUrl) {
                    window.open(selectedBook.signedFileUrl, "_blank", "noopener,noreferrer");
                  }
                }}
                className="px-4 py-3 rounded-2xl border border-border bg-white"
              >
                <Download className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="bg-white rounded-3xl border border-border p-5">
            <h2 className="text-lg mb-3" style={{ fontWeight: 700 }}>Мазмұны</h2>
            {chapters.length === 0 ? (
              <div className="text-sm text-muted-foreground">Тараулар тізімі жоқ</div>
            ) : (
              <div className="space-y-2">
                {chapters.map((chapter, index) => (
                  <div key={index} className="p-3 rounded-xl bg-muted/40 flex items-center gap-2">
                    <FileText className="w-4 h-4 text-muted-foreground" />
                    <span>{String(chapter)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <BottomNav currentPage="books" onNavigate={onNavigate} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-20">
      <div className="bg-gradient-to-br from-[#6C3FE8] to-[#8B5CF6] text-white p-6 rounded-b-3xl shadow-lg">
        <h1 className="text-3xl" style={{ fontWeight: 800 }}>Оқулықтар</h1>
        <p className="opacity-90 mt-1">Сыныптар бойынша материалдар</p>

        <div className="flex gap-2 overflow-x-auto mt-4">
          <button
            onClick={() => setSelectedGrade(null)}
            className={`px-4 py-2 rounded-xl whitespace-nowrap ${selectedGrade === null ? "bg-white text-primary" : "bg-white/20 text-white"}`}
            style={{ fontWeight: 700 }}
          >
            Барлық сынып
          </button>
          {grades.map((grade) => (
            <button
              key={grade}
              onClick={() => setSelectedGrade(grade)}
              className={`px-4 py-2 rounded-xl whitespace-nowrap ${selectedGrade === grade ? "bg-white text-primary" : "bg-white/20 text-white"}`}
              style={{ fontWeight: 700 }}
            >
              {grade}-сынып
            </button>
          ))}
        </div>
      </div>

      <div className="p-6 space-y-4">
        {error && <div className="rounded-2xl border border-red-300 bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>}

        {isLoading ? (
          <div className="text-sm text-muted-foreground">Жүктелуде...</div>
        ) : filteredBooks.length === 0 ? (
          <div className="text-sm text-muted-foreground">Кітаптар табылмады</div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            {filteredBooks.map((book) => (
              <button
                key={book.id}
                onClick={() => void openBook(book)}
                className="bg-white rounded-3xl border border-border p-4 text-left hover:border-primary transition-all"
              >
                <div className="h-36 bg-muted rounded-2xl mb-3 flex items-center justify-center text-5xl">📘</div>
                <div style={{ fontWeight: 700 }}>{book.title}</div>
                <div className="text-sm text-muted-foreground">{book.grade}-сынып</div>
                <div className="text-xs text-muted-foreground mt-1">{book.author ?? "Белгісіз"}</div>
              </button>
            ))}
          </div>
        )}

        {isBookLoading && <div className="text-sm text-muted-foreground">Кітап жүктелуде...</div>}
      </div>

      <BottomNav currentPage="books" onNavigate={onNavigate} />
    </div>
  );
}
