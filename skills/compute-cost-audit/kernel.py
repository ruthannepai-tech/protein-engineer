"""Pure-compute helpers for compute-cost-audit. See SKILL.md."""

# Approximate on-demand $/GPU-hr (Modal, ~2026). Spot/committed 30-60% cheaper.
PROVIDER_RATES = {
    "A100-40": 2.10, "A100-80": 2.50, "L40S": 1.95, "L4": 0.80,
    "H100": 3.95, "A10": 1.10, "T4": 0.59,
}

COST_COLS = ["id", "campaign", "task", "tool", "gpu", "gpu_hr_low",
             "gpu_hr_high", "iter_factor", "source", "rate_hr", "clean_low",
             "clean_high", "real_hr_low", "real_hr_high", "real_low", "real_high"]


def rate_for(gpu, rates=None):
    """$/hr for a GPU class; falls back to A100-40 if unknown."""
    if rates is None:
        rates = PROVIDER_RATES
    return rates.get(gpu, rates.get("A100-40", 2.10))


def estimate_cost(gpu_hr_low, gpu_hr_high, gpu, iter_factor=1.0, rates=None):
    """Return dict with clean-pass and realistic (iteration-adjusted) costs.

    clean = gpu_hr * rate. realistic = gpu_hr * iter_factor * rate.
    iter_factor should be 1.0 for deterministic steps and 2-2.5 for generative
    steps (RFdiffusion, affinity maturation) that get re-run with tuned params.
    """
    rate = rate_for(gpu, rates)
    real_hr_low = gpu_hr_low * iter_factor
    real_hr_high = gpu_hr_high * iter_factor
    return {
        "rate_hr": rate,
        "clean_low": round(gpu_hr_low * rate, 2),
        "clean_high": round(gpu_hr_high * rate, 2),
        "real_hr_low": round(real_hr_low, 2),
        "real_hr_high": round(real_hr_high, 2),
        "real_low": round(real_hr_low * rate, 2),
        "real_high": round(real_hr_high * rate, 2),
    }


def cost_row(id, campaign, task, tool, gpu, gpu_hr_low, gpu_hr_high,
             iter_factor=1.0, source="", rates=None):
    """One canonical costs.csv row (dict), costs filled in."""
    c = estimate_cost(gpu_hr_low, gpu_hr_high, gpu, iter_factor, rates)
    row = {"id": id, "campaign": campaign, "task": task, "tool": tool,
           "gpu": gpu, "gpu_hr_low": gpu_hr_low, "gpu_hr_high": gpu_hr_high,
           "iter_factor": iter_factor, "source": source}
    row.update(c)
    return row


def campaign_subtotals(rows):
    """Sum realistic + clean cost ranges per campaign. Returns dict
    campaign -> {clean_low, clean_high, real_low, real_high, n_tasks}.
    """
    out = {}
    for r in rows:
        c = out.setdefault(r["campaign"], {"clean_low": 0.0, "clean_high": 0.0,
                                           "real_low": 0.0, "real_high": 0.0,
                                           "n_tasks": 0})
        for k in ("clean_low", "clean_high", "real_low", "real_high"):
            c[k] = round(c[k] + r[k], 2)
        c["n_tasks"] += 1
    return out
