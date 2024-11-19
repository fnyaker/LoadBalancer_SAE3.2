from LocalLibs import Backend
from LocalLibs.Backend import ControlClient
import time


def main():
    # Create a new Backend object
    backend = ControlClient(serverAddress="localhost", serverPort=12345, certfile="../certfile.pem")
    backend.requestUid()
    time.sleep(0.5)
    print(f"UID: {backend.uid}")

    while True:
        try :
            backend.ping()
            time.sleep(1)
        except KeyboardInterrupt:
            break

    backend.sayBye()

if __name__ == "__main__":
    main()