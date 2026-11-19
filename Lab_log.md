# Lab log

Project: Decentralized Multi-Robot Collaboration (CMPE 295A)
Advisor: Dr. Wencen Wu
Owner: Ritwik
Updated: 2026-11-18

Dated record of what we tried, what we decided, and where the machines are. Current task split is in `team_workflow.md`. Phase plan and dates are in `project_phases.md`.

## Where we are

Training stays on the HPC3 H100 and A100 queues.

The simulator host for Phase 1 is a **RunPod A40**. Dr. Wu's on-campus workstation is
the later host, after this submission. The HPC login-node A40 is not the plan: Isaac Sim
4.5 renders there, but the picture cannot leave the cluster.

Isaac Sim stays at 4.5.0 (`nvcr.io/nvidia/isaac-sim:4.5.0`). On the login node the driver is 560.35.03, and Isaac 5.x fails on that driver. The pod still needs its own `nvidia-smi` (driver, CUDA, memory) written into this file before anything is installed on it. Install 4.5.0 unless that driver reading says otherwise. Do not install Isaac 5.x on driver 560.

Dataset and model tracks are done under `phase1/`. Simulator setup and the first rollout
are next, once a pod is free. Both have runbooks.

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

## Open items

- LeRobot version on the pod: tracks 1 and 2 used `0.6.1` on the laptop. On the pod, install
  whatever LeIsaac imports, write it here, use that same version for training and evaluation.
- NGC key: rotate before the RunPod image pull. The September key was pasted into a chat.

## RTX 4090 lab workstation — versions (Nov 18)

This is Dr. Wu's on-campus RTX 4090 workstation, the machine from the Sep 29 decision.

```
nvidia-smi: Driver 580.178.04, CUDA 13.0
GPU: NVIDIA GeForce RTX 4090, 24564 MB
CPU: AMD Ryzen 9 7950X3D 16-Core, 64 GB RAM
OS: Ubuntu 24.04.4 LTS, Kernel 7.0.0-43-generic
```

| Package | Version | Notes |
|---|---|---|
| IsaacSim | 5.1.0.0 | pip install, not Docker |
| IsaacLab | 0.47.2 (v2.3.0) | from LeIsaac submodule |
| LeIsaac | 0.4.0 | from source |
| LeRobot | 0.4.2 | what LeIsaac imports, replaces 0.6.1 from the Mac |
| PyTorch | 2.7.0+cu128 | |
| TorchVision | 0.22.0+cu128 | |
| TorchAudio | 2.7.0+cu128 | |
| NumPy | 1.26.0 | |
| Transformers | 5.23.0 | |
| Python | 3.11 | conda env `leisaac` |
| SmolVLA | lerobot/smolvla_base | 450M, downloaded locally |
| Dataset | LightwheelAI/leisaac-pick-orange | 60 episodes, downloaded locally |

**Version change from the Mac:** LeRobot 0.4.2 here (what LeIsaac 0.4.0 requires) vs
0.6.1 on the laptop. Training on HPC must use the same LeRobot version as this
workstation. The contract test (phase 1 track 2) was run on 0.6.1 and the API may
differ slightly; the SmolVLA checkpoint is the same.

**Isaac Sim change:** 5.1.0 here vs the 4.5.0 planned in the runbook. Driver 580
supports 5.x. LeIsaac 0.4.0 targets 5.1.0 + Isaac Lab v2.3.0. The 4.5.0 runbook
steps do not apply to this setup.

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

- Do not view Isaac on g17 from a laptop. For Phase 1 the simulator host is a RunPod A40.
- Run Isaac headless on the pod and write camera frames to disk.
- Leave SmolVLA's third camera key out. Do not feed it a black image.
- Always pass `--policy_language_instruction="Grab orange and place into plate"`.
- Do not `srun` to get the g17 A40. Slurm will not schedule it.
- Do not upgrade Isaac past 4.5 on driver 560.35.03.
- Do not pass `primaryStream/publicIp` or `publicEndpointAddress` on this 4.5 image.
- Do not run a placeholder `python.sh` with `path/to/your/headless_script.py`. The streaming app is `./runheadless.sh` inside the container.
- Do not put NGC API keys, passwords, or tokens in the repo. The key used for the image pull was pasted into an earlier chat. Rotate it in NGC.

## RTX 4090 first rollout and baseline (Nov 18 night)

The scene loads in the native Isaac Sim 5.1 viewport on this machine. Headless
evaluation is what we use for numbers. Viewport rendering is too slow for batch runs.

Success for an episode is LeIsaac's `task_done`: all three oranges inside the plate
window and the arm back at rest. `oranges_placed` is the count of oranges whose XY
is within 10 cm of the plate, which is the per-orange piece of that check.

| Baseline | Episodes | Seed | Length | Horizon | Episode success | Oranges placed |
|---|---|---|---|---|---|---|
| Pretrained `lerobot/smolvla_base` | 3 | 1000 | 60 s at 60 Hz | 16 | 0/3 | 0, 0, 0 |
| Random joint targets | 3 | 1000 | 60 s at 60 Hz | 16 | 0/3 | 0, 0, 0 |

A shorter smoke run (one 30 s pretrained episode) also timed out at 0/1. Both floors
are 0%. That is the score the HPC fine-tune has to beat. Rows are in
`phase1/04_rollout/report/rollout_results.csv`.

Policy inference runs headless against a local gRPC policy server
(`start_policy_server.py`, lerobot 0.4.2 async inference). LeIsaac 0.4.0's client
was written for lerobot 0.3.3, so the client now sends cameras as `camera1`/`camera2`
and sets `must_go` so the server does not drop near-zero pretrained actions as
"too similar".

## Next, on the RunPod A40

Full step-by-step is in `phase1/03_sim_setup/RUNBOOK.md`. In short:

1. Rotate the NGC key before the image pull.
2. Create the pod: A40, Secure Cloud, container image set directly to
   `nvcr.io/nvidia/isaac-sim:4.5.0`, network volume of 100 GB or more in the same region as
   the GPU.
3. Record `nvidia-smi`: driver, CUDA, memory, and how the pod is reached. Before installing.
4. Import check: `isaacsim`, `isaaclab`, `leisaac`, and `list_envs.py` finding PickOrange.
5. Install from source: Python 3.10, Isaac Lab v2.1.1, CUDA 11.8, PyTorch 2.5.1.
6. Write the LeRobot version into this file.
7. Load `LeIsaac-SO101-PickOrange-v0` headless with `--enable_cameras` and save a front and
   a wrist frame to `phase1/03_sim_setup/report/`.

Then `phase1/04_rollout/RUNBOOK.md`.
