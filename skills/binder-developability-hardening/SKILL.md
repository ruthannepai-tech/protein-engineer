---
name: binder-developability-hardening
description: Score a protein binder/biologic sequence for developability liabilities and, for oral/gut-restricted formats, map GI-protease cleavage sites and propose interface-preserving hardening. Use whenever the task is to check a designed binder for manufacturability risks (deamidation, isomerization, oxidation, N-glycosylation, aggregation, unpaired cysteines), to make a biologic protease-stable for the gut lumen, to "harden" a sequence without breaking its binding interface, or to spec an oral-delivery (VHH / disulfide-lock / mucin-anchor) reformatting path. Runs on CPU from sequence alone. Disease- and scaffold-agnostic; pairs with binder-design-campaign as the developability gate.
---

# Binder developability & protease-hardening

A designed binder that folds and binds in-silico can still be undevelopable: it
may deamidate on the shelf, glycosylate in the wrong place, aggregate, or — for
an **oral / gut-restricted** modality — be shredded by digestive proteases
before it reaches its target. This skill scores those liabilities from sequence
and, when the format demands protease stability, maps the cleavage sites and
proposes **interface-preserving** hardening.

`kernel.py` ships the scanners: `chemical_liabilities`, `protease_sites`,
`developability_scorecard`, and `harden_omit_set`.

## Part A — Chemical / manufacturability liabilities (any biologic)

Scan the sequence for the standard CMC liability motifs (`chemical_liabilities`):

- **N-glycosylation** sequon `N-X-S/T` (X≠P) — especially bad *in* the paratope.
- **Deamidation** `NG/NS/NN` (Asn) and `QG` — shelf-life / charge heterogeneity.
- **Isomerization** `DG/DS/DD` (Asp).
- **Oxidation** — surface Met, Trp.
- **Unpaired cysteines** — mispairing / aggregation; count vs. expected disulfides.
- **Aggregation / hydrophobic patches** — long hydrophobic runs, high GRAVY.
- **Charge** — net charge and % charged (extremes hurt solubility *and* PK).

Flag any liability that falls **on an interface residue** separately — those are
the expensive ones, because you cannot mutate them away without risking binding.

## Part B — GI-protease liability (oral / gut-restricted formats only)

For a luminally-delivered biologic, map cleavage sites for the four major GI
proteases with PeptideCutter-style rules (`protease_sites`):

| Protease | Cleaves after | Note |
|----------|---------------|------|
| pepsin | F, L, W, Y, (A,E,Q) | acidic stomach; broad |
| trypsin | K, R | **not** when followed by P |
| chymotrypsin | F, Y, W, L, M | aromatic-preferring |
| elastase | A, V, G, S, I, L | small aliphatics |

Cross-reference every predicted cut against the **fixed binding-interface
residues**. Sites *on* the interface are unremovable without breaking binding —
that sets a floor on achievable protease resistance and is itself a finding
(often the argument for a purpose-built scaffold over indefinite hardening).

Output `protease_map.csv`:
`binder, position, residue, n_proteases, proteases, in_interface, removable`.

## Part C — Interface-preserving hardening

Do **not** make blind point mutations. Re-run the inverse-folding model
(`solublempnn`, or `proteinmpnn`) with:

- the **binding-interface positions held fixed** (the model skill's fixed-position mechanism), and
- the cleavage-prone residue types **forbidden outside the paratope**:
  `omit_AAs = "KRFWYM"` (`harden_omit_set`) — this removes trypsin's K/R and the
  chymotrypsin/pepsin aromatics F/W/Y/M while leaving the aliphatic residues the
  fold needs, and retaining cysteines for disulfide engineering.

This lets the network pick structurally-compatible protease-resistant residues.
Expect a **large reduction in trypsin + chymotrypsin + pepsin sites** (the
reference celiac campaign cut trypsin sites ~32→5 and ~18→1 on two binders, ~46–49%
total reduction on the hardenable proteases) with **all interface residues
preserved exactly** — verify that at the sequence level and report it.

**Report the trade-off honestly.** Forbidding basic + aromatic residues pushes
composition toward small aliphatics (A/V/G/S/I/L), so **elastase sites rise**.
Elastase liability is intrinsic to any folded chain and cannot be engineered
away at the sequence level — it is managed at the **format** level (a compact,
disulfide-locked VHH resists elastase structurally). Watch net charge too:
hardening often drives it strongly negative, which *aids* non-absorption for a
gut-restricted goal but must be checked against folding/solubility.

## Part D — Delivery-format specification (oral / gut-restricted)

Spec the reformatting path as a JSON (`delivery_spec.json`) — the reference
6-step path: (1) minimize to the folded paratope-bearing core; (2) **graft the
fixed epitope onto a VHH / single-domain scaffold** (~13 kDa; reference oral
anti-TNF VHH V565 reached the inflamed gut intact); (3) apply Part-C hardening
to the framework; (4) **disulfide-lock** (canonical VHH Cys22–Cys92 + retained
structural cysteines); (5) **mucin-anchor** for mucosal residence. The decisive
input is **target depth**: an *apical-surface* target (e.g. NKG2D–MIC) is
reachable by a luminal agent (favorable); a *submucosal* pool is a caveat
(moderate fit). This surface-vs-deep rule governs the whole field.

## Output schema

- `developability.csv` — `binder, variant, length, net_charge, n_cys, n_aromatic, pct_charged, gravy, trypsin_sites, chymo_sites, pepsin_sites, elastase_sites, harden_target_sites, total_sites` (one row each for native / design / hardened).
- `protease_map.csv` — per-position cleavage table (columns above).
- `hardened.fasta` — interface-intact hardened sequences.
- `delivery_spec.json` — the reformatting path + target-depth assessment.
- Before/after figures (cleavage sites per protease; liability map with interface
  residues) — load `figure-style` first.

## The honesty bar

Protease **rules are predictions, not digestion** — empirical stability needs an
in-vitro simulated-gastric/simulated-intestinal-fluid (SGF/SIF) digest. Hardening
preserves the interface *sequence* but does **not** prove the fold or binding
survived — co-fold the hardened sequence against target (`boltz`/`chai1`) and
check ipTM before claiming the binder still works. A VHH graft is a
*specification* until it is actually modeled (RFdiffusion motif-scaffolding +
AF-multimer).
