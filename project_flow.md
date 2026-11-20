# Project flow

Ritwik. Updated 20 Nov 2026.

The simulator is Dr. Wu's RTX 4090. Training stays on the HPC. Dated notes are in `Lab_log.md`.

## Done

1. Dataset check on the laptop. 60 episodes, 36,293 frames, 30 fps, six joints, front and wrist at 480×640.
2. Model check on the laptop. `lerobot/smolvla_base` loads, 450M parameters, and returns six numbers. Those numbers sit near zero. The demonstrations on that frame are in the tens of degrees.
3. Isaac Sim 5.1.0, Isaac Lab 0.47.2, LeIsaac 0.4.0 on the 4090. The kitchen scene loads.
4. Headless baseline. Seed 1000, 3 episodes, 60 seconds, horizon 16.

| Policy | Grasp | Place | Task complete | Gripper |
|---|---|---|---|---|
| Pretrained SmolVLA | 0/3 | 0/3 | 0/3 | about -10 to 0 deg |
| Random | 0/3 | 0/3 | 0/3 | wide swing, no grasp |

Clips are under `videos/`. Rows are in `flow/04_rollout/report/eval_metrics.csv`. The script is `flow/04_rollout/eval_rollout.py`.

## Next

1. Smoke test on an H100 or A100. Fine-tune on 3 to 5 episodes and watch the loss drop. Those weights only prove training runs.
2. Full fine-tune on all 60 episodes, about 20,000 steps. LeRobot 0.4.2, same as the 4090, or the checkpoint will not load.
3. Bring the checkpoint back and run `eval_rollout.py` again. Same scene, seed 1000, 60 seconds. Write the clips into `videos/finetune/` and append rows to the same csv.

That comparison is the result. RL comes after it, if there is time before 4 December.

## Settings

| Item | Value |
|---|---|
| Policy | `lerobot/smolvla_base` |
| Dataset | `LightwheelAI/leisaac-pick-orange` |
| Scene | `LeIsaac-SO101-PickOrange-Direct-v0` |
| Simulator | Isaac Sim 5.1.0, Isaac Lab 0.47.2, LeIsaac 0.4.0 |
| LeRobot | 0.4.2 |
| Sim machine | Lab RTX 4090, headless |
| Train machine | HPC H100 or A100 |
| Cameras | front → `camera1`, wrist → `camera2` |
| Instruction | `Grab orange and place into plate` |
| Horizon | 16 |
| Metric | grasp rate, place rate, task completion, gripper range |
