# OnayMath

Платформа для обучения математике по школьной программе:
- регистрация с выбором города, школы и класса;
- темы и уроки по классу ученика;
- тесты, прогресс и XP;
- рейтинг одноклассников/школы/города;
- раздел с книгами;
- AI-ассистент для объяснения тем.

## Backend

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API будет доступен по `http://127.0.0.1:8000/api`.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend по умолчанию использует backend `http://localhost:8000/api`.

## AI и PDF хранилище

Backend использует переменные из `.env`:
- `GROQ_API_TOKEN` (+ опционально `GROQ_MODEL`) для AI-ассистента;
- `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME` для Cloudflare R2.
- `CORS_ORIGINS` (через запятую) и `CORS_ALLOW_ORIGIN_REGEX` для разрешенных frontend-origin.

Эндпоинт `GET /api/books/{id}` возвращает `signedFileUrl` как presigned URL из R2.
