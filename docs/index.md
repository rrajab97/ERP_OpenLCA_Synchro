---
hide:
  - navigation
---
# ERP – openLCA Synchronisation Kit

Dieses Repository dokumentiert die Integration von Odoo (ERP) mit openLCA (LCA-Software) zur automatisierten Berechnung und Ausgabe von Umweltindikatoren (GWP/CO₂-Äquivalente) für Produkte und Fertigungsaufträge (Manufacturing Orders, MO).

Ziel ist eine wiederverwendbare, praxistaugliche Lösung, bei der LCA-Daten aus einer LCA-Datenbank über openLCA berechnet und in Odoo strukturiert abgelegt werden.

## Was liefert die Integration?
### Auf Produktebene (Odoo Produkt)
| Wert                                                     | Feld                                                        |
| -------------------------------------------------------- | ----------------------------------------------------------- |
| GWP pro kg                                               | **x_lca_gwp_per_kg**                                        |
| GWP pro Stück                                            | **x_lca_gwp_per_unit**                                      |
| Impact-Tabelle (HTML)&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;  | **x_studio_lca_impact_tabelle** &nbsp; &nbsp; &nbsp; &nbsp; |


### Auf Fertigungsauftragsebene
| Wert                       | Feld                               |
| -------------------------  | ---------------------------------- |
| Gesamt-CO₂ für den Auftrag | **x_studio_total_co**              |
| Impact-Tabelle Gesamtwerte | **x_studio_lca_impact_ergebnisse** |


## Quickstart
1. openLCA starten und IPC-Server aktivieren (Port 8080).
2. LCA-Datenbank in openLCA importieren und öffnen.
3. Python Dependencies installieren (Operation View → Configuration Guide).
4. FastAPI starten:
   ```bash
   python -m uvicorn src.lca_api:app --reload --port 8000
   ```
