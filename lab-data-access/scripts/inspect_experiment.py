#!/usr/bin/env python3
import argparse
import csv
import os
import pickle
from pathlib import Path, PureWindowsPath

import numpy as np

MOVIE_FRAME_ROOT = Path("/home/adamranson/data/vid_for_decoder/cinematic_clips")


def derive_animal_id(exp_id: str) -> str:
    parts = exp_id.split("_")
    if len(parts) < 3:
        raise ValueError(f"Cannot derive animalID from expID: {exp_id}")
    return parts[2]


def resolve_root(user_id: str, exp_id: str) -> Path:
    animal_id = derive_animal_id(exp_id)
    return Path("/home") / user_id / "data" / "Repository" / animal_id / exp_id


def summarise_value(value):
    if isinstance(value, np.ndarray):
        return {"type": "ndarray", "shape": tuple(value.shape), "dtype": str(value.dtype)}
    if hasattr(value, "shape"):
        return {"type": type(value).__name__, "shape": tuple(value.shape)}
    return {"type": type(value).__name__}


def summarise_pickle(path: Path):
    with path.open("rb") as handle:
        obj = pickle.load(handle)
    if isinstance(obj, dict):
        return {
            "type": "dict",
            "keys": list(obj.keys()),
            "summary": {key: summarise_value(value) for key, value in obj.items()},
        }
    return {"type": type(obj).__name__}


def preview_csv(path: Path, rows: int):
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        preview = []
        for index, row in enumerate(reader):
            if index >= rows:
                break
            preview.append(row)
    return columns, preview


def print_section(title: str):
    print(f"\n== {title} ==")


def load_trial_rows(path: Path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def parse_value(text):
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return text


def feature_prefixes(columns):
    prefixes = sorted({col.split("_", 1)[0] for col in columns if "_" in col and col.startswith("F")})
    return [prefix for prefix in prefixes if prefix[1:].isdigit()]


def resolve_movie_npy_from_feature_name(feature_name: str) -> Path:
    stem = Path(PureWindowsPath(str(feature_name)).name).stem
    return MOVIE_FRAME_ROOT / f"{stem}.npy"


def movie_feature_blocks(row, columns):
    blocks = []
    for prefix in feature_prefixes(columns):
        type_key = f"{prefix}_type"
        if row.get(type_key) != "movie":
            continue
        name_key = f"{prefix}_name"
        onset_key = f"{prefix}_onset"
        duration_key = f"{prefix}_duration"
        speed_key = f"{prefix}_speed"
        loop_key = f"{prefix}_loop"
        feature_name = row.get(name_key)
        if not feature_name:
            continue
        movie_path = resolve_movie_npy_from_feature_name(feature_name)
        blocks.append(
            {
                "prefix": prefix,
                "name": feature_name,
                "movie_npy": movie_path,
                "onset": parse_value(row.get(onset_key)),
                "duration": parse_value(row.get(duration_key)),
                "speed": parse_value(row.get(speed_key)),
                "loop": row.get(loop_key),
            }
        )
    return blocks


def summarize_movie_feature_rows(rows, columns, max_rows=5):
    summary = []
    for index, row in enumerate(rows[:max_rows]):
        blocks = movie_feature_blocks(row, columns)
        if not blocks:
            continue
        payload = {"trial_index": index, "movie_features": blocks}
        if len(blocks) > 1:
            payload["warning"] = "multiple movie features detected; request disambiguation"
        summary.append(payload)
    return summary


def main():
    parser = argparse.ArgumentParser(description="Inspect an experiment folder by userID and expID.")
    parser.add_argument("--userID", required=True)
    parser.add_argument("--expID", required=True)
    parser.add_argument("--csv-rows", type=int, default=3)
    parser.add_argument("--filter-column")
    parser.add_argument("--filter-value")
    args = parser.parse_args()

    root = resolve_root(args.userID, args.expID)
    print(f"root: {root}")
    if not root.exists():
        raise SystemExit(f"Experiment root does not exist: {root}")

    csv_path = root / f"{args.expID}_all_trials.csv"
    print_section("trial csv")
    if csv_path.exists():
        columns, preview = preview_csv(csv_path, args.csv_rows)
        all_rows = load_trial_rows(csv_path)
        print(f"path: {csv_path}")
        print(f"columns ({len(columns)}): {columns}")
        print(f"rows: {len(all_rows)}")
        print(f"preview_rows: {len(preview)}")
        for row in preview:
            print(row)
        if args.filter_column:
            if args.filter_column not in columns:
                print(f"filter_error: missing column {args.filter_column!r}")
            else:
                target = parse_value(args.filter_value)
                matched = []
                for index, row in enumerate(all_rows):
                    value = parse_value(row.get(args.filter_column))
                    if value == target:
                        matched.append(index)
                print(f"filter: {args.filter_column} == {args.filter_value}")
                print(f"matched_trials: {len(matched)}")
                print(f"matched_indices: {matched[:25]}{'...' if len(matched) > 25 else ''}")

        print_section("movie feature resolution")
        movie_summaries = summarize_movie_feature_rows(all_rows, columns, max_rows=min(args.csv_rows, len(all_rows)))
        if not movie_summaries:
            print("no movie features found in preview rows")
        else:
            for item in movie_summaries:
                print(f"trial_index: {item['trial_index']}")
                if "warning" in item:
                    print(f"  warning: {item['warning']}")
                for block in item["movie_features"]:
                    print(f"  feature: {block['prefix']}")
                    print(f"    name: {block['name']}")
                    print(f"    movie_npy: {block['movie_npy']}")
                    print(f"    exists: {block['movie_npy'].exists()}")
                    print(f"    onset: {block['onset']}")
                    print(f"    duration: {block['duration']}")
                    print(f"    speed: {block['speed']}")
                    print(f"    loop: {block['loop']}")
                    if block["movie_npy"].exists():
                        arr = np.load(block["movie_npy"], mmap_mode="r")
                        print(f"    movie_shape: {arr.shape}")
    else:
        print(f"missing: {csv_path}")

    print_section("root files")
    for path in sorted(root.iterdir()):
        kind = "dir" if path.is_dir() else "file"
        print(f"{kind}: {path.name}")

    for subdir_name, interesting in [
        (
            "recordings",
            [
                "s2p_ch0.pickle",
                "s2p_tokenised_ch0.pickle",
                "wheel.pickle",
                "dlcEyeLeft_resampled.pickle",
                "dlcEyeRight_resampled.pickle",
                "dlcEyeLeft.pickle",
                "dlcEyeRight.pickle",
                "eye_frame_times.npy",
                "ephys.npy",
            ],
        ),
        ("cut", sorted([p.name for p in (root / "cut").iterdir()]) if (root / "cut").exists() else []),
    ]:
        subdir = root / subdir_name
        print_section(subdir_name)
        if not subdir.exists():
            print(f"missing: {subdir}")
            continue

        for name in interesting:
            path = subdir / name
            if not path.exists():
                print(f"missing: {name}")
                continue
            print(f"{name}:")
            if path.suffix == ".pickle":
                summary = summarise_pickle(path)
                print(f"  type: {summary['type']}")
                if "keys" in summary:
                    print(f"  keys: {summary['keys']}")
                    for key, value in summary["summary"].items():
                        if subdir_name == "cut" and key == "0":
                            label = "EEG"
                        elif subdir_name == "cut" and key == "1":
                            label = "EMG"
                        else:
                            label = None
                        if label:
                            print(f"    {key} ({label}): {value}")
                            continue
                        print(f"    {key}: {value}")
            elif path.suffix == ".npy":
                array = np.load(path, allow_pickle=True)
                print(f"  ndarray shape={array.shape} dtype={array.dtype}")
            else:
                print(f"  file")


if __name__ == "__main__":
    main()
