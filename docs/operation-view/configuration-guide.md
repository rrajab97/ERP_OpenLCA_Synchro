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
**FastAPI** ist ein modernes, schnelles Web-Framework für Python, das die Erstellung von APIs vereinfacht. Es nutzt Python-Typen und Pydantic-Modelle zur Validierung von Daten und bietet automatisch eine Swagger-Oberfläche für die API-Dokumentation. FastAPI wird hier verwendet, um einen Microservice zu erstellen, der als Schnittstelle zu OpenLCA dient.

### uvicorn
**Uvicorn** ist ein hochleistungsfähiger ASGI-Server, der für die Ausführung von FastAPI-Anwendungen verwendet wird. Uvicorn sorgt dafür, dass deine FastAPI-App reibungslos ausgeführt werden kann und hohe Performance erreicht wird. Er ist speziell auf Asynchronität optimiert, was ihn ideal für Webanwendungen macht.

### requests
Die **requests**-Bibliothek wird verwendet, um HTTP-Anfragen zu senden. Diese Bibliothek ist sehr benutzerfreundlich und erleichtert das Arbeiten mit Webanfragen. In dieser Dokumentation verwenden wir `requests` für die Kommunikation zwischen deinem ERP-System und dem OpenLCA-Microservice.

### olca-ipc
**olca-ipc** ermöglicht die Kommunikation mit OpenLCA über den IPC (Inter-Process Communication)-Server. Mit `olca-ipc` kannst du OpenLCA-Daten anfragen, Berechnungen ausführen und mit der LCA-Datenbank interagieren. Es stellt eine einfache Schnittstelle bereit, um die OpenLCA-Daten zu integrieren und zu verwalten.

### olca-schema
**olca-schema** ist ein Paket, das die Definition der OpenLCA-Datenstrukturen bereitstellt. Es enthält die Modellklassen für die verschiedenen Datentypen, die in der Kommunikation mit OpenLCA verwendet werden. Dieses Schema erleichtert das Arbeiten mit den OpenLCA-Daten, da es die Komplexität der Datentransformation übernimmt und es ermöglicht, die Daten in der für OpenLCA benötigten Form zu strukturieren.
