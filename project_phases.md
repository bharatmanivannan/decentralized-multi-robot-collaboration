# Project phases

Ritwik. Updated 18 Nov 2026.

The simulator ended up on Dr. Wu's RTX 4090, not a RunPod. Isaac Sim 5.1 is what LeIsaac 0.4.0 wants on this driver, so that is what I installed. Dated notes are in `Lab_log.md`.

## Flow

1. Dataset and model checks on the laptop. Done.
2. Isaac Sim on the RTX 4090, scene visible. Done.
3. First rollout, pretrained SmolVLA. Done. 0/3.
4. Random-action baseline, same script. Done. 0/3.
5. Fine-tune on HPC. Smoke test, then all 60 episodes.
6. Score that checkpoint on the 4090, same script, seed 1000.
7. RL fine-tuning only if the imitation-learning numbers are already in.

## What is done

| Track | Status |
|---|---|
| Dataset, `LightwheelAI/leisaac-pick-orange` | Done. 60 episodes, 36,293 frames, 30 fps. |
| Model, `lerobot/smolvla_base` | Done. 450M parameters, six numbers in our joint order. |
| Simulator on the RTX 4090 | Done. Isaac Sim 5.1.0, Isaac Lab 0.47.2, LeIsaac 0.4.0. Viewport works. |
| Pretrained rollout | Done. 3 episodes, seed 1000, 60 s, horizon 16. Success 0/3. Oranges in plate: 0, 0, 0. |
| Random baseline | Done. Same setup. Success 0/3. Oranges in plate: 0, 0, 0. |

Rows are in `phase1/04_rollout/report/rollout_results.csv`.

An episode is a success only when all three oranges are in the plate and the arm is back at rest. `oranges_placed` is how many oranges finished within 10 cm of the plate. The eval script is LeIsaac's `scripts/evaluation/policy_inference.py`. The policy server is `start_policy_server.py`.

## What is left

Fine-tune SmolVLA on the HPC H100 or A100, on `LightwheelAI/leisaac-pick-orange`.

1. Smoke test: overfit 3 to 5 episodes and watch the loss drop. Those weights only prove training runs. They are not the policy we score.
2. Full fine-tune on all 60 episodes, around 20,000 steps. Use LeRobot 0.4.2, the same version as the 4090, or the checkpoint will not load in the eval.
3. Copy the checkpoint back to the lab machine and run `policy_inference.py` again. Same scene, seed 1000, 60 s, horizon 16, instruction `Grab orange and place into plate`.

That comparison, fine-tuned versus the 0/3 floor, is the result for the demo.

RL fine-tuning comes after that, if there is time before the 4 December demo.

## Settings

| Item | Value |
|---|---|
| Policy | `lerobot/smolvla_base`, 450M |
| Dataset | `LightwheelAI/leisaac-pick-orange`, 60 episodes |
| Simulator | Isaac Sim 5.1.0, Isaac Lab 0.47.2, LeIsaac 0.4.0 |
| LeRobot | 0.4.2, on the 4090 and on the HPC |
| Scene | `LeIsaac-SO101-PickOrange-Direct-v0` |
| Simulator machine | Lab RTX 4090 |
| Training machine | HPC3 H100 or A100 |
| Action | 6 joints, dataset order |
| Cameras | `front` → `camera1`, `wrist` → `camera2` |
| Instruction | `Grab orange and place into plate` |
| Episode length | 60 s at 60 Hz for the baseline. The runbook still says 120 s at 30 Hz. |
| Action horizon | 16 |
| Metric | episode success, plus oranges in the plate (0 to 3) |
