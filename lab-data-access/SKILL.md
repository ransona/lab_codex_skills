---
name: lab-data-access
description: Locate and inspect mouse neural and behavioural experiment data stored by `userID` and `expID`. Use when Codex needs to resolve experiment roots, read trial tables, inspect `recordings/` or `cut/` data, summarize pickle keys or array shapes, compare experiments, or work with these repository layouts without assuming every optional file is present.
---

# Lab Data Access

Resolve an experiment path from `userID` and `expID`, inspect the files that exist, describe the schema conservatively, and extract trial subsets from the trial table when needed.

## Workflow

1. Resolve the root path as `/home/{userID}/data/Repository/{animalID}/{expID}`.
2. Derive `animalID` from the experiment ID suffix. For IDs like `2025-08-28_03_ESPM171`, use `ESPM171`.
3. Inspect the root, `recordings/`, and `cut/` instead of assuming every file exists.
4. Read the trial CSV header before interpreting trial features.
5. Report optional or version-specific files explicitly.
6. When asked for trial subsets, filter the trial CSV first and then apply the resulting trial indices to cut arrays.

If you need a quick machine-readable summary, run `scripts/inspect_experiment.py`.

## Path Rules

## Platform-Specific Repository Rules

- On Windows workstations for this lab setup, schemas are accessed from `\\ar-lab-nas1\DataServer\opto_schemas`.
- On Ubuntu workstations for this lab setup, schemas are accessed from `/mnt/opto_schemas`.
- Imaging-to-photostim ROI target import from experiment pixel coordinates is supported on Ubuntu only, not on Windows.
- On Ubuntu, raw TIFF data for ROI-target lookup is stored under `/data/Remote_Repository/[animalID]/[expID]/[path name]/[roi name]`.
- For P1 imaging, expect ROI-target raw imaging data under `/data/Remote_Repository/[animalID]/[expID]/P1/[roi name]`.

- Expect `expID` to look like `YYYY-MM-DD_NN_ANIMALID`.
- Infer `animalID` as the third underscore-delimited field.
- Treat this path rule and `expID` format as fixed for this skill.
- Verify the resolved path exists before doing deeper work.

## What To Inspect First

Inspect these items in this order:

- Root-level `*_all_trials.csv`
- Root-level config pickles such as `pipeline_config.pickle` and `step2_config.pickle`
- `recordings/` for continuous aligned signals
- `cut/` for per-trial snippets

Use `references/data-layout.md` for the observed schema and known variations.

## Trial Table Guidance

- Treat `time` as trial start time in Timeline time.
- Treat `stim` as the stimulus configuration ID shown on that trial.
- Treat `duration` as trial duration.
- Interpret feature columns by prefix, for example `F1_*`, `F2_*`.
- Do not assume only one feature exists. One inspected experiment had only `F1_*`; another had both `F1_*` and `F2_*`.
- Do not assume a given feature type. Observed values included `movie` and `grating`.

## Movie Feature Rules

- For movie features, the authoritative movie source field is the feature `name` parameter:
  - for example `F1_name` when `F1_type == "movie"`
  - or `F2_name` when `F2_type == "movie"`
- Do not use the original full path in the trial table to locate the movie frames file.
- Instead:
  - take only the basename stem from the feature `name` value
  - prepend `/home/adamranson/data/vid_for_decoder/cinematic_clips/`
  - append `.npy`
- Example:
  - `D:\bonsai_resources\all_movie_clips_bv_sets\002\00438`
  - maps to `/home/adamranson/data/vid_for_decoder/cinematic_clips/00438.npy`
- Treat the loaded `.npy` as the authoritative movie frame source.
- Determine frame count from the loaded `.npy` array itself, not from duration or speed alone.
- If multiple movie features are present on the same trial, warn and request disambiguation instead of guessing.

## Trial Subsets

- Build subsets from the trial CSV, not from assumptions about stimulus numbering alone.
- Return or preserve the original row indices so cut arrays can be indexed consistently.
- Common filters include `stim`, `F1_type`, `F2_type`, feature parameters such as `F1_angle`, and time windows derived from `time` or `duration`.
- If a feature column is missing in a given experiment, report that clearly instead of fabricating an empty subset.
- Apply filtered trial indices to cut arrays along the trial axis:
  - neural cut data: axis 1 in `[neuron, trial, time]`
  - wheel/eye/eeg/emg cut data: axis 0 in `[trial, time]`

## Recording Guidance

- Processed calcium recordings in `recordings/s2p_ch*.pickle` can include `OriginalSuite2pCellIDs`, a row-aligned array mapping each processed neuron row back to its original Suite2p ROI index.
- Expect `recordings/s2p_ch0.pickle` to hold continuous neural traces with time vector `t`.
- In multi-channel Suite2p experiments, ROI detection outputs and extracted traces are commonly split by functional channel:
  - the first/green functional channel uses the root `suite2p/planeN/` tree
  - the second/red functional channel uses the parallel `ch2/suite2p/planeN/` tree
  - inspect `ops.npy` for `nchannels` and `functional_chan` to confirm which tree was processed as channel 1 or channel 2
  - only assume the binary for that channel is available in its channel-specific tree; inspect the plane directory before assuming `data.bin` or `data_chan2.bin` exists there
- Expect `recordings/wheel.pickle` to hold continuous wheel traces with time vector `t`.
- Expect `recordings/dlcEyeLeft_resampled.pickle` and `recordings/dlcEyeRight_resampled.pickle` to hold eye traces already aligned to Timeline time.
- Treat `recordings/s2p_tokenised_ch0.pickle` as optional.
- Treat raw eye pickles (`dlcEyeLeft.pickle`, `dlcEyeRight.pickle`) as versioned: key sets can differ slightly across experiments.

## Raw Stimulus And Behavior Synchronization

Visual stimulus experiments use Bonvision plus two DAQ systems: Timeline and Harp.

- Bonvision generates the visual stimulus and a synchronization square in a screen corner.
- The sync square switches from black to white at trial start and then continues alternating.
- A photodiode pointed at that corner is acquired into the Timeline `Photodiode` analog channel.
- The same photodiode signal is also acquired by Harp.

## Bonvision Raw Outputs

Bonvision provides three relevant raw outputs.

- Timeline `Bonvision` channel:
  - This is a digital synchronization signal acquired in Timeline.
  - It leads the photodiode signal because it does not wait for monitor refresh.
  - It is guaranteed to start high at experiment start.
- `expID + '_FrameEvents.csv'`:
  - Contains frame number, Bonvision timestamp, sync-square state, and current trial number.
- `expID + '_Encoder.csv'`:
  - Contains locomotion samples logged by Bonvision.
- Bonvision is always running and always produces both CSV files.

## Harp Raw Outputs

Harp always acquires at `1000 Hz`.

- Harp stores the photodiode signal.
- Harp also stores locomotion data.
- Harp locomotion is preferred when available because of its higher time resolution.
- Two Harp raw file variants are supported:
  - `expID + '_Behavior_Event44.bin'`
  - `expID + '_Behavior_44.bin'`
- These variants differ in how encoder values should be interpreted, so file version must be checked before decoding.

## Timebase Linking

There are three timebases in this raw part of the pipeline.

- Bonvision time from `FrameEvents.csv`
- Timeline time from `*_Timeline.mat`
- Harp time from the Harp binary stream

Current preprocessing links them as follows.

- In visual-stimulus experiments:
  - Use the shared photodiode signal to link Harp time to Timeline time.
  - Use Bonvision flip times to link Bonvision time to Timeline time.
- In screen-off experiments:
  - No visual sync square is present, so photodiode alignment is unavailable.
  - Use the Bonvision digital output signal in Timeline to link Bonvision time to Timeline time.
  - Use Bonvision encoder data for locomotion in this case.

## Trial Start Rule

Trial onset is defined from Bonvision trial numbers.

- A new trial begins when the `Trial` value in `expID + '_FrameEvents.csv'` increments.

## Flip Detection And Filtering

Timeline and Harp analog inputs can contain noise, so threshold crossing alone can produce spurious flips.

Current preprocessing detects and filters sync pulses as follows.

- Count positive-going transitions only:
  - low to high transitions are treated as sync events
  - high to low transitions are ignored for synchronization
- This avoids end-of-acquisition ambiguity when a final falling edge is not fully acquired on one system.
- The first pulse can be depended upon to be detected.
- The signals should end low at experiment end.
- Current preprocessing filters detected pulses by rejecting intervals that are too short.
- This is intended to suppress spurious boundary crossings caused by noisy analog inputs.
- The current minimum interval is `0.05 s`.
- The current maximum interval is effectively unbounded in preprocessing.
- The last detected pulse should not be excluded just because there is no following interval available.
- BV CSV-derived flips are filtered to stay consistent with Timeline Bonvision flips, so Bonvision-side filtering is partly constrained by Timeline-derived timing.


## Sleep Scoring Data

- Sleep scoring outputs are stored in the processed experiment directory, not the raw repository root.
- When processed paths are available, inspect `exp_dir_processed/sleep_score/` for sleep-state products.
- The canonical hypnogram file is:
  - `sleep_state.pickle`
  - or `sleep_state_sim.pickle` when simulated EEG/EMG mode was used
- Treat these files as Python pickles containing whole-experiment sleep-state annotations and derived features.
- Also treat `sleep_score/figs/` as optional QC output only; figures are not the authoritative sleep-state source.

## Sleep State Schema

- Expect `sleep_state*.pickle` to contain downsampled continuous traces and epoch-level state labels.
- Common required keys observed in this repo are:
  - `emg_rms_10hz`, `emg_rms_10hz_t`
  - `wheel_10hz`, `wheel_10hz_t`
  - `face_motion_10hz`, `face_motion_10hz_t`
  - `eeg_10hz`, `eeg_10hz_t`
  - `epoch_t`
  - `theta_power`, `delta_power`
  - `eeg_spectrogram`, `eeg_spectrogram_freqs`, `eeg_spectrogram_t`
  - `state_epoch`, `state_epoch_t`
  - `state_10hz`, `state_10hz_t`
  - `epoch_features`
- Common metadata and thresholds include:
  - `state_labels`
  - `emg_rms_threshold`
  - `theta_ratio_threshold` and sometimes the alias `theta_delta_ratio_threshold`
  - `low_freq_threshold` and sometimes the alias `delta_power_threshold`
  - `locomotion_threshold`
  - `delta_band`, `theta_band`, `low_freq_max_hz`
  - optional GUI edits such as `left_video_crop`, `right_video_crop`
- In this repo, `state_epoch` is the epoch-wise hypnogram and `state_10hz` is the nearest-neighbor interpolation of that hypnogram onto the 10 Hz timeline.
- Treat `epoch_features` as cached per-epoch features for fast rescoring, not as the authoritative state labels themselves.
- In this repo, the numeric sleep-state mapping is:
  - `0` = active wake
  - `1` = quiet wake
  - `2` = NREM
  - `3` = REM

## Sleep State Analysis Guidance

- Use `sleep_state*.pickle` as the authoritative source for whole-recording sleep-state labels.
- For state-dependent continuous analyses, align continuous signals to either:
  - `state_10hz_t` with `state_10hz` for 10 Hz analyses
  - `state_epoch_t` with `state_epoch` for epoch-wise analyses
- When summarizing the file, report array shapes for `state_epoch`, `state_10hz`, and the major trace/time pairs.
- When both `sleep_state.pickle` and `sleep_state_sim.pickle` exist, do not mix them; state clearly which one is being analyzed.
- If thresholds are relevant to the analysis, report both the stored threshold keys and any aliasing, for example `theta_ratio_threshold` versus `theta_delta_ratio_threshold`.

## Cut Data Guidance

- Expect cut neural arrays to be shaped `[neuron, trial, time]`.
- Expect cut wheel and eye arrays to be shaped `[trial, time]`.
- Expect a shared relative time vector `t` inside each cut pickle.
- Treat cut `t` as relative to trial onset, not absolute Timeline time.
- Treat extra cut products such as OASIS-derived files as optional.
- Check shapes directly before indexing; at least one inspected eye cut file had `frame` shaped `(trials + 1, time)` while sibling arrays were `(trials, time)`.

## Reporting Rules

- Separate observed facts from inferences.
- Name missing optional files instead of treating them as errors.
- Include keys and array shapes when summarizing a pickle.
- Call out schema differences across experiments when they matter.
- Label `ephys_cut.pickle["0"]` as EEG and `ephys_cut.pickle["1"]` as EMG.
- If multiple movie features are detected for a trial and the intended one is unclear, warn and request disambiguation.

## Movie Frame Timing

- To determine which movie frame is visible at a particular trial-relative time, use the movie feature parameters:
  - `onset`
  - `duration`
  - `speed`
  - `loop`
- Treat `onset` as relative to trial start.
- Treat `speed` as frames per second.
- Treat `loop` as `0` or `1`:
  - `0` means false
  - `1` means true
- At the exact onset time, show the first frame.
- If the queried trial-relative time is outside the movie play period, no frame is visible.
  - movie play period is `onset <= t_rel < onset + duration`
- Use the following procedure:
  1. Find the feature block where `F*_type == "movie"`.
  2. If more than one such block exists, warn and request disambiguation.
  3. Resolve the movie `.npy` path from the feature `name` field basename.
  4. Load the `.npy` and get `num_frames` from the array shape.
  5. If `t_rel` is outside the play period, return no visible frame.
  6. Compute `elapsed = t_rel - onset`.
  7. Compute `frame_index = floor(elapsed * speed)`.
  8. If `loop == 1`, wrap with modulo `num_frames`.
  9. If `loop == 0`, keep the frame only while `frame_index < num_frames`; otherwise no frame is visible.

## Helper Script

Run:

```bash
python scripts/inspect_experiment.py --userID melinatimplalexi --expID 2025-08-28_03_ESPM171
```

The script resolves the root path, prints the trial CSV header and a small preview, then summarizes representative files in `recordings/` and `cut/`.
