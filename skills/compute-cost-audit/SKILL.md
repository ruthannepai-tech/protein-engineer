---
name: compute-cost-audit
description: Audit a project for compute-blocked (GPU-deferred) tasks, estimate per-task runtime and dollar cost against provider rates, map the dependency chain, and prioritize against a budget. Use whenever the task is to figure out what work is stalled waiting on GPU/compute, to estimate what it would cost to unblock a backlog, to plan spend across cloud GPU jobs, to decide the cheapest high-value first move, or to build a compute budget/resource plan. Distinguishes pure-compute gaps from tool/skill gaps (a tool not yet wrapped). Emits a costs table, a prioritized report with a dependency graph, and a cost chart. Provider- and domain-agnostic.
---

# Compute cost audit

Answer: **which tasks are stalled purely because compute (usually a GPU) wasn't
available, what would each cost to run, and in what order should they run once
compute is added?** Built for a hackathon GPU backlog but works for any
compute-bound program.

`kernel.py` ships `estimate_cost`, `cost_row`, `campaign_subtotals`, and the
default `PROVIDER_RATES`.

## Stage 1 — Find the stalled work (evidence, not guesses)

Audit the project's actual history, don't estimate from memory:

- Read the work-session transcripts (`host.frames(...)`) and search for
  GPU/compute/deferral language ("no GPU host", "deferred", "specification
  only", "run once compute is added").
- Cross-check each deferred item against the **executable protocol specs** the
  agent wrote *in lieu of* running them (these carry the real GPU-hour and tool
  estimates) and against design rosters / config files.
- **Separate the causes.** Not every deferral is a GPU deferral — a CLT boot
  failure, a server outage, or a CPU-only bottleneck is not fixed by a GPU. Only
  count the genuinely compute-blocked tasks, and say which sessions produced
  none.

## Stage 2 — Cost each task

For every compute-blocked task, record the tool, the recommended GPU class, a
low/high GPU-hour range (from the protocol spec), and the source of that
estimate. Then cost it two ways (`estimate_cost`):

- **single clean pass** = GPU-hours × provider $/hr.
- **realistic** = GPU-hours × **iteration factor** (2–2.5× on *generative* steps,
  because real design campaigns re-run with tuned parameters) × $/hr.

Report **both** totals — the clean pass is the floor, realistic is the plan.
Use current provider rates (defaults in `PROVIDER_RATES`, approximate Modal
on-demand 2026: A100-40 ~$2.10, A100-80 ~$2.50, L40S ~$1.95, L4 ~$0.80/hr; note
spot/committed-use runs 30–60% cheaper). If the user names a provider, use its
rates.

Emit `costs.csv`:
`id, campaign, task, tool, gpu, gpu_hr_low, gpu_hr_high, iter_factor, source,
rate_hr, clean_low, clean_high, real_hr_low, real_hr_high, real_low, real_high`.

## Stage 3 — Dependencies matter more than the dollars

Tasks are usually **not** independent. Draw the chain (e.g. `generate backbones
→ triage fold → rank complexes → immunogenicity`) — downstream tasks whose
inputs don't exist yet cannot be cherry-picked. Then identify:

- what **must run front-to-back**,
- what is **already decoupled** and can run immediately (inputs exist),
- the **cheapest high-value first move** — the smallest spend that validates
  something already built.

This sequencing is the actionable output; the total dollar figure is often a
rounding error next to the value it unblocks.

## Stage 4 — Flag skill/tool gaps distinct from compute

A task can be blocked by **two different things**: no compute, or no wrapped
tool. If a step needs a model that isn't a catalog skill yet (e.g. RFdiffusion),
say so explicitly — adding a GPU won't unblock it until the tool is packaged.
This distinction changes the unblocking plan.

## Output

- `costs.csv` (schema above).
- A report (`*_costs_report.md`): headline total (clean + realistic ranges), the
  per-task table, the dependency graph, campaign subtotals, the cheapest-first
  recommendation, and the skill-gap flags.
- A cost bar chart (per-task or per-campaign, clean vs realistic) — load
  `figure-style` first.

## The honest framing

State the estimate's assumptions plainly: which provider and rate tier, that
first-run image builds add one-time cold-start GPU-minutes, and what is
explicitly **out of scope** (CPU-only work that was never GPU-blocked). The
decision this audit supports is usually "is it worth wiring up a GPU host" — and
the answer is frequently yes on cost grounds alone, with the real gating items
being infrastructure setup and tool packaging, not dollars.
