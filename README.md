# PulseBoard

**AI-powered real-time operations intelligence dashboard**  
Next.js 15 · FastAPI · WebSockets · scikit-learn · Clean Architecture

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js&logoColor=white)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> PulseBoard streams live operational metrics (CPU, memory, latency, error rate, revenue, active users) to a web dashboard in real time and detects anomalies using an **Isolation Forest** model—triggering alerts with severity classification the moment something goes wrong.

**What this project demonstrates**
- Clean Architecture + Ports & Adapters (domain is framework-agnostic)
- Real-time systems (WebSocket streaming + reconnect/backoff)
- Applied ML in a product workflow (detection → business rules → alert lifecycle)
- Full-stack implementation (FastAPI backend + Next.js frontend)

---

## Key Features
- **Real-time dashboard**: live metric updates via WebSocket stream
- **Anomaly detection**: Isolation Forest-based detection with confidence + expected range
- **Alerting workflow**: anomaly → alert triggered → acknowledge → resolve
- **Resilient client**: exponential backoff reconnect (1s → 2s → 4s → max 30s)
- **Testable business logic**: domain rules unit-testable without FastAPI/DB/ML dependencies

---

## Quickstart (Local)
### Prerequisites
- Python 3.9+
- Node.js 20+

### 1) Clone
```bash
git clone https://github.com/pkb94/pulseboard.git
cd pulseboard
```

### 2) Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3) Frontend
```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

### 4) Open
| Service | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Health | http://localhost:8000/api/health |

> The metric simulator starts automatically. After ~20 seconds you'll see live data populating the dashboard. Anomalies are injected randomly (~2% of ticks) to demonstrate the ML detection pipeline.

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

<details>
<summary><strong>Architecture (Clean Architecture + Data Flow)</strong></summary>

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
│  presentation/api/routes/     ← HTTP + WebSocket entry points   │
│  application/use_cases/       ← GetMetrics, DetectAnomalies     │
│  application/dto/             ← Pydantic serialisation          │
│  domain/entities/             ← Metric, Anomaly, Alert          │
│  domain/repositories/         ← Abstract interfaces (ports)     │
│  domain/services/             ← AnomalyDetectionService         │
│  infrastructure/ml/           ← IsolationForest (scikit-learn)  │
│  infrastructure/repositories/ ← InMemory implementations        │
│  infrastructure/simulator/    ← Realistic metric generation     │
│  infrastructure/websocket/    ← ConnectionManager (broadcast)   │
│  core/dependencies.py         ← Composition root (DI wiring)    │
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
        ├─► IsolationForestDetector.detect(series)
        │         └─ returns (is_anomaly, confidence, expected_range)
        ├─► AnomalyDetectionService.evaluate(series)
        │         └─ applies business rules (severity, dedup)
        ├─► InMemoryAnomalyRepository.save(anomaly)
        ├─► InMemoryAlertRepository.save(alert)
        └─► ConnectionManager.broadcast({type: "anomaly_detected", ...})
                  └─► all connected WebSocket clients
```

</details>

---

## Tech Stack
### Backend
| Layer | Technology | Why |
|---|---|---|
| Web framework | **FastAPI** | Async-first, auto-generates OpenAPI docs, typed |
| ML / Anomaly detection | **scikit-learn** Isolation Forest | Unsupervised, fast |
| WebSocket hub | **asyncio** + FastAPI WebSocket | Native async broadcast |
| Configuration | **Pydantic Settings** | Type-safe env config |
| Concurrency | **uvicorn** + asyncio | Async without threading complexity |

### Frontend
| Layer | Technology | Why |
|---|---|---|
| Framework | **Next.js 15** (App Router) | App Router, modern routing |
| Language | **TypeScript** (strict) | Safer refactors |
| State management | **Zustand** | Minimal boilerplate |
| Charts | **Recharts** | Composable charting |
| Styling | **Tailwind CSS** | Consistent UI |
| HTTP client | **Axios** | Interceptors for auth/errors |

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

## Roadmap
- [ ] Docker + Docker Compose setup
- [ ] GitHub Actions CI/CD pipeline
- [ ] TimescaleDB / InfluxDB persistence layer
- [ ] Auth with JWT (login page → protected routes)
- [ ] Alert notification channels (email, Slack webhook)
- [ ] Configurable alert thresholds via API

---

## Author
**Pooja Kittanakere Balaji**  
[github.com/pkb94](https://github.com/pkb94)

*Built as a portfolio project demonstrating Clean Architecture, real-time systems, and applied ML for operations intelligence.*