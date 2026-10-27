# Decentralized Multi-Robot Collaboration

CMPE 295A. Advisor: Dr. Wencen Wu.

One simulated SO-101 arm, driven by SmolVLA, that can see an orange, pick it up and put it
on a plate. Later we copy the same policy onto a second arm. Everything is in simulation.

## Where to start

- [Phase 1](phase1/README.md) — current work. Dataset and model are done. Simulator and the
  first rollout are next, once a RunPod A40 is available.
- [Phases](project_phases.md) — what comes after this: evaluation in November, then
  fine-tuning on HPC.
- [Lab log](Lab_log.md) — machines, versions, and the dated decisions.
- [Workbook 1](workbook/Multi-Robot%20Collaboration%20Project%20Workbook.pdf)

## The setup we are using

| Piece | Choice |
|---|---|
| Policy | `lerobot/smolvla_base` |
| Dataset | `LightwheelAI/leisaac-pick-orange` |
| Simulator | Isaac Sim 4.5.0, Isaac Lab v2.1.1, LeIsaac |
| Scene | `LeIsaac-SO101-PickOrange-Direct-v0` |
| Instruction | `Grab orange and place into plate` |
| Cameras | `observation.images.front` and `observation.images.wrist` |
| Action | 6 joints: shoulder pan, shoulder lift, elbow flex, wrist flex, wrist roll, gripper |
