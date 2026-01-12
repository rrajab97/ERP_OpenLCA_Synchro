# Configuration Guide

## Voraussetzungen
- Windows/Linux Rechner mit:
  - openLCA installiert
  - Python 3.11+
  - Zugriff auf Odoo Instanz (URL, DB, User, API Key)

## openLCA Setup
1. Datenbank importieren: `idemat_2023`
2. IPC-Server aktivieren: Port 8080

## Python Setup
```bash
python -m pip install -U olca-ipc olca-schema fastapi uvicorn requests
