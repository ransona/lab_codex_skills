# Lab Data Layout

This reference records the layout observed in two inspected experiments:

- `pmateosaparicio / 2025-07-04_04_ESPM154`
- `melinatimplalexi / 2025-08-28_03_ESPM171`

Use this as a schema guide for the fixed repository convention used by this lab. Individual files can still vary.

## Root Path Convention

Root path pattern:

```text
/home/{userID}/data/Repository/{animalID}/{expID}
```

`animalID` extraction:

```text
expID = YYYY-MM-DD_NN_ANIMALID
animalID = third underscore-delimited field
```

Examples:

- `/home/pmateosaparicio/data/Repository/ESPM154/2025-07-04_04_ESPM154`
- `/home/melinatimplalexi/data/Repository/ESPM171/2025-08-28_03_ESPM171`

## Root-Level Files

Observed common files:

- `{expID}_all_trials.csv`
- `pipeline_config.pickle`
- `step2_config.pickle`
- camera videos and DLC exports for left and right eye
- `recordings/`
- `cut/`

Observed extra folders or products in some experiments:

- `composer/`
- `reconstructions/`
- `sleep_score/`
- `suite2p_combined/`
- OASIS cut products

## Trial CSV

Observed invariant columns:

- `time`
- `stim`
- `duration`

Observed feature columns:

- `F1_*`
- `F2_*`

Observed examples:

- `2025-07-04_04_ESPM154`: 128 rows, 14 columns, only `F1_*`, `F1_type = movie`
- `2025-08-28_03_ESPM171`: 174 rows, 31 columns, both `F1_*` and `F2_*`, `F1_type/F2_type = grating`

Observed feature fields included:

- `angle`
- `contrast`
- `dcycle`
- `duration`
- `freq`
- `height`
- `loop`
- `name`
- `onset`
- `opacity`
- `phase`
- `speed`
- `type`
- `width`
- `x`
- `y`

Interpretation:

- `time`: trial start in Timeline time
- `stim`: stimulus configuration ID
- `duration`: total trial duration
- `F*_onset`: onset relative to trial start

## `recordings/`

### `s2p_ch0.pickle`

Observed keys:

- always observed: `dF`, `F`, `Spikes`, `Depths`, `AllRoiPix`, `AllRoiMaps`, `AllFOV`, `t`
- present in one experiment and absent in another: `Baseline`

Observed shapes:

- `ESPM154`: `dF/F/Spikes` shape `(5443, 141306)`, `t` shape `(141306,)`
- `ESPM171`: `dF/F/Spikes` shape `(105, 85695)`, `t` shape `(85695,)`

Interpretation:

- axis order is `[neuron, time]`
- `t` is the continuous Timeline-aligned time vector

### `s2p_tokenised_ch0.pickle`

Observed as optional.

- `ESPM154`: present with key `all_tokenised_dF_spikes`, shape `(85416999, 3)`
- `ESPM171`: absent

Do not assume this file exists.

### `wheel.pickle`

Observed keys:

- `position`
- `position_smoothed`
- `speed`
- `t`

Observed shapes:

- `ESPM154`: `(93960,)`
- `ESPM171`: `(56860,)`

Interpretation:

- continuous wheel traces indexed by Timeline time `t`

### `dlcEyeLeft_resampled.pickle` and `dlcEyeRight_resampled.pickle`

Observed keys:

- `t`
- `x`
- `y`
- `radius`
- `velocity`
- `qc`
- `frame`

Observed shapes:

- `ESPM154`: `(47150,)`
- `ESPM171`: `(28600,)`

Interpretation:

- already resampled and aligned to Timeline time

### `dlcEyeLeft.pickle` and `dlcEyeRight.pickle`

Observed common keys:

- `x`
- `y`
- `radius`
- `qc`
- `eye_lid_x`
- `eye_lid_y`
- `eyeX`
- `eyeY`
- `pupilX`
- `pupilY`
- `topLid`
- `botLid`
- `inEye`
- `velocity`

Observed variation:

- `ESPM154` also had uppercase `QC`
- `ESPM171` did not

Observed shapes:

- scalar traces like `x`, `y`, `radius`, `velocity`: `(n_frames,)`
- `eye_lid_x`, `eye_lid_y`: `(n_frames, 40)`
- `eyeX`, `eyeY`: `(n_frames, 4)`
- `pupilX`, `pupilY`, `inEye`: `(n_frames, 8)`
- `topLid`, `botLid`: `(n_frames, 3)`

Associated file:

- `eye_frame_times.npy` shape `(n_frames,)`

## `ephys.npy`

Observed shape:

- `(3, 4715000)` for `ESPM154`
- `(3, 2860000)` for `ESPM171`

This is continuous ephys-like data. Channel identities were supplied later:

- channel `0` = EEG
- channel `1` = EMG

The third channel remains undocumented from the information currently provided.

## `cut/`

### Neural cut files

Observed files:

- `s2p_ch0_dF_cut.pickle`
- `s2p_ch0_F_cut.pickle`
- `s2p_ch0_Spikes_cut.pickle`

Observed optional files:

- `s2p_ch0_oasis_dF_cut.pickle`
- `s2p_ch0_oasis_spikes_cut.pickle`

Observed keys and shapes:

- `dF` or `F` or `Spikes`: `[neuron, trial, time]`
- `t`: `(time,)`

Examples:

- `ESPM154`: `dF` shape `(5443, 128, 1200)`
- `ESPM171`: `dF` shape `(105, 174, 1200)`

### Wheel cut file

Observed file:

- `wheel.pickle`

Observed keys:

- `position`
- `speed`
- `t`

Observed shapes:

- `position/speed`: `(trial, time)`
- `ESPM154`: `(128, 800)`
- `ESPM171`: `(174, 800)`

### Eye cut files

Observed files:

- `eye_left_cut.pickle`
- `eye_right_cut.pickle`

Observed keys:

- `x`
- `y`
- `radius`
- `velocity`
- `qc`
- `frame`
- `t`

Observed shapes:

- most arrays: `(trial, time)`
- `ESPM154`: `(128, 400)`
- `ESPM171`: `(174, 400)`

Observed anomaly:

- `frame` had shape `(129, 400)` for `ESPM154`
- `frame` had shape `(175, 400)` for `ESPM171`

So `frame` was `(trials + 1, time)` in both inspected experiments. Check this directly before assuming strict alignment with the other eye arrays.

### Ephys cut file

Observed file:

- `ephys_cut.pickle`

Observed keys:

- `"0"`
- `"1"`
- `t`

Observed shapes:

- channel arrays: `(trial, 40001)`
- `ESPM154`: `(128, 40001)`
- `ESPM171`: `(174, 40001)`

Channel meanings supplied later:

- `"0"` = EEG
- `"1"` = EMG

The cut `t` vector is relative to trial onset.

## Config Pickles

### `pipeline_config.pickle`

Observed fields:

- `command`
- `userID`
- `expID`
- `config`

Observed `config` members included:

- `runs2p`
- `rundlc`
- `runfitpupil`
- `suite2p_config`
- `settings`

### `step2_config.pickle`

Observed fields:

- `userID`
- `expIDs`
- `pre_secs`
- `post_secs`
- `run_bonvision`
- `run_s2p_timestamp`
- `run_ephys`
- `run_dlc_timestamp`
- `run_cuttraces`
- `settings`

Observed values in both experiments:

- `pre_secs = 5`
- `post_secs = 5`

These values are consistent with the cut arrays spanning pre/post trial windows.

## Trial Axis Conventions

Use the trial table row order as the trial order for cut data unless there is explicit evidence otherwise.

- trial CSV rows: one row per trial
- neural cut arrays: `[neuron, trial, time]`
- wheel cut arrays: `[trial, time]`
- eye cut arrays: `[trial, time]` for most keys
- ephys cut arrays: `[trial, time]`

Observed caveat:

- `eye_left_cut["frame"]` and `eye_right_cut["frame"]` were `(trials + 1, time)` in both inspected experiments, while the other eye-cut arrays matched the trial table row count exactly

This does not mean there was one extra trial in the trial table. It means the `frame` entry had one extra row relative to the other cut arrays and relative to the trial CSV row count.
