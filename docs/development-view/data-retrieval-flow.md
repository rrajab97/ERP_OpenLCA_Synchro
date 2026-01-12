# Data Retrieval Flow (Sequenz)

## Sequenz
1. Odoo XML-RPC: Produkt + BoM + Komponenten lesen
2. FastAPI: Request validieren und normieren
3. openLCA IPC:
   - Flows anhand UUID auflösen
   - Prozess + Produktsystem erstellen/aktualisieren
   - LCIA mit gewählter Methode berechnen
4. FastAPI: Ergebnisse aggregieren und als JSON + HTML zurückgeben
5. Odoo XML-RPC: Felder in Produkt/MO schreiben

> Diagramm-Platzhalter:
- *docs/assets/diagrams/sequence.png*

## Variantenlogik
Odoo nutzt:
- Template (product.template) für Stammdaten
- Variante (product.product) für konkrete Ausprägungen

Wenn Flow-UUID/Gewicht nur auf Variante gepflegt ist, muss die BoM-Komponente als Variante ausgelesen und dort gelesen werden.
