# SafetyPulse: Industrial Safety Intelligence Engine 🛡️

**SafetyPulse** is a production-ready telemetry monitoring platform designed for MSA Safety's subsidiary, Safety.io. It bridges the gap between raw IoT sensor data and actionable compliance intelligence.

Built to run efficiently on legacy hardware (8GB RAM environments), it provides a high-fidelity monitoring experience without the overhead of heavy enterprise suites.

## 🚀 Project Overview

In hazardous industrial environments, "data" is a life-saving asset. SafetyPulse ingests real-time readings for Carbon Monoxide (CO), Hydrogen Sulfide (H2S), Oxygen (O2), and Lower Explosive Limits (LEL). 

### Key Capabilities:
- **Real-Time Telemetry**: Sub-second ingestion and visualization of gas levels.
- **Automated AI Analysis**: Powered by Gemini-3 Flash to generate stark, high-contrast compliance summaries from raw data clusters.
- **Enterprise-Grade Auth**: Secure registration and login with real-time password complexity validation and strength metering.
- **Integrated Test Lab**: A built-in unit testing suite that verifies safety-critical logic directly in the browser environment.
- **Industrial UX**: Designed with an "Industrial Dark" aesthetic for high visibility and professional reliability.

## 🛠️ Tech Stack

- **Frontend**: React 19 (Hooks, Context API, Performance-optimized).
- **Styling**: Tailwind CSS (Stark industrial theme).
- **AI Intelligence**: Google Gemini API (Gemini-3 Flash Preview) for anomaly detection.
- **Iconography**: Lucide React.
- **State Management**: React Context with LocalStorage persistence for user sessions.
- **Testing**: Custom modular Unit Testing framework (`/tests/`).
- **Data Modeling**: Strict TypeScript typing for Sensors, Readings, and Alerts.

## 📦 Project Structure

```text
safetypulse/
├── app/                  # (Conceptual) Backend API logic
├── logic.ts              # Core business & safety logic
├── tests/                # Unit Testing Suite
│   ├── auth.ts           # Security & Auth assertions
│   ├── sensors.ts        # Threshold & Safety assertions
│   └── suite.ts          # Master test runner
├── index.tsx             # Main application entry & UI
└── README.md             # You are here
```

## 🔐 Security & Compliance

SafetyPulse takes security seriously. Passwords must meet specific complexity requirements (Upper, Lower, Number, Special, 8+ chars). The system includes a built-in "Test Lab" so safety engineers can verify that the gas thresholds haven't been tampered with or regressed during software updates.

## ☕ Developer Notes

*Built with late-night coffee and a obsession for clean industrial UI.* 

**TODO for v0.4.0:**
- [ ] Implement real-time WebSocket connection for live hardware simulation.
- [ ] Add PDF export capability for the AI Analysis reports.
- [ ] Refactor the sidebar state to use `sessionStorage` instead of local component state.

---
