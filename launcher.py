import json
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path

def get_base_dir():
    if getattr(sys, "frozen", False):
        # Saat dibundle PyInstaller, __file__ resolve ke folder temp
        # ekstraksi (_MEIPASS), bukan ke lokasi exe di disk. Folder
        # tmu-v2-standard/ dan tmu-v2-smart/ harus dicari relatif ke
        # lokasi exe-nya sendiri.
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

BASE_DIR = get_base_dir()
CONFIG_PATH = BASE_DIR / "launcher_config.json"

PROGRAM_FOLDERS = {
    "standard": "tmu-v2-standard",
    "smart": "tmu-v2-smart",
}

def prompt_first_time_setup():
    result = {"type": None}

    def choose(t):
        result["type"] = t
        root.destroy()

    root = tk.Tk()
    root.title("Setup TMU - Pilih Tipe")
    root.geometry("320x150")
    root.resizable(False, False)

    tk.Label(root, text="File config belum ada.\nSite ini pakai tipe TMU apa?",
             font=("Arial", 11), justify="center").pack(pady=20)

    btn_frame = tk.Frame(root)
    btn_frame.pack()
    tk.Button(btn_frame, text="Standard", width=12,
              command=lambda: choose("standard")).pack(side="left", padx=10)
    tk.Button(btn_frame, text="Smart", width=12,
              command=lambda: choose("smart")).pack(side="left", padx=10)

    root.mainloop()

    if result["type"] is None:
        print("Dibatalkan oleh user - tidak ada tipe yang dipilih.")
        sys.exit(1)
    return result["type"]


def save_config(tmu_type):
    with open(CONFIG_PATH, "w") as f:
        json.dump({"type": tmu_type}, f, indent=2)
    print(f"Tersimpan ke {CONFIG_PATH}: type={tmu_type}")


def load_config():
    if not CONFIG_PATH.exists():
        tmu_type = prompt_first_time_setup()
        save_config(tmu_type)
        return tmu_type

    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: {CONFIG_PATH} bukan JSON yang valid ({e})")
        sys.exit(1)

    tmu_type = config.get("type")
    if tmu_type not in PROGRAM_FOLDERS:
        print(
            f"Error: 'type' di {CONFIG_PATH} harus 'standard' atau 'smart', "
            f"ditemukan: {tmu_type!r}"
        )
        sys.exit(1)

    return tmu_type


def ensure_smart_config(program_dir):
    config_path = program_dir / "smart_config.json"
    if config_path.exists():
        return

    result = {"submitted": False}

    root = tk.Tk()
    root.title("Setup TMU Smart")
    root.geometry("340x240")
    root.resizable(False, False)

    tk.Label(root, text="smart_config.json belum ada.\nAtur flag untuk site ini:",
             font=("Arial", 11), justify="center").pack(pady=15)

    dry_type_var = tk.BooleanVar(value=False)
    oltc_var = tk.BooleanVar(value=False)
    pressure_var = tk.BooleanVar(value=False)
    gas_var = tk.BooleanVar(value=False)

    tk.Checkbutton(root, text="Aktifkan DryType", variable=dry_type_var).pack(anchor="w", padx=25)
    tk.Checkbutton(root, text="Aktifkan OLTC", variable=oltc_var).pack(anchor="w", padx=25)
    tk.Checkbutton(root, text="Aktifkan Pressure Sensing", variable=pressure_var).pack(anchor="w", padx=25)
    tk.Checkbutton(root, text="Aktifkan Gas Sensing", variable=gas_var).pack(anchor="w", padx=25)

    def submit():
        result["submitted"] = True
        result["dry_type"] = dry_type_var.get()
        result["oltc"] = oltc_var.get()
        result["pressure"] = pressure_var.get()
        result["gas"] = gas_var.get()
        root.destroy()

    tk.Button(root, text="Simpan", width=12, command=submit).pack(pady=20)

    root.mainloop()

    if not result["submitted"]:
        print("Dibatalkan oleh user - smart_config.json tidak dibuat.")
        sys.exit(1)

    config = {
        "dryTypeStat": result["dry_type"],
        "OLTCstat": result["oltc"],
        "pressureStat": result["pressure"],
        "gasStat": result["gas"],
    }
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Tersimpan ke {config_path}")


def main():
    tmu_type = load_config()
    program_dir = BASE_DIR / PROGRAM_FOLDERS[tmu_type]
    main_script = program_dir / "main.py"

    if not main_script.exists():
        print(f"Error: {main_script} tidak ditemukan")
        sys.exit(1)

    if tmu_type == "smart":
        ensure_smart_config(program_dir)

    print(f"Menjalankan TMU tipe '{tmu_type}' dari {main_script}")

    if getattr(sys, "frozen", False):
        # sys.executable saat frozen menunjuk ke exe launcher itu sendiri,
        # bukan python3 - standard/smart tetap harus dijalankan sebagai
        # script Python biasa, jadi panggil python3 secara eksplisit.
        python_cmd = "python3"

        # Bootloader PyInstaller mengubah LD_LIBRARY_PATH/LD_PRELOAD agar
        # proses ini pakai library yang di-bundle. Nilai asli (sebelum
        # diubah bootloader) disimpan di *_ORIG oleh PyInstaller sendiri -
        # kembalikan itu supaya python3 anak tidak ikut memakai library
        # bundle-an launcher.
        child_env = os.environ.copy()
        for var in ("LD_LIBRARY_PATH", "LD_PRELOAD"):
            orig_var = var + "_ORIG"
            if orig_var in child_env:
                child_env[var] = child_env[orig_var]
            else:
                child_env.pop(var, None)
    else:
        python_cmd = sys.executable
        child_env = None

    # cwd diarahkan ke folder program aslinya, karena program itu kemungkinan
    # pakai path relatif untuk file/config-nya sendiri
    #
    # start_new_session=True: melepaskan child ke session/process group-nya
    # sendiri, supaya begitu launcher (dan bootloader PyInstaller-nya) exit,
    # child (main.py) tidak ikut mati karena masih satu process group dengan
    # launcher.
    subprocess.Popen(
        [python_cmd, str(main_script)],
        cwd=str(program_dir),
        env=child_env,
        start_new_session=True,
    )

    # Tidak menunggu/mengawasi proses ini - start sekali lalu launcher selesai
    print("Program berhasil di-spawn. Launcher selesai.")


if __name__ == "__main__":
    main()