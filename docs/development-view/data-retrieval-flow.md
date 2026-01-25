# Data Retrieval Flow

## Sequenz
1. Skript (odoo_lca_sync) startet Prozess
2. FastAPI: Alle Anfragen werden validiert, normiert und weitergeleitet
3. Odoo XML-RPC: Produkt + BoM + Komponenten auslesen und zurückgeben
4. FastAPI: Request mit Produktdaten an openLCA schicken
5. openLCA IPC: <BR>
  &nbsp;&nbsp; a. Flows anhand UUID auflösen <BR>
  &nbsp;&nbsp; b. Prozess + Produktsystem erstellen/aktualisieren <BR>
  &nbsp;&nbsp; c. LCIA mit gewählter Methode berechnen <BR>
6. FastAPI: Ergebnisse aggregieren und als JSON + HTML zurückgeben
7. Odoo XML-RPC: Felder in Produkt/MO schreiben

``` mermaid
sequenceDiagram
  autonumber

  FastAPI->>Odoo: Anfrage Produkt, BoM, Komponente
  Odoo->>Odoo: UUIDs zur Anfrage suchen
  Odoo->>FastAPI: Anfrage mit UUIDs
  FastAPI->>openLCA: Anfrage weiterleiten
  openLCA->>openLCA: Prozess & Produktsystem zu UUIDs erstellen/aktualisieren
  openLCA->>openLCA: Starte LCIA
  openLCA->>FastAPI: LCIA-Daten zurückgeben
  FastAPI->>Odoo: Daten weiterleiten
  Odoo->>Odoo: LCIA-Daten eintragen
```

## Variantenlogik
Odoo nutzt:
1. Template (product.template) für Stammdaten
2. Variante (product.product) für konkrete Ausprägungen

Wenn Flow-UUID/Gewicht nur auf Variante gepflegt ist, muss die BoM-Komponente als Variante ausgelesen und dort gelesen werden.
