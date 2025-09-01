import os
import json
import requests
import tkinter as tk
from tkinter import filedialog
import webbrowser
from colorama import Fore, init

init(autoreset=True)

MODRINTH_API = "https://api.modrinth.com/v2"

def select_mod_folder(root) -> str:
    """Let the user select their mods folder (using the given hidden root)."""
    folder = filedialog.askdirectory(parent=root, title="Select your Minecraft mods folder")
    return folder


def ask_mc_version(root) -> str | None:
    dialog = tk.Toplevel(root)
    dialog.title("Select Minecraft Version")
    dialog.geometry("320x120")
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.grab_set()

    tk.Label(dialog, text="Enter the desired version:").pack(pady=(10, 4))

    version_var = tk.StringVar()
    entry = tk.Entry(dialog, textvariable=version_var)
    entry.pack(pady=4)
    entry.focus_set()

    selected = {"version": None}

    def confirm(event=None):
        v = version_var.get().strip()
        if v:
            selected["version"] = v
            dialog.destroy()

    def on_close():
        selected["version"] = None
        dialog.destroy()

    tk.Button(dialog, text="OK", command=confirm).pack(pady=(6, 10))
    entry.bind("<Return>", confirm)
    dialog.protocol("WM_DELETE_WINDOW", on_close)

    dialog.wait_window()  
    return selected["version"]

def search_modrinth(mod_name: str, mc_version: str):
    """Search for a mod on Modrinth filtered by game version."""
    url = f"{MODRINTH_API}/search"
    facets = json.dumps([[f"versions:{mc_version}"]])
    params = {"query": mod_name, "facets": facets}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(Fore.RED + f"Error while querying Modrinth API for {mod_name}: {e}")
        return None

    data = r.json()
    return data.get("hits", [None])[0]


def download_mod(project_id: str, mod_name: str, mc_version: str, output_folder: str) -> bool:
    """Download the latest *.jar file of a project that supports mc_version."""
    url = f"{MODRINTH_API}/project/{project_id}/version"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print(Fore.RED + f"Failed to fetch versions for {mod_name}: {e}")
        return False

    versions = r.json()
    for v in versions:
        if mc_version in v.get("game_versions", []):
            jar_files = [f for f in v.get("files", []) if f.get("filename", "").endswith(".jar")]
            if not jar_files:
                continue

            file_url = jar_files[0].get("url")
            file_name = jar_files[0].get("filename", f"{mod_name}.jar")

            print(Fore.YELLOW + f"Downloading {Fore.RED}{mod_name} {Fore.YELLOW}→ {Fore.GREEN}{file_name}")
            file_path = os.path.join(output_folder, file_name)

            try:
                with requests.get(file_url, stream=True, timeout=60) as f:
                    f.raise_for_status()
                    with open(file_path, "wb") as out_file:
                        for chunk in f.iter_content(chunk_size=8192):
                            if chunk:
                                out_file.write(chunk)
                return True
            except Exception as e:
                print(Fore.RED + f"Download failed for {mod_name}: {e}")
                return False
    return False

def main():
    os.system("title Mod Updater by Sypherox")

    root = tk.Tk()
    # root.withdraw()  # die wichse macht nur errors, sollte auch so gehen
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(lambda: root.attributes('-topmost', False))

    mods_folder = filedialog.askdirectory(parent=root, title="Select your Minecraft mods folder")
    if not mods_folder:
        print(Fore.RED + "❌ No mods folder selected – exiting.")
        root.destroy()
        return

    mods = [f for f in os.listdir(mods_folder) if f.endswith(".jar")]
    if not mods:
        print(Fore.YELLOW + "⚠️ No .jar mods found in the selected folder.")
        root.destroy()
        return
    else:
        print(Fore.CYAN + f"Found {len(mods)} mods: {mods}")

    mc_version = ask_mc_version(root)
    if not mc_version:
        print(Fore.RED + "❌ No Minecraft version provided – exiting.")
        root.destroy()
        return

    root.destroy()

    print(Fore.LIGHTCYAN_EX + f"\n🔹 Searching Mods for version: {mc_version}\n")

    output_folder = os.path.join(mods_folder, "updated_mods")
    os.makedirs(output_folder, exist_ok=True)

    for mod_file in mods:
        try:
            mod_name = os.path.splitext(mod_file)[0]
            print(Fore.CYAN + f"\n🔍 Checking for update: {mod_name}")

            result = search_modrinth(mod_name, mc_version)
            if result and result.get("project_id"):
                project_id = result["project_id"]
                if download_mod(project_id, mod_name, mc_version, output_folder):
                    print(Fore.GREEN + f"✅ {mod_name} updated successfully!")
                else:
                    print(Fore.YELLOW + f"⚠️ No version available for {mc_version}")
            else:
                print(Fore.RED + f"❌ No match found on Modrinth for {mod_name}")
        except Exception as e:
            print(Fore.RED + f"❌ Error processing {mod_file}: {e}")

    webbrowser.open(output_folder)

    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
