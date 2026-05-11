import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

import { locationsApi } from "../api";
import { useAuth } from "../state/auth";
import { getErrorMessage } from "../utils/errors";

interface OnboardingProps {
  onComplete: () => void;
}

type Mode = "register" | "login";

const grades = Array.from({ length: 11 }, (_, i) => i + 1);

export default function Onboarding({ onComplete }: OnboardingProps) {
  const { register, login } = useAuth();

  const [mode, setMode] = useState<Mode>("register");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [cities, setCities] = useState<Array<{ id: string; name: string; region: string }>>([]);
  const [schools, setSchools] = useState<Array<{ id: string; name: string }>>([]);
  const [isLocationsLoading, setIsLocationsLoading] = useState(false);

  const [registerForm, setRegisterForm] = useState({
    name: "",
    email: "",
    password: "",
    cityId: "",
    schoolId: "",
    grade: 7,
  });

  const [loginForm, setLoginForm] = useState({
    email: "",
    password: "",
  });

  useEffect(() => {
    let mounted = true;

    const loadCities = async () => {
      setIsLocationsLoading(true);
      try {
        const response = await locationsApi.getCities({ limit: 100 });
        if (!mounted) return;
        setCities(response.data);
      } catch (err) {
        if (!mounted) return;
        setError(getErrorMessage(err, "Failed to load cities"));
      } finally {
        if (mounted) setIsLocationsLoading(false);
      }
    };

    void loadCities();

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!registerForm.cityId) {
      setSchools([]);
      setRegisterForm((prev) => ({ ...prev, schoolId: "" }));
      return;
    }

    let mounted = true;

    const loadSchools = async () => {
      setIsLocationsLoading(true);
      try {
        const response = await locationsApi.getSchoolsByCity(registerForm.cityId, { limit: 100 });
        if (!mounted) return;
        setSchools(response.data.map((school) => ({ id: school.id, name: school.name })));
      } catch (err) {
        if (!mounted) return;
        setError(getErrorMessage(err, "Failed to load schools"));
      } finally {
        if (mounted) setIsLocationsLoading(false);
      }
    };

    void loadSchools();

    return () => {
      mounted = false;
    };
  }, [registerForm.cityId]);

  const canRegister = useMemo(() => {
    return (
      registerForm.name.trim().length >= 2
      && registerForm.email.trim().length > 4
      && registerForm.password.length >= 8
      && registerForm.cityId
      && registerForm.schoolId
      && registerForm.grade >= 1
      && registerForm.grade <= 11
    );
  }, [registerForm]);

  const canLogin = useMemo(() => {
    return loginForm.email.trim().length > 4 && loginForm.password.length >= 8;
  }, [loginForm]);

  const handleRegister = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!canRegister) {
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        name: registerForm.name.trim(),
        email: registerForm.email.trim(),
        password: registerForm.password,
        cityId: registerForm.cityId,
        schoolId: registerForm.schoolId,
        grade: registerForm.grade,
      });
      onComplete();
    } catch (err) {
      setError(getErrorMessage(err, "Registration failed"));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogin = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!canLogin) {
      return;
    }

    setIsSubmitting(true);
    try {
      await login({
        email: loginForm.email.trim(),
        password: loginForm.password,
      });
      onComplete();
    } catch (err) {
      setError(getErrorMessage(err, "Login failed"));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-lg bg-white rounded-3xl shadow-sm border border-border p-6 space-y-6">
        <div className="text-center">
          <div className="text-5xl mb-3">📐</div>
          <h1 className="text-3xl" style={{ fontWeight: 800 }}>OnayMath</h1>
          <p className="text-muted-foreground mt-1">Школьная математика 1-11 классы</p>
        </div>

        <div className="flex gap-2 bg-muted p-1 rounded-2xl">
          <button
            onClick={() => {
              setMode("register");
              setError(null);
            }}
            className={`flex-1 py-2 rounded-xl transition-all ${mode === "register" ? "bg-white shadow-sm" : ""}`}
            style={{ fontWeight: 700 }}
            type="button"
          >
            Регистрация
          </button>
          <button
            onClick={() => {
              setMode("login");
              setError(null);
            }}
            className={`flex-1 py-2 rounded-xl transition-all ${mode === "login" ? "bg-white shadow-sm" : ""}`}
            style={{ fontWeight: 700 }}
            type="button"
          >
            Вход
          </button>
        </div>

        {error && (
          <div className="rounded-2xl border border-red-300 bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>
        )}

        {mode === "register" ? (
          <form className="space-y-3" onSubmit={handleRegister}>
            <input
              value={registerForm.name}
              onChange={(event) => setRegisterForm((prev) => ({ ...prev, name: event.target.value }))}
              placeholder="Ваше имя"
              className="w-full px-4 py-3 border border-border rounded-xl focus:outline-none focus:border-primary"
            />
            <input
              value={registerForm.email}
              onChange={(event) => setRegisterForm((prev) => ({ ...prev, email: event.target.value }))}
              placeholder="Email"
              type="email"
              className="w-full px-4 py-3 border border-border rounded-xl focus:outline-none focus:border-primary"
            />
            <input
              value={registerForm.password}
              onChange={(event) => setRegisterForm((prev) => ({ ...prev, password: event.target.value }))}
              placeholder="Пароль (минимум 8 символов)"
              type="password"
              className="w-full px-4 py-3 border border-border rounded-xl focus:outline-none focus:border-primary"
            />

            <div className="grid grid-cols-2 gap-3">
              <select
                value={registerForm.cityId}
                onChange={(event) => setRegisterForm((prev) => ({ ...prev, cityId: event.target.value }))}
                className="w-full px-4 py-3 border border-border rounded-xl focus:outline-none focus:border-primary"
                disabled={isLocationsLoading}
              >
                <option value="">Выберите город</option>
                {cities.map((city) => (
                  <option key={city.id} value={city.id}>
                    {city.name}
                  </option>
                ))}
              </select>

              <select
                value={registerForm.schoolId}
                onChange={(event) => setRegisterForm((prev) => ({ ...prev, schoolId: event.target.value }))}
                className="w-full px-4 py-3 border border-border rounded-xl focus:outline-none focus:border-primary"
                disabled={!registerForm.cityId || isLocationsLoading}
              >
                <option value="">Выберите школу</option>
                {schools.map((school) => (
                  <option key={school.id} value={school.id}>
                    {school.name}
                  </option>
                ))}
              </select>
            </div>

            <select
              value={registerForm.grade}
              onChange={(event) => setRegisterForm((prev) => ({ ...prev, grade: Number(event.target.value) }))}
              className="w-full px-4 py-3 border border-border rounded-xl focus:outline-none focus:border-primary"
            >
              {grades.map((grade) => (
                <option key={grade} value={grade}>
                  {grade}-класс
                </option>
              ))}
            </select>

            <button
              type="submit"
              disabled={!canRegister || isSubmitting}
              className="w-full bg-primary text-white py-3 rounded-xl disabled:opacity-50"
              style={{ fontWeight: 700 }}
            >
              {isSubmitting ? "Регистрация..." : "Зарегистрироваться"}
            </button>
          </form>
        ) : (
          <form className="space-y-3" onSubmit={handleLogin}>
            <input
              value={loginForm.email}
              onChange={(event) => setLoginForm((prev) => ({ ...prev, email: event.target.value }))}
              placeholder="Email"
              type="email"
              className="w-full px-4 py-3 border border-border rounded-xl focus:outline-none focus:border-primary"
            />
            <input
              value={loginForm.password}
              onChange={(event) => setLoginForm((prev) => ({ ...prev, password: event.target.value }))}
              placeholder="Пароль"
              type="password"
              className="w-full px-4 py-3 border border-border rounded-xl focus:outline-none focus:border-primary"
            />

            <button
              type="submit"
              disabled={!canLogin || isSubmitting}
              className="w-full bg-primary text-white py-3 rounded-xl disabled:opacity-50"
              style={{ fontWeight: 700 }}
            >
              {isSubmitting ? "Вход..." : "Войти"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
