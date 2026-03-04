# -*- coding: utf-8 -*-
"""
This thing downloads the NDFD CONUS (this is CONUS ONLY) forecast air temperature files (ds.temp.bin)
from the VP.001-003 and VP.004-007 directories, save each as: a .bin copy, and  a .grib2 copy,
in a chosen folder
"""
#----------------------------------------------------------------
# Author (so you know who to yell at) Kat Feingold
# Last updated: 3/3/2026
# Updated Changes:
# 3/2/2026 - script created
# 3/4/2026 - updated with script complete dialog 
#----------------------------------------------------------------

import os
import nest_asyncio
nest_asyncio.apply()   # allow asyncio in environments that already have a loop
import asyncio
import aiohttp
import async_timeout
import tkinter as tk
from tkinter import filedialog, messagebox

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


def get_destination_folder():
    """
    Show a folder selection dialog and return the chosen path.
    If the user cancels, return None.
    """
    root = tk.Tk()
    root.withdraw()  # hide the root window, we just want the dialog

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
                    print(f"Downloading {url} ->")
                    print(f"  {out_path_bin}")
                    print(f"  {out_path_grib2}")

                    # ------------------------------------------
                    # Reads into memory
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
                    # Non-200 HTTP status just in case
                    # ------------------------------------------
                    print(f"MISSING (HTTP {response.status}): {url}")
    except Exception as e:
        # ------------------------------------------
        # Catch and log errors
        # ------------------------------------------
        print(f"ERROR for {url}: {e}")


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


def show_completion_popup():
    """
    Show a simple popup that just says the script is complete.
    """
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("NDFD AirTemp Download", "Download completed.")
    root.destroy()



def main():
    # ------------------------------------------
    # This is what does the thing!!!!
    # ------------------------------------------
    dest = get_destination_folder()
    if not dest:
        return

    # ----------------------------------------------------
    # Run the asynchronous part and get list of saved files
    # -----------------------------------------------------
    saved_files = asyncio.run(main_async(dest))

    # ------------------------------------
    # Show completion popup to the user
    # ------------------------------------
    show_completion_popup()  # <-- no arguments



if __name__ == "__main__":
    main()
