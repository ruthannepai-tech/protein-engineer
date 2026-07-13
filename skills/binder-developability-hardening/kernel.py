"""Pure-compute scanners for binder-developability-hardening.

Sequence-only, CPU-only. Protease rules are PeptideCutter-style approximations
(predictions, not digestion). See SKILL.md.
"""
import re

# Kyte-Doolittle hydropathy
KD_HYDROPATHY = {"A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5, "Q": -3.5,
       "E": -3.5, "G": -0.4, "H": -3.2, "I": 4.5, "L": 3.8, "K": -3.9,
       "M": 1.9, "F": 2.8, "P": -1.6, "S": -0.8, "T": -0.7, "W": -0.9,
       "Y": -1.3, "V": 4.2}
HARDEN_OMIT_AAS = "KRFWYM"  # trypsin K/R + chymo/pepsin aromatics F/W/Y/M


def harden_omit_set():
    """The omit_AAs string to pass to SolubleMPNN/ProteinMPNN for hardening."""
    return HARDEN_OMIT_AAS


def gravy(seq):
    """Grand average of hydropathy."""
    vals = [KD_HYDROPATHY[a] for a in seq if a in KD_HYDROPATHY]
    return round(sum(vals) / len(vals), 3) if vals else 0.0


def net_charge(seq):
    """Crude net charge at neutral pH: (K+R) - (D+E)."""
    return sum(seq.count(a) for a in "KR") - sum(seq.count(a) for a in "DE")


def chemical_liabilities(seq, interface_positions=None):
    """Scan for CMC liability motifs. Returns a dict of motif -> list of
    0-based positions (start of the match). interface_positions (a set/list of
    0-based indices) flags overlaps in the 'on_interface' sub-dict.
    """
    iface = set(interface_positions or [])
    hits = {
        "n_glycosylation": [m.start() for m in re.finditer(r"N[^P][ST]", seq)],
        "deamidation": [m.start() for m in re.finditer(r"N[GSN]|QG", seq)],
        "isomerization": [m.start() for m in re.finditer(r"D[GSD]", seq)],
        "oxidation_MW": [i for i, a in enumerate(seq) if a in "MW"],
        "cysteines": [i for i, a in enumerate(seq) if a == "C"],
    }
    on_iface = {k: [p for p in v if p in iface] for k, v in hits.items()}
    return {"hits": hits, "on_interface": on_iface,
            "n_cys": len(hits["cysteines"]),
            "unpaired_cys_risk": len(hits["cysteines"]) % 2 == 1}


def protease_sites(seq, interface_positions=None):
    """Map GI-protease cleavage sites (PeptideCutter-style, cleave-after rules).

    Returns a list of per-position dicts:
    {position, residue, n_proteases, proteases, in_interface, removable}.
    Only positions with >=1 predicted cut are returned.
    """
    iface = set(interface_positions or [])
    rows = []
    n = len(seq)
    for i, a in enumerate(seq):
        nxt = seq[i + 1] if i + 1 < n else ""
        cutters = []
        if a in "KR" and nxt != "P":
            cutters.append("trypsin")
        if a in "FYWLM":
            cutters.append("chymotrypsin")
        if a in "FLWYAEQ":
            cutters.append("pepsin")
        if a in "AVGSIL":
            cutters.append("elastase")
        if cutters:
            in_if = i in iface
            rows.append({
                "position": i, "residue": a, "n_proteases": len(cutters),
                "proteases": ",".join(cutters), "in_interface": in_if,
                "removable": not in_if,
            })
    return rows


def developability_scorecard(seq, variant, binder="binder",
                             interface_positions=None):
    """One canonical developability.csv row (dict) for a sequence variant."""
    sites = protease_sites(seq, interface_positions)
    def count(p):
        return sum(1 for s in sites if p in s["proteases"])
    aromatic = sum(seq.count(a) for a in "FWY")
    charged = sum(seq.count(a) for a in "KRDEH")
    harden_target = count("trypsin") + count("chymotrypsin") + count("pepsin")
    return {
        "binder": binder, "variant": variant, "length": len(seq),
        "net_charge": net_charge(seq),
        "n_cys": seq.count("C"), "n_aromatic": aromatic,
        "pct_charged": round(100.0 * charged / len(seq), 1) if seq else 0.0,
        "gravy": gravy(seq),
        "trypsin_sites": count("trypsin"), "chymo_sites": count("chymotrypsin"),
        "pepsin_sites": count("pepsin"), "elastase_sites": count("elastase"),
        "harden_target_sites": harden_target, "total_sites": len(sites),
    }
