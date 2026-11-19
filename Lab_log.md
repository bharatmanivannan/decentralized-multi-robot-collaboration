# Lab log

Project: Decentralized Multi-Robot Collaboration (CMPE 295A)
Advisor: Dr. Wencen Wu
Owner: Ritwik
Updated: 2026-11-18

Dated record of what we tried, what we decided, and where the machines are. Current task split is in `team_workflow.md`. Phase plan and dates are in `project_phases.md`.

## Where we are

Training stays on the HPC3 H100 and A100 queues.

The simulator host for the Phase 1 baseline was a **RunPod A40** on 18 Nov 2026.
Isaac Sim 4.5.0 rendered the pick-orange scene headless, and the pretrained SmolVLA
rollout scored 0/5. The campus RTX 4090 I sat at that day is `10.31.82.76`
(`cmpe-4090`). The address Dr. Wu wrote down, `enp14s0: 10.31.82.102`, is a different
machine. I have not logged into it. SSH from my Mac to `.102` timed out.

Isaac Sim on the pod is 4.5.0, installed with pip, not from `nvcr.io/nvidia/isaac-sim:4.5.0`.
The pod has no Docker daemon. Driver on that A40 is `570.211.01`, which is new enough
for Isaac 5.x, and I still installed 4.5 because that is the version this project is
pinned to. LeIsaac is `493f91c`, not current HEAD.

Dataset and model tracks were already done on my laptop. The pod run is written up in
`phase1/README.md` on branch `feature/baselinework_runpod`. `feature/ritwik_workflow`
does not contain it.

## Decisions

| Date | Decision | Why |
|---|---|---|
| 2026-09-19 | Train on HPC3 H100 or A100. Simulate only on an RT-core GPU. | H100 and A100 have no RT cores. Isaac Sim will not render cameras on them. |
| 2026-09-22 | Isaac on the g17 login node stays at 4.5. Driver there is 560.35.03. | Dr. Wu. Isaac 5.x wants a newer driver. |
| 2026-09-22 | Training stays on the H100 and A100 queues. | Dr. Wu. |
| 2026-09-23 | Stop trying to view g17 Isaac through SSH. | Signaling is TCP `49100`. Video is UDP `47998`. SSH forwards TCP only. |
| 2026-09-29 | Simulator host is Dr. Wu's on-campus RTX 4090 workstation. | The login-node A40 renders, and the picture cannot leave the cluster. RunPod was only a stand-in while this machine was unconfirmed. |
| 2026-10-26 | Phase 1 simulator host is a RunPod A40. | Lets Phase 1 run now. The A40 is the card we already had Isaac Sim 4.5.0 rendering on at driver 560.35.03. |
| 2026-10-26 | Instruction is `Grab orange and place into plate`. | That is the task string in the dataset. |
| 2026-10-26 | Action horizon first rollout is 16, sweep later is 1 to 50. | `smolvla_base` returns at most 50 future actions per query. |
| 2026-10-26 | Camera mapping is front → `camera1`, wrist → `camera2`. Third camera unused. | Checkpoint names cameras `camera1/2/3`. SO-101 has two. |
| 2026-11-18 | Pod Isaac is pip Isaac Sim 4.5.0, not the NGC container. LeIsaac stays at `493f91c`. | This pod image has no Docker. Current LeIsaac targets Isaac 5.1. |
| 2026-11-18 | Policy server is LeRobot 0.3.3, separate from the Isaac env. Laptop checks stay on 0.6.1. | LeIsaac's gRPC client was generated against 0.3.3. |
| 2026-11-18 | Pretrained rollout uses the 24 Jun 2025 `smolvla_base` weights plus the current camera names. | LeRobot 0.3.3 left the Hub checkpoint's normalization buffers at infinity, so the first actions were all zeros. |
| 2026-11-18 | WebRTC is not a blocker for the baseline. | Saved frames and the CSV are the record. The live viewer was not confirmed. |

## Open items

- Eval script: more seeds, per-orange rate, 95% CI, horizon sweep. Random-action baseline was started and not finished.
- Fine-tune on HPC3. Not started.
- WebRTC from a machine that can send UDP. Pod publishes TCP `22077` → `49100` and UDP `22078` → `47998`. The client still dials `49100` and `47998`. Isaac 4.5 cannot advertise the public ports. I did not get a picture.
- `10.31.82.102` is not the 4090 I used (`10.31.82.76`). Login there is still unknown.
- The normalization-stat load fix is in the pod's `/workspace/lerobot` checkout, not in this repo. A fresh 0.3.3 install will hit the infinity-buffer failure again unless that load path is patched or the 24 Jun 2025 weights are used with the same fix.

## What we tried

### 1. HPC access and the GPU census (Sep 19)

`ssh coe-hpc3` lands on `g17.hpc.coe`. An A100 job on the `condo` partition ran and exited. The only working RT-core GPU on that login node is an A40. Slurm marks it `IDLE+DRAIN` and will not schedule it. `condo3` has another A40 and is down.

### 2. Isaac Sim 4.5 on the g17 A40 (Sep 22)

Pulled `docker://nvcr.io/nvidia/isaac-sim:4.5.0` into `$HOME/isaac/isaac-sim-4.5.0.sif` (5.9 GB, Ubuntu 22.04, version `4.5.0-rc.36`). g17 cannot open port 443, so the pull went through an HTTP proxy on `coe-hpc1`. Runtime is Apptainer (`apptainer exec --nv`), not Docker. A 40 GB overlay at `/tmp/isaac-overlay.img` disappears on reboot.

The streaming app loaded (`Isaac Sim Full Streaming App is loaded.`). The GPU was in use (about 2814 MiB, high utilization), so the viewport was rendering on the A40. Launch needs `ACCEPT_EULA=Y` and `--/rtx/verifyDriverVersion/enabled=false`. Without `http_proxy=http://127.0.0.1:8888` the process sits in libcurl timeouts against the asset server.

### 3. The WebRTC window stayed black (Sep 22)

The desktop client is the Isaac Sim WebRTC Streaming Client. It uses TCP `49100` for signaling and UDP `47998` for the picture. From a laptop, the only path to g17 is SSH. `ssh -L` forwards TCP, so the client connects and the window stays black. g17's address `172.16.1.81` is not reachable from off-cluster machines.

Killing the Apptainer parent does not stop Isaac. Kit gets reparented to PID 1 and keeps the GPU. The kit process itself has to be killed. That leftover process was stopped at 23:27 PDT on Sep 22.

### 4. Flags that do not steer this image (Sep 22 night)

- `--/exts/omni.kit.livestream.app/primaryStream/publicIp=127.0.0.1`. That extension is Isaac Sim 5/6. It is not in this image.
- `--/app/livestream/publicEndpointAddress=127.0.0.1`. Kit accepted it on the command line. The string is not in the 4.5 livestream plugins, and the log never showed the advertised address changing.

This image's WebRTC extension is `omni.kit.livestream.webrtc` 6.0.0. The settings it declares are `app.livestream.port = 49100`, `app.livestream.proto = "websocket"`, `app.livestream.ipversion = "ipv4"`.

### 5. Socat, considered and dropped (Sep 23)

Wrapping UDP `47998` in TCP and carrying it through SSH was not run. The picture travels from Isaac out to the client, `coe-hpc1` has no `socat`, and plain socat drops RTP datagram boundaries. Do not retry it.

### 6. Omniverse Streaming Client, considered and dropped (Sep 23)

That client speaks the older native protocol (`isaacsim.exp.full.old_streaming.kit`, signaling websocket on TCP `48010`). It does not attach to the WebRTC process we ran. The native path in the same image is still UDP for the picture, so SSH would leave the window black again.

### 7. Dataset and model, laptop (Oct 26)

Both done on an M-series Mac, no GPU, no simulator. Writeups are under `phase1/`.

Dataset, 7/7. 60 episodes, 36,293 frames, 30 fps, SO-101, action and state `[6]` in our
joint order, front and wrist at 480×640. Task string: `Grab orange and place into plate`.
Median episode about 18 s. Three oranges per episode.

Model, 5/5. `lerobot/smolvla_base` loads at 450.0M and returns six numbers in our joint
order, chunk `(1, 50, 6)`. Camera mapping, instruction and horizon cap of 50 are in the
decisions table.

## Notes

- Do not view Isaac on g17 from a laptop. The Phase 1 baseline was a RunPod A40, headless, frames on disk.
- LeRobot on the pod is 0.3.3. The laptop contract test is 0.6.1. Do not mix those envs.
- Leave SmolVLA's third camera key out. Do not feed it a black image.
- Always pass the instruction `Grab orange and place into plate`.
- Do not `srun` to get the g17 A40. Slurm will not schedule it.
- Do not upgrade this project's Isaac past 4.5 just because the pod driver is 570.
- Do not pass `primaryStream/publicIp` or `publicEndpointAddress` on this 4.5 image.
- Do not put NGC API keys, passwords, or tokens in the repo.
- Stop the pod when it is idle. Do not terminate it if the network volume should keep the install, the weights, and this checkout.

## 8. RunPod A40 baseline (18 Nov 2026)

Pod `tdafx5vwk5z19c`, EU-SE-1, public address `194.68.245.65` while it was up. That address changes if the pod is recreated. SSH was public TCP `22076` to container `22`.

`nvidia-smi`: NVIDIA A40, driver `570.211.01`, CUDA 12.8, 46068 MiB. The machine is the container, so there is no Docker socket. I did not pull `nvcr.io/nvidia/isaac-sim:4.5.0`.

Installed into `/workspace/isaac/env`: Isaac Sim 4.5.0.0, Isaac Lab v2.1.1, LeIsaac `493f91c`. `isaaclab.sh` forced `torch 2.7.0+cu128`. Headless `LeIsaac-SO101-PickOrange-v0` saved `phase1/03_sim_setup/report/front.png` and `wrist.png`. Both are real pictures of the scene.

Policy server: `/workspace/lerobot` at v0.3.3, its own venv, port 8080. Client is `phase1/04_rollout/run_pretrained_rollout.py`. It renames `front` to `camera1` and `wrist` to `camera2`. Five episodes, seed 1000, horizon 16, 120 s. Result: **0 oranges in every episode, 0/5 successes, every episode timed out.** CSV: `phase1/04_rollout/report/rollout_results.csv`.

A random-action episode was not completed. I killed it after the simulator stalled.

WebRTC was not started. Signaling and video would have had to cross `22077` and `22078`, and the 4.5 client does not know those public ports.

## Next

1. Eval script, then the horizon sweep.
2. Fine-tune on HPC3 and score it with the same seeds.
3. Live viewer only after the client machine rewrites ports `49100` and `47998`.
