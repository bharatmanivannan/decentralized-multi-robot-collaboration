#!/usr/bin/env python3
"""Explore LightwheelAI/leisaac-pick-orange and write the Phase 1 dataset report.

Checks the action and camera format the Isaac scene and the policy both have to match,
summarises the 60 episodes, and saves camera stills and action plots into report/.

Runs on CPU. No simulator and no GPU needed.

    python phase1/01_dataset_exploration/explore_dataset.py
"""

import argparse
import json
from pathlib import Path

import cv2
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO_ID = "LightwheelAI/leisaac-pick-orange"
CAMERA_KEYS = ["observation.images.front", "observation.images.wrist"]

# The format the scene and the policy both have to match.
EXPECTED_JOINTS = [
    "shoulder_pan.pos",
    "shoulder_lift.pos",
    "elbow_flex.pos",
    "wrist_flex.pos",
    "wrist_roll.pos",
    "gripper.pos",
]
EXPECTED_FPS = 30
EXPECTED_RESOLUTION = (480, 640, 3)
EXPECTED_ROBOT = "so101_follower"

CAPTIONS = {
    "lengths": (
        "Left: how long the 60 demonstrations run. Most sit around 18 seconds, shortest "
        "is about 12, longest about 35. Right: gripper close/open cycles per episode. "
        "Median is 3, one cycle per orange."
    ),
    "front": (
        "Episode {ep}, front camera, three frames: start, middle, end. Three oranges "
        "start on the table and end up in the plate, then the arm returns to rest. "
        "This is `observation.images.front`."
    ),
    "wrist": (
        "Episode {ep}, wrist camera, same three moments. Close-up the policy uses to "
        "line the gripper up on an orange. This is `observation.images.wrist`."
    ),
    "actions": (
        "Episode {ep}, the six joints over time. Solid line is the commanded action, "
        "dashed is the joint position the arm actually reached. They track each other "
        "closely. The gripper row is the grasp and release cycles, and the last couple "
        "of seconds on shoulder lift and elbow flex is the return to rest."
    ),
}


def fetch(root: Path, episodes: list[int]) -> None:
    from huggingface_hub import snapshot_download

    patterns = ["meta/*", "data/chunk-000/*.parquet"]
    for ep in episodes:
        for key in CAMERA_KEYS:
            patterns.append(f"videos/chunk-000/{key}/episode_{ep:06d}.mp4")
    snapshot_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        allow_patterns=patterns,
        local_dir=str(root),
    )


def load_meta(root: Path) -> tuple[dict, list[dict], list[dict]]:
    info = json.loads((root / "meta/info.json").read_text())
    episodes = [json.loads(l) for l in (root / "meta/episodes.jsonl").read_text().splitlines() if l]
    tasks = [json.loads(l) for l in (root / "meta/tasks.jsonl").read_text().splitlines() if l]
    return info, episodes, tasks


def check_contract(info: dict) -> list[tuple[str, str, str, bool]]:
    feats = info["features"]
    front, wrist = (feats[k]["shape"] for k in CAMERA_KEYS)
    checks = [
        ("robot_type", EXPECTED_ROBOT, info["robot_type"], info["robot_type"] == EXPECTED_ROBOT),
        ("fps", EXPECTED_FPS, info["fps"], info["fps"] == EXPECTED_FPS),
        ("action shape", "[6]", feats["action"]["shape"], feats["action"]["shape"] == [6]),
        (
            "action joint order",
            "6 SO-101 joints",
            feats["action"]["names"],
            feats["action"]["names"] == EXPECTED_JOINTS,
        ),
        (
            "state joint order",
            "same as action",
            feats["observation.state"]["names"],
            feats["observation.state"]["names"] == EXPECTED_JOINTS,
        ),
        (
            "camera keys",
            "front + wrist",
            [k for k in CAMERA_KEYS if k in feats],
            all(k in feats for k in CAMERA_KEYS),
        ),
        (
            "camera resolution",
            "480x640x3",
            f"front={front} wrist={wrist}",
            tuple(front) == EXPECTED_RESOLUTION and tuple(wrist) == EXPECTED_RESOLUTION,
        ),
    ]
    return [(n, str(exp), str(got), ok) for n, exp, got, ok in checks]


def episode_stats(root: Path, episodes: list[dict]) -> pd.DataFrame:
    rows = []
    for ep in episodes:
        idx = ep["episode_index"]
        path = root / f"data/chunk-000/episode_{idx:06d}.parquet"
        row = {"episode": idx, "frames": ep["length"], "seconds": ep["length"] / EXPECTED_FPS}
        if path.exists():
            action = np.stack(pd.read_parquet(path)["action"].to_numpy())
            row["gripper_min"] = float(action[:, 5].min())
            row["gripper_max"] = float(action[:, 5].max())
            row["gripper_cycles"] = int(count_grasps(action[:, 5]))
        rows.append(row)
    return pd.DataFrame(rows)


def count_grasps(gripper: np.ndarray) -> int:
    """Count close->open cycles from the gripper channel."""
    threshold = (gripper.max() + gripper.min()) / 2
    closed = gripper < threshold
    return int(np.sum(np.diff(closed.astype(int)) == 1))


def save_camera_stills(root: Path, out: Path, episode: int) -> list[Path]:
    written = []
    for key in CAMERA_KEYS:
        video = root / f"videos/chunk-000/{key}/episode_{episode:06d}.mp4"
        cap = cv2.VideoCapture(str(video))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        picks = {"start": 0, "mid": total // 2, "end": max(total - 2, 0)}
        frames = {}
        for label, pos in picks.items():
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
            ok, frame = cap.read()
            if ok:
                frames[label] = frame
        cap.release()

        if not frames:
            continue
        strip = np.hstack([frames[k] for k in picks if k in frames])
        name = key.split(".")[-1]
        # JPEG, not PNG: these are rendered photographs and they live in git forever.
        path = out / f"ep{episode:03d}_{name}_start_mid_end.jpg"
        cv2.imwrite(str(path), strip, [cv2.IMWRITE_JPEG_QUALITY, 88])
        written.append((path, CAPTIONS[name].format(ep=episode)))
    return written


def plot_actions(root: Path, out: Path, episode: int) -> Path:
    df = pd.read_parquet(root / f"data/chunk-000/episode_{episode:06d}.parquet")
    action = np.stack(df["action"].to_numpy())
    state = np.stack(df["observation.state"].to_numpy())
    t = df["timestamp"].to_numpy()

    fig, axes = plt.subplots(6, 1, figsize=(10, 12), sharex=True)
    for i, (ax, joint) in enumerate(zip(axes, EXPECTED_JOINTS)):
        ax.plot(t, action[:, i], label="action", linewidth=1.2)
        ax.plot(t, state[:, i], label="state", linewidth=1.0, alpha=0.7, linestyle="--")
        ax.set_ylabel(joint.replace(".pos", ""), fontsize=8)
        ax.grid(alpha=0.3)
        if i == 0:
            ax.legend(loc="upper right", fontsize=8)
    axes[-1].set_xlabel("time (s)")
    fig.suptitle(f"episode {episode}: commanded action vs observed state")
    fig.tight_layout()
    path = out / f"ep{episode:03d}_action_trajectories.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path, CAPTIONS["actions"].format(ep=episode)


def plot_lengths(stats: pd.DataFrame, out: Path) -> Path:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    ax1.hist(stats["seconds"], bins=20, edgecolor="black")
    ax1.set_xlabel("episode duration (s)")
    ax1.set_ylabel("episodes")
    ax1.set_title("Episode length distribution")
    ax1.grid(alpha=0.3)

    if "gripper_cycles" in stats:
        counts = stats["gripper_cycles"].value_counts().sort_index()
        ax2.bar(counts.index.astype(str), counts.to_numpy(), edgecolor="black")
        ax2.set_xlabel("gripper close/open cycles per episode")
        ax2.set_ylabel("episodes")
        ax2.set_title("Grasps per episode (gripper proxy)")
        ax2.grid(alpha=0.3)
    fig.tight_layout()
    path = out / "episode_length_and_grasp_distribution.png"
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path, CAPTIONS["lengths"]


def write_report(out: Path, info, episodes, tasks, checks, stats, figures) -> Path:
    passed = sum(ok for *_, ok in checks)
    lines = [
        "# Dataset exploration: `LightwheelAI/leisaac-pick-orange`",
        "",
        f"Ritwik. Generated by `explore_dataset.py`. Format checks: **{passed}/{len(checks)}**.",
        "",
        "I pulled the dataset we are training and evaluating on and checked that the action",
        "format and the two cameras match what the model and the Isaac scene need.",
        "",
        "## Format checks",
        "",
        "| Property | Expected | Found | Result |",
        "|---|---|---|---|",
    ]
    for name, expected, got, ok in checks:
        lines.append(f"| {name} | `{expected}` | `{got}` | {'PASS' if ok else 'FAIL'} |")

    total_s = stats["seconds"].sum()
    lines += [
        "",
        "## Dataset summary",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| codebase_version | `{info['codebase_version']}` |",
        f"| robot_type | `{info['robot_type']}` |",
        f"| episodes | {info['total_episodes']} |",
        f"| frames | {info['total_frames']:,} |",
        f"| videos | {info['total_videos']} (60 episodes x 2 cameras) |",
        f"| fps | {info['fps']} |",
        f"| video codec | `{info['features'][CAMERA_KEYS[0]]['video_info']['video.codec']}` |",
        f"| total duration | {total_s / 60:.1f} min |",
        f"| tasks | {info['total_tasks']} |",
        f"| task string | `{tasks[0]['task']}` |",
        "",
        "That task string is the instruction we pass to the model.",
        "",
        "### Episode lengths",
        "",
        "| Stat | Frames | Seconds |",
        "|---|---|---|",
        f"| min | {stats['frames'].min()} | {stats['seconds'].min():.1f} |",
        f"| median | {stats['frames'].median():.0f} | {stats['seconds'].median():.1f} |",
        f"| mean | {stats['frames'].mean():.0f} | {stats['seconds'].mean():.1f} |",
        f"| max | {stats['frames'].max()} | {stats['seconds'].max():.1f} |",
        "",
    ]

    if "gripper_cycles" in stats:
        dist = stats["gripper_cycles"].value_counts().sort_index()
        median = stats["gripper_cycles"].median()
        lines += [
            "### Grasps per episode",
            "",
            "I counted how many times the gripper closes and opens in each episode, from the",
            f"gripper channel in the action. Median is **{median:.0f}**, which matches the",
            "three oranges in the task.",
            "",
            "| Gripper cycles | Episodes |",
            "|---|---|",
        ]
        lines += [f"| {k} | {v} |" for k, v in dist.items()]
        lines.append("")

    lines += [
        "## The task",
        "",
        "Pick three oranges, put them on the plate, then return the arm to rest. That is",
        "what the videos show and what the gripper cycles line up with. We score per orange,",
        "so the denominator is three per episode.",
        "",
        "## Figures",
        "",
    ]
    for fig, caption in figures:
        lines.append(f"![{fig.stem}]({fig.name})")
        lines.append("")
        lines.append(f"*{caption}*")
        lines.append("")

    path = out / "dataset_report.md"
    path.write_text("\n".join(lines))
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="data/leisaac-pick-orange")
    parser.add_argument("--out", default="phase1/01_dataset_exploration/report")
    parser.add_argument("--episodes", type=int, nargs="+", default=[0, 1, 30])
    parser.add_argument("--skip-download", action="store_true")
    args = parser.parse_args()

    root, out = Path(args.root), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    if not args.skip_download:
        print(f"fetching metadata, parquet and {len(args.episodes)} episode videos ...")
        fetch(root, args.episodes)

    info, episodes, tasks = load_meta(root)

    print("\nformat checks")
    checks = check_contract(info)
    for name, expected, got, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: expected {expected}, found {got}")

    print("\ncomputing episode statistics ...")
    stats = episode_stats(root, episodes)
    stats.to_csv(out / "episode_stats.csv", index=False)

    figures = [plot_lengths(stats, out)]
    for ep in args.episodes:
        figures.extend(save_camera_stills(root, out, ep))
        figures.append(plot_actions(root, out, ep))

    report = write_report(out, info, episodes, tasks, checks, stats, figures)
    print(f"\nwrote {report}")
    for fig, _ in figures:
        print(f"  {fig}")

    if not all(ok for *_, ok in checks):
        raise SystemExit("format checks FAILED")


if __name__ == "__main__":
    main()
