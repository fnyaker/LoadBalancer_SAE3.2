from LocalLibs import Backend
from LocalLibs.Backend import ControlClient
import time

examplecode = """
print("Hello World")
"""

def main():
    # Create a new Backend object
    backend = ControlClient(serverAddress="localhost", serverPort=12345, certfile="../certfile.pem")
    backend.requestUid()
    time.sleep(0.5)
    print(f"UID: {backend.uid}")
    print("Requesting a node with python installed")
    backend.runCode(examplecode)

    time.sleep(0.5)

    #backend.sayBye()

if __name__ == "__main__":
    main()