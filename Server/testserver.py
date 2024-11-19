from Server.Master.InternalLibs.Users.Users import UserControlServer

def main():
    server_ip = 'localhost'
    server_port = 12345
    certfile = '../certfile.pem'
    keyfile = '../keyfile.pem'

    # Create and start the UserControlServer
    server = UserControlServer(listener_port=server_port, listener_ip=server_ip, certfile=certfile, keyfile=keyfile)
    server.start()
    print(f"Server started on {server_ip}:{server_port}")

    try:
        while True:
            pass  # Keep the server running
    except KeyboardInterrupt:
        print("Shutting down the server...")
        server.stop()

if __name__ == "__main__":
    main()