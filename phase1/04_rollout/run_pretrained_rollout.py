#!/usr/bin/env python3
"""Headless pick-orange rollouts for the pretrained SmolVLA baseline and a random-action floor.

The Isaac Lab python has to be on PATH. From the pod:

    cd /workspace/isaac/leisaac
    /workspace/isaac/env/bin/python \
        /workspace/decentralized-multi-robot-collaboration/phase1/04_rollout/run_pretrained_rollout.py \
        --baseline pretrained \
        --task LeIsaac-SO101-PickOrange-Direct-v0 \
        --policy_type lerobot-smolvla \
        --policy_checkpoint_path /workspace/hf/smolvla_base \
        --policy_host 127.0.0.1 \
        --policy_port 8080 \
        --policy_action_horizon 16 \
        --policy_language_instruction "Grab orange and place into plate" \
        --episode_length_s 120 \
        --step_hz 30 \
        --eval_rounds 5 \
        --seed 1000 \
        --device cuda \
        --enable_cameras \
        --headless

The scene cameras are named front and wrist. lerobot/smolvla_base was trained with
camera1, camera2, and camera3. This script sends front as camera1 and wrist as camera2
and leaves camera3 out. SmolVLA masks an image key that is absent.
"""

import argparse
import csv
import os
import time
from pathlib import Path

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Record a headless pick-orange rollout.")
parser.add_argument("--baseline", choices=("pretrained", "random"), default="pretrained")
parser.add_argument("--task", type=str, default="LeIsaac-SO101-PickOrange-Direct-v0")
parser.add_argument("--step_hz", type=int, default=30)
parser.add_argument("--seed", type=int, default=1000)
parser.add_argument("--episode_length_s", type=float, default=120.0)
parser.add_argument("--eval_rounds", type=int, default=5)
parser.add_argument("--policy_type", type=str, default="lerobot-smolvla")
parser.add_argument("--policy_host", type=str, default="127.0.0.1")
parser.add_argument("--policy_port", type=int, default=8080)
parser.add_argument("--policy_timeout_ms", type=int, default=180000)
parser.add_argument("--policy_action_horizon", type=int, default=16)
parser.add_argument(
    "--policy_language_instruction",
    type=str,
    default="Grab orange and place into plate",
)
parser.add_argument("--policy_checkpoint_path", type=str, default="/workspace/hf/smolvla_base")
parser.add_argument(
    "--report_dir",
    type=str,
    default="/workspace/decentralized-multi-robot-collaboration/phase1/04_rollout/report",
)
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(vars(args_cli))
simulation_app = app_launcher.app

import numpy as np  # noqa: E402
import torch  # noqa: E402
import gymnasium as gym  # noqa: E402
from PIL import Image  # noqa: E402

os.chdir("/workspace/isaac/leisaac")
import leisaac  # noqa: E402,F401
from isaaclab.sensors import Camera  # noqa: E402
from isaaclab_tasks.utils import parse_env_cfg  # noqa: E402
from leisaac.assets.robots.lerobot import SO101_FOLLOWER_MOTOR_LIMITS  # noqa: E402
from leisaac.utils.constant import SINGLE_ARM_JOINT_NAMES  # noqa: E402
from leisaac.utils.env_utils import dynamic_reset_gripper_effort_limit_sim, get_task_type  # noqa: E402
from leisaac.utils.robot_utils import convert_lerobot_action_to_leisaac  # noqa: E402

CAMERA_MAP = {"front": "camera1", "wrist": "camera2"}
CSV_FIELDS = [
    "run_id",
    "baseline",
    "episode",
    "seed",
    "oranges_placed",
    "episode_success",
    "termination_reason",
    "duration_s",
    "policy_action_horizon",
    "checkpoint",
    "language_instruction",
    "camera_map",
    "isaac_sim_version",
    "isaac_lab_version",
    "leisaac_commit",
    "lerobot_version",
    "driver_version",
    "gpu",
    "notes",
]


class RateLimiter:
    def __init__(self, hz: int):
        self.hz = hz
        self.last_time = time.time()
        self.sleep_duration = 1.0 / hz
        self.render_period = min(0.0166, self.sleep_duration)

    def sleep(self, env) -> None:
        next_wakeup_time = self.last_time + self.sleep_duration
        while time.time() < next_wakeup_time:
            time.sleep(self.render_period)
            env.sim.render()
        self.last_time = self.last_time + self.sleep_duration
        if self.last_time < time.time():
            while self.last_time < time.time():
                self.last_time += self.sleep_duration


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


def count_oranges(obs: dict) -> int:
    placed = 0
    for key, value in obs.get("subtask_terms", {}).items():
        if not (key.startswith("put_orange") and key.endswith("_to_plate")):
            continue
        if torch.is_tensor(value):
            value = bool(value.reshape(-1)[0].item())
        if value:
            placed += 1
    return placed


def save_views(obs: dict, directory: Path, tag: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    policy = obs["policy"]
    for name in ("front", "wrist"):
        frame = to_uint8(policy[name])
        path = directory / f"{name}_{tag}.png"
        Image.fromarray(frame).save(path)
        print(f"FRAME {path} shape={frame.shape} mean={frame.mean():.1f}", flush=True)


def make_policy(env):
    from leisaac.policy.service_policy_clients import LeRobotServicePolicyClient

    class MappedClient(LeRobotServicePolicyClient):
        """Rename scene cameras to the checkpoint feature names before the RPC."""

        def __init__(self, *args, source_to_policy: dict[str, str], **kwargs):
            self.source_to_policy = source_to_policy
            super().__init__(*args, **kwargs)

        def _send_observation(self, observation_dict: dict) -> None:
            from leisaac.policy.lerobot.helpers import TimedObservation

            mapped = {self.source_to_policy.get(key, key): value for key, value in observation_dict.items()}
            original_init = TimedObservation.__init__

            def force_must_go(obs_self, *args, **kwargs):
                kwargs["must_go"] = True
                original_init(obs_self, *args, **kwargs)

            TimedObservation.__init__ = force_must_go
            try:
                super()._send_observation(mapped)
            finally:
                TimedObservation.__init__ = original_init

        def get_action(self, observation_dict: dict) -> torch.Tensor:
            # An empty reply used to latch this flag and stop sending observations.
            self.skip_send_observation = False
            if self.last_action is not None and np.ndim(self.last_action) == 1:
                self.last_action = np.asarray(self.last_action)[None, :]
            action = super().get_action(observation_dict)
            if self.last_action is not None and np.ndim(self.last_action) == 1:
                self.last_action = np.asarray(self.last_action)[None, :]
            if action.shape[-1] != 6:
                action = action[..., :6]
            return action

    camera_infos = {}
    for key, sensor in env.scene.sensors.items():
        if isinstance(sensor, Camera) and key in CAMERA_MAP:
            camera_infos[CAMERA_MAP[key]] = sensor.image_shape
    if set(camera_infos) != {"camera1", "camera2"}:
        raise RuntimeError(f"Expected front and wrist cameras, got {list(env.scene.sensors)}")

    policy_type = args_cli.policy_type.split("-", 1)[1]
    return MappedClient(
        host=args_cli.policy_host,
        port=args_cli.policy_port,
        timeout_ms=args_cli.policy_timeout_ms,
        camera_infos=camera_infos,
        task_type="so101leader",
        policy_type=policy_type,
        pretrained_name_or_path=args_cli.policy_checkpoint_path,
        actions_per_chunk=args_cli.policy_action_horizon,
        device=args_cli.device,
        source_to_policy=CAMERA_MAP,
    )


def random_action(rng: np.random.Generator, device: torch.device) -> torch.Tensor:
    degrees = np.array(
        [[rng.uniform(*SO101_FOLLOWER_MOTOR_LIMITS[name]) for name in SINGLE_ARM_JOINT_NAMES]],
        dtype=np.float32,
    )
    radians = convert_lerobot_action_to_leisaac(degrees)
    return torch.from_numpy(np.asarray(radians, dtype=np.float32)).to(device)


def main() -> None:
    report_dir = Path(args_cli.report_dir)
    frame_root = report_dir / "frames" / args_cli.baseline
    frame_root.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / "rollout_results.csv"

    env_cfg = parse_env_cfg(args_cli.task, device=args_cli.device, num_envs=1)
    task_type = get_task_type(args_cli.task)
    if task_type != "so101leader":
        raise RuntimeError(f"Expected so101leader so gravity stays on, got {task_type}")
    env_cfg.use_teleop_device(task_type)
    env_cfg.seed = args_cli.seed
    env_cfg.episode_length_s = args_cli.episode_length_s
    env_cfg.recorders = None

    env = gym.make(args_cli.task, cfg=env_cfg).unwrapped
    policy = make_policy(env) if args_cli.baseline == "pretrained" else None
    rng = np.random.default_rng(args_cli.seed)
    rate_limiter = RateLimiter(args_cli.step_hz)

    obs, _ = env.reset(seed=args_cli.seed)
    print(
        f"ROLLOUT baseline={args_cli.baseline} episodes={args_cli.eval_rounds} "
        f"seed={args_cli.seed} horizon={args_cli.policy_action_horizon} "
        f"max_steps={env.max_episode_length}",
        flush=True,
    )

    rows = []
    logged_action = False
    for episode in range(1, args_cli.eval_rounds + 1):
        print(f"[Evaluation] Episode {episode}", flush=True)
        episode_dir = frame_root / f"episode_{episode:02d}"
        save_views(obs, episode_dir, "start")
        oranges = count_oranges(obs)
        success = False
        timed_out = False
        steps = 0
        started = time.time()

        while simulation_app.is_running() and not success and not timed_out:
            with torch.inference_mode():
                if policy is None:
                    actions = random_action(rng, env.device).unsqueeze(0)
                    horizon = 1
                else:
                    policy_obs = dict(obs["policy"])
                    policy_obs["task_description"] = args_cli.policy_language_instruction
                    actions = policy.get_action(policy_obs).to(env.device)
                    horizon = min(args_cli.policy_action_horizon, actions.shape[0])
                if not logged_action:
                    sample = actions[0, 0].detach().cpu().numpy()
                    print(f"ACTION_SHAPE {tuple(actions.shape)} first={np.array2string(sample, precision=4)}", flush=True)
                    logged_action = True

                for index in range(horizon):
                    action = actions[index, :, :]
                    if getattr(env.cfg, "dynamic_reset_gripper_effort_limit", False):
                        dynamic_reset_gripper_effort_limit_sim(env, task_type)
                    obs, _, reset_terminated, reset_time_outs, _ = env.step(action)
                    steps += 1
                    oranges = count_oranges(obs)
                    if steps == 450:
                        save_views(obs, episode_dir, "mid")
                    if reset_terminated[0]:
                        success = True
                        break
                    if reset_time_outs[0]:
                        timed_out = True
                        break
                    rate_limiter.sleep(env)

        save_views(obs, episode_dir, "end")
        reason = "success" if success else "time_out" if timed_out else "app_closed"
        duration_s = steps * (args_cli.episode_length_s / float(env.max_episode_length))
        wall_s = time.time() - started
        horizon_value = args_cli.policy_action_horizon if policy is not None else 1
        checkpoint = args_cli.policy_checkpoint_path if policy is not None else "none"
        note = (
            f"steps={steps}; wall_s={wall_s:.1f}; camera3 omitted; so100 norm stats; "
            + ("pretrained chunk held for the horizon" if policy is not None else "uniform motor target every step")
        )
        run_id = f"{'B1-smolvla-zeroshot' if policy is not None else 'B0-random'}-ep{episode}"
        baseline = "B1-smolvla-zeroshot" if policy is not None else "B0-random"
        row = {
            "run_id": run_id,
            "baseline": baseline,
            "episode": episode,
            "seed": args_cli.seed,
            "oranges_placed": oranges,
            "episode_success": success,
            "termination_reason": reason,
            "duration_s": f"{duration_s:.3f}",
            "policy_action_horizon": horizon_value,
            "checkpoint": checkpoint,
            "language_instruction": args_cli.policy_language_instruction,
            "camera_map": "front->camera1;wrist->camera2",
            "isaac_sim_version": "4.5.0",
            "isaac_lab_version": "v2.1.1",
            "leisaac_commit": "493f91c",
            "lerobot_version": "0.3.3" if policy is not None else "n/a",
            "driver_version": "570.211.01",
            "gpu": "A40",
            "notes": note,
        }
        rows.append(row)
        write_header = not csv_path.exists()
        with csv_path.open("a", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            if write_header:
                writer.writeheader()
            writer.writerow(row)
        print(
            f"EPISODE {episode} success={success} oranges={oranges} reason={reason} "
            f"steps={steps} duration_s={duration_s:.1f} wall_s={wall_s:.1f}",
            flush=True,
        )
        if episode < args_cli.eval_rounds:
            with torch.inference_mode():
                obs, _ = env.reset()

    successes = sum(row["episode_success"] for row in rows)
    print(
        f"ROLLOUT_DONE baseline={args_cli.baseline} success={successes}/{len(rows)} csv={csv_path}",
        flush=True,
    )
    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
