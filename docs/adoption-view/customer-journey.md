# Customer Journey

Diese Journey beschreibt die Nutzung aus Sicht eines Anwenders (z.B. Einkauf, Arbeitsvorbereitung, Nachhaltigkeit).

## 1) Stammdatenpflege
1. Produkt/Komponenten in Odoo anlegen.
2. Gewicht pflegen.
3. Flow-UUID pflegen:
   - Feldname: **x_studio_lca_flow_uuid**

![Produkt mit Flow-UUID](../assets/screenshots/odoo_product_flow_uuid.png)



## 2) Stückliste (BoM)
1. Für das Endprodukt BoM erstellen.
2. Variantenartikel: sicherstellen, dass Gewicht und UUID der genutzten Variante verfügbar sind.

![Stückliste in Odoo](../assets/screenshots/odoo_bom.png)

## 3) LCA Berechnung auslösen
Manuelles Auslösen per Skript (odoo_lca_sync.py)




## 4) Ergebnisse im Produkt prüfen
- x_lca_gwp_per_kg
- x_lca_gwp_per_unit
- x_studio_lca_impact_tabelle

## 5) Fertigungsauftrag erstellen und Gesamtwerte prüfen
- MO: x_studio_total_co
- MO Tabelle: x_studio_lca_impact_ergebnisse

![MO mit CO₂-Gesamtwert](../assets/screenshots/odoo_mo_total_co2.png)
