# Training

Ritwik. 25 Nov 2026.

SmolVLA fine-tuned on the college HPC. The simulator stayed on the lab RTX 4090. This file is the training run: what was pinned, what the cluster forced us to do, the loss, and where the weights are. Scoring those weights is the next step, and it is not done yet.

The 4090 baseline is still the number to beat. Seed 1000, three episodes, 60 seconds, horizon 16. Pretrained SmolVLA and a random policy were both 0/3. Clips are in `videos/`. The script is `flow/04_rollout/eval_rollout.py`.

## What I trained

| Item | Value |
|---|---|
| Policy | `lerobot/smolvla_base`, about 450M |
| Dataset | `LightwheelAI/leisaac-pick-orange` |
| Episodes | 60, 36,293 frames, 30 fps |
| Task string | `Grab orange and place into plate` |
| Cameras | `observation.images.front` → `camera1`, `observation.images.wrist` → `camera2` |
| Action | 6 joints: shoulder pan, shoulder lift, elbow flex, wrist flex, wrist roll, gripper |
| LeRobot | 0.4.2, same as the 4090 |
| Python | 3.11. The 3.12 module exists. The venv is 3.11, which is what the 4090 conda env uses. |
| Torch | 2.7.1+cu126 |
| Transformers | 4.57.6 |
| Machine | One H100 PCIe, node `g19`, partition `gpuqm` |
| Seed | 1000, same seed as the eval |

`train_expert_only` and `freeze_vision_encoder` were both on. The vision backbone stays frozen. The action expert is what moves. The loss is SmolVLA's flow-matching loss. It says how close the predicted actions are to the demonstrations. It is not a grasp rate. Grasp, place, and task completion still come from the 4090.

There is no Isaac on the H100. The job did not set `--env`, and `eval_freq` was 0. Evaluation during training would have had nothing to run.

## Where it lives

The GPU nodes and the login node `g17` cannot open HTTPS. Downloads happened on the login node, through the HTTP proxy on `coe-hpc1`, into lab scratch. The job then ran offline against that cache.

| What | Path |
|---|---|
| Scratch root | `/scratch/cmpe295-wu/019151535` |
| Hugging Face cache | `/scratch/cmpe295-wu/019151535/hf` |
| LeRobot venv | `/scratch/cmpe295-wu/019151535/venvs/lerobot042` |
| Smoke output | `/scratch/cmpe295-wu/019151535/dmrc/smolvla_smoke` |
| Full output | `/scratch/cmpe295-wu/019151535/dmrc/smolvla_full` |
| Job scripts | `/scratch/cmpe295-wu/019151535/dmrc/smolvla_smoke.sbatch`, `smolvla_full.sbatch` |
| Full log | `/scratch/cmpe295-wu/019151535/dmrc/logs/full-161676.err` |

`$SCRATCH` is not set on this cluster. The lab directory is `/scratch/cmpe295-wu`, and my files are under `019151535`. Scratch is shared storage. Logging out does not delete it. It is still the right place to copy from. It is not an archive.

Hugging Face keys and the WandB key are outside the repo, mode 600. They are not in git.

## What had to happen before the job

The public SmolVLA repo and the public dataset were downloaded into `HF_HOME`. Both are ungated.

SmolVLA also loads `HuggingFaceTB/SmolVLM2-500M-Video-Instruct` when the policy is built. That repo is separate from `model.safetensors`. It was cached too, or the GPU node would have sat there trying to download it.

The hub dataset is codebase v2.1. LeRobot 0.4.2 reads v3.0. I copied the snapshot into the LeRobot cache and converted it in place with `lerobot.datasets.v30.convert_dataset_v21_to_v30`, `--push-to-hub=false`. After conversion the local set was still 60 episodes and 36,293 frames, now marked v3.0. The conversion was not pushed back to `LightwheelAI`.

Video decode used PyAV. TorchCodec is installed, and it wanted FFmpeg shared libraries the compute node does not have. PyAV opened the mp4s.

The login-node Python is 3.9, and `coe-hpc1` is 3.6. The venv was built on `g17` from `/usr/bin/python3.11`, which the GPU nodes also have.

## Smoke test

Job `161675` on `g19`. Five episodes, indices 0 through 4. 500 steps. Batch size 8. This only proved the loss moves. Those weights are not the policy we score.

| Step | Loss |
|---|---|
| 100 | 0.111 |
| 500 | 0.042 |

`checkpoints/000500/pretrained_model/` and `checkpoints/last/pretrained_model/` both had the files the 4090 loader asks for:

- `model.safetensors`
- `config.json`
- `policy_preprocessor.json`
- `policy_postprocessor.json`
- `policy_preprocessor_step_5_normalizer_processor.safetensors`
- `policy_postprocessor_step_0_unnormalizer_processor.safetensors`

`train_config.json` is there too. It is the run config, not a weight the sim needs.

## Full run

Job `161676` on `g19`. Submitted with `sbatch` to `gpuqm`, account `coe`, 8 CPUs, 64 GB, 24 hour limit. It finished in 42 minutes, exit 0. All 60 episodes. 20,000 steps. Batch size 8. Log every 100 steps. Save every 2,000 steps. An update took about 0.10 seconds.

| Step | Loss |
|---|---|
| 100 | 0.147 |
| 1,000 | 0.079 |
| 2,000 | 0.068 |
| 5,000 | 0.046 |
| 10,000 | 0.031 |
| 15,000 | 0.023 |
| 20,000 | 0.022 |

The learning rate in the log peaked near `1e-4` after the warmup and was `2.5e-6` at step 20,000. That `2.5e-6` is `scheduler_decay_lr` in the SmolVLA config. Warmup is 1,000 steps. The configured decay length is 30,000 steps. We stopped at 20,000, which was the plan.

The loss drops fast, then flattens after 15,000. That is the training curve. It still has to be scored on the 4090 before anyone calls it a better policy.

## Checkpoints

Every 2,000 steps has its own folder:

`/scratch/cmpe295-wu/019151535/dmrc/smolvla_full/checkpoints/`

`002000`, `004000`, `006000`, `008000`, `010000`, `012000`, `014000`, `016000`, `018000`, `020000`.

`last` is a shortcut to the newest save. After this run, `last` and `020000` are the same weights.

Each numbered folder has two parts. `pretrained_model/` is the policy, about 829 MB, and `model.safetensors` inside it is 865 MB. `training_state/` is the optimizer, about 377 MB. The eval does not need the optimizer.

For the clips I am bringing back three policy folders:

| Steps | Loss at that step | Why |
|---|---|---|
| 2,000 | 0.068 | Early. The loss has already fallen and the policy should still look rough. |
| 10,000 | 0.031 | Middle. |
| 20,000 | 0.022 | The one that goes in the score table. |

The 20,000-step folder is on the laptop at `~/smolvla_step20000`. The other two use the same copy, from `checkpoints/002000/pretrained_model/` and `checkpoints/010000/pretrained_model/`. Scratch still has every save from 2,000 through 20,000.

## The command that actually ran

```bash
python -m lerobot.scripts.lerobot_train \
  --policy.path=lerobot/smolvla_base \
  --policy.push_to_hub=false \
  --policy.device=cuda \
  --dataset.repo_id=LightwheelAI/leisaac-pick-orange \
  --dataset.video_backend=pyav \
  --rename_map='{"observation.images.front":"observation.images.camera1","observation.images.wrist":"observation.images.camera2"}' \
  --batch_size=8 \
  --steps=20000 \
  --log_freq=100 \
  --save_freq=2000 \
  --eval_freq=0 \
  --num_workers=4 \
  --output_dir=$SCRATCH/dmrc/smolvla_full \
  --seed=1000 \
  --wandb.enable=true \
  --wandb.project=dmrc-smolvla \
  --wandb.mode=offline \
  --wandb.disable_artifact=true \
  --job_name=smolvla_full
```

In the job, `SCRATCH` was `/scratch/cmpe295-wu/019151535`. The smoke command was the same with `--dataset.episodes='[0,1,2,3,4]'`, `--steps=500`, `--save_freq=500`, and `smolvla_smoke` as the output name.

`push_to_hub` was turned off. The base config wants to upload at the end, and the GPU node cannot reach Hugging Face, so the job would have died after a good run. Upload happens later, from the laptop.

## WandB

The GPU node cannot reach WandB either. The job logged offline. A loop on the login node, through the same proxy, uploaded the run when the job ended.

Project: [dmrc-smolvla](https://forge.coreweave.com/wandb/ritwikreddy99-redgod/dmrc-smolvla)

| Run | Link |
|---|---|
| Smoke | [smolvla_smoke](https://forge.coreweave.com/wandb/ritwikreddy99-redgod/dmrc-smolvla/runs/da7mmrzp) |
| Full | [smolvla_full](https://forge.coreweave.com/wandb/ritwikreddy99-redgod/dmrc-smolvla/runs/qm9spzwe) |

Account on that host is `ritwikreddy99`, entity `ritwikreddy99-redgod`. Checkpoint files were not uploaded as WandB artifacts. The curves are the point. The weights stay on scratch until they are copied off.

## What I did not do

- No Isaac, no LeIsaac, no cameras rendered on the H100.
- The smoke checkpoint was not brought back for the real eval.
- The dataset conversion was not pushed to the original hub repo.
- The cluster did not upload the policy to Hugging Face.
- The 4090 has not scored these weights yet. `videos/finetune/` is still empty.
- No RL.

## What is left

Copy the three `pretrained_model` folders onto the 4090. Hugging Face is one way to move them. A folder on the 4090 disk is the other. The 4090 cannot see `/scratch`.

Same eval as the baseline. From `leisaac`, with `start_policy_server.py` already running:

```bash
python ../flow/04_rollout/eval_rollout.py \
  --policy pretrained \
  --checkpoint /path/to/smolvla_step20000 \
  --episodes 3 --seed 1000 --episode_length_s 60 \
  --headless --enable_cameras --device cuda:0
```

`--checkpoint` can be that local folder, or a Hugging Face repo id if the files sit at the root of the repo. Step 20,000 is the row that gets compared to the 0/3 baseline. Steps 2,000 and 10,000 are the clips that show the policy changing. Write the videos under `videos/finetune/` and append the rows to `flow/04_rollout/report/eval_metrics.csv`.

## If asked

**Why this LeRobot version?** The 4090 runs LeIsaac 0.4.0, and that stack imports LeRobot 0.4.2. The laptop checks were on 0.6.1. A checkpoint from a different LeRobot will not load in `eval_rollout.py`.

**Why train on the H100?** The H100 has no RT cores. Isaac Sim will not render the cameras there. The 4090 is the sim machine. Training is a dataset and a GPU, so it stays on the cluster.

**What did the fine-tune change?** The action expert, with the vision encoder frozen. The pretrained policy returns six joint targets near zero, and the demonstrations on that same frame are tens of degrees. The gripper in the baseline never really closes. The fine-tune is supposed to pull those outputs toward the demos.

**Why is the loss not the result?** The loss is how well the network matches the recorded actions. The result is grasp, place, and whether all three oranges end in the plate with the arm back at rest. Those are measured by replaying the checkpoint in the same scene, seed 1000, 60 seconds.

**Why did it flatten?** From 0.147 at step 100 to 0.023 at step 15,000, then 0.022 at step 20,000. Sixty demonstrations, batch 8. Most of the fit happened in the first half of the run. The last 5,000 steps did not buy much training loss. The 4090 still has to show whether that shows up as a grasp.

**Why these cameras?** The dataset calls them front and wrist. SmolVLA's inputs are `camera1` and `camera2`. The rename map is that translation. The third camera on the base checkpoint is left unused. We do not feed it a black image.

**Why PyAV?** TorchCodec could not load its FFmpeg libraries on the compute node. PyAV could read the episode videos, so the job used `--dataset.video_backend=pyav`.

**Why is `last` not its own set of weights?** It is a pointer to the latest numbered checkpoint. Today that is `020000`.

**Why keep 2,000 and 10,000?** So the video can show an early policy, a middle one, and the final one. The scoreboard uses 20,000 only.

**What has to be in the folder or the upload fails on the 4090?** `model.safetensors`, `config.json`, both processor json files, and both normalizer `.safetensors` files. If the processor files are missing, stop. The eval client cannot load the checkpoint.
