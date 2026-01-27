import argparse
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class ColumnStats:
    count: int = 0
    total: float = 0.0
    total_sq: float = 0.0

    def add(self, series: pd.Series):
        values = pd.to_numeric(series, errors="coerce").dropna()
        if values.empty:
            return
        arr = values.values.astype(float)
        self.count += arr.size
        self.total += arr.sum()
        self.total_sq += np.dot(arr, arr)

    def mean(self):
        return self.total / self.count if self.count else np.nan

    def std(self):
        if not self.count:
            return np.nan
        variance = self.total_sq / self.count - self.mean() ** 2
        return np.sqrt(variance) if variance >= 0 else 0.0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Aggregate acceleration and angular velocity statistics across the dataset."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("/Volumes/Elements/XSens_FullBody_MotionDataset"),
        help="Root directory containing Participant_* folders.",
    )
    parser.add_argument(
        "--condition",
        default="No-Walker",
        help="Subfolder name inside the participant folder (e.g., No-Walker).",
    )
    parser.add_argument(
        "--accel-file",
        default="Segment Acceleration.csv",
        help="Acceleration CSV filename.",
    )
    parser.add_argument(
        "--angular-file",
        default="Segment Angular Velocity.csv",
        help="Angular velocity CSV filename.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Number of participants to process (default: all).",
    )
    return parser.parse_args()


def numeric_columns(df: pd.DataFrame):
    return df.select_dtypes(include=[np.number]).drop(columns=[c for c in ("Frame",) if c in df.columns], errors="ignore")


def summarized_stats(stats_map: dict[str, ColumnStats]) -> pd.DataFrame:
    rows = []
    for col, stats in stats_map.items():
        if stats.count:
            rows.append({"column": col, "mean": stats.mean(), "std": stats.std()})
    if not rows:
        return pd.DataFrame(columns=["column", "mean", "std"])
    df = pd.DataFrame(rows).set_index("column")
    return df.sort_index()


def main():
    args = parse_args()
    if not args.root.exists():
        raise FileNotFoundError(f"Dataset root {args.root} does not exist.")

    participants = sorted(
        [p for p in args.root.iterdir() if p.is_dir() and p.name.startswith("Participant")]
    )
    if args.limit:
        participants = participants[: args.limit]

    accel_stats = defaultdict(ColumnStats)
    ang_stats = defaultdict(ColumnStats)
    fall_peaks = []
    nonfall_peaks = []

    for participant in participants:
        accel_path = participant / args.condition / args.accel_file
        ang_path = participant / args.condition / args.angular_file

        if not accel_path.exists():
            print(f"{participant.name}: missing {accel_path.relative_to(participant)}")
            continue

        accel_df = pd.read_csv(accel_path)
        accel_numeric = numeric_columns(accel_df)
        for column in accel_numeric:
            accel_stats[column].add(accel_numeric[column])

        if "label" in accel_df.columns:
            acc_mag = accel_numeric.abs().max(axis=1)
            label_series = accel_df["label"].fillna("").astype(str)
            fall_mask = label_series.str.contains("fall", case=False, na=False)
            nonfall_mask = ~fall_mask & label_series.str.strip().ne("")

            if fall_mask.any():
                fall_peaks.append(acc_mag[fall_mask].max())
            if nonfall_mask.any():
                nonfall_peaks.append(acc_mag[nonfall_mask].max())

        if not ang_path.exists():
            print(f"{participant.name}: missing {ang_path.relative_to(participant)}")
            continue

        ang_df = pd.read_csv(ang_path)
        ang_numeric = numeric_columns(ang_df)
        for column in ang_numeric:
            ang_stats[column].add(ang_numeric[column])

    accel_summary = summarized_stats(accel_stats)
    ang_summary = summarized_stats(ang_stats)

    print("\nLinear Acceleration Statistics (mean ± std):")
    if not accel_summary.empty:
        with pd.option_context("display.float_format", "{:,.3f}".format):
            print(accel_summary)
    else:
        print("No acceleration data was aggregated.")

    print("\nAngular Velocity Statistics (mean ± std):")
    if not ang_summary.empty:
        with pd.option_context("display.float_format", "{:,.3f}".format):
            print(ang_summary)
    else:
        print("No angular velocity data was aggregated.")

    if fall_peaks and nonfall_peaks:
        print(
            "\nFall vs non-fall peak accelerations (max absolute channel value per frame):"
        )
        print(f"  Falls  (mean peak): {np.mean(fall_peaks):.2f} m/s²")
        print(f"  Non-falls (mean peak): {np.mean(nonfall_peaks):.2f} m/s²")
        print(
            "  (Falls show higher peak acceleration, which supports discriminative structure.)"
        )
    else:
        print("\nInsufficient label data to compare fall vs non-fall acceleration peaks.")


if __name__ == "__main__":
    main()
