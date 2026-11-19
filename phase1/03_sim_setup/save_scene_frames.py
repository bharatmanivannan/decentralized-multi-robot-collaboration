#!/usr/bin/env python3
"""Load the SO-101 pick-orange scene and save one front frame and one wrist frame.

The Isaac Lab python has to be on PATH. From the pod:

    cd /workspace/isaac/leisaac
    /workspace/isaac/env/bin/python \
        /workspace/decentralized-multi-robot-collaboration/phase1/03_sim_setup/save_scene_frames.py \
        --task LeIsaac-SO101-PickOrange-v0 \
        --device cuda \
        --enable_cameras \
        --headless
"""

import argparse
import os
from pathlib import Path

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Save front and wrist frames from the pick-orange scene.")
parser.add_argument("--task", type=str, default="LeIsaac-SO101-PickOrange-v0")
parser.add_argument("--num_envs", type=int, default=1)
parser.add_argument("--warmup_steps", type=int, default=30)
parser.add_argument(
    "--out",
    type=str,
    default="/workspace/decentralized-multi-robot-collaboration/phase1/03_sim_setup/report",
)
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(vars(args_cli))
simulation_app = app_launcher.app

import torch  # noqa: E402
import gymnasium as gym  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

# Asset paths resolve from the LeIsaac git root. Stay in that repo before importing it.
os.chdir("/workspace/isaac/leisaac")
import leisaac  # noqa: E402,F401
from isaaclab_tasks.utils import parse_env_cfg  # noqa: E402


def to_uint8(image: torch.Tensor) -> np.ndarray:
    frame = image.detach().cpu()
    if frame.ndim == 4:
        frame = frame[0]
    array = frame.numpy()
    if array.dtype != np.uint8:
        array = np.clip(array, 0.0, 1.0)
        array = (array * 255.0).round().astype(np.uint8)
    if array.shape[-1] != 3 and array.shape[0] == 3:
        array = np.transpose(array, (1, 2, 0))
    return array


def main() -> None:
    out = Path(args_cli.out)
    out.mkdir(parents=True, exist_ok=True)

    env_cfg = parse_env_cfg(args_cli.task, device=args_cli.device, num_envs=args_cli.num_envs)
    env_cfg.use_teleop_device("keyboard")
    env_cfg.seed = 0
    env_cfg.recorders = None
    if hasattr(env_cfg, "terminations") and hasattr(env_cfg.terminations, "time_out"):
        env_cfg.terminations.time_out = None

    env = gym.make(args_cli.task, cfg=env_cfg)
    obs, _ = env.reset()
    action = torch.zeros(env.action_space.shape, device=env.unwrapped.device)
    for _ in range(args_cli.warmup_steps):
        obs, _, _, _, _ = env.step(action)

    policy = obs["policy"]
    saved = []
    for name, dataset_key in (("front", "observation.images.front"), ("wrist", "observation.images.wrist")):
        frame = to_uint8(policy[name])
        path = out / f"{name}.png"
        Image.fromarray(frame).save(path)
        mean = float(frame.mean())
        print(f"{dataset_key} {frame.shape} mean={mean:.2f} -> {path}")
        if frame.shape != (480, 640, 3):
            raise SystemExit(f"{name} is {frame.shape}, expected (480, 640, 3)")
        if mean < 1.0:
            raise SystemExit(f"{name} looks black (mean pixel {mean:.2f})")
        saved.append(path)

    env.close()
    print("saved", ", ".join(str(path) for path in saved))


if __name__ == "__main__":
    main()
    simulation_app.close()
