# Team workflow

Project: Decentralized Multi-Robot Collaboration (CMPE 295A)
Advisor: Dr. Wencen Wu
Written: 2026-09-24
This is the working plan.

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
| 1. RunPod, Isaac 4.5, SO-101 visible in the browser and loaded in Isaac Lab | Ritwik | In progress | Yes. This is the simulator. |
| 2. Pretrained SmolVLA, one dataset frame, 6-number action | ________ | Start now | No |
| 3. One rollout: arm moves, 6 joints, cameras render | Ritwik | Starts when track 1 is done | Yes |
| 4. Eval script and the zero-training success rate | ________ drafts, Ritwik finalizes with them | Start the metric draft now. The sim hookup waits on track 1. | The final run does |
| 5. `leisaac-pick-orange` dataset notes | ________ | Start now | No |
| 6. Reference paper stack, from the team PPT | ________ | Start now | No |
| 7. Workbook 1 draft, group submission, due Oct 1 | ________ | Start now | No |
| 8. Meeting log for advisor meetings and team meetings | Whole team | Next meeting | No |
| 9. Five-episode smoke test, then the real HPC fine-tune | Unassigned | Pending. Do not start. | No. This is HPC, after 1–4. |

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

**Done when:** the SO-101 arm from that scene is visible in the browser and loaded in Isaac Lab on the pod.

The lab RTX 5090 visit is a separate host decision. Record `nvidia-smi` and how that machine is reached (console, SSH, or remote desktop) before anyone changes an Isaac version on it. Training does not move. It stays on the H100 and A100 queues.

---

## 2. Pretrained checkpoint, one frame — assignee

Load the Hugging Face SmolVLA weights. Run the pretrained checkpoint on one frame from `LightwheelAI/leisaac-pick-orange`. No training. No simulator.

**Done when:** the script prints 6 numbers, in this order: shoulder pan, shoulder lift, elbow flex, wrist flex, wrist roll, gripper. Write down the checkpoint id and the output shape in the repo.

This is the test that the model loads and speaks SO-101. It can finish before the pod exists.

---

## 3. One rollout — Ritwik, after track 1

Load the SO-101 arm from the `leisaac-pick-orange` scene. Feed it actions. Confirm three things:

- the arm moves
- the action is 6 numbers, same order as track 2
- the front and wrist cameras render

**Done when:** those three are true and written into `LAB_LOG.md` the same day (driver, Isaac version, arm moved, action shape, cameras rendered).

---

## 4. Eval script and the zero-training score — assignee plus Ritwik

Write a Python eval script that talks to the simulator, runs the pretrained unfine-tuned checkpoint in the `leisaac-pick-orange` scene, and prints a success rate.

The assignee researches the metric and brings a draft. Ritwik sits with them and they finalize it together: what counts as a success, what counts as a failure, how many trials, and what the script prints.

**Done when:** the script runs on the pod and prints a success rate. Zero percent is a pass. The scoreboard existing is the milestone. That number is what the later fine-tune has to beat.

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

**Done when:** that note is in the repo and track 4 is using it.

---

## 6. Reference papers — assignee

Dr. Wu asked for a stacked reference set. Start from the team PPT already made, then read the papers behind those slides and file short working notes, one page each. Keep the CASE see-center-grasp loop and its metrics, and the CHORUS point that identical weights might replace communication. Add the other references the PPT already cites. Working notes, not new slides.

**Done when:** the stack is in the repo, each paper tied back to the slide it supports.

---

## 7. Workbook 1 — assignee

Group submission, due **October 1**. One teammate drafts. The group reviews before submit. One person submits for the group. This is the nearest deadline. Keep it off the simulator work.

**Done when:** a draft is in front of the group with enough time to review before Oct 1.

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

**Done when:** the log file exists, the Dr. Wu decisions already in `LAB_LOG.md` are copied in as the first entries, and every track above has a name.

---

## 9. Pending, unassigned — do not start

Smoke test, then the real training run. Both wait until tracks 1 through 4 are done. There is too much in front of this.

When it is assigned, the order is:

1. On an HPC H100 or A100, with Python 3.12, fine-tune SmolVLA on 3 to 5 episodes of `leisaac-pick-orange` for a few hundred steps and watch the loss collapse. That only proves LeRobot can train. Those weights memorized a handful of demos.
2. Then start the real fine-tune on that same dataset on HPC. Hugging Face’s full SmolVLA fine-tune is about 20,000 steps, roughly 4 hours on one A100. The eval script from track 4 is how we score it.

**Not done until:** someone is named, and tracks 1 through 4 are already checked off.

---

## Order

```text
Now, in parallel
  Ritwik:        RunPod → Isaac 4.5.0 → SO-101 visible → Isaac Lab scene
  Teammate:      SmolVLA, one frame, 6 numbers
  Teammate:      leisaac-pick-orange notes (task, success, failure)
  Teammate:      paper stack from the team PPT
  Teammate:      Workbook 1 draft (due Oct 1)

After the arm is in the scene
  Ritwik:        one rollout (moves, 6 joints, cameras)

Together
  Eval owner + Ritwik:  finalize the script, print a success rate (0% passes)

Next meeting
  Everyone:      meeting log, names on the blank rows, clear the open doubts

Later, still unassigned
  HPC smoke test (3–5 episodes), then the real fine-tune on leisaac-pick-orange
