__version__ = "1.2.2"

import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import pandas as pd
from geopy.geocoders import OpenCage
import time
import threading
import os
import json
from datetime import datetime, timedelta
import webbrowser

stop_geocoding = False
continue_button = None
CONFIG_FILE = "geolocation_config.json"
DAILY_LIMIT = 2500

# Load or create config
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
else:
    config = {"api_key": "", "last_reset": "", "usage": 0}
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

# Reset usage if a new UTC day has started
current_date = datetime.utcnow().strftime("%Y-%m-%d")
if config.get("last_reset") != current_date:
    config["last_reset"] = current_date
    config["usage"] = 0
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

OPENCAGE_API_KEY = config.get("api_key", "")

# --- API KEY POPUP LOGIC ---
def show_api_key_popup(root, status_area, update_api_btn=None):
    popup = tk.Toplevel(root)
    popup.title("Enter OpenCage API Key")
    popup.geometry("420x140")
    popup.grab_set()
    popup.resizable(False, False)
    current_key = config.get("api_key", "")
    if current_key:
        tk.Label(popup, text="Paste your API key here (current value shown below):").pack(pady=5)
    else:
        tk.Label(popup, text="Paste your API key here:").pack(pady=5)
    api_var = tk.StringVar(value=current_key)
    api_entry = tk.Entry(popup, textvariable=api_var, width=45)
    api_entry.pack(padx=10, pady=5)
    api_entry.focus_set()

    def save_popup_key():
        key = api_var.get().strip()
        if key:
            save_api_key(key)
            popup.destroy()
            status_area.insert(tk.END, "API key saved.\n")
            status_area.see(tk.END)
            if update_api_btn is not None:
                update_api_btn.config(text="API Key", bg='gray', fg='white')
                if hasattr(root, 'api_link_widget') and root.api_link_widget:
                    root.api_link_widget.destroy()
                    root.api_link_widget = None
        else:
            status_area.insert(tk.END, "No API key entered.\n")
            status_area.see(tk.END)
    tk.Button(popup, text="Save API Key", command=save_popup_key, bg="#10b300", fg="white", height=2).pack(pady=8)
# --- END API KEY POPUP LOGIC ---

def show_about_popup():
    popup = tk.Toplevel()
    popup.title("About Geolocation Lookup Tool")
    popup.geometry("410x285")
    popup.grab_set()
    popup.resizable(False, False)
    about_txt = (
        f"Geolocation Lookup Tool\n"
        f"Version {__version__}\n\n"
        "Author: Angry Munky\n"
        "Powered by OpenCage and OpenStreetMap\n\n"
        "- This app geocodes a list of street intersections from a CSV file.\n"
        "- You must supply an OpenCage API key.\n"
        "- Usage is tracked and limited to 2,500 lookups per UTC day.\n\n"
        "GitHub: https://github.com/AngryMunky/geolocation_lookup_tool\n"
        "For more info or to obtain an API key:\nhttps://opencagedata.com/api"
    )
    tk.Label(popup, text=about_txt, justify=tk.LEFT, anchor="w").pack(padx=12, pady=10)
    def open_opencage():
        webbrowser.open_new_tab("https://opencagedata.com/api")
    link = tk.Label(popup, text="Open OpenCage API website", fg="blue", cursor="hand2")
    link.pack(pady=2)
    link.bind("<Button-1>", lambda e: open_opencage())
    # Taller button for close/exit
    tk.Button(popup, text="Close", command=popup.destroy, height=2, width=16).pack(pady=8)

def save_api_key(api_key):
    global OPENCAGE_API_KEY
    OPENCAGE_API_KEY = api_key.strip()
    config['api_key'] = OPENCAGE_API_KEY
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def increment_usage():
    config["usage"] += 1
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def hours_until_utc_reset():
    now = datetime.utcnow()
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    delta = tomorrow - now
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    return hours, minutes

def geocode_csv(input_csv, status_area, run_button, progress_bar, container):
    global stop_geocoding, continue_button, OPENCAGE_API_KEY
    stop_geocoding = False
    run_button.config(text="Cancel", bg='red', command=lambda: stop_geocode(run_button))

    if not OPENCAGE_API_KEY:
        status_area.insert(tk.END, "Missing API key. Please use the API Key button below to paste your key.\n")
        status_area.see(tk.END)
        return

    try:
        df = pd.read_csv(input_csv)
        total_entries = len(df)
        estimated_time = total_entries
        remaining = max(0, DAILY_LIMIT - config.get("usage", 0))

        status_area.insert(tk.END, f"File loaded successfully! {total_entries} addresses found.\n")
        status_area.insert(tk.END, f"Estimated completion time: {estimated_time} seconds (~{estimated_time // 60} mins).\n")
        status_area.insert(tk.END, f"API usage: {config.get('usage', 0)} used, {remaining} remaining for today.\n")
        hours, minutes = hours_until_utc_reset()
        status_area.insert(tk.END, f"API key resets in: {hours} hour(s) and {minutes} minute(s) (UTC).\n")
        status_area.see(tk.END)

        geolocator = OpenCage(api_key=OPENCAGE_API_KEY)

        def geocode_intersection(address):
            global stop_geocoding
            if stop_geocoding:
                raise Exception("Geocoding canceled by user.")
            try:
                location = geolocator.geocode(address, exactly_one=True, timeout=10)
                time.sleep(1)
                increment_usage()
                if location:
                    status_area.insert(tk.END, f"Geocoded: {address}\n")
                    status_area.see(tk.END)
                    return pd.Series([location.latitude, location.longitude])
                else:
                    status_area.insert(tk.END, f"Address not found: {address}\n")
                    status_area.see(tk.END)
                    return pd.Series([None, None])
            except Exception as e:
                status_area.insert(tk.END, f"Error geocoding '{address}': {e}\n")
                status_area.see(tk.END)
                return pd.Series([None, None])

        first_result = geocode_intersection(df.iloc[0, 1])
        if pd.isnull(first_result[0]) and pd.isnull(first_result[1]):
            status_area.insert(tk.END, "The first address could not be geocoded.\n")
            status_area.insert(tk.END, "Please fix the file or press 'Continue' to proceed with the rest.\n")
            status_area.see(tk.END)

            def continue_process():
                if continue_button:
                    continue_button.destroy()
                continue_button = None
                continue_with_geocoding(df, first_result, status_area, progress_bar, run_button)

            continue_button = tk.Button(container, text="Continue Anyway", bg='orange', command=continue_process)
            continue_button.pack(pady=5)
            return

        continue_with_geocoding(df, first_result, status_area, progress_bar, run_button)

    except Exception as e:
        status_area.insert(tk.END, f"{e}\n")
        status_area.see(tk.END)

    finally:
        run_button.config(text="RUN", bg='green', command=lambda: threading.Thread(target=geocode_csv,
                                                                                    args=(input_csv, status_area, run_button, progress_bar, container)).start())

def continue_with_geocoding(df, first_result, status_area, progress_bar, run_button):
    global continue_button
    results = [first_result]

    for i in range(1, len(df)):
        result = geocode_intersection(df.iloc[i, 1], status_area)
        results.append(result)
        progress_bar['value'] = (i + 1) / len(df) * 100
        progress_bar.update_idletasks()

    df[['Latitude', 'Longitude']] = pd.DataFrame(results)
    output_csv = file_path_var.full.replace('.csv', '-geolocation.csv')
    df.to_csv(output_csv, index=False)

    status_area.insert(tk.END, f"\nGeocoding completed! File saved as: {output_csv}\n")
    status_area.see(tk.END)

    if continue_button:
        continue_button.destroy()
        continue_button = None

def geocode_intersection(address, status_area):
    global stop_geocoding, OPENCAGE_API_KEY
    if stop_geocoding:
        raise Exception("Geocoding canceled by user.")
    try:
        geolocator = OpenCage(api_key=OPENCAGE_API_KEY)
        location = geolocator.geocode(address, exactly_one=True, timeout=10)
        time.sleep(1)
        increment_usage()
        if location:
            status_area.insert(tk.END, f"Geocoded: {address}\n")
            status_area.see(tk.END)
            return pd.Series([location.latitude, location.longitude])
        else:
            status_area.insert(tk.END, f"Address not found: {address}\n")
            status_area.see(tk.END)
            return pd.Series([None, None])
    except Exception as e:
        status_area.insert(tk.END, f"Error geocoding '{address}': {e}\n")
        status_area.see(tk.END)
        return pd.Series([None, None])

def stop_geocode(run_button):
    global stop_geocoding, continue_button
    stop_geocoding = True
    if continue_button:
        continue_button.destroy()
        continue_button = None

def create_gui():
    global file_path_var
    root = tk.Tk()
    root.title(f"Geolocation Lookup Tool v{__version__}")
    root.geometry('560x550')

    tk.Label(root, text="Select your .csv file of street intersections to geolocate:").pack(pady=5)

    file_path_var = tk.StringVar()

    def browse_file():
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        short_path = filename if len(filename) <= 40 else f"...{filename[-37:]}"
        file_path_var.set(short_path)
        file_path_var.full = filename

    file_frame = tk.Frame(root)
    file_frame.pack(pady=5)

    file_entry = tk.Entry(file_frame, textvariable=file_path_var, width=50, state='readonly')
    file_entry.pack(side=tk.LEFT, padx=5)

    browse_button = tk.Button(file_frame, text="Browse", command=browse_file)
    browse_button.pack(side=tk.LEFT)

    run_button = tk.Button(root, text="RUN", bg='green', fg='white')
    run_button.pack(pady=5)

    progress_bar = ttk.Progressbar(root, orient="horizontal", length=500, mode="determinate")
    progress_bar.pack(pady=5)

    tk.Label(root, text="Status and Information:").pack(pady=3)

    status_area = scrolledtext.ScrolledText(root, height=10, width=65)
    status_area.pack(pady=5)

    # On startup, show status with API info
    remaining = max(0, DAILY_LIMIT - config.get("usage", 0))
    hours, minutes = hours_until_utc_reset()
    if not config.get("api_key"):
        status_area.insert(tk.END, "No API key found. You need an OpenCage API key to use the geocoder.\n")
        status_area.insert(tk.END, "Use the API Key button below to paste your API key, or click the link to obtain a key from OpenCage.\n")
    status_area.insert(tk.END, f"API usage: {config.get('usage', 0)} used, {remaining} remaining for today.\n")
    status_area.insert(tk.END, f"API key resets in: {hours} hour(s) and {minutes} minute(s) (UTC).\n")
    status_area.see(tk.END)

    # --- Centered link above bottom buttons ---
    root.api_link_widget = None
    bottom_controls = tk.Frame(root)
    bottom_controls.pack(side=tk.BOTTOM, fill=tk.X, pady=12)

    if not config.get("api_key"):
        def open_opencage():
            webbrowser.open_new_tab("https://opencagedata.com/api")
        api_link = tk.Label(root, text="Click to Obtain your OpenCage API", fg="blue", cursor="hand2", font=('Segoe UI', 10, 'underline'))
        api_link.pack(side=tk.BOTTOM, pady=2)
        api_link.bind("<Button-1>", lambda e: open_opencage())
        root.api_link_widget = api_link

    # Center the buttons in bottom_controls
    btn_frame = tk.Frame(bottom_controls)
    btn_frame.pack(pady=3)
    help_btn = tk.Button(btn_frame, text="Help/About", command=show_about_popup, width=16, height=2)
    api_btn_bg = "#10b300" if not config.get("api_key") else "gray"
    api_btn_fg = "white"
    api_btn_txt = "Enter API Key" if not config.get("api_key") else "API Key"
    api_btn = tk.Button(btn_frame, text=api_btn_txt, bg=api_btn_bg, fg=api_btn_fg, width=16, height=2,
                       command=lambda: show_api_key_popup(root, status_area, update_api_btn=api_btn))
    # Center horizontally
    help_btn.grid(row=0, column=0, padx=14)
    api_btn.grid(row=0, column=1, padx=14)

    run_button.config(command=lambda: threading.Thread(target=geocode_csv,
                                                       args=(getattr(file_path_var, 'full', file_path_var.get()),
                                                             status_area, run_button, progress_bar, root)).start())

    root.mainloop()

if __name__ == "__main__":
    create_gui()
