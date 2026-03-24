# PulseBoard

> **AI-powered real-time operations intelligence platform**  
> Built with Clean Architecture · Next.js 15 · FastAPI · scikit-learn · WebSockets

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js&logoColor=white)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What is PulseBoard?

PulseBoard monitors live system metrics (CPU, memory, latency, error rate, revenue, active users), streams them to a browser dashboard in real time over WebSocket, and uses an **Isolation Forest ML model** to automatically detect anomalies — raising alerts with severity classification the moment something goes wrong.

Designed to demonstrate senior full-stack + ML engineering skills

---

## Live Demo

| Service | URL |
|---|---|
| Dashboard | http://localhost:3000/dashboard |
| REST API | http://localhost:8000/docs |
| Health | http://localhost:8000/api/health |

---

## Architecture

PulseBoard is built on **Clean Architecture** (Robert C. Martin). Dependencies only ever point **inward** — the domain has zero knowledge of FastAPI, React, or scikit-learn.

```
╔══════════════════════════════════════════════════════════════════╗
║  4. Frameworks & Drivers          (outermost — changes freely)  ║
║  ┌────────────────────────────────────────────────────────────┐  ║
║  │  3. Interface Adapters                                     │  ║
║  │  ┌──────────────────────────────────────────────────────┐  │  ║
║  │  │  2. Application Layer  (Use Cases)                   │  │  ║
║  │  │  ┌────────────────────────────────────────────────┐  │  │  ║
║  │  │  │  1. Domain  (Entities · Business rules)        │  │  │  ║
║  │  │  │  — Pure Python / Pure TypeScript               │  │  │  ║
║  │  │  │  — Zero external dependencies                  │  │  │  ║
║  │  │  └────────────────────────────────────────────────┘  │  │  ║
║  │  └──────────────────────────────────────────────────────┘  │  ║
║  └────────────────────────────────────────────────────────────┘  ║
╚══════════════════════════════════════════════════════════════════╝

        Dependency Rule:  →  always points INWARD  ←
```

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (Next.js)                        │
│                                                                 │
│  presentation/      application/       infrastructure/          │
│  components/        use-cases/         api/ (REST)              │
│  (React UI)         dashboard-store    websocket/ (WS stream)   │
│                     (Zustand)                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │  REST /api/*  │  WebSocket ws://
                         ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python)                     │
│                                                                 │
│  presentation/api/routes/     ← HTTP + WebSocket entry points  │
│  application/use_cases/       ← GetMetrics, DetectAnomalies    │
│  application/dto/             ← Pydantic serialisation         │
│  domain/entities/             ← Metric, Anomaly, Alert         │
│  domain/repositories/         ← Abstract interfaces (ports)    │
│  domain/services/             ← AnomalyDetectionService        │
│  infrastructure/ml/           ← IsolationForest (scikit-learn) │
│  infrastructure/repositories/ ← InMemory implementations       │
│  infrastructure/simulator/    ← Realistic metric generation    │
│  infrastructure/websocket/    ← ConnectionManager (broadcast)  │
│  core/dependencies.py         ← Composition root (DI wiring)   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
MetricSimulator (1s tick)
        │
        ▼
DetectAnomaliesUseCase.execute(metric, value)
        │
        ├─► InMemoryMetricRepository.save_point()
        │
        ├─► IsolationForestDetector.detect(series)
        │         └─ returns (is_anomaly, confidence, expected_range)
        │
        ├─► AnomalyDetectionService.evaluate(series)
        │         └─ applies business rules (severity, dedup)
        │
        ├─► InMemoryAnomalyRepository.save(anomaly)
        ├─► InMemoryAlertRepository.save(alert)
        │
        └─► ConnectionManager.broadcast({type: "anomaly_detected", ...})
                  └─► all connected WebSocket clients
```

---

## Project Structure

```
pulseboard/
│
├── backend/                        Python / FastAPI
│   ├── app/
│   │   ├── domain/                 ── LAYER 1: Pure Python
│   │   │   ├── entities/
│   │   │   │   ├── metric.py       MetricName enum, MetricPoint, MetricSeries
│   │   │   │   ├── anomaly.py      Anomaly entity + AnomalySeverity
│   │   │   │   └── alert.py        Alert entity + lifecycle state machine
│   │   │   ├── repositories/
│   │   │   │   ├── metric_repository.py    IMetricRepository (ABC)
│   │   │   │   └── anomaly_repository.py   IAnomalyRepository, IAlertRepository
│   │   │   └── services/
│   │   │       └── anomaly_detection_service.py  Business rules + dedup
│   │   │
│   │   ├── application/            ── LAYER 2: Use Cases + DTOs
│   │   │   ├── use_cases/
│   │   │   │   ├── get_metrics.py          GetMetricsUseCase
│   │   │   │   └── detect_anomalies.py     DetectAnomaliesUseCase, AcknowledgeAnomaly, ResolveAlert
│   │   │   └── dto/
│   │   │       ├── metric_dto.py           MetricPointDTO, MetricSeriesDTO, MetricsSnapshotDTO
│   │   │       └── anomaly_dto.py          AnomalyDTO, AlertDTO
│   │   │
│   │   ├── infrastructure/         ── LAYER 3: Concrete Implementations
│   │   │   ├── ml/
│   │   │   │   └── isolation_forest_detector.py  scikit-learn Isolation Forest
│   │   │   ├── repositories/
│   │   │   │   ├── in_memory_metric_repo.py
│   │   │   │   └── in_memory_anomaly_repo.py
│   │   │   ├── simulator/
│   │   │   │   └── metric_simulator.py     Diurnal cycles + synthetic spikes
│   │   │   └── websocket/
│   │   │       └── connection_manager.py   Broadcast hub + heartbeat
│   │   │
│   │   ├── presentation/           ── LAYER 4: FastAPI Routers
│   │   │   └── api/routes/
│   │   │       ├── metrics.py      GET /api/metrics, GET /api/metrics/{name}
│   │   │       ├── anomalies.py    GET /api/anomalies, PATCH acknowledge/resolve
│   │   │       ├── health.py       GET /api/health
│   │   │       └── websocket.py    WS  /ws/metrics
│   │   │
│   │   ├── core/
│   │   │   ├── config.py           Pydantic Settings (reads .env)
│   │   │   └── dependencies.py     Composition root — DI wiring
│   │   │
│   │   └── main.py                 App factory + lifespan (startup/shutdown)
│   │
│   └── requirements.txt
│
├── frontend/                       TypeScript / Next.js 15
│   └── src/
│       ├── domain/                 ── LAYER 1: Pure TypeScript types
│       │   └── entities/metric.ts  MetricSeries, Anomaly, Alert interfaces
│       │
│       ├── application/            ── LAYER 2: State management
│       │   └── use-cases/
│       │       └── dashboard-store.ts  Zustand store (actions = use cases)
│       │
│       ├── infrastructure/         ── LAYER 3: External adapters
│       │   ├── api/
│       │   │   └── metrics-repository.ts  Axios REST client
│       │   └── websocket/
│       │       └── useMetricsStream.ts    WS hook + exponential backoff
│       │
│       ├── presentation/           ── LAYER 4: React components
│       │   └── components/
│       │       ├── ui/             Badge, Card, ConnectionStatus, Spinner
│       │       ├── charts/         Recharts wrappers
│       │       ├── dashboard/      MetricCard, AnomalyPanel, AlertFeed
│       │       └── layout/         Sidebar, Topbar
│       │
│       └── app/                    Next.js App Router (entry points)
│           ├── layout.tsx          Root shell
│           ├── page.tsx            Redirects → /dashboard
│           ├── dashboard/page.tsx  Main dashboard
│           └── (auth)/login/       Login page
│
├── .github/
│   └── workflows/                  GitHub Actions CI/CD (coming)
│
└── .gitignore
```

---

## Tech Stack

### Backend
| Layer | Technology | Why |
|---|---|---|
| Web framework | **FastAPI** | Async-first, auto-generates OpenAPI docs, typed |
| ML / Anomaly detection | **scikit-learn** Isolation Forest | Unsupervised, no labelled data needed, fast |
| WebSocket hub | **asyncio** + FastAPI WebSocket | Native async broadcast without extra broker |
| Configuration | **Pydantic Settings** | Type-safe env config, fail-fast on startup |
| Concurrency | **uvicorn** + asyncio | Single-threaded async — no threading complexity |

### Frontend
| Layer | Technology | Why |
|---|---|---|
| Framework | **Next.js 15** (App Router) | Server components, file-based routing, Turbopack |
| Language | **TypeScript** (strict) | Catches a whole class of bugs at compile time |
| State management | **Zustand** | Minimal boilerplate, hooks-based, devtools support |
| Charts | **Recharts** | Composable React charting library |
| Styling | **Tailwind CSS** | Utility-first, consistent dark theme |
| HTTP client | **Axios** | Interceptors for auth headers + error handling |

### Infrastructure
| Tool | Purpose |
|---|---|
| **Docker + Compose** | Reproducible local + production environment |
| **GitHub Actions** | CI (lint, type-check, test) + CD (build images) |
| **`.gitignore`** | Excludes node_modules, .venv, .env, ML model binaries |

---

## Key Engineering Decisions

### 1. Clean Architecture — not MVC
> "I chose Clean Architecture over MVC so that the domain logic — anomaly severity rules, alert lifecycle state machine, metric deduplication — can be unit tested without mocking FastAPI, databases, or the ML model."

### 2. Isolation Forest for Anomaly Detection
> "Isolation Forest is unsupervised — no labelled anomaly data required. It works well on operational metrics because it handles multimodal distributions (e.g., traffic is naturally high at 9am and low at 3am) without assuming normality like Z-score does."

### 3. WebSocket with Exponential Backoff
> "The client reconnects with exponential backoff (1s → 2s → 4s → max 30s) so the dashboard recovers gracefully from network blips without manual refresh — critical for an operations tool."

### 4. Dependency Inversion (Ports & Adapters)
> "Every concrete implementation (InMemoryMetricRepo, IsolationForestDetector) is wired in a single composition root (`core/dependencies.py`). To scale to production, I'd replace `InMemoryMetricRepository` with a `TimescaleDBMetricRepository` — zero changes to domain or use cases."

### 5. Domain Services vs. Infrastructure
> "Business rules — deduplication, severity classification, alert lifecycle — live in domain services. The ML score is infrastructure. This separation lets us swap the model (Isolation Forest → Z-score → LLM) by touching only one infrastructure file."

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness probe |
| `GET` | `/api/health/system` | Full system status |
| `GET` | `/api/metrics` | All metrics snapshot |
| `GET` | `/api/metrics/{name}` | Single metric time-series |
| `GET` | `/api/anomalies` | Recent anomalies |
| `PATCH` | `/api/anomalies/{id}/acknowledge` | Acknowledge anomaly |
| `GET` | `/api/alerts` | All alerts (filterable by status) |
| `PATCH` | `/api/alerts/{id}/resolve` | Resolve an alert |
| `WS` | `/ws/metrics` | Real-time stream |

### WebSocket Message Format
```json
{
  "type": "anomaly_detected",
  "payload": {
    "id": "uuid",
    "metric": "error_rate",
    "observed_value": 18.4,
    "expected_range": [0.5, 5.2],
    "confidence": 0.94,
    "severity": "critical",
    "description": "error_rate spiked to 18.40 (expected 0.50–5.20). Severity: CRITICAL"
  },
  "timestamp": "2026-03-17T22:00:00.000Z",
  "sequence": 142
}
```

Message types: `metrics_update` · `anomaly_detected` · `alert_triggered` · `alert_resolved` · `heartbeat`

---

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 20+

### 1. Clone the repo
```bash
git clone https://github.com/pkb94/pulseboard.git
cd pulseboard
```

### 2. Start the backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Start the frontend
```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

### 4. Open the app
| | |
|---|---|
| **Dashboard** | http://localhost:3000 |
| **API docs (Swagger)** | http://localhost:8000/docs |

> The metric simulator starts automatically. After ~20 seconds you'll see live data populating the dashboard. Anomalies are injected randomly (~2% of ticks) to demonstrate the ML detection pipeline.

---

## Running Tests

```bash
# Backend unit tests
cd backend
source .venv/bin/activate
pytest tests/ -v

# Frontend type-check
cd frontend
npm run type-check

# Frontend lint
npm run lint
```

---

## Environment Variables

### Backend (`backend/.env`)
```env
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:3000
DEBUG=false
```

### Frontend (`frontend/.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## Roadmap
- [ ] Docker + Docker Compose setup
- [ ] GitHub Actions CI/CD pipeline
- [ ] TimescaleDB / InfluxDB persistence layer
- [ ] Recharts time-series chart components
- [ ] Auth with JWT (login page → protected routes)
- [ ] Alert notification channels (email, Slack webhook)
- [ ] Configurable alert thresholds via API

---

## Author

**Pooja Kittanakere Balaji**  
[github.com/pkb94](https://github.com/pkb94)

---

*Built as a portfolio project demonstrating Clean Architecture, real-time systems, and applied ML for operations intelligence.*
