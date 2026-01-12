# Semantic Models (Begriffe & Mapping)

## Begriffe
- Flow (openLCA): Referenz auf einen Stoff/Material/Produktfluss aus der LCA-Datenbank.
- Flow UUID: Eindeutige ID des Flows in der Datenbank.
- Prozess (openLCA): Modelliert Inputs/Outputs (z.B. Komponenten der BoM).
- Produktsystem (openLCA): Verknüpft Prozesse/Provider für eine vollständige LCIA Berechnung.
- Impact-Kategorie: Ergebnisdimension (z.B. climate change, acidification etc.)
- Methode: Sammlung von Impact-Kategorien/Faktoren

## Mapping Odoo ↔ LCA
### Odoo
- product.template / product.product → Produkt / Variante
- mrp.bom / mrp.bom.line → Stückliste
- mrp.production → Fertigungsauftrag

### Felder
- Flow-UUID: **x_studio_lca_flow_uuid**
- GWP/kg: **x_lca_gwp_per_kg**
- GWP/Stück: **x_lca_gwp_per_unit**
- Produkt-Impact Tabelle: **x_studio_lca_impact_tabelle**
- MO Gesamt-CO₂: **x_studio_total_co**
- MO Impact Tabelle: **x_studio_lca_impact_ergebnisse**

## Einheiten & Skalierung
- Gewichte werden in Odoo typischerweise in kg gepflegt.
- Bei Requests an OpenLCa werden Gewichte, die in gramm angegeben sind, in kilogramm umgerechnet.
- Output:
  - pro kg: normiert auf 1 kg Endprodukt
  - pro Stück: normiert auf 1 Stück
  - MO-Gesamt: pro Stück × MO Menge