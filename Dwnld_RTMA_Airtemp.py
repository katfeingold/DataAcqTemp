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
from tkinter import filedialog, messagebox, ttk  # ttk for Progressbar



# --------------------------------------------
# Expected format for user-entered datetimes
# --------------------------------------------
DATE_FORMAT = "%Y-%m-%d %H:%M"



# --------------------------------------------------------
# Simple progress bar globals (similar style to other scripts)
# --------------------------------------------------------
_progress_root = None
_progress_var = None
_progress_label = None
_progress_total = 0


def create_progress_window(total_steps: int):
    """
    Create a small Tk window with a determinate progress bar showing
    how many RTMA files (hours) have been processed out of total_steps.
    """
    global _progress_root, _progress_var, _progress_label, _progress_total
    _progress_total = total_steps

    _progress_root = tk.Tk()
    _progress_root.title("RTMA Download Progress")
    _progress_root.resizable(False, False)

    frame = ttk.Frame(_progress_root, padding=10)
    frame.grid(row=0, column=0, sticky="nsew")

    _progress_var = tk.IntVar(value=0)

    ttk.Label(frame, text="Downloading RTMA temperature files...").grid(
        row=0, column=0, sticky="w"
    )

    bar = ttk.Progressbar(
        frame,
        orient="horizontal",
        mode="determinate",
        maximum=total_steps,
        variable=_progress_var,
        length=300,
    )
    bar.grid(row=1, column=0, pady=(5, 5))

    _progress_label = ttk.Label(frame, text=f"0 of {total_steps} hours")
    _progress_label.grid(row=2, column=0, sticky="w")

    # Center the window a bit
    _progress_root.update_idletasks()
    w = _progress_root.winfo_width()
    h = _progress_root.winfo_height()
    sw = _progress_root.winfo_screenwidth()
    sh = _progress_root.winfo_screenheight()
    x = (sw // 2) - (w // 2)
    y = (sh // 2) - (h // 2)
    _progress_root.geometry(f"+{x}+{y}")
    _progress_root.attributes("-topmost", True)
    _progress_root.lift()

    _progress_root.update()


def update_progress_window():
    """
    Increment the file counter and refresh the progress window.
    """
    global _progress_root, _progress_var, _progress_label, _progress_total
    if _progress_root is None:
        return

    current = _progress_var.get() + 1
    _progress_var.set(current)
    if _progress_label is not None:
        _progress_label.config(text=f"{current} of {_progress_total} hours")
    _progress_root.update_idletasks()


def close_progress_window():
    """
    Close and destroy the progress window if it exists.
    """
    global _progress_root
    if _progress_root is not None:
        _progress_root.destroy()
        _progress_root = None



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

    # --------------------------------------------
    # Pre-compute number of hours for progress bar
    # --------------------------------------------
    total_steps = int((end - start).total_seconds() // 3600)
    if total_steps < 1:
        total_steps = 1  # just in case
    create_progress_window(total_steps)

    date = start
    try:
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
            # Update progress after each hour processed
            # --------------------------------------------
            update_progress_window()
    finally:
        # always close the progress window at the end
        close_progress_window()

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



def show_completion_popup(saved_files, missing_dates, destination):
    """
    Show a popup summarizing:
      - destination folder
      - which files were saved and where
      - whether any dates were missing

    Uses a scrollable list so the window doesn't fill the whole screen.
    """
    root = tk.Tk()
    root.withdraw()

    # Small top-level window
    win = tk.Toplevel(root)
    win.title("RTMA Download")
    win.resizable(True, True)

    # Frame for everything
    frame = tk.Frame(win, padx=10, pady=10)
    frame.grid(row=0, column=0, sticky="nsew")

    win.grid_rowconfigure(0, weight=1)
    win.grid_columnconfigure(0, weight=1)

    # Summary label
    if saved_files:
        summary_text = f"Download completed. Saved {len(saved_files)} file(s)."
    else:
        summary_text = "Download completed, but no files were saved."

    tk.Label(frame, text=summary_text).grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(0, 5)
    )

    # Destination folder line (your new request)
    tk.Label(
        frame,
        text=f"Destination folder: {destination}",
        anchor="w",
        justify="left",
        wraplength=600,
    ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 5))

    # List label
    tk.Label(frame, text="Saved files:").grid(
        row=2, column=0, columnspan=2, sticky="w"
    )

    # Listbox + vertical scrollbar
    list_frame = tk.Frame(frame)
    list_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(2, 5))

    frame.grid_rowconfigure(3, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    listbox = tk.Listbox(list_frame, height=10, width=80)
    scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
    listbox.config(yscrollcommand=scrollbar.set)

    listbox.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    list_frame.grid_rowconfigure(0, weight=1)
    list_frame.grid_columnconfigure(0, weight=1)

    # Populate listbox with saved files
    for path in saved_files:
        listbox.insert(tk.END, path)

    # Missing dates (short text, separate area)
    if missing_dates:
        miss_label = tk.Label(frame, text="Missing dates (no file found or error):")
        miss_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(5, 0))

        miss_text = tk.Text(frame, height=5, width=80, wrap="none")
        miss_scroll = tk.Scrollbar(frame, orient="vertical", command=miss_text.yview)
        miss_text.config(yscrollcommand=miss_scroll.set, state="normal")

        miss_text.grid(row=5, column=0, sticky="nsew", pady=(2, 5))
        miss_scroll.grid(row=5, column=1, sticky="ns", padx=(2, 0))

        frame.grid_rowconfigure(5, weight=1)

        for d in missing_dates:
            miss_text.insert(tk.END, str(d) + "\n")
        miss_text.config(state="disabled")

    # Close button
    btn = tk.Button(frame, text="Close", width=10, command=win.destroy)
    btn.grid(row=6, column=0, columnspan=2, pady=(8, 0))

    # Center the window nicely
    win.update_idletasks()
    w = win.winfo_width()
    h = win.winfo_height()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw // 2) - (w // 2)
    y = (sh // 2) - (h // 2)
    win.geometry(f"+{x}+{y}")
    win.attributes("-topmost", True)
    win.lift()

    win.grab_set()
    root.wait_window(win)
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
        show_completion_popup(saved, missing, dest)
