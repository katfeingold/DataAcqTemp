"""
This will Download RTMA temperature (TMP) GRIB2 files from the IA State Mesonet archive
for a date/time range, and save them to a chosen folder.
"""
#----------------------------------------------------------------
# Author (so you know who to yell at) Kat Feingold
# Last updated: 3/3/2026
# Updated Changes:
# 3/2/2026 - script created
#----------------------------------------------------------------


import urllib.request
from urllib.error import HTTPError
from datetime import datetime, timedelta
import os
import tkinter as tk
from tkinter import filedialog, messagebox

# --------------------------------------------
# Expected format for user-entered datetimes
# --------------------------------------------
DATE_FORMAT = "%Y-%m-%d %H:%M"


def get_user_inputs():
    def on_ok():
        nonlocal start_dt, end_dt, dest
        s = start_entry.get().strip()
        e = end_entry.get().strip()

        # -----------------------------------------------------------------
        # Parse dates, yes i know there are better ways, fix it if it bothers you
        # -----------------------------------------------------------------
        try:
            start_dt = datetime.strptime(s, DATE_FORMAT)
            end_dt = datetime.strptime(e, DATE_FORMAT)
        except ValueError:
            messagebox.showerror(
                "Invalid format",
                f"Please use format: {DATE_FORMAT}",
                parent=win,
            )
            return

        # --------------------------------------------
        # Pumpkin spiced latte (Basic) range check
        # --------------------------------------------
        if end_dt <= start_dt:
            messagebox.showerror(
                "Invalid range",
                "End must be after start.",
                parent=win,
            )
            return

        # -----------------------------------------------------------------
        # Ask for destination folder after dates are valid and not before
        # -----------------------------------------------------------------
        dest = filedialog.askdirectory(
            title="Select download folder",
            parent=win,
        )
        if not dest:
            # --------------------------------------------
            # User cancelled folder selection
            # --------------------------------------------
            start_dt = end_dt = dest = None
            win.destroy()
            return

        # -------------------------------------------
        # Close dialog and continue
        # -------------------------------------------
        win.destroy()

    def on_cancel():
        # --------------------------------------------
        # Handle Cancel button: clear values and close the dialog
        # --------------------------------------------
        nonlocal start_dt, end_dt, dest
        start_dt = end_dt = dest = None
        win.destroy()

    # --------------------------------------------
    # Initialize return values
    # --------------------------------------------
    start_dt = end_dt = dest = None

    # --------------------------------------------
    # Root Tk window (hidden, at least its supposed to be)
    # --------------------------------------------
    root = tk.Tk()
    root.withdraw()

    # --------------------------------------------
    # Top-level dialog window
    # --------------------------------------------
    win = tk.Toplevel(root)
    win.title("RTMA download settings")
    win.resizable(False, False)

    # --------------------------------------------
    # Instruction label
    # --------------------------------------------
    tk.Label(
        win,
        text=f"Enter date/time in format: {DATE_FORMAT}",
    ).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5))

    # --------------------------------------------
    # Start datetime entry
    # --------------------------------------------
    tk.Label(win, text="Start (UTC):").grid(
        row=1, column=0, sticky="e", padx=10, pady=5
    )
    start_entry = tk.Entry(win, width=20)
    start_entry.grid(row=1, column=1, padx=10, pady=5)

    # --------------------------------------------
    # End datetime entry
    # --------------------------------------------
    tk.Label(win, text="End (UTC):").grid(
        row=2, column=0, sticky="e", padx=10, pady=5
    )
    end_entry = tk.Entry(win, width=20)
    end_entry.grid(row=2, column=1, padx=10, pady=5)

    # -----------------------------------------------------------------------------------
    # Prefill with a default: I chose the last 24 hours, you can change it if you want
    # -----------------------------------------------------------------------------------
    now = datetime.utcnow()
    start_entry.insert(0, (now - timedelta(hours=24)).strftime(DATE_FORMAT))
    end_entry.insert(0, now.strftime(DATE_FORMAT))

    # --------------------------------------------
    # Buttons frame
    # --------------------------------------------
    btn_frame = tk.Frame(win)
    btn_frame.grid(row=3, column=0, columnspan=2, pady=(5, 10))

    tk.Button(btn_frame, text="OK", width=10, command=on_ok).pack(
        side="left", padx=5
    )
    tk.Button(btn_frame, text="Cancel", width=10, command=on_cancel).pack(
        side="left", padx=5
    )

    # ---------------------------------------------------------------------
    # Center the dialog on screen, because it bothers me when it's not
    # ---------------------------------------------------------------------
    win.update_idletasks()
    win.geometry(
        f"+{win.winfo_screenwidth() // 2 - win.winfo_width() // 2}"
        f"+{win.winfo_screenheight() // 2 - win.winfo_height() // 2}"
    )

    # Make dialog modal
    win.grab_set()
    root.wait_window(win)

    root.destroy()
    return start_dt, end_dt, dest


def download_rtma(start, end, destination):
    """
    Loop hourly between 'start' (inclusive) and 'end' (exclusive),
    building RTMA TMP GRIB2 URLs and saving any existing files
    into 'destination'.

    Returns:
        saved_files: list of full paths to successfully saved files
        missing_dates: list of datetime objects for which the file was missing or errored
    """
    hour = timedelta(hours=1)
    missing_dates = []
    saved_files = []

    date = start
    while date < end:
        # ------------------------------------------------------------
        # Build the IA State Mesonet RTMA URL for this date/hour
        # ------------------------------------------------------------
        url = (
            "http://mtarchive.geol.iastate.edu/{:04d}/{:02d}/{:02d}/grib2/ncep/RTMA/"
            "{:04d}{:02d}{:02d}{:02d}00_TMP.grib2"
        ).format(
            date.year,
            date.month,
            date.day,
            date.year,
            date.month,
            date.day,
            date.hour,
        )

        filename = os.path.basename(url)
        print(f"Processing {date} -> {filename}")

        try:
            # --------------------------------------------
            # Retrieve the GRIB2 file
            # --------------------------------------------
            with urllib.request.urlopen(url) as response:
                data = response.read()
        except HTTPError as e:
            print(f"  MISSING (HTTP {e.code})")
            missing_dates.append(date)
        except Exception as e:
            print(f"  ERROR: {e}")
            missing_dates.append(date)
        else:
            # --------------------------------------------
            # Save to destination folder
            # --------------------------------------------
            os.makedirs(destination, exist_ok=True)
            out_path = os.path.join(destination, filename)
            with open(out_path, "wb") as f:
                f.write(data)
            print(f"  Saved to {out_path}")
            saved_files.append(out_path)

        # --------------------------------------------
        # Advance to next hour
        # --------------------------------------------
        date += hour

    # --------------------------------------------
    # summary
    # --------------------------------------------
    if missing_dates:
        print("\nMissing dates:")
        for d in missing_dates:
            print(d)
    else:
        print("\nAll requested hours downloaded successfully.")

    return saved_files, missing_dates


def show_completion_popup(saved_files, missing_dates):
    """
    Show a popup summarizing:
      - which files were saved and where
      - whether any dates were missing
    """
    root = tk.Tk()
    root.withdraw()

    lines = []

    if saved_files:
        lines.append("Download completed.")
        lines.append("")
        lines.append("Saved files:")
        lines.extend(saved_files)
    else:
        lines.append("Download completed, but no files were saved.")

    if missing_dates:
        lines.append("")
        lines.append("Missing dates (no file found or error):")
        for d in missing_dates:
            lines.append(str(d))

    msg = "\n".join(lines)

    messagebox.showinfo("RTMA Download", msg)
    root.destroy()


if __name__ == "__main__":
    # -------------------------------------------
    # Get user inputs via the cute little popup
    # -------------------------------------------
    start_dt, end_dt, dest = get_user_inputs()
    if start_dt is None:
        # --------------------------------------------
        # Either cancel or invalid input message
        # --------------------------------------------
        print("User cancelled input or provided invalid values.")
    else:
        # --------------------------------------------
        # Run download and show completion popup
        # --------------------------------------------
        saved, missing = download_rtma(start_dt, end_dt, dest)
        show_completion_popup(saved, missing)
