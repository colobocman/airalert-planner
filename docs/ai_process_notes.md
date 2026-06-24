# AI-Assisted Development Notes

Use this file to record important engineering decisions made during AI-assisted development.

Recommended log entries:

- Prompt or question asked.
- What the AI suggested.
- What was accepted, rejected, or modified.
- Why the final decision is better.

Good examples:

- Rejected random train/test split because the data is time-series.
- Chose an explainable historical baseline before complex ML.
- Split product interfaces from analytical core to avoid coupling.
- Kept Telegram bot optional to protect MVP deadline and reproducibility.
