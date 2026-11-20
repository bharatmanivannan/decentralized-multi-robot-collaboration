# Decentralized Multi-Robot Collaboration

CMPE 295A. Advisor: Dr. Wencen Wu.

One simulated SO-101 arm, driven by SmolVLA, picking three oranges onto a plate. Later the same policy goes on a second arm. Everything is simulation.

We are about halfway. The lab RTX 4090 runs the scene, the baseline is scored, and the videos are saved. What is left is the HPC fine-tune, then scoring that checkpoint the same way.

## Baseline

Seed 1000. Three episodes. 60 seconds. Headless. Front and wrist cameras.

| Policy | Grasp | Place | Task complete | Gripper |
|---|---|---|---|---|
| Pretrained SmolVLA | 0/3 | 0/3 | 0/3 | stuck around -10 to 0 deg |
| Random | 0/3 | 0/3 | 0/3 | swings wide, still no grasp |

Grasp means the gripper got onto an orange. Place means an orange ended in the plate. Task complete means all three are in the plate and the arm is back at rest. The pretrained gripper never closes, so the later rates stay at zero.

Per-episode rows: [flow/04_rollout/report/eval_metrics.csv](flow/04_rollout/report/eval_metrics.csv).

## Videos

Front camera on the left, wrist on the right. [videos/README.md](videos/README.md).

| Folder | What |
|---|---|
| `videos/ground_truth/` | Dataset demos. This is a finished pick. |
| `videos/baseline/pretrained/` | Untrained SmolVLA. |
| `videos/baseline/random/` | Random joint targets. |
| `videos/finetune/` | Empty until the HPC checkpoint is scored. |

## Flow

1. Dataset and model checks on the laptop. Done.
2. Isaac Sim on the RTX 4090. Kitchen scene loads. Done.
3. Headless baseline, pretrained and random, with video. Done. Both 0/3.
4. Smoke test on HPC, a few episodes, watch the loss drop.
5. Full fine-tune on all 60 episodes. LeRobot 0.4.2.
6. Score that checkpoint on the 4090. Same script, seed 1000. Clips go in `videos/finetune/`.
7. RL only after those numbers are in, if there is time.

Detail is in [project_flow.md](project_flow.md). The working notes are in [flow/README.md](flow/README.md).

## Setup

| Piece | Choice |
|---|---|
| Policy | `lerobot/smolvla_base`, 450M |
| Dataset | `LightwheelAI/leisaac-pick-orange`, 60 episodes |
| Scene | `LeIsaac-SO101-PickOrange-Direct-v0` |
| Simulator | Isaac Sim 5.1.0, Isaac Lab 0.47.2, LeIsaac 0.4.0 |
| LeRobot | 0.4.2, on the 4090 and on the HPC |
| Machines | RTX 4090 for sim. H100 or A100 for training. |
| Instruction | `Grab orange and place into plate` |
| Cameras | front → `camera1`, wrist → `camera2` |
| Action | shoulder pan, shoulder lift, elbow flex, wrist flex, wrist roll, gripper |
