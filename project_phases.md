# Project phases

Ritwik. Updated 18 Nov 2026.

Phase 1 is the current work. Phases 2 and 3 run through November. Ownership is in
`team_workflow.md`. Machines and dated decisions are in `Lab_log.md`.

---

## Phase 1 — now, through the end of October

Dataset, model, simulator, first rollout.

| # | Track | GPU? | Status |
|---|---|---|---|
| 1 | Dataset exploration | No | Done on my laptop |
| 2 | Model, one frame → six numbers | No | Done on my laptop |
| 3 | RunPod A40, Isaac Sim 4.5, Isaac Lab, LeIsaac | Yes | Done, 18 Nov. Headless frames saved |
| 4 | One rollout with the pretrained checkpoint | Yes | Done, 18 Nov. 0/5, all timeouts |

Tracks 1 and 2 are in `phase1/`. Tracks 3 and 4 have runbooks ready.

Phase 1 is done. The arm moved, both cameras saved to disk, and the pretrained
checkpoint scored 0/5. Writeup is in `phase1/README.md`. The pod branch is
`feature/baselinework_runpod`. `feature/ritwik_workflow` is unchanged, so the campus
4090 can pull that and start from the October plan.

## Phase 2 — first two weeks of November

Evaluation script. This is the piece we write ourselves.

LeIsaac's inference script already runs the loop. We wrap it so we get a per-orange
success rate, a 0-to-3 breakdown per episode, and a few seeded runs we can compare
across checkpoints.

| Work | Owner |
|---|---|
| Success definition, read from the environment | Evaluation owner, with Ritwik |
| Wrapper: N rounds, M seeds, one CSV row per episode | Evaluation owner |
| Per-orange rate, per-episode histogram, 95% CI | Evaluation owner |
| Action horizon sweep, 1 to 50 | Ritwik |
| Score random-action and zero-shot SmolVLA | Evaluation owner |

Done when one command scores a checkpoint on fixed seeds and writes the table.

## Phase 3 — first two weeks of November, alongside phase 2

Fine-tuning on HPC.

1. Smoke test: overfit 3 to 5 episodes on an H100 or A100, watch the loss drop.
2. Full fine-tune on all 60 episodes, around 20,000 steps, about four hours on one A100.
3. Copy the checkpoint to the simulator machine and score it with the phase 2 script,
   same seeds as the pretrained run.

If phase 2 and phase 3 compete for time, the eval script goes first, since we need it
to score the fine-tune.

## Last two weeks of November

Metrics summary, documentation, results presentation. RL fine-tuning if we have time
after the imitation-learning numbers are in. Demo to Dr. Wu on 4 December.

---

## Settings

| Item | Value |
|---|---|
| Policy | `lerobot/smolvla_base`, 450.0M |
| Dataset | `LightwheelAI/leisaac-pick-orange`, 60 episodes |
| Simulator | Isaac Sim 4.5.0, Isaac Lab v2.1.1 |
| Scene | `LeIsaac-SO101-PickOrange-Direct-v0` |
| Simulator machine | RunPod A40 for phase 1 |
| Training machine | HPC3 H100 or A100 |
| Action | 6 joints, dataset order |
| Cameras | `front` → `camera1`, `wrist` → `camera2` |
| Instruction | `Grab orange and place into plate` |
| Episode length | 120 s at 30 Hz |
| Action horizon | 16 first, then sweep 1 to 50 |
| Metric | per-orange success rate |

## What is left

1. Eval script. Same scene, more seeds, per-orange success, 95% confidence interval,
   and the horizon sweep from 1 to 50. A finished random-action run is still missing.
2. Fine-tune on HPC3, H100 or A100, on all 60 episodes. Then score that checkpoint
   with the eval script, same seeds as this 0/5 run.
3. WebRTC, only if we want a live view. It is not required for the numbers. Isaac 4.5
   on this pod cannot advertise the public UDP port, so the stock client stays black
   until the client machine rewrites `49100` and `47998` onto the pod's published ports.
