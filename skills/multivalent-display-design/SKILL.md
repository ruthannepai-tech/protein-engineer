---
name: multivalent-display-design
description: Design a multivalent display construct — a nanoparticle or scaffold that presents many copies of a payload (pMHC, antigen, binder, or peptide) — and sweep valency/spacing/avidity assembly scenarios. Use whenever the task is to display a payload multivalently, to spec a nanoparticle-pMHC or antigen-array immunotherapy, to choose copies-per-particle / inter-epitope spacing for receptor cross-linking, or to build a fusion/conjugation architecture with an assembly model. Emits a component architecture table, a valency-scenario sweep with estimated avidity, and a parameter spec table. Disease- and payload-agnostic; complements binder-design-campaign (which designs the payload) and antigen-epitope-pipeline (which defines the pMHC).
---

# Multivalent display design

Many immunotherapeutic and vaccine modalities work by presenting a payload
**multivalently** — a nanoparticle studded with pMHC-II to cross-link and
tolerize a T-cell clone, an antigen array to cluster BCRs, a scaffold displaying
binders for avidity. This skill turns **a payload + a display goal** into a
concrete construct: the component architecture, a valency/spacing scenario
sweep, and a parameter spec sheet — with an honest avidity model and the
receptor-biology rationale.

`kernel.py` ships `avidity_scenarios`, `inter_epitope_spacing`, and the schema
builders `architecture_row` / `spec_row`.

## Inputs to nail down first

- **Payload**: what is displayed (pMHC-II monomer, antigen domain, minibinder),
  its size, and its **conjugation handle** (free cysteine → maleimide, SpyTag,
  His-tag, sortase motif). The handle must not sit in the functional
  interface — check against the payload's binding/presentation face.
- **Display goal & receptor biology**: what the multivalency is *for*. For a
  tolerogenic pMHC-NP the goal is **TCR cross-linking → sustained signal →
  Tr1 (CD39⁺CD73⁺ IL-10) differentiation**; that dictates an inter-epitope
  spacing in the receptor-clustering range (~5–6 nm is a reasonable target for
  TCR). A different receptor (BCR, integrin) has a different optimal spacing.
- **Scaffold class**: inorganic core (iron-oxide, gold), protein cage
  (ferritin, encapsulin, I3-01), polymer/liposome, or a defined oligomer. Note
  the precedent — reusing a published conjugation chemistry (e.g. the
  Santamaria/Navacim pMHC:Fe₃O₄ platform) de-risks manufacturing.

## Stage 1 — Component architecture

Enumerate every component as one `fusion_architecture.csv` row
(`component, spec, function, notes`; see `architecture_row`): core (material +
diameter), surface chemistry (linker + density), the payload and its handle,
any spacer/PEG, and targeting/stability moieties. Ground each spec in a real
reference where one exists.

## Stage 2 — Valency & avidity scenario sweep

Sweep copies-per-particle (a conservative / standard / high triple is a good
default) and, for each, compute surface occupancy, **inter-epitope spacing**,
whether receptor cross-linking is geometrically feasible, and an **estimated
avidity fold-gain** (`avidity_scenarios`). Emit
`assembly_scenarios.csv`:
`Scenario, Valency, Surface_occupancy_%, Inter_epitope_nm, Cross_link_feasible,
Estimated_avidity_fold, Advantages, Disadvantages`.

The trade-off to surface honestly: **more copies ≠ strictly better**. Higher
valency raises avidity and signal but risks aggregation, steric crowding, and
harder stoichiometric QC; too-tight spacing can block clean receptor geometry.
The "standard" scenario is usually the one where cross-linking is feasible *and*
assembly stays clean.

## Stage 3 — Parameter spec sheet

Consolidate the chosen design into `specs.csv` (`Parameter, Value,
Rationale/Reference`) — core material/diameter, linker chemistry and pH/time,
copies/particle, spacing, occupancy, avidity gain, and the precedent citations.
This is the sheet a CMC/manufacturing partner reads.

## Avidity model — what it is and is not

The avidity fold-gain is a **geometric/statistical estimate** (valency and
rebinding-driven), not a measured Kd shift. State that. Real avidity depends on
linker flexibility, receptor surface density, and on-rate, none of which the
estimate captures. The construct is a *design*; SPR/BLI on the assembled
particle and a functional receptor-clustering assay are the validation path.

## Output schema

- `fusion_architecture.csv`, `assembly_scenarios.csv`, `specs.csv` (columns above).
- An assembly-model figure (valency scenarios; spacing vs occupancy vs avidity)
  and a labeled architecture schematic — load `figure-style` first.

## Mechanism framing (immunotherapy payloads)

For a tolerogenic pMHC display, the causal chain to state is: multivalent pMHC →
TCR cross-linking + sustained signal-1 (no costim) → Tr1/anergy → antigen-specific
tolerance. This is a **mechanistic hypothesis grounded in published multivalent-pMHC
precedent**, testable by IL-10 ELISPOT and CD39⁺CD73⁺ Tr1 flow — not a validated
claim of the specific construct. Keep presentation-vs-pathology discipline: the
construct can present the epitope; whether it tolerizes the pathogenic clone is
the experiment.
