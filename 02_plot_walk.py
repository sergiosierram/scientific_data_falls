import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# -----------------------------------------------------
# Settings
# -----------------------------------------------------
csv_path = "/Volumes/Elements/XSens_FullBody_MotionDataset/Participant_3/No-Walker/Segment Acceleration.csv"
sampling_rate = 120              # XSens sampling rate (Hz)
window_seconds = 10              # duration to plot
window_samples = sampling_rate * window_seconds

# -----------------------------------------------------
# Load data
# -----------------------------------------------------
df = pd.read_csv(csv_path)

segment = "Left Toe"
cols = [f"{segment} x", f"{segment} y", f"{segment} z"]

# Walk window
walking_df = df[df["label"] == "Walk"].reset_index(drop=True)
if len(walking_df) < window_samples:
    print("Not enough walking-labeled data, using first 10 seconds of full recording.")
    walking_df = df
walking_window = walking_df[cols].iloc[:window_samples]
walking_time = np.arange(len(walking_window)) / sampling_rate

# Fall window
fall_df = df[df["label"].str.contains("fall", case=False, na=False)].reset_index(drop=True)
fall_window = None
fall_time = None
if len(fall_df) == 0:
    print("No labeled fall event found in the recording.")
else:
    fall_window = fall_df[cols].iloc[:window_samples]
    fall_time = np.arange(len(fall_window)) / sampling_rate
    if len(fall_window) < window_samples:
        print("Fall event shorter than 10 seconds, plotting available samples.")

# -----------------------------------------------------
# Plot acceleration + fall subplot
# -----------------------------------------------------
fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=False)

for axis in axes:
    axis.grid(True, alpha=0.3)

# Walking subplot
ax_walk = axes[0]
for coord in cols:
    ax_walk.plot(walking_time, walking_window[coord], label=coord)
ax_walk.set_title(f"{segment} Acceleration During Walking")
ax_walk.set_xlabel("Time (s)")
ax_walk.set_ylabel("Acceleration (m/s²)")
ax_walk.legend()

# Fall subplot
ax_fall = axes[1]
if fall_window is not None and fall_time is not None:
    for coord in cols:
        ax_fall.plot(fall_time, fall_window[coord], label=coord)
    ax_fall.set_title(f"{segment} Acceleration During Fall Event")
    ax_fall.set_xlabel("Time (s)")
    ax_fall.set_ylabel("Acceleration (m/s²)")
    ax_fall.legend()
else:
    ax_fall.text(
        0.5,
        0.5,
        "Fall event data not available",
        ha="center",
        va="center",
        fontsize=12,
        alpha=0.7,
    )
    ax_fall.set_title("Fall Event")
    ax_fall.set_xticks([])
    ax_fall.set_yticks([])

plt.tight_layout()
plt.show()
fig.savefig('filename.eps', format='eps')