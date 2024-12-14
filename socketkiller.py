import sys
import os

# Ajouter le répertoire parent au sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def force_free_socket(port):
    # Trouver les connexions utilisant le port
    result = os.popen(f"ss -tuln | grep :{port}").read()
    # Extraire les PIDs
    pids = [line.split()[4].split(':')[0] for line in result.splitlines()]
    # Tuer les connexions
    for pid in pids:
        print(f"Killing process {pid}")
        os.system(f"kill -9 {pid}")

# Exemple d'utilisation
force_free_socket(12345)
force_free_socket(12346)
force_free_socket(22345)
force_free_socket(22346)