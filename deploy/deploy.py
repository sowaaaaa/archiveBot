import paramiko
from pathlib import Path

HOST = "185.240.121.121"
USER = "root"
KEY = Path.home() / ".ssh" / "id_ed25519"
PROJECT = Path(__file__).parent.parent

FILES = {
    PROJECT / "bot" / "handlers" / "analysis.py": "/app/bot/handlers/analysis.py",
    PROJECT / "bot" / "handlers" / "admin.py": "/app/bot/handlers/admin.py",
    PROJECT / "bot" / "keyboards" / "inline.py": "/app/bot/keyboards/inline.py",
    PROJECT / "bot" / "states.py": "/app/bot/states.py",
    PROJECT / "bot" / "i18n.py": "/app/bot/i18n.py",
    PROJECT / "bot" / "webhook_server.py": "/app/bot/webhook_server.py",
    PROJECT / "bot" / "config.py": "/app/bot/config.py",
    PROJECT / "bot" / "database" / "db.py": "/app/bot/database/db.py",
}

CONTAINER = "archivebot-archivebot-1"


def run(client, cmd):
    _, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    if out:
        print(out.encode("ascii", errors="replace").decode())
    if err:
        print("ERR:", err.encode("ascii", errors="replace").decode())


def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password="5C5JEdp5", timeout=15)

    sftp = client.open_sftp()

    for local, remote_path in FILES.items():
        remote_tmp = f"/root/{local.name}"
        print(f"Uploading {local.name}...")
        sftp.put(str(local), remote_tmp)
        run(client, f"docker cp {remote_tmp} {CONTAINER}:{remote_path}")

    sftp.close()

    print("Restarting container...")
    run(client, f"docker restart {CONTAINER}")
    run(client, f"docker logs {CONTAINER} --tail=8")

    client.close()
    print("Deploy complete.")


if __name__ == "__main__":
    main()
