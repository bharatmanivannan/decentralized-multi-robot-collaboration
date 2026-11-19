# Decentralized Multi-Robot Collaboration

CMPE 295A. Advisor: Dr. Wencen Wu.

One simulated SO-101 arm, driven by SmolVLA, that picks three oranges and puts them on a plate. Later we copy that same policy onto a second arm. Everything is simulation.

## Where we are

The simulator is Dr. Wu's RTX 4090 in the lab. Isaac Sim is up, the kitchen scene loads, and the arm is visible in the viewport.

I scored the pretrained checkpoint and a random policy. Both are 0/3. That is the floor. What is left is the fine-tune on HPC, then scoring that checkpoint back on this machine with the same script and the same seed.

## Flow

1. Dataset and model checks on the laptop. Done. The dataset is 60 episodes. The pretrained model loads and returns six joint numbers.
2. Isaac Sim on the RTX 4090, pick-orange scene visible. Done.
3. First rollout with pretrained SmolVLA. Done. The arm moves. Episode success is 0/3, and no orange ends up in the plate.
4. Same eval with random joint targets. Done. Also 0/3.
5. Fine-tune SmolVLA on the HPC. Smoke test on a few episodes, then all 60.
6. Bring that checkpoint back to the 4090 and run the same eval, seed 1000.
7. RL fine-tuning only after those imitation-learning numbers are in, if we still have time.

## Where to look

- [Lab log](Lab_log.md) — versions, the baseline table, and what I tried.
- [Phases](project_phases.md) — the same flow, with the settings.
- [Phase 1](phase1/README.md) — dataset and model writeups, plus the rollout.
- [Baseline rows](phase1/04_rollout/report/rollout_results.csv) — six episodes, three pretrained and three random.

## Setup

| Piece | Choice |
|---|---|
| Policy | `lerobot/smolvla_base` |
| Dataset | `LightwheelAI/leisaac-pick-orange` |
| Simulator | Isaac Sim 5.1.0, Isaac Lab 0.47.2, LeIsaac 0.4.0 |
| LeRobot | 0.4.2 |
| Scene | `LeIsaac-SO101-PickOrange-Direct-v0` |
| Machine | Lab RTX 4090 for simulation. HPC H100 or A100 for training. |
| Instruction | `Grab orange and place into plate` |
| Cameras | front → `camera1`, wrist → `camera2` |
| Action | shoulder pan, shoulder lift, elbow flex, wrist flex, wrist roll, gripper |
