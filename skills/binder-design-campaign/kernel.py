"""Pure-compute helpers for the binder-design-campaign skill.

No network or GPU here — these are the scoring/filtering/schema utilities that
run on the CPU around the model-skill calls. See SKILL.md for the workflow.
"""

# Community-standard acceptance thresholds (Accept tier). See SKILL.md table.
ACCEPT_IPTM = 0.6
ACCEPT_PAE = 10.0
ACCEPT_BINDER_PLDDT = 80.0
ACCEPT_EPITOPE_RECAP = 0.50

STRONG_IPTM = 0.8
STRONG_PAE = 5.0
STRONG_BINDER_PLDDT = 90.0
STRONG_EPITOPE_RECAP = 0.75

TARGET_COLS = ["target", "modality", "framework", "epitope", "key_hotspots",
               "target_KD_nM", "selectivity_screen", "gpu_design"]
DESIGN_COLS = ["design", "target", "binder_len", "mpnn_score", "iptm",
               "complex_plddt", "confidence", "pass", "seq"]


def on_target_score(iptm, epitope_coverage, plddt):
    """Composite that rewards confident AND on-epitope designs.

    epitope_coverage is a fraction in [0,1] (mapped hotspots contacted /
    hotspots defined). plddt may be given 0-1 or 0-100; it is normalized to
    0-1 so the score is comparable across folding tools.
    """
    p = plddt / 100.0 if plddt > 1.0 else plddt
    return float(iptm) * float(epitope_coverage) * float(p)


def passes_thresholds(iptm, epitope_recap, binder_plddt=None, pae=None,
                      tier="accept"):
    """True if a folded design clears the interface + on-epitope gate.

    The two load-bearing gates are iptm and epitope_recap (a confident fold on
    the wrong surface is not a hit). binder_plddt / pae are checked only when
    provided. tier is 'accept' or 'strong'.
    """
    if tier == "strong":
        i, e, pl, pa = STRONG_IPTM, STRONG_EPITOPE_RECAP, STRONG_BINDER_PLDDT, STRONG_PAE
    else:
        i, e, pl, pa = ACCEPT_IPTM, ACCEPT_EPITOPE_RECAP, ACCEPT_BINDER_PLDDT, ACCEPT_PAE
    if float(iptm) <= i:
        return False
    if float(epitope_recap) < e:
        return False
    if binder_plddt is not None:
        p = binder_plddt * 100.0 if binder_plddt <= 1.0 else binder_plddt
        if p <= pl:
            return False
    if pae is not None and float(pae) >= pa:
        return False
    return True


def sequence_complexity_ok(seq, max_homopolymer_run=5, max_single_aa_frac=0.5):
    """Reject low-complexity designs before spending fold-back compute.

    Flags long homopolymer runs and single-residue domination — both are
    undevelopable and inflate MPNN scores. Returns (ok: bool, reason: str).
    """
    if not seq:
        return False, "empty"
    run, longest, prev = 1, 1, None
    for a in seq:
        if a == prev:
            run += 1
            longest = max(longest, run)
        else:
            run = 1
        prev = a
    if longest > max_homopolymer_run:
        return False, f"homopolymer_run={longest}"
    from collections import Counter
    top_frac = max(Counter(seq).values()) / len(seq)
    if top_frac > max_single_aa_frac:
        return False, f"single_aa_frac={top_frac:.2f}"
    return True, "ok"


def rank_designs(designs, iptm_key="iptm", cov_key="epitope_coverage",
                 plddt_key="complex_plddt"):
    """Sort a list of design dicts by on-target score, descending.

    Returns a new list; each dict gains an 'on_target_score' key.
    """
    out = []
    for d in designs:
        d = dict(d)
        d["on_target_score"] = on_target_score(
            d[iptm_key], d[cov_key], d[plddt_key])
        out.append(d)
    out.sort(key=lambda x: x["on_target_score"], reverse=True)
    return out


def binder_targets_row(target, modality, framework, epitope, key_hotspots,
                       target_KD_nM=None, selectivity_screen=None,
                       gpu_design="pending"):
    """Build one canonical binder_design_targets.csv row (dict)."""
    return {
        "target": target, "modality": modality, "framework": framework,
        "epitope": epitope, "key_hotspots": key_hotspots,
        "target_KD_nM": target_KD_nM, "selectivity_screen": selectivity_screen,
        "gpu_design": gpu_design,
    }


def design_row(design, target, seq, iptm, complex_plddt, mpnn_score=None,
               epitope_recap=None):
    """Build one canonical <campaign>_binder_designs.csv row (dict).

    Sets 'confidence' = on_target_score when epitope_recap is given (else iptm),
    and 'pass' = 'Y'/'N' from the accept-tier gate.
    """
    conf = on_target_score(iptm, epitope_recap, complex_plddt) \
        if epitope_recap is not None else float(iptm)
    ok = passes_thresholds(iptm, epitope_recap if epitope_recap is not None else 1.0,
                           binder_plddt=complex_plddt)
    return {
        "design": design, "target": target, "binder_len": len(seq),
        "mpnn_score": mpnn_score, "iptm": round(float(iptm), 3),
        "complex_plddt": round(float(complex_plddt), 3),
        "confidence": round(conf, 3), "pass": "Y" if ok else "N", "seq": seq,
    }
