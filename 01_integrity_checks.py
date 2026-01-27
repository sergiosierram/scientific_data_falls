import argparse
from pathlib import Path

import pandas as pd

DEFAULT_ROOT = Path("/Volumes/Elements/XSens_FullBody_MotionDataset")
DEFAULT_SUBDIR = "No-Walker"
DEFAULT_ACCEL_FILE = "Segment Acceleration.csv"
DEFAULT_ANG_FILE = "Segment Angular Velocity.csv"
DEFAULT_ANG_MIN = -500.0
DEFAULT_ANG_MAX = 500.0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Check each participant's acceleration log for missing frames and angular velocity ranges."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Root folder containing the participant directories.",
    )
    parser.add_argument(
        "--subdir",
        default=DEFAULT_SUBDIR,
        help="Subdirectory inside each participant where the CSV files live.",
    )
    parser.add_argument(
        "--file",
        default=DEFAULT_ACCEL_FILE,
        help="CSV file to inspect for missing frames.",
    )
    parser.add_argument(
        "--ang-file",
        default=DEFAULT_ANG_FILE,
        help="CSV file containing angular velocity data.",
    )
    parser.add_argument(
        "--ang-min",
        type=float,
        default=DEFAULT_ANG_MIN,
        help="Minimum acceptable angular velocity value (deg/s).",
    )
    parser.add_argument(
        "--ang-max",
        type=float,
        default=DEFAULT_ANG_MAX,
        help="Maximum acceptable angular velocity value (deg/s).",
    )
    return parser.parse_args()


def load_csv(csv_path: Path, require_frame: bool = False):
    try:
        df = pd.read_csv(csv_path)
    except (ValueError, pd.errors.EmptyDataError) as exc:
        raise RuntimeError(f"failed to read {csv_path}: {exc}")
    if require_frame and "Frame" not in df:
        raise RuntimeError(f"no 'Frame' column found in {csv_path}.")
    return df


def evaluate_dataframe_range(df: pd.DataFrame, min_value: float, max_value: float, exclude_columns=None):
    exclude_columns = set(exclude_columns or [])
    issues = []
    numeric = df.select_dtypes(include=["number"]).drop(
        columns=[c for c in exclude_columns if c in df.columns],
        errors="ignore",
    )
    for column in numeric.columns:
        col_min = numeric[column].min(skipna=True)
        col_max = numeric[column].max(skipna=True)
        if pd.isna(col_min) or pd.isna(col_max):
            continue
        if col_min < min_value or col_max > max_value:
            issues.append(
                f"{column} range ({col_min:.2f}, {col_max:.2f}) outside [{min_value}, {max_value}]"
            )
    return issues


def find_participants(root: Path):
    if not root.exists():
        print(f"Dataset root {root} does not exist.")
        return []
    participants = [p for p in root.iterdir() if p.is_dir() and p.name.startswith("Participant")]
    return sorted(participants)


def find_missing_frame_ranges(frames: pd.Series):
    numeric = pd.to_numeric(frames, errors="coerce").dropna().astype(int)
    if numeric.empty:
        return []
    values = numeric.reset_index(drop=True).tolist()
    missing_ranges = []
    for prev, current in zip(values, values[1:]):
        gap_length = current - prev - 1
        if gap_length <= 0:
            continue
        gap_start = prev + 1
        gap_end = current - 1
        missing_ranges.append(
            f"{gap_start}" if gap_start == gap_end else f"{gap_start}-{gap_end}"
        )
    return missing_ranges


def main():
    args = parse_args()

    participants = find_participants(args.root)
    if not participants:
        print("No participant directories found.")
        return

    summary = []
    for participant in participants:
        report = {
            "name": participant.name,
            "error": None,
            "missing_frames": None,
            "ang_checked": False,
            "ang_issues": None,
            "angular_warning": None,
        }

        data_dir = participant / args.subdir
        csv_path = data_dir / args.file
        if not csv_path.exists():
            report["error"] = f"missing {csv_path.relative_to(participant)}"
            print(f"{participant.name}: {report['error']}")
            summary.append(report)
            continue

        try:
            acc_df = load_csv(csv_path, require_frame=True)
        except RuntimeError as exc:
            report["error"] = str(exc)
            print(f"{participant.name}: {report['error']}")
            summary.append(report)
            continue

        report["missing_frames"] = find_missing_frame_ranges(acc_df["Frame"])

        ang_path = data_dir / args.ang_file
        if not ang_path.exists():
            report["angular_warning"] = f"missing {ang_path.relative_to(participant)}"
        else:
            try:
                ang_df = load_csv(ang_path)
            except RuntimeError as exc:
                report["angular_warning"] = str(exc)
            else:
                report["ang_checked"] = True
                report["ang_issues"] = evaluate_dataframe_range(
                    ang_df, args.ang_min, args.ang_max, exclude_columns={"Frame"}
                )

        status = []
        if report["missing_frames"]:
            status.append(f"missing frames {', '.join(report['missing_frames'])}")
        else:
            status.append("no missing frames")

        if report["ang_checked"]:
            if report["ang_issues"]:
                status.append("angular velocity out-of-range: " + "; ".join(report["ang_issues"]))
            else:
                status.append("angular velocity within limits")
        elif report["angular_warning"]:
            status.append(report["angular_warning"])
        else:
            status.append("angular velocity not evaluated")

        print(f"{participant.name}: {'; '.join(status)}")
        summary.append(report)

    processed = sum(1 for r in summary if r["error"] is None)
    missing_frames_count = sum(1 for r in summary if r["missing_frames"])
    ang_issues_count = sum(1 for r in summary if r["ang_issues"])
    ang_warnings = sum(1 for r in summary if r["angular_warning"])

    print("\nSummary:")
    print(f"  Participants processed: {processed}/{len(summary)}")
    print(f"  Participants skipped due to errors: {len(summary) - processed}")
    print(f"  Participants with missing frames: {missing_frames_count}")
    print(f"  Participants with angular velocity violations: {ang_issues_count}")
    print(f"  Angular velocity warnings (missing or unreadable file): {ang_warnings}")


if __name__ == "__main__":
    main()
