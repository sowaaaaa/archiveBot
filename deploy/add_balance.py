import paramiko

HOST = "185.240.121.121"
USER = "root"
PASSWORD = "5C5JEdp5"
CONTAINER = "archivebot-archivebot-1"

TELEGRAM_ID = 800730615
AMOUNT = 100000  # центы EUR = 1000 EUR

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD, timeout=15)

cmd = (
    f'docker exec {CONTAINER} python -c "'
    f"import asyncio, sys; sys.path.insert(0, '/app'); "
    f"from bot.database.db import add_balance, get_balance; "
    f"asyncio.run(add_balance({TELEGRAM_ID}, {AMOUNT})); "
    f"bal = asyncio.run(get_balance({TELEGRAM_ID})); "
    f"print(f'Balance: {{bal}} cents = {{bal/100:.2f}} EUR')"
    f'"'
)

_, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode("utf-8", errors="replace").strip())
err = stderr.read().decode("utf-8", errors="replace").strip()
if err:
    print("ERR:", err)

client.close()
