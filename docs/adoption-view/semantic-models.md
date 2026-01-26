# Semantic Models (Begriffe & Mapping)

| Begriife                          |                                                                       |
|---------------------------------- | --------------------------------------------------------------------- |
| Flow (openLCA)                    | Referenz auf einen Stoff/Material/Produktfluss aus der LCA-Datenbank  |
| Flow UUID                         | Eindeutige ID des Flows in der Datenbank                              |
| Prozess (openLCA)                 | Modelliert Inputs/Outputs (z.B. Komponenten der BoM)                  |
| Produktsystem (openLCA)           | Verknüpft Prozesse/Provider für eine vollständige LCIA Berechnung     |
| Impact-Kategorie                  | Ergebnisdimension (z.B. climate change, acidification etc.)           |
| Methode                           | Sammlung von Impact-Kategorien/Faktoren                               |

## Mapping Odoo ↔ LCA

| Odoo                              |                                      |
|---------------------------------- | ------------------------------------ |
|product.template                   | &nbsp; Produkt                              |
|product.product                    | &nbsp; Variante          &nbsp;&nbsp;&nbsp; |
|mrp.bom / mrp.bom.line             | &nbsp; Stückliste        &nbsp;&nbsp;&nbsp; |
|mrp.production                     | &nbsp; Fertigungsauftrag               &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; |



| Felder                            |                                           |
|---------------------------------- | ----------------------------------------- |
| Flow-UUID                         | &nbsp; &nbsp; **x_studio_lca_flow_uuid**         |
| GWP/kg                            | &nbsp; &nbsp; **x_lca_gwp_per_kg**               |
| GWP/Stück                         | &nbsp; &nbsp; **x_lca_gwp_per_unit**             |
| Produkt-Impact Tabelle            | &nbsp; &nbsp; **x_studio_lca_impact_tabelle**    |
| MO Gesamt-CO₂                     | &nbsp; &nbsp; **x_studio_total_co**              |
| MO Impact Tabelle                 | &nbsp; &nbsp; **x_studio_lca_impact_ergebnisse** |

## Einheiten & Skalierung
- Gewichte werden in Odoo typischerweise in kg gepflegt.
- Bei Requests an OpenLCa werden Gewichte, die in gramm angegeben sind, in kilogramm umgerechnet.
- Output: <BR>
 &nbsp;&nbsp; - pro kg: normiert auf 1 kg Endprodukt <BR>
 &nbsp;&nbsp; - pro Stück: normiert auf 1 Stück <BR>
 &nbsp;&nbsp; - MO-Gesamt: pro Stück × MO Menge <BR>