import urllib.request
from urllib.error import HTTPError
from datetime import datetime, timedelta
import os
import tkinter as tk
from tkinter import filedialog, messagebox


DATE_FORMAT = "%Y-%m-%d %H:%M"


def get_user_inputs():
    def on_ok():
        nonlocal start_dt, end_dt, dest
        s = start_entry.get().strip()
        e = end_entry.get().strip()

        # Parse dates
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

        if end_dt <= start_dt:
            messagebox.showerror(
                "Invalid range",
                "End must be after start.",
                parent=win,
            )
            return

        # Ask for folder
        dest = filedialog.askdirectory(
            title="Select download folder",
            parent=win,
        )
        if not dest:
            # User cancelled folder selection
            start_dt = end_dt = dest = None
            win.destroy()
            return

        win.destroy()

    def on_cancel():
        nonlocal start_dt, end_dt, dest
        start_dt = end_dt = dest = None
        win.destroy()

    start_dt = end_dt = dest = None

    root = tk.Tk()
    root.withdraw()

    win = tk.Toplevel(root)
    win.title("RTMA download settings")
    win.resizable(False, False)

    tk.Label(
        win,
        text=f"Enter date/time in format: {DATE_FORMAT}",
    ).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5))

    tk.Label(win, text="Start (UTC):").grid(row=1, column=0, sticky="e", padx=10, pady=5)
    start_entry = tk.Entry(win, width=20)
    start_entry.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(win, text="End (UTC):").grid(row=2, column=0, sticky="e", padx=10, pady=5)
    end_entry = tk.Entry(win, width=20)
    end_entry.grid(row=2, column=1, padx=10, pady=5)

    # Optional: prefill with something sensible
    # from datetime import datetime, timedelta
    now = datetime.utcnow()
    start_entry.insert(0, (now - timedelta(hours=24)).strftime(DATE_FORMAT))
    end_entry.insert(0, now.strftime(DATE_FORMAT))

    btn_frame = tk.Frame(win)
    btn_frame.grid(row=3, column=0, columnspan=2, pady=(5, 10))

    tk.Button(btn_frame, text="OK", width=10, command=on_ok).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Cancel", width=10, command=on_cancel).pack(side="left", padx=5)

    # Center and block
    win.update_idletasks()
    win.geometry(
        f"+{win.winfo_screenwidth() // 2 - win.winfo_width() // 2}"
        f"+{win.winfo_screenheight() // 2 - win.winfo_height() // 2}"
    )
    win.grab_set()
    root.wait_window(win)

    root.destroy()
    return start_dt, end_dt, dest


def download_rtma(start, end, destination):
    hour = timedelta(hours=1)
    missing_dates = []

    date = start
    while date < end:
        url = (
            "http://mtarchive.geol.iastate.edu/{:04d}/{:02d}/{:02d}/grib2/ncep/RTMA/"
            "{:04d}{:02d}{:02d}{:02d}00_TMPK.grib2"
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
            with urllib.request.urlopen(url) as response:
                data = response.read()
        except HTTPError as e:
            print(f"  MISSING (HTTP {e.code})")
            missing_dates.append(date)
        except Exception as e:
            print(f"  ERROR: {e}")
            missing_dates.append(date)
        else:
            os.makedirs(destination, exist_ok=True)
            out_path = os.path.join(destination, filename)
            with open(out_path, "wb") as f:
                f.write(data)
            print(f"  Saved to {out_path}")

        date += hour

    if missing_dates:
        print("\nMissing dates:")
        for d in missing_dates:
            print(d)
    else:
        print("\nAll requested hours downloaded successfully.")


if __name__ == "__main__":
    start_dt, end_dt, dest = get_user_inputs()
    if start_dt is None:
        print("User cancelled input.")
    else:
        download_rtma(start_dt, end_dt, dest)
