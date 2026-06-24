# AI Interaction Log — AirAlert Planner Initial Planning & Environment Setup

**Date:** 2026-06-24  
**Context:** Initial AI-assisted planning and environment preparation for a Python MVP that analyzes historical Ukrainian air raid alert time series and exposes the analysis as a practical planning assistant for trips, events, city visits, and work shifts.

---

## 1. AI Assistant / Environment Specification

### Assistant identity

The interaction was conducted with **Hermes Agent by Nous Research**, used as a planning, orchestration, and technical consulting layer.

The assistant role in this phase was not to silently generate a final product, but to act as:

- product strategist,
- technical architect,
- AI-development workflow consultant,
- repository/environment bootstrapper,
- reviewer of MVP scope and deadline risk.

### Communication channel

The interaction happened through a Telegram chat interface connected to Hermes Agent.

### Model/runtime context

The active Hermes runtime reported:

- **Main model:** `gpt-5.5`
- **Provider:** `openai-codex`
- **Host OS:** Linux
- **Working directory:** `/home/roma`
- **Active Hermes profile:** `default`

Hermes also had persistent project/user context available from previous interactions, including the user's preference for:

- concise but strategic engineering guidance,
- using AI agents as a development-control layer,
- building useful applied tools rather than only demo code,
- avoiding unnecessary token waste,
- keeping agentic workflows modular and verifiable.

### Tooling used by the assistant

During this setup phase, Hermes used tools for:

- reading relevant skills and workflows,
- creating files,
- running shell commands,
- initializing and pushing a Git repository,
- validating Python tests and CLI commands,
- checking GitHub Actions CI status.

Key external tools involved:

- `git`
- GitHub CLI: `gh`
- Python virtual environment: `python3 -m venv`
- `pip install -e ".[dev]"`
- `pytest`
- `ruff`
- `make`
- GitHub Actions CI

### Loaded Hermes skills / procedural references

The assistant loaded and used these skills:

1. **systematic-debugging**  
   Used to keep the process grounded in verification, root-cause thinking, and not stopping at unverified plans.

2. **claude-code**  
   Used to prepare the project for future development inside Claude Code, including `CLAUDE.md`, `.claude/agents`, `.claude/skills`, and `.claude/commands`.

3. **github-repo-management**  
   Used to create and publish a public GitHub repository through `gh` and `git`.

### Important prompt-design decision

A deliberate decision was made **not to include explicit references to the selection/test context inside the Claude Code project instructions**.

Reasoning:

- mentioning an external evaluation program in prompts could bias Claude toward writing for a test instead of building a useful product;
- unnecessary context might increase hallucination risk;
- the repository should stand on its own as a serious product-oriented MVP;
- task-relevant constraints are still encoded indirectly: MVP discipline, reproducibility, time-series correctness, conservative claims, and product usefulness.

Therefore, files such as `CLAUDE.md` and `docs/claude_prompts.md` describe the work as **AirAlert Planner**, a practical product MVP, not as a test submission.

---

## 2. Initial Problem Framing

The initial task was to design an approach for a Python mini-project around:

> Time Series Analysis of air raid alerts in Ukraine.

The first interpretation was an analytical project:

- load alert data,
- explore regional/hourly patterns,
- build a simple baseline,
- validate results,
- produce a reproducible repository and report.

However, the user clarified that the desired output should be more than a static analysis. The user wanted a product-oriented MVP with practical use, for example:

- planning trips,
- visiting cities,
- choosing event time windows,
- planning work shifts,
- potentially exposing the assistant through a Telegram bot.

The assistant agreed that this product direction was valuable, but warned that it could hurt the submission if the Telegram wrapper consumed time or distracted from the required time-series core.

---

## 3. Key Strategic Decision

The central architectural decision was:

> Build the analytical core first, then expose it through a thin product interface.

The chosen architecture:

```text
Historical alert events
        ↓
Data loading and validation
        ↓
Hourly regional time-series panel
        ↓
Explainable historical risk baseline
        ↓
Planner service
        ↓
CLI assistant
        ↓
Optional Telegram bot adapter
```

This design keeps the project compliant with the time-series-analysis goal while still making it useful as a product.

---

## 4. Product Concept

The product was named:

# AirAlert Planner

Working description:

> A lightweight Python decision-support MVP that analyzes historical Ukrainian air raid alert time series and turns them into practical planning guidance for trips, city visits, events, and work shifts.

The product intentionally avoids claiming operational prediction ability. It uses historical patterns to provide planning context.

Safety boundary:

> This is historical planning support only. It must not replace official air alert channels, local security instructions, or real-time safety decisions.

---

## 5. Target Users

The following target users were identified:

### Traveler

A person planning an intercity trip who wants to understand historical alert-risk patterns by region and time window.

### Event organizer

A person choosing a time window for a public/private event and wanting to compare historical risk by hour and weekday.

### Shift planner / operations manager

A person planning work shifts or on-site activity who wants to understand regional alert intensity and build time buffers.

### Technical reviewer

A reviewer who needs to see that the project is:

- reproducible,
- testable,
- grounded in time-series analysis,
- product-oriented,
- honest about limitations.

---

## 6. MVP Scope

### Must-have

- Python package structure.
- CSV data ingestion.
- Required fields:
  - `region`
  - `started_at`
  - `ended_at`
- Timestamp normalization.
- Duration calculation.
- Hourly regional panel.
- Explainable historical-frequency risk baseline.
- Chronological validation.
- CLI interface for planning queries.
- Tests.
- README and assumptions documentation.
- Synthetic sample data so the repository runs immediately.

### Nice-to-have

- Optional Telegram bot wrapper.
- Route-like planning over a sequence of regions.
- More realistic dataset integration.
- Better uncertainty communication.

### Explicitly out of scope for the first MVP

- Web dashboard.
- Neural forecasting model.
- Real-time alert ingestion.
- Full geospatial routing.
- Tactical prediction claims.
- Any feature that makes the project harder to reproduce quickly.

---

## 7. Initial Prompt Strategy for Claude Code

The assistant prepared a Claude Code prompt strategy that avoids the external evaluation context and focuses on the product.

Example initial prompt:

```text
We are building AirAlert Planner: a Python MVP that analyzes historical Ukrainian air raid alert time series and helps users plan trips, events, city visits, and work shifts using explainable regional/hourly risk patterns.

Before writing code, act as a skeptical product + ML architect. Define target users, MVP user stories, non-goals, analytical architecture, validation strategy, and risks of overbuilding. Keep the scope realistic and product-oriented.
```

Recommended first prompt after entering Claude Code:

```text
Read CLAUDE.md, docs/product_brief.md, and docs/assumptions.md.

Do not overbuild. First review the current repository as a product-minded Python/data engineering mentor.

Then propose the next smallest development step that improves the analytical core or the CLI planning assistant.

Keep Telegram optional until the core, tests, and README are strong.
```

---

## 8. Repository Created

The assistant created a public GitHub repository:

**Repository:** https://github.com/colobocman/airalert-planner

Local working copy:

```text
/home/roma/airalert-planner
```

The repository was initialized with branch:

```text
main
```

Initial commit message:

```text
Initial AirAlert Planner scaffold
```

---

## 9. Files Created

### Root project files

```text
README.md
pyproject.toml
Makefile
.gitignore
.env.example
CLAUDE.md
```

### Data files

```text
data/README.md
data/sample_alerts.csv
```

The sample dataset is synthetic and intended only to make the project runnable immediately.

### Documentation

```text
docs/product_brief.md
docs/assumptions.md
docs/ai_process_notes.md
docs/claude_prompts.md
```

### Python package

```text
src/airalert_planner/__init__.py
src/airalert_planner/data.py
src/airalert_planner/features.py
src/airalert_planner/risk.py
src/airalert_planner/planner.py
src/airalert_planner/analysis.py
src/airalert_planner/plots.py
src/airalert_planner/report.py
src/airalert_planner/cli.py
src/airalert_planner/telegram_bot.py
```

### Tests

```text
tests/test_data.py
tests/test_features.py
tests/test_risk.py
tests/test_planner.py
```

### Claude Code configuration

```text
.claude/settings.json
.claude/agents/product-architect.md
.claude/agents/time-series-reviewer.md
.claude/agents/code-reviewer.md
.claude/skills/product-scope-guard.md
.claude/skills/time-series-validation.md
.claude/commands/plan-next.md
.claude/commands/harsh-review.md
```

### CI

```text
.github/workflows/ci.yml
```

---

## 10. Claude Code Support Files

### `CLAUDE.md`

Purpose:

- tells Claude what the product is;
- enforces architecture boundaries;
- defines scope guardrails;
- prioritizes analytical core before Telegram;
- bans overconfident prediction claims;
- provides commands and review checklist.

Key architectural instruction:

```text
data.py -> features.py -> risk.py -> planner.py -> cli.py / telegram_bot.py
```

### Claude agents

Three project agents were added:

#### `product-architect`

Keeps the project useful and scoped. Reviews:

- user value,
- scope creep,
- interface/core separation,
- non-goals,
- safety disclaimers.

#### `time-series-reviewer`

Reviews:

- chronological validation,
- leakage risks,
- timestamp assumptions,
- sparse-data fallbacks,
- conservative forecasting claims.

#### `code-reviewer`

Reviews:

- Python module boundaries,
- tests,
- reproducibility,
- dependency minimalism,
- secrets safety.

### Claude skills

#### `product-scope-guard`

Used to prevent overbuilding and keep Telegram optional.

#### `time-series-validation`

Used to enforce chronological validation and avoid random train/test split.

### Claude commands

#### `/plan-next`

Asks Claude to propose the next smallest implementation step.

#### `/harsh-review`

Asks Claude to review the project for reproducibility, leakage, weak tests, overclaiming, unclear assumptions, and scope creep.

---

## 11. Initial Implementation Details

### Data layer

`data.py` implements:

- CSV loading,
- required-column validation,
- timestamp parsing,
- duration calculation,
- invalid-row separation,
- duplicate removal.

Invalid data is not silently ignored; invalid rows are returned separately.

### Feature layer

`features.py` converts alert intervals into an hourly regional panel.

Important correction made during setup:

The first version only included hours touched by alerts. This made risk scores trivially equal to `1.0` for observed buckets. The assistant identified this as a modeling issue and changed the feature logic to densify each regional time series with explicit zero-alert hours.

This was an important early example of AI-assisted verification and correction.

### Risk model

`risk.py` implements an explainable historical-frequency baseline:

```text
risk(region, weekday, hour) = historical alert-active probability
```

Sparse-data fallback order:

1. region + weekday + hour,
2. region + hour,
3. global hour,
4. global mean.

Validation uses chronological split, not random split.

### Planner service

`planner.py` provides product-facing summaries:

- selected region/date/time-window risk summary,
- lowest-risk and highest-risk hour inside the window,
- route-like regional sequence sketch,
- safety disclaimer.

### CLI

`cli.py` exposes:

```bash
python -m airalert_planner.cli analyze --input data/sample_alerts.csv --out outputs
python -m airalert_planner.cli risk --input data/sample_alerts.csv --region Kyiv --date 2026-06-26 --from-hour 18 --to-hour 22
python -m airalert_planner.cli plan-trip --input data/sample_alerts.csv --regions Ivano-Frankivsk Lviv Rivne Zhytomyr Kyiv --date 2026-06-26
```

### Telegram wrapper

`telegram_bot.py` is included as an optional adapter. It reads `TELEGRAM_BOT_TOKEN` from the environment and calls the same planner service.

This preserves the rule:

> Telegram must not duplicate business logic.

---

## 12. Verification Performed

The assistant created a virtual environment and installed the package:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Tests were run:

```bash
make test
```

Result:

```text
8 passed
```

Lint was run:

```bash
make lint
```

Result:

```text
All checks passed!
```

The analysis pipeline was run:

```bash
make run
```

Result:

```text
Wrote outputs to outputs
Valid events: 18; invalid rows: 0
Validation: MAE=0.088, Brier=0.072
```

CLI risk command was run:

```bash
python -m airalert_planner.cli risk \
  --input data/sample_alerts.csv \
  --region Kyiv \
  --date 2026-06-26 \
  --from-hour 18 \
  --to-hour 22
```

Example output:

```text
Region: Kyiv
Window: 2026-06-26 18:00-22:00
Average historical risk: 0.00
Relatively lower-risk hour: 18:00
Relatively higher-risk hour: 18:00

Hourly profile:
- 18:00 risk=0.00
- 19:00 risk=0.00
- 20:00 risk=0.00
- 21:00 risk=0.00

Historical planning support only. Always follow official alerts and local security guidance.
```

GitHub Actions CI was watched after pushing.

CI result:

```text
CI passed
```

The GitHub Actions job successfully ran:

- install,
- tests,
- pipeline.

---

## 13. Issues Found and Fixed During Setup

### Issue 1: Missing optional `tabulate` dependency

The first implementation used:

```python
summary.to_markdown(index=False)
```

This failed because pandas requires optional dependency `tabulate` for Markdown table rendering.

Error summary:

```text
ImportError: `Import tabulate` failed. Use pip or conda to install the tabulate package.
```

Decision:

Instead of adding a new dependency, the assistant implemented a small internal Markdown table renderer in `report.py`.

Reasoning:

- dependency minimalism,
- reproducibility,
- faster setup,
- enough for a small MVP report.

### Issue 2: Risk scores were trivially `1.0`

The first hourly panel only included alert-active hours. This meant every row had `alert_active = 1`, so the model could not learn non-alert hours.

Fix:

`features.py` now densifies each regional timeline and fills non-alert hours with:

```text
alert_active = 0
alert_count = 0
alert_minutes = 0.0
```

This made the risk baseline more meaningful.

### Issue 3: Generated package metadata was committed

After editable install, `src/airalert_planner.egg-info` appeared in the commit.

Fix:

- added `*.egg-info/` to `.gitignore`,
- removed generated metadata from git,
- amended the initial commit,
- force-pushed the corrected clean commit.

---

## 14. Final Repository State After Setup

Public repository:

```text
https://github.com/colobocman/airalert-planner
```

Verified commands:

```bash
git clone https://github.com/colobocman/airalert-planner.git
cd airalert-planner
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
make test
make run
```

Expected state:

- tests pass,
- analysis outputs generated,
- CLI risk query works,
- CI passes on GitHub,
- Claude Code project context is prepared.

---

## 15. Recommended Next Step in Claude Code

The user decided to continue development inside Claude Code.

Recommended startup commands:

```bash
git clone https://github.com/colobocman/airalert-planner.git
cd airalert-planner
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
make test
make run
claude
```

Recommended first Claude prompt:

```text
Read CLAUDE.md, docs/product_brief.md, and docs/assumptions.md.

Do not overbuild. First review the current repository as a product-minded Python/data engineering mentor.

Then propose the next smallest development step that improves the analytical core or the CLI planning assistant.

Keep Telegram optional until the core, tests, and README are strong.
```

---

## 16. Summary of AI-Assisted Reasoning

The AI-assisted process evolved through several decisions:

1. Started from a basic time-series-analysis task.
2. Reframed it into a practical product MVP.
3. Avoided letting the Telegram bot dominate scope.
4. Designed the analytical core as reusable service logic.
5. Added Claude Code project instructions without external evaluation context.
6. Created a public GitHub repository.
7. Implemented a runnable scaffold with tests and CI.
8. Verified the scaffold locally and through GitHub Actions.
9. Fixed early implementation problems found during real execution.
10. Prepared the user to continue development in Claude Code.

The result is not only a plan, but a working repository prepared for iterative AI-assisted development.

---

## 17. Reflection Seed

A possible short reflection based on this phase:

> I initially considered building a Telegram bot around air raid alerts, but the planning phase showed that this could distract from the actual time-series problem. With AI assistance, I separated the analytical core from product adapters: first data normalization, hourly time-series features, explainable historical risk scoring, and chronological validation; then a CLI planning assistant; and only then an optional Telegram wrapper. This made the project more reproducible, safer, and easier to review. The AI was most useful not as a code generator, but as an architectural critic that helped identify scope risks, validation leakage, and weak assumptions early.
