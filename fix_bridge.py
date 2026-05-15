from arkhe_moire.bridge import MoireArkheBridge
from arkhe_moire.materials_2d_db import MATERIALS_2D_CATALOG, MaterialsMapper

def get_best_materials_for_phi_c(self, min_phi_c: float = 0.99):
    mapper = MaterialsMapper()
    candidates = mapper.find_by_phi_c_range(min_phi_c, 1.0)

    results = []
    for name, phi_c in candidates:
        mat_key = next((k for k, v in MATERIALS_2D_CATALOG.items() if v.name == name), None)
        if mat_key:
            mat = MATERIALS_2D_CATALOG[mat_key]
            results.append({
                "material": name,
                "phi_c_peak": phi_c,
                "critical_angles": mat.critical_angles,
                "applications": mat.applications,
            })
    return results

MoireArkheBridge.get_best_materials_for_phi_c = get_best_materials_for_phi_c
