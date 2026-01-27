import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from collections import Counter

# -----------------------------------------------------
# Settings: point this to your dataset root and condition
# -----------------------------------------------------
DATASET_ROOT = Path("/Volumes/Elements/XSens_FullBody_MotionDataset")
CONDITION = "No-Walker"
ACC_FILE = "Segment Acceleration.csv"
EXCLUDE_LABELS = {"", "NO LABEL", "NONE", "NA", "UNKNOWN"}
EXPECTED_PARTICIPANTS = 30
OUT_IMAGE = Path("label_distribution.eps")


def get_participant_dirs(root: Path):
    if not root.exists():
        raise FileNotFoundError(f"Dataset root {root} does not exist.")
    parts = sorted([p for p in root.iterdir() if p.is_dir() and p.name.startswith("Participant")])
    return parts


def main():
    participants = get_participant_dirs(DATASET_ROOT)
    label_counts = Counter()
    processed = 0
    missing_files = 0
    missing_label = 0

    for participant in participants:
        csv_path = participant / CONDITION / ACC_FILE
        if not csv_path.exists():
            print(f"{participant.name}: missing file {csv_path.relative_to(participant)}")
            missing_files += 1
            continue

        print(f"{participant.name}: loading {csv_path}")
        acc = pd.read_csv(csv_path)
        if "label" not in acc.columns:
            print(f"{participant.name}: 'label' column missing")
            missing_label += 1
            continue

        labels = acc["label"].dropna().astype(str).str.strip().str.upper()
        valid_labels = labels[~labels.isin(EXCLUDE_LABELS)]
        label_counts.update(valid_labels)
        processed += 1

    print(f"\nParticipants processed: {processed}/{len(participants)}")
    print(f"Files missing: {missing_files}")
    print(f"Label column missing: {missing_label}")

    if not label_counts:
        print("No label data available to plot.")
        return

    label_series = pd.Series(label_counts).sort_values(ascending=False)

    plt.figure(figsize=(10, 5))
    label_series.plot(kind="bar", color="steelblue")
    plt.title("Distribution of Activity Labels Across Participants", fontsize=14)
    plt.xlabel("Activity", fontsize=12)
    plt.ylabel("Frame Count", fontsize=12)
    plt.xticks(rotation=45, ha="right")
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(OUT_IMAGE, format="eps")
    plt.show()


if __name__ == "__main__":
    main()
