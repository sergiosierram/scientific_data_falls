# Scientific Data Falls

Small utilities for inspecting and summarizing the XSens FullBody Motion Dataset (falls + walking).

## Requirements
- Python 3.9+
- Dataset on disk (default path used by scripts: `/Volumes/Elements/XSens_FullBody_MotionDataset`)
- Python dependencies listed in `requirements.txt`

Install:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Expected dataset layout
```
/Volumes/Elements/XSens_FullBody_MotionDataset/
  Participant_1/
    No-Walker/
      Segment Acceleration.csv
      Segment Angular Velocity.csv
  Participant_2/
    No-Walker/
      ...
```

## Scripts

### 01_integrity_checks.py
Checks for missing frames in the acceleration log and out-of-range angular velocity values.

Default limits: -500 to 500 deg/s.

Usage:
```bash
python 01_integrity_checks.py \
  --root /Volumes/Elements/XSens_FullBody_MotionDataset \
  --subdir No-Walker \
  --file "Segment Acceleration.csv" \
  --ang-file "Segment Angular Velocity.csv" \
  --ang-min -500 \
  --ang-max 500
```

### 02_plot_walk.py
Plots a 10-second window of walking data and a fall event window for a selected segment (default: Left Toe) from a single participant file. Adjust the `csv_path`, `segment`, and `window_seconds` variables at the top of the script as needed.

Outputs an EPS file (`filename.eps`) and also shows the plot.

Run:
```bash
python 02_plot_walk.py
```

### 03_label_check.py
Aggregates label counts across participants and produces `label_distribution.eps`.

Update the settings at the top of the script to match your dataset root and condition (defaults to `No-Walker`).

Run:
```bash
python 03_label_check.py
```

### 04_summary_quality.py
Computes dataset-wide summary statistics for acceleration and angular velocity, plus a fall vs non-fall peak comparison if labels are available.

Usage:
```bash
python 04_summary_quality.py \
  --root /Volumes/Elements/XSens_FullBody_MotionDataset \
  --condition No-Walker \
  --accel-file "Segment Acceleration.csv" \
  --angular-file "Segment Angular Velocity.csv"
```

## Notes
- Scripts assume the dataset uses `Participant_*` folders.
- EPS outputs are saved in the project folder by default.
