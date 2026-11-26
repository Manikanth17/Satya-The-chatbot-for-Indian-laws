# SATYA Frontend

Responsive React + TypeScript + Vite frontend for SATYA.

## Requirements
- Node.js 20.19+ or 22.12+
- npm
- Java Spring Boot backend for live chat

## Install and run
```bash
npm install
cp .env.example .env
npm run dev
```
Open http://127.0.0.1:5173

## API integration — important
The default frontend configuration expects:
- `GET /api/health`
- `POST /api/chat` with JSON `{ "question": "..." }`
- A response matching the SATYA public `ChatResponse` model.

Confirm the actual public route and request DTO in your Java `PublicController.java` and `Contract.java`. If they differ, change `.env` and/or `src/lib/api.ts`. Do not call Python's `/internal/chat` directly from the browser; that is a server-to-server endpoint and requires the internal token.

`.env.example`:
```env
VITE_API_BASE_URL=http://127.0.0.1:8080
VITE_CHAT_ENDPOINT=/api/chat
VITE_HEALTH_ENDPOINT=/api/health
```

## Production build
```bash
npm run build
npm run preview
```

## Included
- Responsive SATYA legal research workspace
- Chat UI, suggested questions and follow-up messages
- Source cards for official URL, document, page and supporting quotation when returned by API
- Backend health indicator and readable API errors
- Explicit status badges for answered, partial, refusal, clarification and conflict
- No fabricated demo legal answers

## Structure
```text
src/
  components/ Brand.tsx, ChatMessage.tsx, SourceCard.tsx
  lib/         api.ts
  App.tsx
  main.tsx
  styles.css
  types.ts
```
