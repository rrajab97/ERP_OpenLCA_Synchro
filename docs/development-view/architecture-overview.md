# Architecture Overview

## Komponenten
- **Odoo (SaaS, Browser):** Datenquelle (Produkte, Varianten, BoMs, MOs)
- **FastAPI Service:** REST-API als Integrationsschicht
- **openLCA IPC:** Berechnungsengine (Prozess/Produktsystem/LCIA)
- **LCA Datenbank:** [idemat_2023](https://www.openlca.org/idemat-2023-available-for-openlca/)

## Warum Microservice statt direkter Odoo-Logik?
- Odoo SaaS erlaubt keine freien Python-Imports/Requests in Server Actions.
- openLCA IPC benötigt lokalen Zugriff (Port 8080).
- Microservice kapselt Berechnung + Datenmodell

## Datenfluss

``` mermaid
graph LR
  A[Odoo] --> B[FastAPI];
  B --> C[openLCA IPC];
  C --> D[LCIA Ergebnis];
  D --> B;
  B --> A;

```
