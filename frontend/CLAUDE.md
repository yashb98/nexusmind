# Frontend Context (frontend/)

## Stack
React 18 + Next.js App Router + TypeScript + TailwindCSS + shadcn/ui

## Pages
/dashboard (Home/Feed), /network (Graph), /groups, /events, /learn, /profile, /onboarding

## API Client
All calls through `src/lib/api.ts`. JWT in localStorage, attached via interceptor.
Base URL from NEXT_PUBLIC_API_URL env var (default: http://localhost:8000).

## WebSocket
Conversations stream token-by-token via WebSocket.
Two channels per live conversation: /live (debate) + /tutor (commentary).

## Components
Max 200 lines. Extract sub-components. ALWAYS handle loading + error + empty states.
NEVER use `any` type. All API types in `src/types/`.

## Styling
Dark theme. Background: gray-900. Cards: gray-800. Primary: purple-600.
Use shadcn/ui components. Tailwind utilities only.

## Testing
`pnpm test --run` for unit tests.
