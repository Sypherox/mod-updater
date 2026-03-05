# ============================================================
#   Mod Updater — by Sypherox
#   © sypherox.dev — All rights reserved
# ============================================================

import os
import re
import json
import time
import hashlib
import requests
import tkinter as tk
from tkinter import filedialog, ttk
import webbrowser
from datetime import datetime
from colorama import Fore, init

init(autoreset=True)

MODRINTH_API  = "https://api.modrinth.com/v2"
REQUEST_DELAY = 0.3
MAX_RETRIES   = 3

SLUG_ALIASES = {
    "waveycapes":             "wavey-capes",
    "yet_another_config_lib": "yacl",
}

def extract_mod_slug(filename: str) -> str:
    name = os.path.splitext(filename)[0]
    name = re.sub(r'[-_](fabric|forge|neoforge|quilt|rift)([-_+].*)?$', '', name, flags=re.IGNORECASE)
    name = re.split(r'[-_+][v]?\d', name)[0]
    return name.lower().strip('-_')

def extract_mod_version(filename: str) -> str | None:
    match = re.search(r'[-_+]([0-9]+\.[0-9]+[^\s]*?)(?:[-_+](?:fabric|forge|neoforge|quilt)|\.jar)', filename, re.IGNORECASE)
    return match.group(1) if match else None

def detect_loader(filename: str) -> str | None:
    name = filename.lower()
    for loader in ("neoforge", "fabric", "forge", "quilt"):
        if loader in name:
            return loader
    return None

def get_project_by_slug(slug: str):
    url = f"{MODRINTH_API}/project/{slug}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def search_modrinth_verified(mod_slug: str, mc_version: str):
    mod_slug = SLUG_ALIASES.get(mod_slug, mod_slug)

    project = get_project_by_slug(mod_slug)
    if project:
        return project["id"], project["slug"]

    url    = f"{MODRINTH_API}/search"
    facets = json.dumps([[f"versions:{mc_version}"]])
    params = {"query": mod_slug, "facets": facets, "limit": 5}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(Fore.RED + f"Error searching Modrinth for '{mod_slug}': {e}")
        return None, None

    hits = r.json().get("hits", [])
    for hit in hits:
        hit_slug = hit.get("slug", "").lower()
        if hit_slug == mod_slug or hit_slug.startswith(mod_slug) or mod_slug in hit_slug:
            return hit["project_id"], hit_slug

    return None, None

def get_latest_version_info(project_id: str, mc_version: str, preferred_loader: str | None):
    url = f"{MODRINTH_API}/project/{project_id}/version"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print(Fore.RED + f"Failed to fetch version list: {e}")
        return None, None, None

    versions = r.json()

    versions = [v for v in versions if mc_version in v.get("game_versions", [])]

    if preferred_loader:
        loader_versions = [v for v in versions if preferred_loader in [l.lower() for l in v.get("loaders", [])]]
        if loader_versions:
            versions = loader_versions

    for v in versions:
        jar_files = [f for f in v.get("files", []) if f.get("filename", "").endswith(".jar")]
        if not jar_files:
            continue

        best = jar_files[0]
        sha1 = best.get("hashes", {}).get("sha1")
        return best["url"], best.get("filename", "mod.jar"), sha1

    return None, None, None

def verify_sha1(file_path: str, expected: str) -> bool:
    h = hashlib.sha1()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest() == expected

def download_file(url: str, dest_path: str) -> bool:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(dest_path, "wb") as out:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            out.write(chunk)
            return True
        except Exception as e:
            print(Fore.YELLOW + f"   Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(1)
    return False

def ask_version_and_loader(root) -> tuple[str | None, str | None]:
    dialog = tk.Toplevel(root)
    dialog.title("Mod Updater Settings")
    dialog.geometry("340x160")
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.lift()
    dialog.attributes('-topmost', True)
    dialog.focus_force()
    dialog.grab_set()

    frame = tk.Frame(dialog, padx=16, pady=12)
    frame.pack(fill="both", expand=True)

    tk.Label(frame, text="Minecraft version:").grid(row=0, column=0, sticky="w", pady=(0, 6))
    version_var = tk.StringVar()
    version_entry = tk.Entry(frame, textvariable=version_var, width=20)
    version_entry.grid(row=0, column=1, sticky="w", pady=(0, 6), padx=(8, 0))
    version_entry.focus_set()

    tk.Label(frame, text="Mod loader:").grid(row=1, column=0, sticky="w", pady=(0, 6))
    loader_var = tk.StringVar(value="fabric")
    loader_box = ttk.Combobox(frame, textvariable=loader_var, width=18,
                               values=["fabric", "forge", "neoforge", "quilt"],
                               state="readonly")
    loader_box.grid(row=1, column=1, sticky="w", pady=(0, 6), padx=(8, 0))

    tk.Label(frame, text="© sypherox.dev", fg="gray", font=("Arial", 7)).grid(
        row=2, column=0, columnspan=2, pady=(4, 0))

    selected = {"version": None, "loader": None}

    def confirm(event=None):
        v = version_var.get().strip()
        if v:
            selected["version"] = v
            selected["loader"]  = loader_var.get() or None
            dialog.destroy()

    def on_close():
        dialog.destroy()

    btn_frame = tk.Frame(frame)
    btn_frame.grid(row=3, column=0, columnspan=2, pady=(8, 0))
    tk.Button(btn_frame, text="Start", command=confirm, width=12).pack()

    version_entry.bind("<Return>", confirm)
    dialog.protocol("WM_DELETE_WINDOW", on_close)
    dialog.wait_window()

    return selected["version"], selected["loader"]

def write_log(log_path: str, entries: list[str], mc_version: str, loader: str, mods_folder: str, results: dict):
    timestamp  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    py_version = os.popen("python --version").read().strip()

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("  Mod Updater — © sypherox.dev\n")
        f.write("  Support: https://sypherox.dev/modupdater/\n")
        f.write("=" * 60 + "\n\n")

        f.write("[[ SYSTEM INFO ]]\n")
        f.write(f"  Date/Time:       {timestamp}\n")
        f.write(f"  Python:          {py_version}\n")
        f.write(f"  OS:              {os.name} / {os.sys.platform}\n")
        f.write(f"  Mods folder:     {mods_folder}\n\n")

        f.write("[[ RUN CONFIG ]]\n")
        f.write(f"  Minecraft:       {mc_version}\n")
        f.write(f"  Loader:          {loader or 'auto-detect'}\n\n")

        f.write("[[ RESULTS SUMMARY ]]\n")
        f.write(f"  ✅ Updated:       {len(results['ok'])}\n")
        f.write(f"  ⏭️  Skipped:       {len(results['skipped'])}\n")
        f.write(f"  ⚠️  No version:    {len(results['no_version'])}\n")
        f.write(f"  ❌ Not found:     {len(results['not_found'])}\n")
        f.write(f"  💥 Errors:        {len(results['error'])}\n\n")

        f.write("[[ DETAILED LOG ]]\n")
        for line in entries:
            f.write(f"  {line}\n")

        if results["not_found"] or results["no_version"] or results["error"]:
            f.write("\n[[ ACTION REQUIRED ]]\n")
            f.write("  The following mods could not be updated automatically.\n")
            f.write("  Please update them manually or report this log to us:\n")
            f.write("  https://sypherox.dev/modupdater/\n\n")
            for m in results["not_found"]:
                f.write(f"  [NOT FOUND]  {m}\n")
            for m in results["no_version"]:
                f.write(f"  [NO VERSION] {m}\n")
            for m in results["error"]:
                f.write(f"  [ERROR]      {m}\n")

        f.write("\n" + "=" * 60 + "\n")
        f.write("  If you need help, join our Discord and send this file:\n")
        f.write("  https://sypherox.dev/modupdater/\n")
        f.write("=" * 60 + "\n")

def main():
    os.system("title Mod Updater  ^|  sypherox.dev")

    print(Fore.LIGHTBLACK_EX + "=" * 50)
    print(Fore.WHITE         + "   Mod Updater  —  © sypherox.dev")
    print(Fore.LIGHTBLACK_EX + "=" * 50 + "\n")

    root = tk.Tk()
    root.geometry("0x0+0+0")
    root.overrideredirect(True)
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

    print(Fore.CYAN + f"Found {len(mods)} mod(s):")
    for m in mods:
        print(Fore.CYAN + f"  • {m}")

    mc_version, chosen_loader = ask_version_and_loader(root)
    root.destroy()

    if not mc_version:
        print(Fore.RED + "❌ No Minecraft version provided – exiting.")
        return

    print(Fore.LIGHTCYAN_EX + f"\n🔹 Target: Minecraft {mc_version}  |  Loader: {chosen_loader or 'auto-detect'}\n")

    output_folder = os.path.join(mods_folder, "updated_mods")
    if os.path.exists(output_folder):
        for old_file in os.listdir(output_folder):
            if old_file.endswith(".jar"):
                os.remove(os.path.join(output_folder, old_file))
        print(Fore.LIGHTBLACK_EX + "🗑️  Cleared previous updated_mods folder.\n")
    os.makedirs(output_folder, exist_ok=True)

    results   = {"ok": [], "skipped": [], "no_version": [], "not_found": [], "error": []}
    log_lines = []

    for mod_file in mods:
        try:
            mod_slug = extract_mod_slug(mod_file)
            print(Fore.CYAN + f"\n🔍 {mod_file}  →  Slug: '{mod_slug}'")

            project_id, found_slug = search_modrinth_verified(mod_slug, mc_version)
            time.sleep(REQUEST_DELAY)

            if not project_id:
                print(Fore.RED + "❌ No matching project found on Modrinth.")
                results["not_found"].append(mod_file)
                log_lines.append(f"[NOT FOUND]  {mod_file}")
                continue

            print(Fore.CYAN + f"   Project matched: {found_slug}")

            loader = chosen_loader or detect_loader(mod_file)

            file_url, file_name, sha1 = get_latest_version_info(project_id, mc_version, loader)
            time.sleep(REQUEST_DELAY)

            if not file_url:
                print(Fore.YELLOW + f"⚠️ No version available for {mc_version}.")
                results["no_version"].append(mod_file)
                log_lines.append(f"[NO VERSION] {mod_file}")
                continue

            existing_version = extract_mod_version(mod_file)
            new_version      = extract_mod_version(file_name)
            if existing_version and new_version and existing_version == new_version:
                print(Fore.LIGHTBLACK_EX + f"   ⏭️  Already up to date ({existing_version}) – skipping.")
                results["skipped"].append(mod_file)
                log_lines.append(f"[SKIPPED]    {mod_file}  →  already {existing_version}")
                continue

            print(Fore.YELLOW + f"   Downloading {Fore.RED}{found_slug} {Fore.YELLOW}→ {Fore.GREEN}{file_name}")
            file_path = os.path.join(output_folder, file_name)

            if not download_file(file_url, file_path):
                print(Fore.RED + f"❌ Download failed after {MAX_RETRIES} attempts.")
                results["error"].append(mod_file)
                log_lines.append(f"[ERROR]      {mod_file}  →  download failed")
                continue

            if sha1:
                if verify_sha1(file_path, sha1):
                    print(Fore.LIGHTBLACK_EX + "   ✔ Checksum verified.")
                else:
                    print(Fore.RED + "   ⚠️ Checksum mismatch! File may be corrupted.")
                    log_lines.append(f"[CHECKSUM]   {file_name}  →  SHA1 mismatch!")

            print(Fore.GREEN + "✅ Successfully updated!")
            results["ok"].append(mod_file)
            log_lines.append(f"[OK]         {mod_file}  →  {file_name}")

        except Exception as e:
            print(Fore.RED + f"❌ Error processing {mod_file}: {e}")
            results["error"].append(mod_file)
            log_lines.append(f"[ERROR]      {mod_file}  →  {e}")

    print(Fore.LIGHTBLACK_EX + f"\n{'=' * 50}")
    print(Fore.GREEN          + f"✅ Updated:           {len(results['ok'])}")
    print(Fore.LIGHTBLACK_EX  + f"⏭️  Skipped (latest):  {len(results['skipped'])}")
    print(Fore.YELLOW         + f"⚠️  No version found:  {len(results['no_version'])}")
    print(Fore.RED            + f"❌ Not found:         {len(results['not_found'])}")
    if results["error"]:
        print(Fore.RED        + f"💥 Errors:            {len(results['error'])}")

    unresolved = results["not_found"] + results["no_version"]
    if unresolved:
        print(Fore.YELLOW + "\n📋 Mods to update manually:")
        for m in unresolved:
            print(Fore.YELLOW + f"   • {m}")

    print(Fore.LIGHTBLACK_EX + f"{'=' * 50}\n")

    log_lines += [
        "",
        f"Updated:        {len(results['ok'])}",
        f"Skipped:        {len(results['skipped'])}",
        f"No version:     {len(results['no_version'])}",
        f"Not found:      {len(results['not_found'])}",
        f"Errors:         {len(results['error'])}",
    ]
    write_log(
        os.path.join(output_folder, "update_log.txt"),
        log_lines,
        mc_version,
        chosen_loader,
        mods_folder,
        results
    )
    print(Fore.LIGHTBLACK_EX + "📄 Log saved to updated_mods/update_log.txt")

    webbrowser.open(output_folder)
    time.sleep(0.5)
    webbrowser.open("https://sypherox.dev/modupdater/")

    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
