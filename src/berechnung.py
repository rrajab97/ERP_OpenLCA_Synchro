import json
import olca_ipc as ipc
import olca_schema as o

# Port des openLCA-IPC-Servers
PORT = 8080

# Exakte Impact-Kategorie
PREFERRED_IMPACT_CATEGORY_NAME = "Climate change - fossil"

# Impact-Methode
LCIA_METHOD_NAME = "EN 15804 +A2 Method"


# ----------------------------------------------------------
# Hilfsfunktion: Prozess aus BoM 
# ----------------------------------------------------------

def ensure_process_from_bom(
    client: ipc.Client,
    product_name: str,
    bom: list[dict],
) -> o.Ref:
    """
    Sucht den korrekten OpenLCA Prozess für das Produkt.
    Wenn er noch nicht existiert, wird er aus der BoM erzeugt.

    BoM-Einträge müssen mindestens enthalten:
      - "name"
      - "flow_uuid"
      - "mass_g" oder "mass_kg"

    """
    process_name = f"LCA Prozess: {product_name}"

    # 1) Prozess existiert schon
    proc_ref = client.get_descriptor(o.Process, name=process_name)
    if proc_ref is not None:
        return proc_ref

    # 2) BoM normalisieren (alle Massen in kg)
    norm_bom: list[dict] = []
    for item in bom:
        if "mass_kg" in item:
            mass_kg = float(item["mass_kg"])
        elif "mass_g" in item:
            mass_kg = float(item["mass_g"]) / 1000.0
        else:
            raise ValueError(f"BoM-Eintrag {item} hat weder mass_g noch mass_kg")
        norm_bom.append(
            {
                "name": item["name"],
                "mass_kg": mass_kg,
                "flow_uuid": item["flow_uuid"],
            }
        )

    # 3) FlowProperty für den Produkt-Output anlegen
    units = o.new_unit_group("ERP mass units", "kg")
    kg_unit = units.units[0]
    mass_fp = o.new_flow_property("ERP product mass", units)

    # Produktfluss für das Produkt
    product_flow = o.new_product(product_name, mass_fp)

    # 4) Prozess anlegen
    process = o.new_process(process_name)
    process.exchanges = process.exchanges or []

    # Gesamtmasse der BoM
    total_mass_kg = sum(it["mass_kg"] for it in norm_bom)

    ref_out = o.Exchange()
    ref_out.internal_id = 1
    ref_out.is_input = False
    ref_out.is_quantitative_reference = True
    ref_out.amount = total_mass_kg
    ref_out.flow = product_flow
    ref_out.flow_property = mass_fp
    ref_out.unit = kg_unit
    process.exchanges.append(ref_out)

    # 5) Inputs aus der BoM
    next_id = 2
    for item in norm_bom:
        comp_name = item["name"]
        mass_kg = item["mass_kg"]
        flow_uuid = item["flow_uuid"]

        comp_flow = client.get(o.Flow, flow_uuid)
        if comp_flow is None:
            raise RuntimeError(f"Flow {flow_uuid} ({comp_name}) nicht gefunden")

        if not comp_flow.flow_properties:
            raise RuntimeError(f"Flow '{comp_flow.name}' hat keine flow_properties")

        # Referenz-FlowPropertyFactor bestimmen
        fp_factor = None
        for f in comp_flow.flow_properties:
            if getattr(f, "is_ref_flow_property", False):
                fp_factor = f
                break
        if fp_factor is None:
            fp_factor = comp_flow.flow_properties[0]

        flow_prop_ref = fp_factor.flow_property

        # FlowProperty und UnitGroup laden
        flow_prop = client.get(o.FlowProperty, flow_prop_ref.id)
        ug_ref = flow_prop.unit_group
        unit_group = client.get(o.UnitGroup, ug_ref.id)

        ref_unit = None
        for u in unit_group.units:
            if getattr(u, "is_ref_unit", False):
                ref_unit = u
                break
        if ref_unit is None:
            ref_unit = unit_group.units[0]

        ex = o.Exchange()
        ex.internal_id = next_id
        next_id += 1
        ex.is_input = True
        ex.is_quantitative_reference = False
        ex.amount = mass_kg
        ex.flow = comp_flow
        ex.flow_property = flow_prop_ref
        ex.unit = ref_unit
        process.exchanges.append(ex)

    # 6) Objekte speichern
    client.put(units)
    client.put(mass_fp)
    client.put(product_flow)
    client.put(process)

    # Descriptor holen und zurückgeben
    proc_ref = client.get_descriptor(o.Process, name=process_name)
    return proc_ref


# ----------------------------------------------------------
# Hilfsfunktion: Produktsystem 
# ----------------------------------------------------------

def ensure_product_system(
    client: ipc.Client,
    ps_name: str,
    proc_ref: o.Ref,
) -> o.Ref:
    """
    Erzeugt Produktsystem, falls noch nicht existent.

    Rückgabe: ProductSystem-Ref
    """
    # 1) Zuerst direkt nach ps_name suchen
    ps_ref = client.get_descriptor(o.ProductSystem, name=ps_name)
    if ps_ref is not None:
        return ps_ref

    # 2) Falls nicht vorhanden, versuchen, ein PS mit Prozessnamen zu finden
    proc_name = proc_ref.name
    ps_ref = client.get_descriptor(o.ProductSystem, name=proc_name)
    if ps_ref is not None:
        return ps_ref

    # 3) Wenn gar keins existiert → neu anlegen
    ps_ref = client.create_product_system(proc_ref)
    return ps_ref


# ----------------------------------------------------------
# High-Level-Funktion für FastAPI / Odoo
# ----------------------------------------------------------

def calculate_lca_for_product(
    product_name: str,
    bom: list[dict],
    port: int = PORT,
) -> dict:
    """
    Nimmt Produktnamen + BoM (Liste von Dicts mit mass_g/mass_kg, flow_uuid),
    berechnet GWP pro kg und pro Stück und erzeugt zusätzlich:

    - impact_table_html: HTML-Tabelle mit pro kg / pro Stück
    - impacts: Liste von Dicts pro Kategorie:
        {
          "category": ...,
          "unit": ...,
          "per_kg": ...,
          "per_unit": ...
        }

    Diese Liste wird für die Fertigungsaufträge genutzt, um dort
    die Gesamtwerte je Auftrag zu berechnen.
    """
    client = ipc.Client(port)

    # Gesamtmasse des Produkts (in kg) aus der BoM
    total_mass_kg = 0.0
    norm_bom: list[dict] = []
    for item in bom:
        if "mass_kg" in item:
            mass_kg = float(item["mass_kg"])
        elif "mass_g" in item:
            mass_kg = float(item["mass_g"]) / 1000.0
        else:
            raise ValueError(f"BoM-Eintrag {item} hat weder mass_g noch mass_kg")
        total_mass_kg += mass_kg
        norm_bom.append(
            {
                "name": item["name"],
                "mass_kg": mass_kg,
                "flow_uuid": item["flow_uuid"],
            }
        )

    if total_mass_kg <= 0:
        raise RuntimeError("Gesamtmasse der BoM ist 0 – keine LCA möglich.")

    # 1) Prozess aus BoM
    proc_ref = ensure_process_from_bom(client, product_name, norm_bom)

    # 2) Produktsystem  (Name = Prozessname, um Duplikate zu vermeiden)
    ps_name = proc_ref.name
    ps_ref = ensure_product_system(client, ps_name, proc_ref)

    # 3) Impact-Methode holen
    method_ref = client.get_descriptor(o.ImpactMethod, name=LCIA_METHOD_NAME)
    if method_ref is None:
        raise RuntimeError(f"Impact-Methode '{LCIA_METHOD_NAME}' nicht gefunden.")

    # 4) CalculationSetup vorbereiten
    setup = o.CalculationSetup()

    # calculation_type (optional)
    if hasattr(o, "CalculationType"):
        ct = getattr(o.CalculationType, "UPSTREAM_ANALYSIS", None)
        if ct is not None:
            setup.calculation_type = ct

    # Ziel: Produktsystem setzen – verschiedene Feldnamen möglich
    for field in ("calculation_target", "target", "product_system", "model"):
        if hasattr(setup, field):
            setattr(setup, field, ps_ref)
            break

    # Impact-Methode setzen
    if hasattr(setup, "impact_method"):
        setup.impact_method = method_ref
    elif hasattr(setup, "method"):
        setup.method = method_ref

    # Menge der Funktionseinheit (1 kg Produkt)
    setup.amount = 1.0

    # 5) Berechnung starten
    result = client.calculate(setup)
    if hasattr(result, "wait_until_ready"):
        result.wait_until_ready()

    # Fehlerzustand prüfen
    err_state = getattr(result, "error", None)
    if err_state and getattr(err_state, "error", None):
        raise RuntimeError(f"Fehler bei der Berechnung: {err_state.error}")

    # 6) Impact-Kategorien holen
    try:
        cats = result.get_impact_categories()
    except Exception as e:
        if hasattr(result, "dispose"):
            result.dispose()
        raise RuntimeError(f"get_impact_categories() fehlgeschlagen: {e}") from e

    if not cats:
        if hasattr(result, "dispose"):
            result.dispose()
        raise RuntimeError("Keine Impact-Kategorien im Result gefunden.")

    preferred_lower = (PREFERRED_IMPACT_CATEGORY_NAME or "").strip().lower()

    gwp_name = None
    gwp_unit = None
    gwp_per_kg = None

    # HTML-Tabelle + strukturierte Liste für alle Kategorien
    rows = []
    rows.append("<table border='1' cellspacing='0' cellpadding='3'>")
    rows.append(
        "<tr>"
        "<th>Kategorie</th>"
        "<th>Einheit</th>"
        "<th>Wert pro kg</th>"
        "<th>Wert pro Stück</th>"
        "</tr>"
    )

    impacts_data = []

    for cat in cats:
        cat_name = getattr(cat, "name", "")
        cat_unit = (
            getattr(cat, "ref_unit", None)
            or getattr(cat, "reference_unit", None)
            or getattr(cat, "unit", None)
            or ""
        )

        try:
            iv = result.get_total_impact_value_of(cat)
            per_kg = iv.amount
        except Exception as e:
            print(f"⚠ Konnte Wert für Kategorie '{cat_name}' nicht lesen: {e}")
            continue

        per_unit = per_kg * total_mass_kg  # 1 Stück

        rows.append(
            "<tr>"
            f"<td>{cat_name}</td>"
            f"<td>{cat_unit}</td>"
            f"<td>{per_kg:.6g}</td>"
            f"<td>{per_unit:.6g}</td>"
            "</tr>"
        )

        impacts_data.append(
            {
                "category": cat_name,
                "unit": cat_unit,
                "per_kg": per_kg,
                "per_unit": per_unit,
            }
        )

        # bevorzugte GWP-Kategorie merken
        if cat_name.strip().lower() == preferred_lower and gwp_per_kg is None:
            gwp_name = cat_name
            gwp_unit = cat_unit
            gwp_per_kg = per_kg

    rows.append("</table>")
    impact_table_html = "\n".join(rows)

    if gwp_per_kg is None:
        # Fallback: erste Kategorie verwenden
        first = impacts_data[0]
        gwp_name = first["category"]
        gwp_unit = first["unit"]
        gwp_per_kg = first["per_kg"]

    if hasattr(result, "dispose"):
        result.dispose()

    gwp_per_unit = gwp_per_kg * total_mass_kg

    return {
        "product_name": product_name,
        "impact_category": gwp_name,
        "gwp_per_kg": gwp_per_kg,
        "gwp_per_unit": gwp_per_unit,
        "unit": gwp_unit,
        "total_mass_kg": total_mass_kg,
        "impact_table_html": impact_table_html,
        "impacts": impacts_data,  # <-- wichtig für Fertigungsaufträge
    }


if __name__ == "__main__":
    # test
    demo_bom = [
        {
            "name": "Gehäuse (PP)",
            "mass_g": 4.0,
            "flow_uuid": "4f19f11d-7b3b-11dd-ad8b-0800200c9a66",
        },
        {
            "name": "Spitze (Stahl)",
            "mass_g": 0.3,
            "flow_uuid": "2126a80d-1cd0-46e4-8f30-341bd20a1d64",
        },
    ]

    res = calculate_lca_for_product("Kugelschreiber blau", demo_bom)
    print(json.dumps(res, indent=2, ensure_ascii=False))
