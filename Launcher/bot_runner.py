# bot_runner.py
import subprocess

def launch_bot(bot_name, password):
    """Lance un bot via subprocess."""
    try:
        subprocess.run(
            ["python", "bot.py", bot_name, "--pasword", password],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Erreur au lancement du bot: {e}")
