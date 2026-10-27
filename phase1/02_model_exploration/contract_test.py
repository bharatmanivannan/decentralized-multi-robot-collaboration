#!/usr/bin/env python3
"""Check that lerobot/smolvla_base speaks SO-101.

Runs one real frame of leisaac-pick-orange through the public pretrained SmolVLA
checkpoint, with no fine-tuning, and checks the output is six numbers in the
dataset's joint order.

Needs no simulator and no CUDA GPU.

    python phase1/02_model_exploration/contract_test.py
"""

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import torch

CHECKPOINT = "lerobot/smolvla_base"
DATASET_ROOT = Path("data/leisaac-pick-orange")

JOINTS = [
    "shoulder_pan.pos",
    "shoulder_lift.pos",
    "elbow_flex.pos",
    "wrist_flex.pos",
    "wrist_roll.pos",
    "gripper.pos",
]

# smolvla_base declares generic camera slots. The dataset and the Isaac scene use
# front/wrist, so the pipeline's rename step bridges the two. The third slot stays
# unmapped: SO-101 has two cameras, and the model masks image features it is not given.
RENAME_MAP = {
    "observation.images.front": "observation.images.camera1",
    "observation.images.wrist": "observation.images.camera2",
}


def pick_device(requested: str) -> torch.device:
    if requested != "auto":
        return torch.device(requested)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def read_frame(camera_key: str, episode: int, frame_index: int) -> np.ndarray:
    video = DATASET_ROOT / f"videos/chunk-000/{camera_key}/episode_{episode:06d}.mp4"
    cap = cv2.VideoCapture(str(video))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError(f"could not read frame {frame_index} from {video}")
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def build_observation(episode: int, frame_index: int, task: str):
    df = pd.read_parquet(DATASET_ROOT / f"data/chunk-000/episode_{episode:06d}.parquet")
    row = df.iloc[frame_index]

    observation = {
        "observation.state": torch.tensor(np.asarray(row["observation.state"]), dtype=torch.float32),
        "task": task,
    }
    for dataset_key in RENAME_MAP:
        frame = read_frame(dataset_key, episode, frame_index)
        observation[dataset_key] = torch.from_numpy(frame).permute(2, 0, 1).float() / 255.0

    state = np.asarray(row["observation.state"], dtype=np.float32)
    ground_truth = np.asarray(row["action"], dtype=np.float32)
    return observation, state, ground_truth


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", type=int, default=0)
    parser.add_argument("--frame", type=int, default=200)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", default="phase1/02_model_exploration/report")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    device = pick_device(args.device)
    # SmolVLA's action expert samples noise, so the output moves between runs unless seeded.
    torch.manual_seed(args.seed)

    task_dataset = json.loads(
        (DATASET_ROOT / "meta/tasks.jsonl").read_text().splitlines()[0]
    )["task"]
    task_alternate = "Pick up the orange and place it on the plate"  # alternate phrasing, used only to confirm the language input is live

    print(f"device: {device}")
    print(f"loading {CHECKPOINT} ...")
    from lerobot.policies.factory import make_pre_post_processors
    from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy

    policy = SmolVLAPolicy.from_pretrained(CHECKPOINT)
    policy.config.device = str(device)
    policy.to(device)
    policy.eval()

    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=policy.config,
        pretrained_path=CHECKPOINT,
        preprocessor_overrides={
            "device_processor": {"device": str(device)},
            "rename_observations_processor": {"rename_map": RENAME_MAP},
        },
    )

    n_params = sum(p.numel() for p in policy.parameters())
    print(f"parameters: {n_params / 1e6:.1f}M")
    print(f"declared camera slots: {list(policy.config.image_features)}")
    print(f"cameras supplied: {list(RENAME_MAP.values())} (third slot masked)")
    print(f"chunk_size: {policy.config.chunk_size}, n_action_steps: {policy.config.n_action_steps}")

    results = {}
    for label, task in [("dataset", task_dataset), ("alternate", task_alternate)]:
        observation, state, ground_truth = build_observation(args.episode, args.frame, task)

        # Same noise draw for both instructions, so the only difference is the text.
        torch.manual_seed(args.seed)
        policy.reset()
        with torch.inference_mode():
            batch = preprocessor(observation)
            action = postprocessor(policy.select_action(batch))
            policy.reset()
            chunk = postprocessor(policy.predict_action_chunk(preprocessor(observation)))

        action = action.squeeze(0).float().cpu().numpy()
        results[label] = {
            "task": task,
            "action": action,
            "chunk_shape": tuple(chunk.shape),
            "state": state,
            "ground_truth": ground_truth,
        }
        print(f"\ninstruction ({label}): {task!r}")
        print(f"  action: {action.shape}  chunk: {tuple(chunk.shape)}")

    primary = results["dataset"]
    predicted = primary["action"]

    checks = [
        ("output is 6 numbers", predicted.shape == (6,), str(predicted.shape)),
        ("output is finite", bool(np.isfinite(predicted).all()), "no NaN or Inf"),
        (
            "chunk is (1, chunk_size, 6)",
            primary["chunk_shape"] == (1, policy.config.chunk_size, 6),
            str(primary["chunk_shape"]),
        ),
        ("state input is 6 numbers", primary["state"].shape == (6,), str(primary["state"].shape)),
        (
            "language path is live",
            not np.allclose(results["dataset"]["action"], results["alternate"]["action"]),
            "action changes when the instruction changes",
        ),
    ]

    print("\nchecks")
    for name, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    print(f"\nsix numbers from the pretrained checkpoint (episode {args.episode}, frame {args.frame}):")
    print(f"  {'joint':<20}{'predicted':>12}{'ground truth':>14}{'state in':>12}")
    for i, joint in enumerate(JOINTS):
        print(
            f"  {joint:<20}{predicted[i]:>12.4f}"
            f"{primary['ground_truth'][i]:>14.4f}{primary['state'][i]:>12.4f}"
        )

    write_report(out, policy, args, device, n_params, results, checks, task_dataset, task_alternate)
    print(f"\nwrote {out / 'contract_test_report.md'}")

    if not all(ok for _, ok, _ in checks):
        raise SystemExit("checks FAILED")


def write_report(out, policy, args, device, n_params, results, checks, task_dataset, task_alternate):
    primary = results["dataset"]
    predicted = primary["action"]
    passed = sum(ok for _, ok, _ in checks)
    mae = float(np.abs(predicted - primary["ground_truth"]).mean())

    lines = [
        "# Model exploration: `lerobot/smolvla_base`",
        "",
        f"Ritwik. Generated by `contract_test.py`. Checks: **{passed}/{len(checks)}**.",
        "",
        "I loaded the public pretrained checkpoint and ran one real frame from",
        "`leisaac-pick-orange` through it. What I wanted from this step: does it load, and does",
        "it return six numbers in our joint order. It does. This runs on a laptop, no simulator.",
        "",
        "## Environment",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| checkpoint | `{CHECKPOINT}` |",
        f"| parameters | {n_params / 1e6:.1f}M |",
        f"| device | `{device}` |",
        f"| torch | `{torch.__version__}` |",
        f"| chunk_size | {policy.config.chunk_size} |",
        f"| n_action_steps | {policy.config.n_action_steps} |",
        f"| frame used | episode {args.episode}, frame {args.frame} |",
        f"| torch seed | {args.seed} |",
        "",
        "## Checks",
        "",
        "| Check | Detail | Result |",
        "|---|---|---|",
    ]
    for name, ok, detail in checks:
        lines.append(f"| {name} | `{detail}` | {'PASS' if ok else 'FAIL'} |")

    lines += [
        "",
        "## The six numbers",
        "",
        "`predicted` is the pretrained checkpoint. `ground truth` is what the demonstrator",
        "commanded on this frame. `state in` is the joint position I fed the model. Units are",
        "degrees, except the gripper.",
        "",
        "| Joint | Predicted | Ground truth | State in |",
        "|---|---|---|---|",
    ]
    for i, joint in enumerate(JOINTS):
        lines.append(
            f"| `{joint}` | {predicted[i]:.4f} | "
            f"{primary['ground_truth'][i]:.4f} | {primary['state'][i]:.4f} |"
        )

    lines += [
        "",
        f"The checkpoint sits around **{mae:.1f}** away from the demonstration on this frame. It has",
        "not been fine-tuned on this scene yet, so this is the starting point. Fine-tuning is",
        "phase 3.",
        "",
        "## Settings for the rest of the work",
        "",
        "### Camera mapping",
        "",
        "The checkpoint names its cameras `camera1`, `camera2`, `camera3`. The dataset and the",
        "Isaac scene use `front` and `wrist`. We map them like this:",
        "",
        "```python",
        "rename_map = {",
        '    "observation.images.front": "observation.images.camera1",',
        '    "observation.images.wrist": "observation.images.camera2",',
        "}",
        "```",
        "",
        "The third camera is unused. SO-101 has two cameras, so we just leave that key out.",
        "Same mapping for training and evaluation.",
        "",
        "### Instruction",
        "",
        f"`{task_dataset}` is the task string in the dataset, so that is what we pass at",
        "evaluation and at fine-tune time.",
        "",
        "I also ran the same frame with a different phrasing to confirm the text actually",
        "reaches the model. It does: the six numbers change. So we keep the wording fixed.",
        "",
        "| Instruction | Predicted action |",
        "|---|---|",
    ]
    for label in ("dataset", "alternate"):
        vec = np.array2string(results[label]["action"], precision=3, separator=", ")
        lines.append(f"| `{results[label]['task']}` | `{vec}` |")

    lines += [
        "",
        "### Action horizon",
        "",
        f"`chunk_size` is {policy.config.chunk_size}, so one query returns at most",
        f"{policy.config.chunk_size} future actions. First rollout uses 16. The later sweep is 1 to 50.",
        "",
    ]

    (out / "contract_test_report.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
