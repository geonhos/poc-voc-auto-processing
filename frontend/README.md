# VOC Auto Processing - Frontend

React 기반 VOC 자동 처리 시스템 관리자 UI

## Tech Stack

- **React 18** + **TypeScript**
- **Vite** - Build tool
- **React Router** - Routing
- **Axios** - API client
- **date-fns** - Date formatting

## Architecture

**Hook-Driven Layered Architecture**를 따릅니다:

```
src/
├── components/          # Presentational Components (UI only)
│   ├── atoms/          # Atomic components (Badge, Button, etc.)
│   ├── molecules/      # Composed components
│   └── organisms/      # Complex components (Layout, Modal, etc.)
├── hooks/              # Custom Hooks (State + Business Logic)
├── services/           # Service Layer (API calls, side effects)
├── domains/            # Domain Logic (Pure functions)
│   ├── ticket/        # Ticket domain
│   └── voc/           # VOC domain
├── types/              # TypeScript types
└── pages/              # Page components (Hook + Component composition)
```

### Architectural Rules

1. **Components** - Presentational only (JSX + props)
2. **Hooks** - State & business logic
3. **Services** - API calls & side effects
4. **Domains** - Pure business logic functions

## Getting Started

### Install Dependencies
```bash
npm install
```

### Development Server
```bash
npm run dev
```

Runs on `http://localhost:5173`

### Build
```bash
npm run build
```

## Routes

- `/` - Ticket 목록
- `/voc/new` - VOC 입력
- `/tickets/:id` - Ticket 상세

## Environment

Backend API: `http://localhost:8000`
