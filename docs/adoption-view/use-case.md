# Use Case

## UC-01: Produktbewertung (Produkt → LCA → Felder in Odoo)
Ziel: Für ein Produkt werden GWP und weitere Impact-Kategorien berechnet und in Odoo gespeichert.

### Eingaben (Odoo)
- Produktgewicht (kg) auf Produkt oder Variante
- Flow-UUID je Komponente (Odoo Feld: **x_studio_lca_flow_uuid**)
- Optional: BoM (Stückliste). Wenn keine BoM vorhanden ist, kann ein 1-Zeilen-Request aus dem Produkt selbst erstellt werden.

### Ausgaben (Odoo)
- x_lca_gwp_per_kg (float)
- x_lca_gwp_per_unit (float)
- x_studio_lca_impact_tabelle (HTML)

---

## UC-02: Fertigungsauftrag (MO-Menge → Gesamtimpact)
Ziel: Beim Fertigungsauftrag wird der Gesamtimpact für die produzierte Menge ausgegeben.

### Eingaben
- MO-Menge 
- Produktbezogene Impacts

### Berechnungslogik
- Gesamtwert je Impact = Impact pro Stück × MO Menge
- Zusätzlich kann pro kg skaliert werden, falls benötigt.

|Ausgaben (mrp.production)   |                                    |
| -------------------------  | ---------------------------------- |
| Gesamt-CO₂ (GWP)           | **x_studio_total_co**              |
| Impact-Tabelle             | **x_studio_lca_impact_ergebnisse** |

