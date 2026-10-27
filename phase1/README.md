# Phase 1

Ritwik. Updated 26 Oct 2026.

This is the current work. Get the dataset, the model and the simulator talking the same
language, then run one rollout with the pretrained checkpoint.

Phases 2 and 3 start in November. Details are in [`../project_phases.md`](../project_phases.md).

| Track | GPU? | Status |
|---|---|---|
| [01 dataset](01_dataset_exploration/report/dataset_report.md) | No | Done |
| [02 model](02_model_exploration/report/contract_test_report.md) | No | Done |
| [03 simulator](03_sim_setup/RUNBOOK.md) | Yes | Waiting on a RunPod A40 |
| [04 one rollout](04_rollout/RUNBOOK.md) | Yes | After the simulator is up |

I did the dataset and the model first because both run on a laptop. The two remaining
tracks need the pod.

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
| Episode length | 120 s at 30 Hz |
| Simulator | Isaac Sim 4.5.0, headless, cameras saved to disk |

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

Both have a runbook with the commands ready. Plan is:

1. Bring up a RunPod A40 with Isaac Sim 4.5.0.
2. Install Isaac Lab v2.1.1 and LeIsaac.
3. Load the pick-orange scene, headless, and save a front frame and a wrist frame.
4. Run one rollout with the pretrained checkpoint and write down the success rate.

I am running the sim headless and saving camera frames to disk. We do not need a live
viewport for this.

## Rerunning the laptop tracks

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python "lerobot[smolvla]==0.6.1" pandas pyarrow matplotlib
.venv/bin/python phase1/01_dataset_exploration/explore_dataset.py
.venv/bin/python phase1/02_model_exploration/contract_test.py
```

Versions I used are in [`requirements-phase1.txt`](requirements-phase1.txt). Both scripts
ran on an M-series Mac, no GPU.
