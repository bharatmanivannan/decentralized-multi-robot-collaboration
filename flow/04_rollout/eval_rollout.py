#!/usr/bin/env python3
"""Headless pick-orange eval. Writes metrics and a front|wrist mp4. No viewport.

Grasp, place, and task completion use LeIsaac's own checks. Gripper range is the
min and max of the gripper joint over the episode, in degrees.

    conda activate leisaac
    cd leisaac
    python ../flow/04_rollout/eval_rollout.py \
        --policy random --episodes 3 --seed 1000 --headless --enable_cameras

Pretrained SmolVLA needs start_policy_server.py already listening on port 8080.
"""

import multiprocessing

if multiprocessing.get_start_method() != "spawn":
    multiprocessing.set_start_method("spawn", force=True)

import argparse
from pathlib import Path

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Headless pick-orange eval with video.")
parser.add_argument("--task", default="LeIsaac-SO101-PickOrange-Direct-v0")
parser.add_argument("--policy", choices=["pretrained", "random"], required=True)
parser.add_argument("--episodes", type=int, default=3)
parser.add_argument("--seed", type=int, default=1000)
parser.add_argument("--episode_length_s", type=float, default=60.0)
parser.add_argument("--action_horizon", type=int, default=16)
parser.add_argument("--instruction", default="Grab orange and place into plate")
parser.add_argument("--checkpoint", default="lerobot/smolvla_base")
parser.add_argument("--policy_host", default="localhost")
parser.add_argument("--policy_port", type=int, default=8080)
parser.add_argument("--policy_timeout_ms", type=int, default=120000)
parser.add_argument("--record_every", type=int, default=6, help="Save one video frame every N sim steps.")
parser.add_argument("--video_root", default="../videos")
parser.add_argument("--csv", default="../flow/04_rollout/report/eval_metrics.csv")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(vars(args_cli))
simulation_app = app_launcher.app

import csv
import time

import cv2
import numpy as np
import torch
import gymnasium as gym
from isaaclab.envs import ManagerBasedRLEnv  # noqa: F401
from isaaclab.managers import SceneEntityCfg
from isaaclab.sensors import Camera
from isaaclab_tasks.utils import parse_env_cfg
from leisaac.tasks.pick_orange import mdp
from leisaac.utils.env_utils import dynamic_reset_gripper_effort_limit_sim, get_task_type
from leisaac.utils.robot_utils import convert_lerobot_action_to_leisaac

import leisaac  # noqa: F401

ORANGES = ["Orange001", "Orange002", "Orange003"]


class RandomPolicy:
    def get_action(self, observation_dict):
        limits = [(-100.0, 100.0)] * 5 + [(0.0, 100.0)]
        sample = np.array([[np.random.uniform(lo, hi) for lo, hi in limits]], dtype=np.float32)
        converted = convert_lerobot_action_to_leisaac(sample)
        chunk = np.repeat(converted, args_cli.action_horizon, axis=0)
        return torch.from_numpy(chunk[:, None, :].astype(np.float32))


def make_policy(env):
    if args_cli.policy == "random":
        return RandomPolicy()

    from leisaac.policy import LeRobotServicePolicyClient

    task_type = get_task_type(args_cli.task)
    return LeRobotServicePolicyClient(
        host=args_cli.policy_host,
        port=args_cli.policy_port,
        timeout_ms=args_cli.policy_timeout_ms,
        camera_infos={key: sensor.image_shape for key, sensor in env.scene.sensors.items() if isinstance(sensor, Camera)},
        task_type=task_type,
        policy_type="smolvla",
        pretrained_name_or_path=args_cli.checkpoint,
        actions_per_chunk=args_cli.action_horizon,
        device=args_cli.device,
    )


def as_uint8_hwc(image):
    if torch.is_tensor(image):
        image = image.detach().cpu().numpy()
    image = np.squeeze(image)
    if image.ndim == 3 and image.shape[0] in (3, 4) and image.shape[-1] not in (3, 4):
        image = np.transpose(image, (1, 2, 0))
    if image.shape[-1] == 4:
        image = image[..., :3]
    if image.dtype != np.uint8:
        scale = 255.0 if float(np.max(image)) <= 1.0 else 1.0
        image = np.clip(image * scale, 0, 255).astype(np.uint8)
    return np.ascontiguousarray(image)


def side_by_side(policy_obs):
    front = as_uint8_hwc(policy_obs["front"])
    wrist = as_uint8_hwc(policy_obs["wrist"])
    if front.shape[0] != wrist.shape[0]:
        wrist = cv2.resize(wrist, (front.shape[1], front.shape[0]))
    return np.hstack([front, wrist])


def gripper_index(env):
    names = list(env.scene["robot"].data.joint_names)
    for i, name in enumerate(names):
        if "gripper" in name:
            return i
    return len(names) - 1


def any_grasped(env):
    for name in ORANGES:
        if bool(mdp.orange_grasped(env, object_cfg=SceneEntityCfg(name))[0].item()):
            return True
    return False


def any_placed(env):
    for name in ORANGES:
        if bool(mdp.put_orange_to_plate(env, object_cfg=SceneEntityCfg(name), plate_cfg=SceneEntityCfg("Plate"))[0].item()):
            return True
    return False


def oranges_in_plate(env):
    plate = env.scene["Plate"]
    plate_x = plate.data.root_pos_w[:, 0] - env.scene.env_origins[:, 0]
    plate_y = plate.data.root_pos_w[:, 1] - env.scene.env_origins[:, 1]
    count = 0
    for name in ORANGES:
        orange = env.scene[name]
        x = orange.data.root_pos_w[:, 0] - env.scene.env_origins[:, 0]
        y = orange.data.root_pos_w[:, 1] - env.scene.env_origins[:, 1]
        inside = (x < plate_x + 0.10) & (x > plate_x - 0.10) & (y < plate_y + 0.10) & (y > plate_y - 0.10)
        count += int(bool(inside[0].item()))
    return count


def task_complete(env):
    return bool(
        mdp.task_done(
            env,
            oranges_cfg=[SceneEntityCfg(name) for name in ORANGES],
            plate_cfg=SceneEntityCfg("Plate"),
        )[0].item()
    )


def open_writer(path, frame):
    path.parent.mkdir(parents=True, exist_ok=True)
    height, width = frame.shape[:2]
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"could not open video writer for {path}")
    return writer


def append_csv(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    with path.open("a", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def main():
    device = args_cli.device if args_cli.device is not None else "cuda:0"
    env_cfg = parse_env_cfg(args_cli.task, device=device, num_envs=1)
    task_type = get_task_type(args_cli.task)
    env_cfg.use_teleop_device(task_type)
    env_cfg.seed = args_cli.seed
    env_cfg.episode_length_s = args_cli.episode_length_s
    env_cfg.recorders = None

    env = gym.make(args_cli.task, cfg=env_cfg).unwrapped
    policy = make_policy(env)
    grip_idx = gripper_index(env)
    video_dir = Path(args_cli.video_root) / "baseline" / args_cli.policy
    csv_path = Path(args_cli.csv)
    rows = []

    print(f"[eval] policy={args_cli.policy} episodes={args_cli.episodes} seed={args_cli.seed}", flush=True)
    print(f"[eval] gripper joint: {env.scene['robot'].data.joint_names[grip_idx]}", flush=True)

    for episode in range(1, args_cli.episodes + 1):
        obs, _ = env.reset()
        grasped = False
        placed = False
        grip_min = float("inf")
        grip_max = float("-inf")
        steps = 0
        writer = None
        video_path = video_dir / f"seed{args_cli.seed}_ep{episode:02d}.mp4"
        done = False
        timed_out = False
        print(f"[eval] episode {episode}", flush=True)

        while simulation_app.is_running():
            policy_obs = obs["policy"]
            grip = float(env.scene["robot"].data.joint_pos[0, grip_idx].item()) * 180.0 / np.pi
            grip_min = min(grip_min, grip)
            grip_max = max(grip_max, grip)
            grasped = grasped or any_grasped(env)
            placed = placed or any_placed(env)

            if steps % args_cli.record_every == 0:
                frame = side_by_side(policy_obs)
                if writer is None:
                    writer = open_writer(video_path, frame)
                writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

            batch = dict(policy_obs)
            batch["task_description"] = args_cli.instruction
            actions = policy.get_action(batch).to(env.device)
            n_actions = min(args_cli.action_horizon, actions.shape[0])
            for i in range(n_actions):
                if env.cfg.dynamic_reset_gripper_effort_limit:
                    dynamic_reset_gripper_effort_limit_sim(env, task_type)
                obs, _, terminated, timed, _ = env.step(actions[i])
                steps += 1
                grip = float(env.scene["robot"].data.joint_pos[0, grip_idx].item()) * 180.0 / np.pi
                grip_min = min(grip_min, grip)
                grip_max = max(grip_max, grip)
                grasped = grasped or any_grasped(env)
                placed = placed or any_placed(env)
                if steps % args_cli.record_every == 0:
                    frame = side_by_side(obs["policy"])
                    if writer is None:
                        writer = open_writer(video_path, frame)
                    writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                if bool(terminated[0].item()):
                    done = True
                    break
                if bool(timed[0].item()):
                    timed_out = True
                    break
            if done or timed_out:
                break

        if writer is not None:
            writer.release()

        in_plate = oranges_in_plate(env)
        complete = task_complete(env) or done
        row = {
            "policy": args_cli.policy,
            "episode": episode,
            "seed": args_cli.seed,
            "grasped": int(grasped),
            "placed": int(placed or in_plate > 0),
            "oranges_in_plate": in_plate,
            "task_complete": int(complete),
            "gripper_min_deg": round(grip_min, 2),
            "gripper_max_deg": round(grip_max, 2),
            "steps": steps,
            "termination": "success" if complete else "time_out",
            "video": str(video_path),
        }
        rows.append(row)
        append_csv(csv_path, row)
        print(
            f"[eval] ep {episode}: grasp={row['grasped']} place={row['placed']} "
            f"in_plate={in_plate} task={row['task_complete']} "
            f"gripper=[{row['gripper_min_deg']}, {row['gripper_max_deg']}] deg "
            f"video={video_path}",
            flush=True,
        )

    n = len(rows)
    print("[eval] summary", flush=True)
    print(f"[eval] grasp rate        {sum(r['grasped'] for r in rows)}/{n}", flush=True)
    print(f"[eval] place rate        {sum(r['placed'] for r in rows)}/{n}", flush=True)
    print(f"[eval] task completion   {sum(r['task_complete'] for r in rows)}/{n}", flush=True)
    print(
        f"[eval] gripper range deg [{min(r['gripper_min_deg'] for r in rows)}, {max(r['gripper_max_deg'] for r in rows)}]",
        flush=True,
    )
    env.close()
    simulation_app.close()


if __name__ == "__main__":
    main()
