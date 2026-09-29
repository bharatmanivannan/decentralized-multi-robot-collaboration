# Lab log

Project: Decentralized Multi-Robot Collaboration (CMPE 295A)
Advisor: Dr. Wencen Wu
Owner: Ritwik
Updated: 2026-09-29

Dated record of what we tried, what we decided, and where the machines are. Current task split is in `team_workflow.md`.

## Where we are

Training stays on the HPC3 H100 and A100 queues.

The simulator host is Dr. Wu's on-campus RTX 4090 workstation. That choice is closed. RunPod is tentative, on hold (I will explore in my free time, if I cant make it to the Lab). The HPC login-node A40 is not the plan either: Isaac Sim 4.5 renders there, and a laptop cannot see the picture.

Isaac Sim stays at 4.5.0 (`nvcr.io/nvidia/isaac-sim:4.5.0`). On the login node the driver is 560.35.03, and Isaac 5.x fails on that driver. The 4090 workstation still needs its own `nvidia-smi` (driver, CUDA, memory) written into this file before anything is installed on it. Install 4.5.0 unless that driver reading says otherwise. Do not install Isaac 5.x on driver 560.

## Decisions

| Date | Decision | Why |
|---|---|---|
| 2026-09-19 | Train on HPC3 H100 or A100. Simulate only on an RT-core GPU. | H100 and A100 have no RT cores. Isaac Sim will not render cameras on them. |
| 2026-09-22 | Isaac on the g17 login node stays at 4.5. Driver there is 560.35.03. | Dr. Wu. Isaac 5.x wants a newer driver. |
| 2026-09-22 | Training stays on the H100 and A100 queues. | Dr. Wu. |
| 2026-09-23 | Stop trying to view g17 Isaac through SSH. | Signaling is TCP `49100`. Video is UDP `47998`. SSH forwards TCP only. |
| 2026-09-29 | Simulator host is Dr. Wu's on-campus RTX 4090 workstation. | The login-node A40 renders, and the picture cannot leave the cluster. RunPod was only a stand-in while this machine was unconfirmed. |

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

## Notes

- Do not view Isaac on g17 from a laptop. The 4090 workstation is the simulator host.
- Do not `srun` to get the g17 A40. Slurm will not schedule it.
- Do not upgrade Isaac past 4.5 on driver 560.35.03.
- Do not pass `primaryStream/publicIp` or `publicEndpointAddress` on this 4.5 image.
- Do not run a placeholder `python.sh` with `path/to/your/headless_script.py`. The streaming app is `./runheadless.sh` inside the container.
- Do not put NGC API keys, passwords, or tokens in the repo. The key used for the image pull was pasted into an earlier chat. Rotate it in NGC.

## Next on the 4090 workstation

1. Record `nvidia-smi`: driver, CUDA, memory, and how the machine is reached.
2. Install Isaac Sim 4.5.0 and the Isaac Lab release built for 4.5.
3. Load the SO-101 arm from the `leisaac-pick-orange` scene and confirm it is visible.
