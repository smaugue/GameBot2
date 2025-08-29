# updater_runner.py
import subprocess
import os
import sys

def run_updater(force=False):
    """Lance l'updater et redémarre le launcher après update."""
    args = ["python", "updater.py"]
    if force:
        args.append("--force")
    try:
        subprocess.run(args, check=True)
        restart_launcher()
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Erreur lors de l'update: {e}")

def restart_launcher():
    """Redémarre le launcher proprement."""
    print("[INFO] Redémarrage du launcher...")
    os.execv(sys.executable, ["python"] + sys.argv)
