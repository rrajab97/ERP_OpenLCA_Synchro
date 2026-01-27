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
```
## Erläuterung der Pakete

### fastapi
**FastAPI** ist ein Web-Framework für Python, das die Erstellung von APIs vereinfacht. Es nutzt Python-Typen und Pydantic-Modelle zur Validierung von Daten und bietet automatisch eine Swagger-Oberfläche für die API-Dokumentation. FastAPI wird hier verwendet, um einen Microservice zu erstellen, der als Schnittstelle zu OpenLCA dient.

### uvicorn
**Uvicorn** ist ein leistungsfähiger ASGI-Server, der für die Ausführung von FastAPI-Anwendungen verwendet wird. Uvicorn sorgt dafür, dass deine FastAPI-App reibungslos ausgeführt werden kann und hohe Performance erreicht wird. Er ist speziell auf Asynchronität optimiert, was ihn ideal für Webanwendungen macht.

### requests
Die **requests**-Bibliothek wird verwendet, um HTTP-Anfragen zu senden. Diese Bibliothek erleichtert das Arbeiten mit Webanfragen.

### olca-ipc
**olca-ipc** ermöglicht die Kommunikation mit OpenLCA über den IPC-Server. Mit `olca-ipc` können OpenLCA-Daten angefragt, Berechnungen ausfgeführt und mit der LCA-Datenbank interagiert werden.

### olca-schema
**olca-schema** ist ein Paket, das die Definition der OpenLCA-Datenstrukturen bereitstellt. Es enthält die Modellklassen für die verschiedenen Datentypen, die in der Kommunikation mit OpenLCA verwendet werden. Dieses Schema erleichtert das Arbeiten mit den OpenLCA-Daten und ermöglicht die Strukturierung der Daten in der für OpenLCA benötigten Form.
