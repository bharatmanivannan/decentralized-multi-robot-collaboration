# Videos

Ritwik. 20 Nov 2026.

The csv is the score. These clips are the proof. Each file is front camera on the left and wrist camera on the right.

| Folder | What it is |
|---|---|
| `ground_truth/` | Demonstrations from `LightwheelAI/leisaac-pick-orange`. Episodes 0, 1, and 30. This is what a finished pick looks like. |
| `baseline/pretrained/` | `lerobot/smolvla_base`, no fine-tune. Headless eval, seed 1000. |
| `baseline/random/` | Random joint targets, same scene and seed. |
| `finetune/` | Empty until the HPC checkpoint is scored with the same script. |

Seed 1000, three episodes, 60 seconds, headless. Grasp, place, and task completion all came out 0/3 for both policies. The pretrained gripper barely moved, about -10 to 0 degrees. The random gripper swung across a wide range and still never closed on an orange.

The per-episode rows are in `flow/04_rollout/report/eval_metrics.csv`.

The mp4 files stay on the lab machine. They are too big for git.
