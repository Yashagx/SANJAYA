# 🔱 SANJAYA | Multi-Agent Shipment Risk Intelligence

**SANJAYA** is a state-of-the-art logistics risk intelligence system that utilizes a multi-agent architecture powered by **BRAHMA (AI Logistics Advisor)**. It provides real-time shipment delay predictions, geopolitical risk assessments, and intelligent routing optimizations.

---

## 📸 System Dashboard & Visual Overview

### 🖥️ Main Dashboard
Experience the live tracking and risk assessment of shipments worldwide.

![Dashboard Preview 1](sanjaya/images/Screenshot%202026-04-16%20164901.png)
*High-level risk monitoring and aggregate system statistics.*

### 🔍 Risk Analysis & Agent Insights
Detailed breakdown of risk scores provided by our specialized AI agents.

| | |
|---|---|
| ![Analysis 1](sanjaya/images/Screenshot%202026-04-16%20164925.png) | ![Analysis 2](sanjaya/images/Screenshot%202026-04-16%20164937.png) |
| *Geopolitical & Weather Risk Analysis* | *Customs & Port Congestion Insights* |

### 🛠️ Predictive Intelligence
Using historical data and real-time signals to predict shipment delays before they happen.

![Prediction 1](sanjaya/images/Screenshot%202026-04-16%20165234.png)
*Shipment specific risk profiling and recommendation engine.*

### 🌍 Global Network Monitoring
Monitoring routes through critical chokepoints and high-risk zones.

![Monitoring 1](sanjaya/images/Screenshot%202026-04-16%20165247.png)
*Route-based risk assessment and historical delay tracking.*

### 🤖 BRAHMA - AI Executive Summary
AI-generated executive narratives for complex logistics scenarios.

![Brahma Analysis](sanjaya/images/Screenshot%202026-04-16%20165318.png)
*Natural Language Risk Intelligence via BRAHMA.*

---

## 🚀 Key Features

*   **Multi-Agent Orchestration**: 7 specialized agents (NIDHI, VAYU, SANCHAR, DARPANA, VIVEKA, MARGA, AKASHA).
*   **BRAHMA AI**: Powered by Amazon Bedrock for deep narrative analysis and executive summaries.
*   **KAVACH Validation**: Predictive input filtering and pre-flight validation.
*   **Real-time Dashboard**: Interactive HTML5 dashboard serving live risk intelligence.
*   **Docker Ready**: Production-grade containerization for seamless deployment.

## 🛠️ Tech Stack

*   **Backend**: FastAPI, Python 3.12, Uvicorn
*   **Database**: PostgreSQL (SQLAlchemy ORM)
*   **AI/ML**: Amazon Bedrock, Scikit-learn
*   **Deployment**: Docker, Docker Compose, systemd

## 🏗️ Quick Start

1.  **Environment Variables**: Copy `docker/.env.docker` to `.env` and fill in your credentials.
2.  **Start with Docker**:
    ```powershell
    docker-compose up -d
    ```
3.  **Access Dashboard**: Open `http://localhost:8000/dashboard` in your browser.

For a detailed deployment guide, see the [Docker README](docker/README.md).

---

© 2026 SANJAYA Team | Logistics Risk Intelligence
