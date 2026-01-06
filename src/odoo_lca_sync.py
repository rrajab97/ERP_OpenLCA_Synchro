import xmlrpc.client
import requests

# ----------------------------------------------------------
# Odoo-Verbindungsdaten
# ----------------------------------------------------------
ODOO_URL = "https://upb-rr.odoo.com"
ODOO_DB = "upb-rr"
ODOO_USER = "raminrajab2@googlemail.com"
ODOO_PASSWORD = "1efd40ff8cf4f5e5f396de6a52b4bcd6211ac112"

#  Modus:
# "single"       -> einzelnes Produkt per Name
# "all_products" -> alle Produkte (mit BoM oder Einzelartikel)
# "mos"          -> Fertigungsaufträge
PROCESS_MODE = "mos"
PRODUCT_NAME = "Kugelschreiber"  # nur für "single"

# Technischer Name des Feldes mit der Flow-UUID
LCA_FLOW_FIELD = "x_studio_lca_flow_uuid"

# Ziel-Felder im Produkt (float)
GWP_PER_KG_FIELD = "x_lca_gwp_per_kg"
GWP_PER_UNIT_FIELD = "x_lca_gwp_per_unit"

# HTML-Tabelle mit allen Impact-Kategorien
IMPACT_TABLE_FIELD = "x_studio_lca_impact_tabelle"

# Felder auf dem Fertigungsauftrag
MO_TOTAL_CO2_FIELD = "x_studio_total_co"                  # float
MO_IMPACT_TABLE_FIELD = "x_studio_lca_impact_ergebnisse"  # HTML

# URL des FastAPI-LCA-Services
LCA_API_URL = "http://localhost:8000/lca/calc"


# ----------------------------------------------------------
# Verbindung zu Odoo herstellen
# ----------------------------------------------------------

def get_odoo_models():
    """Authentifiziert sich gegen Odoo und liefert (uid, models-Proxy)."""
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")

    info = common.version()
    print("Server-Version:", info)

    print(f"Versuche Login: db='{ODOO_DB}', user='{ODOO_USER}'")
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    print("Erhaltenes uid:", uid)

    if not uid:
        raise RuntimeError(
            "Authentifizierung bei Odoo fehlgeschlagen. "
            "Bitte DB-Name, Benutzer und API-Key prüfen."
        )

    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
    return uid, models


# ----------------------------------------------------------
# Hilfsfunktionen für Odoo-Daten
# ----------------------------------------------------------

def get_bom_for_product(models, uid, product_tmpl_id):
    """
    Holt die BoM für ein Produkt-Template und
    baut eine Liste von Dicts mit name, mass_g, flow_uuid.

    Flow-UUID + Gewicht können auf Template (product.template)
    oder Variante (product.product) liegen.
    """
    bom_ids = models.execute_kw(
        ODOO_DB,
        uid,
        ODOO_PASSWORD,
        "mrp.bom",
        "search",
        [[["product_tmpl_id", "=", product_tmpl_id], ["type", "=", "normal"]]],
        {"limit": 1},
    )
    if not bom_ids:
        print(f"   ⚠ Keine BoM für Produkt-Template {product_tmpl_id} gefunden.")
        return None

    boms = models.execute_kw(
        ODOO_DB,
        uid,
        ODOO_PASSWORD,
        "mrp.bom",
        "read",
        [bom_ids],
        {"fields": ["bom_line_ids"]},
    )
    line_ids = boms[0]["bom_line_ids"]

    if not line_ids:
        print("   ⚠ BoM hat keine Zeilen.")
        return None

    lines = models.execute_kw(
        ODOO_DB,
        uid,
        ODOO_PASSWORD,
        "mrp.bom.line",
        "read",
        [line_ids],
        {"fields": ["product_id", "product_tmpl_id", "product_qty"]},
    )

    bom_items = []

    for line in lines:
        qty = line["product_qty"]
        tmpl_id = None
        variant_id = None

        if line.get("product_tmpl_id"):
            tmpl_id = line["product_tmpl_id"][0]
        if line.get("product_id"):
            variant_id = line["product_id"][0]

        tmpl = None
        variant = None

        # Template lesen
        if tmpl_id:
            tmpl = models.execute_kw(
                ODOO_DB,
                uid,
                ODOO_PASSWORD,
                "product.template",
                "read",
                [[tmpl_id]],
                {"fields": ["name", "weight", LCA_FLOW_FIELD]},
            )[0]

        # Variante lesen
        if variant_id:
            variant = models.execute_kw(
                ODOO_DB,
                uid,
                ODOO_PASSWORD,
                "product.product",
                "read",
                [[variant_id]],
                {"fields": ["display_name", "weight", LCA_FLOW_FIELD]},
            )[0]

        # Name bestimmen
        if tmpl and tmpl.get("name"):
            name = tmpl["name"]
        elif variant and variant.get("display_name"):
            name = variant["display_name"]
        else:
            name = f"Produkt {tmpl_id or variant_id}"

        # Flow-UUID: Template bevorzugt, Variante als Fallback
        flow_uuid = None
        if tmpl and tmpl.get(LCA_FLOW_FIELD):
            flow_uuid = tmpl[LCA_FLOW_FIELD]
        if not flow_uuid and variant and variant.get(LCA_FLOW_FIELD):
            flow_uuid = variant[LCA_FLOW_FIELD]

        # Gewicht: Template-Basis, Variante überschreibt, wenn vorhanden
        weight_kg = 0.0
        if tmpl and tmpl.get("weight"):
            weight_kg = tmpl["weight"]
        if variant and variant.get("weight"):
            weight_kg = variant["weight"] or weight_kg

        if not flow_uuid:
            print(f"   ⚠ Komponente '{name}' hat keine {LCA_FLOW_FIELD} – wird übersprungen.")
            continue
        if not weight_kg or weight_kg <= 0:
            print(f"   ⚠ Komponente '{name}' hat kein gültiges Gewicht – wird übersprungen.")
            continue

        mass_g = weight_kg * qty * 1000.0  # kg → g

        bom_items.append(
            {
                "name": name,
                "mass_g": mass_g,
                "flow_uuid": flow_uuid,
            }
        )

    if not bom_items:
        print("   ⚠ Keine gültigen BoM-Komponenten für LCA gefunden.")
        return None

    return bom_items


# ----------------------------------------------------------
# LCA-Berechnung über FastAPI-Service (lca_api)
# ----------------------------------------------------------

def call_lca_service(product_name: str, bom_items):
    """
    Ruft den FastAPI-LCA-Service auf.
    Erwartet: gwp_per_kg, gwp_per_unit, unit, impact_table_html.
    """
    payload = {
        "product_name": product_name,
        "bom": bom_items,
    }

    print(f"   ▶ Rufe LCA-Service auf: {LCA_API_URL}")
    resp = requests.post(LCA_API_URL, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()

def build_mo_impact_table_from_impacts(impacts, qty: float) -> str:
    """
    Baut eine HTML-Tabelle für den Fertigungsauftrag:

        Kategorie | Einheit | Gesamtwert Auftrag

    Gesamtwert Auftrag = per_unit (pro Stück) * qty
    """
    if not impacts:
        return ""

    lines = []
    lines.append("<table border='1' cellspacing='0' cellpadding='3'>")
    lines.append(
        "<tr>"
        "<th>Kategorie</th>"
        "<th>Einheit</th>"
        "<th>Gesamtwert Auftrag</th>"
        "</tr>"
    )

    for imp in impacts:
        cat = imp.get("category", "")
        unit = imp.get("unit", "")
        per_unit = float(imp.get("per_unit", 0.0) or 0.0)
        total = per_unit * qty
        lines.append(
            "<tr>"
            f"<td>{cat}</td>"
            f"<td>{unit}</td>"
            f"<td>{total:.6g}</td>"
            "</tr>"
        )

    lines.append("</table>")
    return "\n".join(lines)

# ----------------------------------------------------------
# Modus 1: einzelnes Produkt
# ----------------------------------------------------------

def sync_lca_for_product_by_name(product_name: str):
    uid, models = get_odoo_models()

    ids = models.execute_kw(
        ODOO_DB,
        uid,
        ODOO_PASSWORD,
        "product.template",
        "search",
        [[["name", "=", product_name]]],
        {"limit": 1},
    )
    if not ids:
        print(f"⚠ Kein product.template mit Name '{product_name}' gefunden.")
        return

    product_tmpl_id = ids[0]

    product = models.execute_kw(
        ODOO_DB,
        uid,
        ODOO_PASSWORD,
        "product.template",
        "read",
        [[product_tmpl_id]],
        {"fields": ["name"]},
    )[0]
    product_name_read = product["name"]

    print(f"=== Produkt '{product_name_read}' (ID {product_tmpl_id}) ===")

    bom = get_bom_for_product(models, uid, product_tmpl_id)
    if not bom:
        print("   ⚠ Keine BoM gefunden oder BoM leer – Abbruch.")
        return

    result = call_lca_service(product_name_read, bom)

    gwp_per_kg = result.get("gwp_per_kg")
    gwp_per_unit = result.get("gwp_per_unit")
    unit = result.get("unit", "kg CO2 eq")
    impact_html = result.get("impact_table_html")

    if gwp_per_kg is None or gwp_per_unit is None:
        print("   ⚠ LCA-Service hat keine gwp_per_kg / gwp_per_unit geliefert:", result)
        return

    print("   ✅ LCA-Ergebnis:")
    print("      GWP pro kg   :", gwp_per_kg, unit)
    print("      GWP pro Stück:", gwp_per_unit, unit)

    vals = {
        GWP_PER_KG_FIELD: gwp_per_kg,
        GWP_PER_UNIT_FIELD: gwp_per_unit,
    }
    if impact_html:
        vals[IMPACT_TABLE_FIELD] = impact_html

    models.execute_kw(
        ODOO_DB,
        uid,
        ODOO_PASSWORD,
        "product.template",
        "write",
        [[product_tmpl_id], vals],
    )

    print("   ✅ CO₂-Werte und Impact-Tabelle im Produkt aktualisiert.")


# ----------------------------------------------------------
# Modus 2: alle Produkte (BoM oder Einzelartikel)
# ----------------------------------------------------------

def sync_lca_for_all_products():
    uid, models = get_odoo_models()

    # Alle physischen Produkte (Lagermaterial + Verbrauchsmaterial)
    tmpl_ids = models.execute_kw(
        ODOO_DB,
        uid,
        ODOO_PASSWORD,
        "product.template",
        "search",
        [[["type", "in", ["product", "consu"]]]],
    )
    if not tmpl_ids:
        print("⚠ Keine physischen Produkte gefunden – nichts zu tun.")
        return

    print(f"Gefundene Produkt-Templates: {tmpl_ids}")

    for product_tmpl_id in tmpl_ids:
        # Basisinfos vom Template holen
        product = models.execute_kw(
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            "product.template",
            "read",
            [[product_tmpl_id]],
            {"fields": ["name", "weight", LCA_FLOW_FIELD]},
        )[0]
        product_name = product.get("name", f"Tmpl {product_tmpl_id}")
        tmpl_weight_kg = product.get("weight") or 0.0
        tmpl_flow_uuid = product.get(LCA_FLOW_FIELD)

        print(f"\n=== Produkt '{product_name}' (ID {product_tmpl_id}) ===")

        # 1) Versuch: BoM-basiert
        bom = get_bom_for_product(models, uid, product_tmpl_id)

        if bom:
            print("   → benutze BoM-basierte LCA-Berechnung.")
            bom_items = bom

        else:
            print("   ⚠ Keine BoM für Produkt-Template", product_tmpl_id, "gefunden.")
            print("   ℹ prüfe, ob Gewicht + Flow direkt am Produkt oder in Varianten gepflegt sind.")

            flow_uuid = tmpl_flow_uuid
            weight_kg = tmpl_weight_kg

            # Varianten durchsuchen, falls nötig
            if (not flow_uuid or weight_kg <= 0):
                variant_ids = models.execute_kw(
                    ODOO_DB,
                    uid,
                    ODOO_PASSWORD,
                    "product.product",
                    "search",
                    [[["product_tmpl_id", "=", product_tmpl_id]]],
                )

                if variant_ids:
                    variants = models.execute_kw(
                        ODOO_DB,
                        uid,
                        ODOO_PASSWORD,
                        "product.product",
                        "read",
                        [variant_ids],
                        {"fields": ["display_name", "weight", LCA_FLOW_FIELD]},
                    )

                    for v in variants:
                        v_name = v.get("display_name")
                        v_weight = v.get("weight") or 0.0
                        v_flow = v.get(LCA_FLOW_FIELD)

                        if v_flow and v_weight > 0:
                            flow_uuid = v_flow
                            weight_kg = v_weight
                            print(f"   → benutze Werte aus Variante '{v_name}' (weight={weight_kg}, flow={flow_uuid}).")
                            break

            # 1-Zeilen-BoM aus Produkt/Variante, falls möglich
            if flow_uuid and weight_kg > 0:
                mass_g = weight_kg * 1000.0
                bom_items = [{
                    "name": product_name,
                    "mass_g": mass_g,
                    "flow_uuid": flow_uuid,
                }]
                print(f"   → benutze 1-Zeilen-BoM aus Produkt/Variante (mass_g={mass_g}).")
            else:
                print("   ⚠ Weder BoM noch Gewicht + Flow-UUID am Produkt oder in Varianten – übersprungen.")
                continue

        # LCA-Berechnung
        try:
            result = call_lca_service(product_name, bom_items)
        except Exception as e:
            print(f"   ⚠ Fehler bei LCA-Berechnung: {e}")
            continue

        gwp_per_kg = result.get("gwp_per_kg")
        gwp_per_unit = result.get("gwp_per_unit")
        unit = result.get("unit", "kg CO2 eq")
        impact_html = result.get("impact_table_html")

        if gwp_per_kg is None or gwp_per_unit is None:
            print("   ⚠ LCA-Service hat keine gwp_per_kg / gwp_per_unit geliefert:", result)
            continue

        print("   ✅ LCA-Ergebnis:")
        print("      GWP pro kg   :", gwp_per_kg, unit)
        print("      GWP pro Stück:", gwp_per_unit, unit)

        vals = {
            GWP_PER_KG_FIELD: gwp_per_kg,
            GWP_PER_UNIT_FIELD: gwp_per_unit,
        }
        if impact_html:
            vals[IMPACT_TABLE_FIELD] = impact_html

        try:
            models.execute_kw(
                ODOO_DB,
                uid,
                ODOO_PASSWORD,
                "product.template",
                "write",
                [[product_tmpl_id], vals],
            )
            print("   ✅ CO₂-Werte und Impact-Tabelle im Produkt aktualisiert.")
        except Exception as e:
            print(f"   ⚠ Fehler beim Schreiben nach Odoo: {e}")


# ----------------------------------------------------------
# Modus 3: Fertigungsaufträge (Total CO₂ + Tabelle)
# ----------------------------------------------------------

def sync_lca_for_mos():
    """
    Geht alle Fertigungsaufträge (mrp.production) durch,
    berechnet Gesamt-CO₂ aus GWP pro Stück * Menge
    und schreibt:

    - Gesamt-CO₂ in MO_TOTAL_CO2_FIELD
    - Impact-Tabelle mit *Gesamtwerten je Auftrag* in MO_IMPACT_TABLE_FIELD,
      aufgebaut aus der 'impacts'-Liste des LCA-Services (ohne HTML-Parsing).
    """
    uid, models = get_odoo_models()

    mo_ids = models.execute_kw(
        ODOO_DB,
        uid,
        ODOO_PASSWORD,
        "mrp.production",
        "search",
        [[
            ["state", "in", ["confirmed", "in_progress", "to_close", "done"]],
            [MO_TOTAL_CO2_FIELD, "=", False],  # nur MOs ohne CO₂-Wert
        ]],
    )
    if not mo_ids:
        print("⚠ Keine passenden Fertigungsaufträge gefunden.")
        return

    mos = models.execute_kw(
        ODOO_DB,
        uid,
        ODOO_PASSWORD,
        "mrp.production",
        "read",
        [mo_ids],
        {"fields": ["name", "product_id", "product_qty", "product_uom_id"]},
    )

    for mo in mos:
        mo_id = mo["id"]
        mo_name = mo["name"]
        qty = mo["product_qty"]

        if not mo.get("product_id"):
            print(f"=== MO {mo_name} (ID {mo_id}) ohne Produkt – übersprungen.")
            continue

        variant_id = mo["product_id"][0]

        variant = models.execute_kw(
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            "product.product",
            "read",
            [[variant_id]],
            {"fields": ["product_tmpl_id"]},
        )[0]

        if not variant.get("product_tmpl_id"):
            print(f"=== MO {mo_name}: keine product_tmpl_id gefunden – übersprungen.")
            continue

        tmpl_id = variant["product_tmpl_id"][0]

        # Produktwerte lesen (für GWP pro Stück)
        product = models.execute_kw(
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            "product.template",
            "read",
            [[tmpl_id]],
            {"fields": ["name", GWP_PER_UNIT_FIELD]},
        )[0]

        product_name = product.get("name", f"Tmpl {tmpl_id}")
        gwp_per_unit = product.get(GWP_PER_UNIT_FIELD) or 0.0

        print(f"\n=== MO {mo_name} (ID {mo_id}) für Produkt '{product_name}' ===")
        print(f"   Menge im Auftrag: {qty}")

        if gwp_per_unit <= 0:
            print(f"   ⚠ Produkt hat keinen gültigen Wert in {GWP_PER_UNIT_FIELD} – MO wird übersprungen.")
            continue

        total_co2 = gwp_per_unit * qty

        print(f"   GWP pro Stück: {gwp_per_unit} kg CO2 eq")
        print(f"   Gesamt-CO2 für Auftrag: {total_co2} kg CO2 eq")

        # BoM für das Produkt holen (oder Fallback 1-Zeilen-BoM)
        bom_items = get_bom_for_product(models, uid, tmpl_id)
        if not bom_items:
            print("   ⚠ Keine BoM für dieses Produkt gefunden – Impact-Tabelle kann nicht erstellt werden.")
            vals = {MO_TOTAL_CO2_FIELD: total_co2}
            try:
                models.execute_kw(
                    ODOO_DB,
                    uid,
                    ODOO_PASSWORD,
                    "mrp.production",
                    "write",
                    [[mo_id], vals],
                )
                print("   ✅ Gesamt-CO2 im Fertigungsauftrag aktualisiert (ohne Tabelle).")
            except Exception as e:
                print(f"   ⚠ Fehler beim Schreiben des Gesamt-CO2: {e}")
            continue

        # LCA-Service für das Produkt (1 Stück) aufrufen, um impacts zu erhalten
        try:
            lca_result = call_lca_service(product_name, bom_items)
        except Exception as e:
            print(f"   ⚠ Fehler bei LCA-Berechnung für MO-Tabelle: {e}")
            vals = {MO_TOTAL_CO2_FIELD: total_co2}
            try:
                models.execute_kw(
                    ODOO_DB,
                    uid,
                    ODOO_PASSWORD,
                    "mrp.production",
                    "write",
                    [[mo_id], vals],
                )
            except Exception as e2:
                print(f"   ⚠ Fehler beim Schreiben des Gesamt-CO2: {e2}")
            continue

        impacts = lca_result.get("impacts") or []
        mo_table_html = build_mo_impact_table_from_impacts(impacts, qty)

        vals = {
            MO_TOTAL_CO2_FIELD: total_co2,
        }
        if mo_table_html:
            vals[MO_IMPACT_TABLE_FIELD] = mo_table_html

        try:
            models.execute_kw(
                ODOO_DB,
                uid,
                ODOO_PASSWORD,
                "mrp.production",
                "write",
                [[mo_id], vals],
            )
            print("   ✅ Gesamt-CO2 und Impact-Tabelle im Fertigungsauftrag aktualisiert.")
        except Exception as e:
            print(f"   ⚠ Fehler beim Schreiben des Gesamt-CO2 / Tabelle: {e}")


# ----------------------------------------------------------
# Einstiegspunkt
# ----------------------------------------------------------

if __name__ == "__main__":
    if PROCESS_MODE == "single":
        sync_lca_for_product_by_name(PRODUCT_NAME)
    elif PROCESS_MODE == "all_products":
        sync_lca_for_all_products()
    elif PROCESS_MODE == "mos":
        sync_lca_for_mos()
    else:
        print(f"Unbekannter PROCESS_MODE: {PROCESS_MODE}")
