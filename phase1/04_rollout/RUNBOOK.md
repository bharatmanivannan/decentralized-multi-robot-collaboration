# Track 4 — One rollout

Ritwik. Status: after track 3.

Close the loop once with the pretrained checkpoint. Arm moves, action is six numbers,
both cameras save to disk, and we write down a success rate.

Needs [`../03_sim_setup/RUNBOOK.md`](../03_sim_setup/RUNBOOK.md) done first.

## Settings from tracks 1 and 2

- Instruction: `Grab orange and place into plate`
- Camera mapping: `front` → `camera1`, `wrist` → `camera2`
- Scene: `LeIsaac-SO101-PickOrange-Direct-v0`
- Horizon: 16
- Episode length: 120 s at 30 Hz

`--policy_language_instruction` has to be set. If it is left off, the policy gets
`None` as the task.

## Run

Start the LeRobot policy server with `lerobot/smolvla_base`, then:

```bash
python scripts/evaluation/policy_inference.py \
    --task=LeIsaac-SO101-PickOrange-Direct-v0 \
    --policy_type=lerobot-smolvla \
    --policy_checkpoint_path=lerobot/smolvla_base \
    --policy_host=localhost \
    --policy_port=5555 \
    --policy_action_horizon=16 \
    --policy_language_instruction="Grab orange and place into plate" \
    --episode_length_s=120 \
    --step_hz=30 \
    --eval_rounds=5 \
    --seed=1000 \
    --device=cuda \
    --enable_cameras \
    --headless
```

The Direct environment is the one with the programmatic success check.

This script reports success per episode. Our headline metric is per-orange, which is
phase 2. For this track, write down the per-episode rate and save frames.

Also run a random-action pass while the loop is up. Cheap, and it is the floor.

## Saving results

A few frames from each camera per episode, into `report/`. One row per episode in
`report/rollout_results.csv`, using the columns in `report/results_template.csv`.
Fill in the version fields. Horizon sweep and pooled numbers are phase 2.

## Done when

- the arm moves
- the action is six numbers in our joint order
- front and wrist frames are in `report/` at 480×640
- a per-episode success rate is written down, with seed and versions
