# Phase 1

Ritwik. Updated 18 Nov 2026.

Dataset, model, simulator, and the first rollout. The later steps, fine-tune then
rescore, are in [`../project_phases.md`](../project_phases.md).

| Track | GPU? | Status |
|---|---|---|
| [01 dataset](01_dataset_exploration/report/dataset_report.md) | No | Done |
| [02 model](02_model_exploration/report/contract_test_report.md) | No | Done |
| [03 simulator](03_sim_setup/RUNBOOK.md) | Yes | Done, on the lab RTX 4090 |
| [04 rollout and baseline](04_rollout/report/rollout_results.csv) | Yes | Done. Pretrained and random are both 0/3 |

I did the dataset and the model on the laptop. The simulator and the rollouts are on
Dr. Wu's RTX 4090. Isaac Sim 5.1.0, Isaac Lab 0.47.2, LeIsaac 0.4.0, LeRobot 0.4.2.
The old runbooks still say RunPod and Isaac 4.5. That plan changed once this machine
was available.

---

## Settings we use from here on

These came out of tracks 1 and 2. Tracks 3 and 4 use them as is.

| Setting | Value |
|---|---|
| Instruction | `Grab orange and place into plate` |
| Camera mapping | `front` → `camera1`, `wrist` → `camera2`. Leave the third camera unused. |
| Joint order | shoulder pan, shoulder lift, elbow flex, wrist flex, wrist roll, gripper |
| Action horizon | 16 for the first rollout. Sweep 1 to 50 later. The model returns at most 50. |
| Scene | `LeIsaac-SO101-PickOrange-Direct-v0` |
| Episode length | 60 s at 60 Hz for the baseline |
| Simulator | Isaac Sim 5.1.0 on the lab RTX 4090. Viewport to look, headless to score. |

## Dataset

```bash
python phase1/01_dataset_exploration/explore_dataset.py
```

60 episodes of the SO-101 picking three oranges into a plate. 36,293 frames at 30 fps,
front and wrist cameras at 480×640, six joint actions.

The task string in the dataset is `Grab orange and place into plate`. That is the
instruction we pass to the model.

![Front camera, episode 0, start / middle / end](01_dataset_exploration/report/ep000_front_start_mid_end.jpg)

*Episode 0 from the front camera. Left is the start: three oranges on the table and the
arm at rest. Middle is mid-episode, one orange already in the plate. Right is the end:
all three in the plate and the arm back at rest.*

Full writeup with every figure:
[dataset report](01_dataset_exploration/report/dataset_report.md)

## Model

```bash
python phase1/02_model_exploration/contract_test.py
```

I loaded `lerobot/smolvla_base` (450M parameters) and ran one real frame from the
dataset through it. It returns six numbers in our joint order. That is what we needed
from this step: the pretrained model loads and talks to this arm.

The numbers themselves are close to zero on every joint, while the demonstration on that
frame is in the tens of degrees. That is the starting point before fine-tuning.

Full writeup: [model report](02_model_exploration/report/contract_test_report.md)

## Simulator and rollout

The scene is `LeIsaac-SO101-PickOrange-Direct-v0`. I loaded it in the viewport first
so I could see the arm, the three oranges, and the plate. Scoring was headless, because
the viewport is too slow for a full episode.

The eval script is LeIsaac's `scripts/evaluation/policy_inference.py`. Pretrained
SmolVLA talks to `start_policy_server.py`. Random actions are `--policy_type=random`.

Three episodes each, seed 1000, 60 seconds, horizon 16.

| Policy | Episode success | Oranges in the plate |
|---|---|---|
| `lerobot/smolvla_base` | 0/3 | 0, 0, 0 |
| random joints | 0/3 | 0, 0, 0 |

The rows are in [rollout_results.csv](04_rollout/report/rollout_results.csv). Zero is
the floor. The fine-tune has to beat it.

## Rerunning the laptop tracks

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python "lerobot[smolvla]==0.6.1" pandas pyarrow matplotlib
.venv/bin/python phase1/01_dataset_exploration/explore_dataset.py
.venv/bin/python phase1/02_model_exploration/contract_test.py
```

Versions I used are in [`requirements-phase1.txt`](requirements-phase1.txt). Both scripts
ran on an M-series Mac, no GPU.
