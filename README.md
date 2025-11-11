# ⚡ Secure Fog-Based Smart Meter Communication

This project is a **working prototype** of the secure fog–cloud communication model described in our professor’s research paper.  
It demonstrates **end-to-end encrypted, authenticated, and aggregated communication** between smart meters, fog nodes, and a cloud server.

---

## 🧠 Overview

The system simulates a **three-tier smart metering architecture**:

```
Smart Meters  →  Fog Node  →  Cloud Server
```

- **Smart Meters:** Generate periodic power usage and voltage readings, encrypt and sign them, then transmit securely to the fog node.  
- **Fog Node:** Decrypts and verifies readings, performs local aggregation (average power & voltage), and forwards encrypted summaries to the cloud.  
- **Cloud Server:** Decrypts fog-level summaries, stores them, and exposes APIs for monitoring and visualization.

This architecture mirrors the approach proposed in the research paper — combining **fog computing** with **lightweight cryptography** to ensure **privacy, scalability, and low latency** in IoT-based energy systems.

---

## 🔐 Cryptographic Design

| Objective | Algorithm | Purpose |
|------------|------------|----------|
| **Key Exchange** | X25519 (ECDH) | Secure symmetric key derivation between communicating nodes |
| **Key Derivation** | HKDF-SHA256 | Derives 256-bit session key from shared secret |
| **Encryption** | ChaCha20-Poly1305 | Lightweight, authenticated encryption (confidentiality + integrity) |
| **Authentication** | Ed25519 | Digital signatures to verify sender authenticity |
| **Replay Protection** | Timestamp + Nonce | Prevents reusing old packets |
| **Integrity Validation** | Poly1305 (built into ChaCha20) | Detects message tampering |

Each communication link (Smart Meter ↔ Fog Node ↔ Cloud Server) uses independent cryptographic sessions for security and isolation.

---

## 🧩 Project Structure

```
secure-fog-communication/
├── cloud/
│   ├── __init__.py
│   └── cloud_server.py        # Cloud API – receives, decrypts & summarizes data
│
├── fog/
│   ├── __init__.py
│   └── fog_node.py            # Fog API – decrypts, aggregates & forwards to cloud
│
├── meters/
│   ├── __init__.py
│   ├── smart_meter.py         # Single smart meter (for debugging)
│   └── meter_simulator.py     # Spawns 10 meters, sending continuous data
│
├── utils/
│   ├── __init__.py
│   └── crypto_utils.py        # Cryptographic helpers (X25519, HKDF, ChaCha20, Ed25519)
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ⚙️ Setup Instructions

### 1️⃣ Environment Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # (Windows)
# or source .venv/bin/activate (Linux/Mac)
pip install -r requirements.txt
```

---

### 2️⃣ Running the System (Open Three Terminals)

#### 🟢 Cloud Server
```bash
uvicorn cloud.cloud_server:app --port 8002
```

#### 🟠 Fog Node
```bash
uvicorn fog.fog_node:app --port 8001
```

#### 🔵 Smart Meter Simulator
```bash
python -m meters.meter_simulator
```

Each simulated meter generates encrypted readings and sends them to the fog node every few seconds.

---

## 📊 Example Output

### **Fog Node Console:**
```
📩 From M-001: 6.4 kWh (230.8 V)
📩 From M-002: 5.98 kWh (214.1 V)
📦 Aggregated → Cloud: {'fog_id': 'FN-01', 'num_meters': 20, 'avg_power': 5.36, 'avg_voltage': 228.0}
✅ Sent aggregated data to cloud
```

### **Cloud Server Console:**
```
✅ Cloud decrypted data: {"fog_id": "FN-01", "num_meters": 20, "avg_power": 5.36, "avg_voltage": 228.0}
```

### **Browser (Cloud Summary):**
Visit → [http://127.0.0.1:8002/summary](http://127.0.0.1:8002/summary)

```json
{
  "total_packets": 5,
  "avg_power_overall": 5.42,
  "avg_voltage_overall": 227.3,
  "latest_data": [
    {"fog_id": "FN-01", "num_meters": 20, "avg_power": 5.28, "avg_voltage": 226.7}
  ]
}
```

---

## 🧾 Semester 1 Achievements

| Feature | Status | Description |
|----------|---------|-------------|
| Secure key generation & exchange | ✅ | X25519 + HKDF session key protocol |
| End-to-end encryption | ✅ | ChaCha20-Poly1305 AEAD |
| Data authentication | ✅ | Ed25519 digital signatures |
| Replay protection | ✅ | Timestamp + nonce validation |
| Local aggregation | ✅ | Fog-level computation of average metrics |
| Cloud summary API | ✅ | Real-time aggregated view at `/summary` |

✅ **Complete proof-of-concept** for fog-based secure communication.  
(Planned extensions — billing, storage, dashboards — will come in Semester 2.)

---

## 🚀 Semester 2 Roadmap

| Next Step | Description |
|------------|-------------|
| **Multi-Fog Setup** | Deploy multiple fog nodes on Raspberry Pis |
| **Per-Meter Billing** | Maintain cumulative kWh and compute bills at cloud |
| **Database Integration** | Store readings persistently (SQLite or PostgreSQL) |
| **Visualization Dashboard** | Real-time usage graphs using Streamlit or Next.js |
| **Blockchain Layer** | Add tamper-proof validation across fog and cloud |

---

## 🧑‍💻 Authors

**Pratyush Kumar Chaturvedi**, **Ozair Malakji**  
B.Tech, CSE, IIT (ISM) Dhanbad  
Mentor: **Prof. Sachin Tripathi**  
Course: Final Year Project – Semester 1  

---

## 🧩 How This Implements the Research Paper

This project operationalizes the cryptographic and architectural model proposed in *Blockchain-assisted Authentication and Key Agreement Scheme for Fog-based Smart Grid (Tomar & Tripathi, 2021)*.  
It implements:
- **Secure key establishment (X25519 + HKDF)** for each device link,  
- **Authenticated encryption (ChaCha20-Poly1305)** for lightweight, efficient data protection,  
- **Edge aggregation (Fog layer)** to reduce bandwidth and preserve privacy, and  
- **End-to-end integrity and authenticity (Ed25519 signatures)** for trustworthy communication.

Thus, it forms the **core communication backbone** described in the paper — a secure, hierarchical IoT data transmission model suitable for smart grids and fog-enabled environments.

---

## 🛡️ License

MIT License – Free for academic and research use.
