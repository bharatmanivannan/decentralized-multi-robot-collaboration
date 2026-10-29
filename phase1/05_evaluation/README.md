# Phase 1 / 05 — Evaluation (Kanaka)

Lane owner: Kanaka Sarat Siripurapu

## Ready
- Metric definitions (per-orange rate, per-episode 0–3 histogram, 95% CI)
- Dataset fields the scorer needs (see `../01_dataset_exploration/`)
- Evaluation wrapper skeleton + per-episode CSV schema
- B0 / B1 run plans
- Failure label categories: collision, missed grasp, dropped orange, wrong placement, timeout, camera/action mismatch, policy server disconnect

## Waiting on
- A40 pod import + first rollout (Ritwik `03_sim_setup` / `04_rollout`)
- Final LeRobot version pin written into `Lab_log.md` (pod install)
- Confirmation that `-Direct-v0` success matches three-orange + return-to-rest

## Instruction / cameras (locked)
- Language: `Grab orange and place into plate`
- front → `camera1`, wrist → `camera2` (leave camera3 unused)
- First horizon: 16; sweep later 1–50

Workbook 2 writeup: `workbook/kanaka_wb2/Kanaka_Workbook2_Contribution.pdf`
