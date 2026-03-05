# -*- coding: utf-8 -*-
"""
Downloads the NDFD CONUS ( this is CONUS ONLY) forecast air temperature files (ds.temp.bin)
from the VP.001-003 and VP.004-007 directories, save each as: a .bin copy, and  a .grib2 copy,
then show a popup listing only the .grib2 files saved.


"""


import os
import nest_asyncio
nest_asyncio.apply()  
import asyncio
import aiohttp
import async_timeout
import tkinter as tk
from tkinter import filedialog, messagebox, ttk  # ttk for Progressbar



# ----------------------------------------------------------
# Base URL for CONUS NDFD data
# ----------------------------------------------------------
BASE_URL = "https://tgftp.nws.noaa.gov/SL.us008001/ST.opnl/DF.gr2/DC.ndfd/AR.conus"


#----------------------------------------------------------------------------------------
#  Identifies the VP directories to download from and the suffix used in output filenames
# VP.001-003 becomes ds.temp.001-003.bin & ds.temp.001-003.grib2
# VP.004-007 becomes ds.temp.004-007.bin & ds.temp.004-007.grib2
# ----------------------------------------------------------------------------------------
VP_DIRS = [
    ("VP.001-003", "001-003"),
    ("VP.004-007", "004-007"),
]


# --------------------------------------------------------
# Simple progress bar globals (similar style to QPF script)
# --------------------------------------------------------
_progress_root = None
_progress_var = None
_progress_label = None
_progress_total = 0


def create_progress_window(total_files: int):
    """
    Create a small Tk window with a determinate progress bar showing
    how many files have been downloaded out of total_files.
    """
    global _progress_root, _progress_var, _progress_label, _progress_total
    _progress_total = total_files

    _progress_root = tk.Tk()
    _progress_root.title("NDFD Download Progress")
    _progress_root.resizable(False, False)

    frame = ttk.Frame(_progress_root, padding=10)
    frame.grid(row=0, column=0, sticky="nsew")

    _progress_var = tk.IntVar(value=0)

    ttk.Label(frame, text="Downloading NDFD temperature files...").grid(
        row=0, column=0, sticky="w"
    )

    bar = ttk.Progressbar(
        frame,
        orient="horizontal",
        mode="determinate",
        maximum=total_files,
        variable=_progress_var,
        length=300,
    )
    bar.grid(row=1, column=0, pady=(5, 5))

    _progress_label = ttk.Label(frame, text=f"0 of {total_files} files")
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
        _progress_label.config(text=f"{current} of {_progress_total} files")
    _progress_root.update_idletasks()


def close_progress_window():
    """
    Close and destroy the progress window if it exists.
    """
    global _progress_root
    if _progress_root is not None:
        _progress_root.destroy()
        _progress_root = None



def get_destination_folder():
    """
    Show a folder selection dialog and return the chosen path.
    If the user cancels, return None.
    """
    root = tk.Tk()
    root.withdraw()  


    dest = filedialog.askdirectory(
        title="Select folder to save NDFD forecast temperature files"
    )


    root.destroy()


    if not dest:
        print("No folder selected. Exiting.")
        return None


    return dest



async def download_file(session, url, out_path_bin, out_path_grib2, saved_files):
 
    # ------------------------------------------------------------
    # Ensure destination folder exists, it thinks therefore it is
    # ------------------------------------------------------------
    os.makedirs(os.path.dirname(out_path_bin), exist_ok=True)


    try:
        # ---------------------------------------
        # Overall timeout for the HTTP request
        # ---------------------------------------
        async with async_timeout.timeout(600):
            async with session.get(url) as response:
                if response.status == 200:
                    print(f"Downloading {url} -> {out_path_bin} and {out_path_grib2}")


                    # ------------------------------------------
                    # Reads  into memory
                    # ------------------------------------------
                    data = bytearray()
                    async for chunk in response.content.iter_chunked(8192):
                        if not chunk:
                            break
                        data.extend(chunk)


                    # ------------------------------------------ 
                    # Write .bin copy , the native file on the site
                    # ------------------------------------------
                    with open(out_path_bin, "wb") as f_bin:
                        f_bin.write(data)


                    # ------------------------------------------ 
                    # Write .grib2 copy (same files, different extension)
                    # ------------------------------------------


                    with open(out_path_grib2, "wb") as f_grb:
                        f_grb.write(data)


                    # ------------------------------------------ 
                    # Track saved files
                    # ------------------------------------------
                    saved_files.append(out_path_bin)
                    saved_files.append(out_path_grib2)
                else:
                    # ------------------------------------------ 
                    # Non-200 HTTP status jsut in case
                    # ------------------------------------------
                    print(f"MISSING (HTTP {response.status}): {url}")
    except Exception as e:
        # ------------------------------------------ 
        # Catch and log  errors
        # ------------------------------------------ 
        print(f"ERROR for {url}: {e}")
    finally:
        # ------------------------------------------
        # Update progress whether success or failure
        # ------------------------------------------
        update_progress_window()



async def main_async(destination):


    saved_files = []


    async with aiohttp.ClientSession() as session:
        tasks = []


        # ------------------------------------------
        # Build download tasks for each VP directory
        # ------------------------------------------
        for vp_dir, suffix in VP_DIRS:
            url = f"{BASE_URL}/{vp_dir}/ds.temp.bin"


            # -------------------------------------------------------------- 
            # Output filenames: one .bin and one .grib2 for each VP range
            # --------------------------------------------------------------
            out_name_bin = f"ds.temp.{suffix}.bin"
            out_name_grib2 = f"ds.temp.{suffix}.grib2"


            out_path_bin = os.path.join(destination, out_name_bin)
            out_path_grib2 = os.path.join(destination, out_name_grib2)


            tasks.append(
                download_file(
                    session, url, out_path_bin, out_path_grib2, saved_files
                )
            )


        # ------------------------------------------
        # Run all downloads concurrently, i like Async
        # ------------------------------------------
        await asyncio.gather(*tasks)


    return saved_files



def show_completion_popup(saved_files, destination):
    # --------------------------------------------------------
    #Show a Tkinter popup indicating that the script completed
    # and list only the .grib2 files that were saved.
    #
    # Uses a scrollable list so the window doesn't fill the whole screen.
    # ---------------------------------------------------------


    # Filter to include only GRIB2 files in the message
    # -----------------------------------------------------------
    grib_files = [f for f in saved_files if f.lower().endswith(".grib2")]

    root = tk.Tk()
    root.withdraw()

    win = tk.Toplevel(root)
    win.title("NDFD Download")
    win.resizable(True, True)

    frame = tk.Frame(win, padx=10, pady=10)
    frame.grid(row=0, column=0, sticky="nsew")

    win.grid_rowconfigure(0, weight=1)
    win.grid_columnconfigure(0, weight=1)

    if grib_files:
        summary_text = f"Download completed. Saved {len(grib_files)} GRIB2 file(s)."
    else:
        summary_text = "Download completed, but no GRIB2 files were saved."

    tk.Label(frame, text=summary_text).grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(0, 5)
    )

    # Destination folder line
    tk.Label(
        frame,
        text=f"Destination folder: {destination}",
        anchor="w",
        justify="left",
        wraplength=600,
    ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 5))

    tk.Label(frame, text="Saved GRIB2 files:").grid(
        row=2, column=0, columnspan=2, sticky="w"
    )

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

    for path in grib_files:
        listbox.insert(tk.END, path)

    btn = tk.Button(frame, text="Close", width=10, command=win.destroy)
    btn.grid(row=4, column=0, columnspan=2, pady=(8, 0))

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



def main():
    # ------------------------------------------
    # This is what does the thing!!!!
    # ------------------------------------------
    
    dest = get_destination_folder()
    if not dest:
        return

    # only create the progress window AFTER folder selection
    create_progress_window(len(VP_DIRS))

    try:
        # ---------------------------------------------------- 
        # Run the asynchronous part and get list of saved files
        # -----------------------------------------------------
        saved_files = asyncio.run(main_async(dest))
    finally:
        # ------------------------------------
        # Close progress window
        # ------------------------------------
        close_progress_window()

    # ------------------------------------
    # Show completion popup to the user
    # -------------------------------------
    show_completion_popup(saved_files, dest)



if __name__ == "__main__":
    main()
