---
name: binder-design-campaign
description: Orchestrate an end-to-end de novo protein binder design campaign against a defined target epitope — backbone generation, sequence design, structural fold-back validation, and on-target ranking — emitting a standardized designs + liabilities table. Use whenever the task is to "design a binder/minibinder/neutralizer to protein X", to build minibinders against a mapped epitope, or to run RFdiffusion→ProteinMPNN→co-fold campaigns and filter them by interface confidence. This skill is the conductor that composes the single-model skills (proteinmpnn, solublempnn, ligandmpnn, alphafold2, boltz, chai1, esmfold2) into one filtered pipeline with defined acceptance thresholds; reach for it even when the user names only one stage, so the whole campaign shares one schema and one honesty bar. Disease- and target-agnostic.
---

# De novo binder design campaign

Turn a **target structure + a mapped epitope** into a ranked set of **de novo
protein binders** that are (a) confidently folded, (b) bound at the *intended*
functional epitope, and (c) screened for basic developability. This skill is a
**conductor** — it sequences the model skills already in the catalog and applies
one consistent filter and output schema, so a campaign against CCL26 looks the
same as one against SIGLEC6 or DKK1.

```
Target PDB + epitope hotspots
   → RFdiffusion backbones (condition on hotspots)
   → ProteinMPNN / SolubleMPNN sequences (temperature sweep)
   → ESMFold2-Fast triage  → Boltz-2 / Chai-1 / AF-Multimer fold-back
   → interface + on-epitope scoring → ranked designs
```

`kernel.py` ships the pure-compute helpers: `on_target_score`,
`passes_thresholds`, `rank_designs`, `sequence_complexity_ok`, and the
canonical output-schema builders `binder_targets_row` / `design_row`.

## The honesty bar that defines this skill

**ipTM and pLDDT are model confidences, not measured affinities.** A design that
"passes" here is a *prioritized hypothesis*, not a validated binder. Every
campaign report must state that these are in-silico designs and name the
wet-lab validation path: recombinant expression, SEC, SPR/BLI for affinity, and
a **functional** assay for the intended mechanism (e.g. chemotaxis inhibition
for a chemokine trap). Never report ipTM as if it were a Kd. This is the same
presentation-vs-pathology discipline the target-mining skills use, applied to
design.

## Stage 1 — Define the target and epitope (do this before any GPU)

Build one `binder_design_targets.csv` row per target. The **epitope hotspots are
the load-bearing input** — a binder that folds confidently onto the wrong face
is a failed design that looks like a success. Columns (see
`binder_targets_row`):

`target, modality, framework, epitope, key_hotspots, target_KD_nM, selectivity_screen, gpu_design`

- **target structure**: a real PDB/mmCIF (experimental or predicted). Note
  resolution/method — an NMR ensemble or a low-pLDDT AlphaFold region weakens
  every downstream number.
- **key_hotspots**: the specific residues that define the *functional* surface
  to occlude (receptor-binding face, catalytic patch, integrin patch). Derive
  these from literature + solvent accessibility, not by eye.
- **selectivity_screen**: the off-targets (paralogs) the design must avoid —
  planned now, because it shapes which epitope sub-patch to target.

## Stage 2 — Backbone generation (GPU)

**RFdiffusion**, conditioned on the mapped hotspots (motif/hotspot scaffolding),
`Complex_base` checkpoint. Binder length 60–90 aa is a good default for a
minibinder. Generate 40 backbones/target for a quick pass; **1,000–5,000/target**
for a real campaign. Confirm each backbone actually engages the hotspot epitope
before spending sequence-design compute on it.

> **Catalog gap:** there is no RFdiffusion skill in this catalog yet. Wrap it on
> the GPU host (or use BindCraft, which bundles the generate→design→filter loop).
> ProteinMPNN, SolubleMPNN, LigandMPNN, AlphaFold2, Boltz, Chai-1 and ESMFold2
> *are* present — load them with `skill({skill: "<name>"})`.

## Stage 3 — Sequence design

Load `proteinmpnn` (or `solublempnn` when solubility/aggregation is the risk, or
`ligandmpnn` when a cofactor/metal lines the interface). Design **8 sequences ×
3 temperatures** per backbone (e.g. T = 0.1 / 0.2 / 0.3); higher T = more
diversity, lower T = more conservative. Hold the interface/hotspot-contacting
positions per the model skill's fixed-position mechanism. Drop low-complexity
sequences (long homopolymer runs, single-residue domination) with
`sequence_complexity_ok` before folding — they waste fold-back compute and are
undevelopable.

## Stage 4 — Fold-back validation

Refold each designed binder–target **complex** and check it landed on the
epitope. Use a cheap→expensive cascade to save GPU:

1. **ESMFold2-Fast** single-sequence triage (~1 s/complex) — kill the obvious failures.
2. **Boltz-2 / Chai-1 / AF-Multimer** for final ranking on survivors (co-fold,
   a few diffusion samples, MSA server).

For each folded complex compute: interface **ipTM**, complex/binder **pLDDT**,
interface **pAE**, **buried surface area**, and **epitope recapitulation** =
fraction of mapped hotspots actually contacted at the interface.

## Stage 5 — Score, filter, rank

Acceptance thresholds (community-standard; `passes_thresholds` encodes them):

| Metric | Accept | Strong |
|--------|--------|--------|
| interface ipTM | > 0.6 | > 0.8 |
| interface pAE (Å) | < 10 | < 5 |
| predicted DockQ | > 0.23 | > 0.49 |
| binder pLDDT | > 80 | > 90 |
| epitope recapitulation | ≥ 50% | ≥ 75% |
| Rosetta ddG (if run, REU) | < −30 | < −45 |

**Filter:** drop any design failing `ipTM > 0.6` **OR** `epitope-recap < 50%` —
a confident fold on the wrong surface is not a hit. **Rank** survivors by the
composite **on-target score = ipTM × epitope_coverage × pLDDT**
(`on_target_score` / `rank_designs`), which rewards designs that are both
confident *and* bound where intended. Take the top 10–20/target forward.

Then **cross-check developability** on the winning sequences — hand off to the
`binder-developability-hardening` skill (N-glyc, deamidation, oxidation,
aggregation, protease liabilities). A high-ipTM design with a glycosylation site
in the paratope is not actually your lead.

## Output schema (keep it identical across campaigns)

- `binder_design_targets.csv` — one row/target (Stage 1 columns above).
- `<campaign>_binder_designs.csv` — `design, target, binder_len, mpnn_score, iptm, complex_plddt, confidence, pass, seq` (see `design_row`).
- `binder_validation.csv` — every folded design with full metrics.
- Lead complex structures as `.pdb`/`.cif` (Mol*-viewable), + a fold-back figure
  (ipTM vs pLDDT, marker size ∝ epitope contacts, thresholds dashed, leads
  circled) — load `figure-style` first.
- A short report: target rationale, pipeline params, results table, leads, and
  the honesty/next-steps section.

## Compute

RFdiffusion ~4–8 GPU-h for thousands of backbones; MPNN is minutes;
ESMFold2-Fast triage <1 GPU-h for thousands; Chai-1/AF-M final ranking ~2–4
GPU-h. A full 3-target campaign is ~1 GPU-day on one 24 GB+ card. Dispatch with
`remote-compute-modal` or `remote-compute-ssh`. For per-model cost estimates
before you commit, use `compute-cost-audit`.
