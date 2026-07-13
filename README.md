# Protein Engineer

In-silico protein design: from a target and mapped epitope to structurally validated, developable binders and scaffolds.

A specialist agent profile and its companion skills for **Claude Science**.
In-silico protein design bench: takes a target + epitope to designed, structurally validated, developable binders and multivalent scaffolds. Composes the binder-design, developability-hardening, and multivalent-display skills with the structure-model skills (RFdiffusion/MPNN/AlphaFold/Boltz/Chai/ESMFold) and remote GPU compute, with strict fold-back and developability discipline.

## What's in this repository

```
agent/
  profile.json        # picker metadata (name, description, access)
  system_prompt.md    # the agent's identity / opening system prompt
skills/               # 5 skill(s), each with SKILL.md (+ kernel.py helpers)
install.py            # one-shot, idempotent installer
```

### Skills bundled

- **antigen-epitope-pipeline**
- **binder-design-campaign**
- **binder-developability-hardening**
- **compute-cost-audit**
- **multivalent-display-design**

## Install it in Claude Science

### Easiest — paste one prompt to your Claude Science agent

> Please install the Protein Engineer from this GitHub repo:
> https://github.com/ruthannepai-tech/protein-engineer
> Clone or download it, then run `install.py` from the repo root in the repl tool
> with `exec(open("install.py").read())`. It will create and publish the skills and
> create the PROTEIN_ENGINEER agent profile with full access. Then create its environment and
> offer to switch me to it.

When it finishes, **Protein Engineer** appears in your agent picker.

### One command — if you already have the repo

From the repo root, in the Claude Science **repl** tool:

```python
exec(open("install.py").read())
```

`install.py` publishes every skill under `skills/` and creates the `PROTEIN_ENGINEER`
agent profile with full catalog + connector access. It is **idempotent** — safe
to re-run; it updates in place. It finishes by printing the optional environment
setup and the switch command:

```python
manage_environments(mode='create', name='protein-engineer',
    packages=['requests'], python_version='3.13')
host.agents.switch('PROTEIN_ENGINEER')
```

### Manual

The `SKILL.md` / `kernel.py` files and `agent/` files are plain text and fully
define everything; create each skill and an unrestricted profile named `PROTEIN_ENGINEER`
by hand if you prefer.

## A note on shared skills

Some skills here are shared with other agents I've published. They're bundled in each repo that needs them so every repo installs standalone. If you improve one of these, the same change may be worth applying wherever it appears:

- `antigen-epitope-pipeline` — also used by other agents in this collection

## License

MIT — see [LICENSE](LICENSE).
