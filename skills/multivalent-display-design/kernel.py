"""Pure-compute helpers for multivalent-display-design.

Geometric/statistical avidity ESTIMATES only — not measured affinities.
See SKILL.md.
"""
import math

ARCH_COLS = ["component", "spec", "function", "notes"]
SCENARIO_COLS = ["Scenario", "Valency", "Surface_occupancy_%", "Inter_epitope_nm",
                 "Cross_link_feasible", "Estimated_avidity_fold",
                 "Advantages", "Disadvantages"]
SPEC_COLS = ["Parameter", "Value", "Rationale/Reference"]


def inter_epitope_spacing(core_diameter_nm, valency):
    """Mean center-to-center spacing (nm) of `valency` points spread evenly on a
    sphere of the given diameter. Uses the equal-area cap approximation.
    """
    if valency < 2:
        return float("nan")
    r = core_diameter_nm / 2.0
    area = 4.0 * math.pi * r * r
    area_per = area / valency
    # cap radius whose base-circle approximates neighbor spacing
    return round(2.0 * math.sqrt(area_per / math.pi), 2)


def avidity_scenarios(core_diameter_nm, payload_footprint_nm2, valencies,
                      cross_link_min_nm=3.0, cross_link_max_nm=20.0,
                      labels=None):
    """Build the valency-scenario sweep (list of dicts, SCENARIO_COLS).

    avidity fold-gain is estimated as valency**0.7 (sub-linear: rebinding gain
    saturates) — a heuristic prior, NOT a measured Kd shift. Cross-linking is
    called feasible when spacing falls in [cross_link_min, cross_link_max] nm.
    """
    r = core_diameter_nm / 2.0
    surf = 4.0 * math.pi * r * r
    labels = labels or {}
    out = []
    for v in valencies:
        spacing = inter_epitope_spacing(core_diameter_nm, v)
        occ = round(100.0 * v * payload_footprint_nm2 / surf, 1)
        feasible = cross_link_min_nm <= spacing <= cross_link_max_nm
        out.append({
            "Scenario": labels.get(v, f"{v} copies/NP"),
            "Valency": v,
            "Surface_occupancy_%": occ,
            "Inter_epitope_nm": spacing,
            "Cross_link_feasible": "Yes" if feasible else "No",
            "Estimated_avidity_fold": round(v ** 0.7, 1),
            "Advantages": "", "Disadvantages": "",
        })
    return out


def architecture_row(component, spec, function, notes=""):
    """One fusion_architecture.csv row (dict)."""
    return {"component": component, "spec": spec, "function": function,
            "notes": notes}


def spec_row(parameter, value, rationale=""):
    """One specs.csv row (dict)."""
    return {"Parameter": parameter, "Value": value,
            "Rationale/Reference": rationale}
