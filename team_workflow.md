# Team workflow

Project: Decentralized Multi-Robot Collaboration (CMPE 295A)
Advisor: Dr. Wencen Wu
Written: 2026-09-24
Current status is in `README.md` and `project_phases.md`. This file is the original task split from September. The simulator is the lab RTX 4090, and the pretrained and random baselines are both 0/3.

Semester 1 is one simulated SO-101 arm, driven by SmolVLA, that can see an object, center on it, and pick it up, with a measured success rate. Semester 2 copies that same brain onto a second arm and cuts communication. Everything is simulation. That is the big picture, need everyone to read the CHORUS Framework (Multi-Robot Collaboration) that will be challenging task for us, anyway we will focus on that at the end of the semester.

Training stays on the HPC3 H100 and A100 queues. The simulator stays on a ray-tracing GPU. We Fill the blank names at the next team meeting.

---

## Already decided

- Isaac Sim image: `nvcr.io/nvidia/isaac-sim:4.5.0`. Driver target: 560.35.03. Isaac 5.x fails on that driver. This was confirmed on the HPC login-node A40. Use the same pin on RunPod.
- Pair Isaac Lab with the release built for Isaac Sim 4.5. Leave the Isaac Lab line that tracks Isaac Sim 5 alone.
- Fine-tune dataset: `LightwheelAI/leisaac-pick-orange`. It was recorded for Isaac. 60 episodes, 30 fps, 6 joint actions, front and wrist cameras.
- The two sibling sets stay as reference only: `LightwheelAI/so101-pick-pen` (61 episodes) and `LightwheelAI/so101-place-orange` (61 episodes). Same robot, same cameras, same 6-number action.
- Action on all three: shoulder pan, shoulder lift, elbow flex, wrist flex, wrist roll, gripper.
- Camera keys the scene has to produce: `observation.images.front` and `observation.images.wrist`. Both are 480×640 color at 30 fps.
- Official SmolVLA guidance: start with about 50 clean episodes of one task. Their own pick-and-place set used 50 episodes across 5 object positions. 25 was not enough. Our set is 60.
- A logged success rate of 0% on the pretrained checkpoint is a pass. The scoreboard existing is the milestone.
- The five-episode overfit is a smoke test. It proves LeRobot can train. Those weights are not the policy we deploy and not the semester baseline.
- The 21,500-episode BenchHub kitchen suite is optional later. Semester 1 is one arm, one pick task.

[Also, note: I met with our advisor, and she is providing us with RTX 4090, so we can do our simulations there, RunPod is something Im trying out instead of sitting idle and waiting for access]

---

## Who owns what

| Track | Owner | Status | Needs the simulator? |
|---|---|---|---|
| 1. Isaac Sim on the lab RTX 4090, SO-101 visible | Ritwik | Done | Yes. This is the simulator. |
| 2. Pretrained SmolVLA, one dataset frame, 6-number action | Ritwik | Done | No |
| 3. One rollout: arm moves, 6 joints, cameras render | Ritwik | Done. 0/3 | Yes |
| 4. Eval script and the zero-training success rate | Ritwik | Done. Pretrained and random are both 0/3 | The final run does |
| 5. `leisaac-pick-orange` dataset notes | ________ | Start now | No |
| 6. Reference paper stack, from the team PPT | ________ | Start now | No |
| 7. Workbook 1 draft, group submission, due Oct 1 | ________ | Start now | No |
| 8. Meeting log for advisor meetings and team meetings | Whole team | Next meeting | No |
| 9. Five-episode smoke test, then the real HPC fine-tune | Ritwik | Next | No. This is HPC. |

Tracks 2, 5, 6, and 7 run at the same time as track 1. Nobody waits on the pod for those.

---

## 1. Simulator — Ritwik

Do these in order.

1. Create a RunPod account.
2. Launch a pod with an RTX 4090. Use an A40 if we want 48 GB from day one. The 4090 is 24 GB and is enough to start; the A40 is the safer VRAM choice.
3. Attach a Network Volume of at least 100 GB. It has to hold Isaac Sim, the container, and the first dataset.
4. Record `nvidia-smi` (driver, CUDA, memory) in `LAB_LOG.md` before installing. Installation target remains Isaac Sim 4.5.0 on the 560.35.03 driver line. If the pod driver is newer, still install 4.5.0. Do not install Isaac 5.x.
5. Pull `nvcr.io/nvidia/isaac-sim:4.5.0` into that volume.
6. Get the SO-101 arm loaded and visible in the browser.
7. Load the same arm in Isaac Lab from the `leisaac-pick-orange` scene definition.

The lab RTX 5090 visit is a separate host decision. Record `nvidia-smi` and how that machine is reached (console, SSH, or remote desktop) before anyone changes an Isaac version on it. Training does not move. It stays on the H100 and A100 queues.

---

## 2. Pretrained checkpoint, one frame — assignee

Load the Hugging Face SmolVLA weights. Run the pretrained checkpoint on one frame from `LightwheelAI/leisaac-pick-orange`. No training. No simulator.

This is the test that the model loads and speaks SO-101. It can finish before the pod exists.

---

## 3. One rollout — Ritwik, after track 1

Load the SO-101 arm from the `leisaac-pick-orange` scene. Feed it actions. Confirm three things:

- the arm moves
- the action is 6 numbers, same order as track 2
- the front and wrist cameras render

---

## 4. Eval script and the zero-training score — assignee plus Ritwik

Write a Python eval script that talks to the simulator, runs the pretrained unfine-tuned checkpoint in the `leisaac-pick-orange` scene, and prints a success rate.

The assignee researches the metric and brings a draft. Ritwik sits with them and they finalize it together: what counts as a success, what counts as a failure, how many trials, and what the script prints.

Draft the success definition from track 5 before the sim hookup, so the script is waiting when the arm can move.

---

## 5. Dataset — assignee

Primary set: `LightwheelAI/leisaac-pick-orange`.

Write one short note the eval script can use:

- what the task is
- what success should mean
- what failure looks like
- episode count, fps, action names, camera keys, resolution

Check the Hugging Face page and a few episode videos. The siblings (`so101-pick-pen`, `so101-place-orange`) are the same robot and the same 6-number action. Note anything that would break a shared loader. We are fine-tuning on `leisaac-pick-orange`.

---

## 6. Reference papers — assignee

Dr. Wu asked for a stacked reference set. Start from the team PPT already made, then read the papers behind those slides and file short working notes, one page each. Keep the CASE see-center-grasp loop and its metrics, and the CHORUS point that identical weights might replace communication. Add the other references the PPT already cites. Working notes, not new slides.

---

## 7. Workbook 1 — assignee

Group submission, due **October 1**. One teammate drafts. The group reviews before submit. One person submits for the group. This is the nearest deadline. Keep it off the simulator work.

---

## 8. Meeting log — next team meeting, everyone

Next time we meet, set up `lab/MEETING_LOG.md` and use it from then on. It covers both advisor meetings and team meetings. Same entry shape every time:

- date, who was there, advisor meeting or team meeting
- decisions, each with a one-line reason
- doubts raised, and whether they are resolved
- open questions
- action items with an owner and a date

At that meeting, also put names on the blank rows above and clear the open doubts we already have:

- lasting simulator host: RunPod, or the lab RTX 5090 after we have its driver and access method
- where large datasets live on HPC, until `/scratch` or `/data` is writable
- the success rule for pick-orange, from tracks 4 and 5

---

## 9. Fine-tune — next

Tracks 1 through 4 are done. The simulator is the lab RTX 4090, and both baselines are 0/3. Training stays on the HPC.

1. On an H100 or A100, fine-tune SmolVLA on 3 to 5 episodes of `leisaac-pick-orange` for a few hundred steps and watch the loss drop. That only proves LeRobot can train. Those weights memorized a handful of demos.
2. Then the real fine-tune on all 60 episodes. About 20,000 steps, roughly 4 hours on one A100. Use LeRobot 0.4.2 so the checkpoint loads in the eval we already ran.
3. Copy the checkpoint back to the 4090 and score it with `policy_inference.py`, seed 1000, 60 s, horizon 16.

---

## Order

```text
Done
  Dataset and model checks on the laptop
  Isaac Sim 5.1 on the lab RTX 4090, scene visible
  Pretrained rollout, 0/3
  Random baseline, 0/3

Next
  HPC smoke test, 3 to 5 episodes
  Full fine-tune, all 60 episodes, LeRobot 0.4.2
  Score that checkpoint on the 4090, same script, seed 1000

After that, if there is time
  RL fine-tuning
```
