# Project phases

Ritwik. Updated 26 Oct 2026.

Phase 1 is the current work. Phases 2 and 3 run through November. Ownership is in
`team_workflow.md`. Machines and dated decisions are in `Lab_log.md`.

---

## Phase 1 — now, through the end of October

Dataset, model, simulator, first rollout.

| # | Track | GPU? | Status |
|---|---|---|---|
| 1 | Dataset exploration | No | Done |
| 2 | Model, one frame → six numbers | No | Done |
| 3 | RunPod A40, Isaac Sim 4.5, Isaac Lab, LeIsaac | Yes | Waiting on a pod |
| 4 | One rollout with the pretrained checkpoint | Yes | After track 3 |

Tracks 1 and 2 are in `phase1/`. Tracks 3 and 4 have runbooks ready.

Done when the arm moves in the scene, both cameras save to disk, and we have a first
success rate from the pretrained checkpoint.

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

## Next on the pod

The LeRobot version used with Isaac. Tracks 1 and 2 used `0.6.1` on the laptop. On the
pod we install whatever LeIsaac imports, write it in the lab log, and use that same
version for training and evaluation.
