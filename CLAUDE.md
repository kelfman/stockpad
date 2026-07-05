# Working agreement

Before building a new feature or chunk of work, talk it through first: intention, plan, key decisions. Keep it simple and brief — no briefer than it needs to be to convey what actually matters — so there's a chance to interject before things go too far.

The talk-through is not a pitch. Whatever model you are, include what's most likely wrong with the plan: the strongest objection, the assumption it leans on hardest, anything that rubs against the principles in README.md or the contracts in ARCHITECTURE.md. If there's genuinely nothing, say so and why. Faithfully executing an unexamined plan is this project's main failure mode — agreement is not the goal of the conversation.

## Model checkpoints

Day-to-day build work runs on a fast model (Sonnet-class) — the docs carry the judgment, so execution doesn't need the strongest model. But some moments do. **Switch to the most capable model available** (Fable/Opus-class) when any of these hit, and if you're an assistant reading this at one of those moments on a smaller model, say so and suggest the switch:

- A build slice just finished (before starting the next one)
- About to change the `Signal` contract in `core`, or any cross-project interface
- Starting the AI synthesis prompt design (Slice 3) — the taste-heavy, differentiated core
- Something feels off and it's hard to articulate why
- It's been a few weeks since the last review pass

**Checkpoint prompt (paste as-is on the strong model):**

> Read README.md, ARCHITECTURE.md, RESEARCH_LOG.md, and the current code. You're a fresh set of eyes. First: what do you see as the purpose of this project, and is the current state and plan actually serving it? Then look specifically for: gaps between what the docs claim and what the code does; scope that serves building rather than understanding; trading-system DNA creeping back in; false precision (composites, invented weights, coarseness posing as humility); and anything I've stopped questioning that deserves questioning. Rank findings by how much they matter. Be direct — critique, don't validate. If the plan's next step is wrong, say what you'd do instead.
