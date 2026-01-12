# Introduction

## Ausgangslage
Unternehmen benötigen zunehmend belastbare Umweltkennzahlen entlang ihrer Produkte und Prozesse. ERP-Systeme enthalten dafür relevante Kerndaten (Material, Stücklisten, Fertigungsaufträge), verfügen aber typischerweise nicht über eine native LCA-Rechenlogik oder valide Impact-Faktoren.

## Ziel
Ziel ist eine Integration, bei der Umweltwirkungen (z.B. GWP/CO₂-eq) automatisiert aus den ERP-Daten berechnet und in Odoo in Echtzeit-naher Form angezeigt werden. Als Berechnungsengine dient openLCA mit einer LCA-Datenbank.

## Kernergebnis
- Produktdaten (Gewicht, Stückliste, Flow-UUID) werden aus Odoo ausgelesen.
- Daraus wird in openLCA ein Prozess + Produktsystem erzeugt/aktualisiert.
- openLCA berechnet LCIA/Impacts (Methode + Impact-Kategorien).
- Ergebnisse werden zurück in Odoo geschrieben:
  - x_lca_gwp_per_kg
  - x_lca_gwp_per_unit
  - x_studio_lca_impact_tabelle 
  - MO: x_studio_total_co, x_studio_lca_impact_ergebnisse

## Abgrenzung
- Für valide Ergebnisse müssen Gewichte und Flow-UUIDs gepflegt sein.
- Für Variantenartikel können Flow-UUID/Gewicht auf Varianten statt übergeordneten Produkten gepflegt werden.
- Die Integration setzt openLCA lokal auf einem Server mit IPC Zugriff voraus.
