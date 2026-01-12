# Architecture Overview

## Komponenten
- **Odoo (SaaS, Browser):** Datenquelle (Produkte, Varianten, BoMs, MOs)
- **FastAPI Service:** REST-API als Integrationsschicht
- **openLCA IPC:** Berechnungsengine (Prozess/Produktsystem/LCIA)
- **LCA Datenbank:** idemat_2023

## Warum Microservice statt direkter Odoo-Logik?
- Odoo SaaS erlaubt keine freien Python-Imports/Requests in Server Actions.
- openLCA IPC benötigt lokalen Zugriff (Port 8080).
- Microservice kapselt Berechnung + Datenmodell

## Datenfluss
Odoo → FastAPI → openLCA IPC → LCIA Ergebnis → FastAPI → Odoo

