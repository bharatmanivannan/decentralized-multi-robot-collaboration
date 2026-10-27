# Track 3 — Simulator setup on a RunPod A40

Ritwik. Status: waiting on a pod.

Goal: Isaac Sim 4.5.0, Isaac Lab v2.1.1 and LeIsaac on a RunPod A40, with the SO-101
loaded in the pick-orange scene and both cameras rendering to disk.

---

## Before starting

**Headless, frames to disk.** Isaac sends the live picture over UDP. A pod will not
give us that reliably, and saved frames are what we need anyway.

**Versions for Isaac Sim 4.5**, from LeIsaac's table:

| | Isaac Sim 4.5 |
|---|---|
| Python | 3.10 |
| Isaac Lab | v2.1.1 |
| CUDA | 11.8 |
| PyTorch | 2.5.1 |

**Why A40.** Ampere card, works on the driver 560 line that Isaac 4.5 wants. We already
had Isaac Sim 4.5.0 rendering on an A40 at driver 560.35.03 on the HPC login node, so
this pairing is one we know.

Rotate the NGC key before the image pull. Put it in RunPod's registry field, not in
the repo.

## Steps

1. **Create the pod.** A40, 48 GB, Secure Cloud. Container image set to
   `nvcr.io/nvidia/isaac-sim:4.5.0`. Network volume ≥ 100 GB in the same region as the
   GPU.

2. **Record the machine before installing.**

   ```bash
   nvidia-smi
   nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
   python3 -V
   ```

   Driver, CUDA, memory, and how the pod is reached go into `Lab_log.md` first.

3. **Import check.**

   ```bash
   python -c "import isaacsim; print('isaacsim', isaacsim.__version__)"
   python -c "import isaaclab; print('isaaclab', isaaclab.__version__)"
   python -c "import leisaac; print('leisaac ok')"
   python scripts/environments/list_envs.py | grep -i pickorange
   ```

   If `leisaac` does not import against Isaac Lab v2.1.1 on Isaac Sim 4.5, stop here.

4. **Install from source.**

   ```bash
   git clone https://github.com/LightwheelAI/leisaac.git --recursive
   conda create -n leisaac python=3.10 && conda activate leisaac
   cd leisaac/dependencies/IsaacLab && ./isaaclab.sh --install   # v2.1.1
   cd ../.. && pip install -e source/leisaac
   ```

   Isaac Sim comes from the container image. Do not pip-install `isaacsim` on top.

5. **LeRobot version.** Install whatever LeIsaac's `lerobot-smolvla` client imports,
   confirm `smolvla_base` still loads, write the version in `Lab_log.md`. Training and
   evaluation both use that version.

6. **Load the scene and save cameras.**

   ```bash
   python scripts/environments/teleoperation/teleop_se3_agent.py \
       --task=LeIsaac-SO101-PickOrange-v0 \
       --device=cuda \
       --enable_cameras \
       --headless
   ```

   `--enable_cameras` creates the sensors. Save one front frame and one wrist frame
   into `report/` at 480×640, keys `observation.images.front` and
   `observation.images.wrist`.

## Done when

- `nvidia-smi` is in `Lab_log.md`
- the four imports in step 3 work
- LeRobot version is written down
- SO-101 is loaded in `LeIsaac-SO101-PickOrange-v0`
- a front frame and a wrist frame are in `report/`

Then [`../04_rollout/RUNBOOK.md`](../04_rollout/RUNBOOK.md).
