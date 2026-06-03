---
name: lab-data-access
description: Locate and inspect mouse neural and behavioural experiment data stored by `userID` and `expID`. Use when Codex needs to resolve experiment roots, read trial tables, inspect `recordings/` or `cut/` data, summarize pickle keys or array shapes, compare experiments, or work with these repository layouts without assuming every optional file is present.
---

# Lab Data Access

Resolve an experiment path from `userID` and `expID`, inspect the files that exist, describe the schema conservatively, and extract trial subsets from the trial table when needed.

Prefer the canonical `lab_pipeline` path resolver over hand-built paths whenever possible:

```python
from preprocess_pipeline.shared import paths

animalID, remote_repository_root, processed_root, exp_dir_processed, exp_dir_raw = paths.find_paths(
    userID,
    expID,
)
```

The canonical repo is `/home/adamranson/code/lab_pipeline`. Its runnable apps prepend `src/` to `sys.path`, but external scripts need either `PYTHONPATH=/home/[username]/code/lab_pipeline/src` or `pip install -e /home/[username]/code/lab_pipeline` in the active environment.

## Workflow

1. Resolve paths with `preprocess_pipeline.shared.paths.find_paths(userID, expID)` when `lab_pipeline` is available.
2. Derive `animalID` from the experiment ID suffix only as a fallback or sanity check. For IDs like `2025-08-28_03_ESPM171`, use `ESPM171`.
3. Inspect the processed experiment root, raw experiment root, `recordings/`, and `cut/` instead of assuming every file exists.
4. Read the trial CSV header before interpreting trial features.
5. Report optional or version-specific files explicitly.
6. When asked for trial subsets, filter the trial CSV first and then apply the resulting trial indices to cut arrays.
7. If the user is starting a stimulus-aligned trial analysis, first check whether the needed `cut/` trial snippets already exist.
8. If the required cut traces are not present, warn clearly that stimulus-aligned trial analysis should not proceed from raw continuous data by default, suggest running pipeline step 2, and stop short of attempting alignment unless the user explicitly asks for alignment work.

If you need a quick machine-readable summary, run `scripts/inspect_experiment.py`.

## Path Rules

Canonical resolver:

- Import from `preprocess_pipeline.shared import paths`.
- Call `paths.find_paths(userID, expID)`.
- It returns:
  - `animalID`
  - `remote_repository_root`
  - `processed_root`
  - `exp_dir_processed`
  - `exp_dir_raw`
- Standard server behavior:
  - `remote_repository_root = /data/Remote_Repository`
  - `processed_root = /home/[userID]/data/Repository`
  - `exp_dir_processed = /home/[userID]/data/Repository/[animalID]/[expID]`
  - `exp_dir_raw = /data/Remote_Repository/[animalID]/[expID]`
- Habituation behavior:
  - if `userID.lower() == "habit"`, processed and raw paths both resolve under `/data/common/habituation/[animalID]/[expID]`.
- Local single-root behavior:
  - pass `local_repository_root=ROOT` to `find_paths()`, or set `LAB_PIPELINE_LOCAL_REPOSITORY_ROOT=ROOT`.
  - raw and processed paths both resolve to `ROOT/[animalID]/[expID]`.
  - this is intended for local Windows/non-server processing where all data live in one repository tree.

External user scripts should use one of:

```bash
PYTHONPATH=/home/[username]/code/lab_pipeline/src python my_script.py
```

or:

```bash
pip install -e /home/[username]/code/lab_pipeline
```

## Platform-Specific Repository Rules

- On Windows workstations for this lab setup, schemas are accessed from `\\ar-lab-nas1\DataServer\opto_schemas`.
- On Ubuntu workstations for this lab setup, schemas are accessed from `/mnt/nas2/opto_schemas`.
- Imaging-to-photostim ROI target import from experiment pixel coordinates is supported on Ubuntu only, not on Windows.
- On Ubuntu, raw TIFF data for ROI-target lookup is stored under `/data/Remote_Repository/[animalID]/[expID]/[path name]/[roi name]`.
- For P1 imaging, expect ROI-target raw imaging data under `/data/Remote_Repository/[animalID]/[expID]/P1/[roi name]`.
- Suite2p configs can be stored in shared user-specific folders under `/data/common/configs/s2p_configs/[userID]`.
- For `adamranson`, expect Suite2p configs under `/data/common/configs/s2p_configs/adamranson`.

- Expect `expID` to look like `YYYY-MM-DD_NN_ANIMALID`.
- Infer `animalID` as the third underscore-delimited field when not using `paths.find_paths()`.
- Treat this `expID` format as fixed for this skill.
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
- Per-plane Suite2p folders can also contain saved Timeline-derived microscope frame timing arrays:
  - `timeline_frame_times.npy`
  - `timeline_frame_start_times.npy`
  - `timeline_output_times.npy`
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

## Microscope Frame Timing

- The authoritative absolute timebase for two-photon frames is Timeline, not the Suite2p `.bin` itself.
- Frame times are derived from positive-going transitions in the relevant Timeline microscope TTL channel.
- Standard non-mesoscope experiments use the Timeline channel `MicroscopeFrames`.
- Mesoscope experiments use:
  - `MicroscopeFrames` for scan path `P1`
  - `MicroscopeFrames2` for scan path `P2`
- Plane timing is formed by counting `plane*` folders and deinterleaving the pulse train:
  - plane `i` uses every `depthCount`-th pulse starting at offset `i`
  - in code terms: `frame_times[iDepth::depthCount]`
- Standard preprocessing stores mid-frame times in `timeline_frame_times.npy` and trigger-edge times in `timeline_frame_start_times.npy`.
- Mesoscope preprocessing currently stores the detected pulse times as both `timeline_frame_times.npy` and `timeline_frame_start_times.npy`.
- `timeline_output_times.npy` is the common 30 Hz resampled Timeline grid used for processed continuous calcium traces in `recordings/s2p_ch*.pickle["t"]`.

## Aligning Microscope Frames To Trial Onset

- Trial start times from `*_all_trials.csv["time"]` are already in Timeline time.
- Saved microscope frame times are also in Timeline time.
- Therefore align microscope frames to stimulus onset by direct subtraction:
  - `t_rel = frame_time - trial_start_time`
- For a given trial, select frames whose `t_rel` falls inside the requested pre/post window.
- If the experiment is multiplane, multi-ROI, or multi-path, do this separately for each relevant `plane*` folder because each folder has its own saved frame-time array.
- Use the folder layout to interpret what each timing file belongs to:
  - standard: `suite2p/planeN/` or `ch2/suite2p/planeN/`
  - mesoscope: `P{path}/{roi}/suite2p/planeN/` or `P{path}/{roi}/ch2/suite2p/planeN/`
- When generating stimulus-aligned registered movies from Suite2p outputs, match frame indices in the registered movie source to indices in `timeline_frame_times.npy` from the same plane folder.

## Reading Imaging Frames Directly From Suite2p Binaries

- The correct direct-reading source for registered imaging frames is the `data.bin` file inside the relevant Suite2p `plane*` folder.
- For second-channel reads, inspect the channel-specific plane folder first:
  - standard: `ch2/suite2p/planeN/`
  - mesoscope: `P{path}/{roi}/ch2/suite2p/planeN/`
- In that channel-specific folder, read whichever registered binary actually exists:
  - usually `data.bin`
  - sometimes `data_chan2.bin`
- Do not guess frame shape from file length alone.
- Before reshaping frames from `data.bin`, inspect the colocated `ops.npy` and use:
  - `Ly` for frame height
  - `Lx` for frame width
- If `Ly`/`Lx` are missing, `meanImg.shape` is an acceptable fallback for frame size.
- The correct direct-reading workflow is:
  1. Resolve the correct `plane*` folder for the desired path / ROI / channel / plane.
  2. For channel 2, switch to the `ch2/suite2p/planeN/` tree when it exists.
  3. Load `timeline_frame_times.npy` from that same folder.
  4. Load `ops.npy` from that same folder and read `Ly` / `Lx`.
  5. Memory-map the registered binary that exists there, usually `data.bin` but sometimes `data_chan2.bin`, as `int16`.
  6. Compute frame count as `mm.size // (Ly * Lx)` and verify it matches the saved timing array closely.
  7. Convert the requested Timeline-time window into frame indices using `timeline_frame_times.npy`.
  8. Reshape only the relevant part of the binary as `(n_frames, Ly, Lx)` and index the selected frames.
- For mesoscope experiments, do this independently for each selected `P{path}/{roi}/suite2p/planeN/` tree.
- For standard experiments, do this independently for each selected `suite2p/planeN/` tree and, when present, each `ch2/suite2p/planeN/` tree.
- If `timeline_frame_times.npy` is missing, do not estimate timing from frame rate alone; backfill the saved timing files first.

## Backfilling Missing Microscope Timing Files

- If `timeline_frame_times.npy` is missing from the relevant `plane*` folder, do not guess frame times from `ops.npy` or frame rate alone.
- Prefer rerunning the relevant `lab_pipeline` Step 2/Suite2p postprocessing path so timing files are generated by the current pipeline.
- Legacy backfill helpers are retained in `lab_pipeline/legacy/preprocess_py/helper/` for reference if a one-off recovery is needed.
- For standard experiments, run:
  - `python /home/adamranson/code/lab_pipeline/legacy/preprocess_py/helper/backfill_s2p_frame_times.py --userID USER --expID EXPID`
- For mesoscope experiments, run:
  - `python /home/adamranson/code/lab_pipeline/legacy/preprocess_py/helper/backfill_s2p_meso_frame_times.py --userID USER --expID EXPID`
- These helpers save the same per-plane files that the main preprocessing scripts now write:
  - `timeline_frame_times.npy`
  - `timeline_frame_start_times.npy`
  - `timeline_output_times.npy`
- Standard backfill reproduces the standard preprocessing convention:
  - `timeline_frame_times.npy` stores mid-frame times
  - `timeline_frame_start_times.npy` stores trigger-edge times
- Mesoscope backfill reproduces the current mesoscope preprocessing convention:
  - `timeline_frame_times.npy` and `timeline_frame_start_times.npy` both store the detected pulse times
- After backfilling, align frame times to trial onset exactly as above using Timeline-time subtraction.

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
- If the user wants stimulus-aligned trial analysis, prefer existing `cut/` data and do not silently substitute raw continuous traces plus Timeline or Bonvision files.
- If the relevant cut traces are missing, explicitly warn that the trial-aligned products were not found.
- In that case, suggest running pipeline step 2 to generate the cut data.
- Do not attempt stimulus alignment yourself unless the user explicitly asks for that lower-level alignment work.

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
