import paramiko, pathlib

pub_key = pathlib.Path.home().joinpath('.ssh', 'id_ed25519.pub').read_text().strip()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('185.240.121.121', username='root', password='5C5JEdp5', timeout=15)

cmd = f'mkdir -p ~/.ssh && echo "{pub_key}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("ERR:", err)
client.close()
print('SSH key added successfully')
