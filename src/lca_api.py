from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from berechnung import calculate_lca_for_product

app = FastAPI(title="LCA Service für Odoo")


class BomItem(BaseModel):
    name: str
    mass_g: float
    flow_uuid: str


class LcaRequest(BaseModel):
    product_name: str
    bom: List[BomItem]


@app.post("/lca/calc")
def calc_lca(req: LcaRequest):
    """
    HTTP-Endpunkt:
    - Input: Produktname + BoM (Komponenten mit mass_g, flow_uuid)
    - Output: GWP pro kg, GWP pro Stück + Impact-Tabelle als JSON
    """
    try:
        bom = [item.dict() for item in req.bom]
        result = calculate_lca_for_product(req.product_name, bom)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
