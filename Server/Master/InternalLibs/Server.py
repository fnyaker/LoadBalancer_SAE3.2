import ssl
import time
from threading import Thread
from socket import socket, AF_INET, SOCK_STREAM

class Client: # this class will be the object passed to the callback function
    def __init__(self, addr, client=None, ssl_client=None):
        self.__addr = addr

        if client:
            self.__client = client
            self.__use_ssl = False
        elif ssl_client:
            self.__client = ssl_client
            self.__use_ssl = True
        else:
            raise ValueError("No client provided")

    def send(self, data):
        if self.__use_ssl:
            self.__client.setblocking(True)
            #print("Blocking to Send")
            self.__client.write(data)
            #print("Unblocking")
            self.__client.setblocking(False)
        else:
            self.__client.send(data)

    def get_last_message(self, size=2048):
        if self.__use_ssl:
            try :
                data = self.__client.recv(size)
            except :
                # print("SSLWantReadError Caught")
                self.__client.setblocking(True)
                # print("Blocking")
                time.sleep(0.1)
                try: # not very clean but it works :)
                    data = self.__client.recv(size)
                except : # it okay, d'ont worry, everyone can fail its human
                    # print("Still Blocking")
                    data = None
                # print("Unblocking")
                self.__client.setblocking(False)
        else:
            data = self.__client.recv(size)
        return data if data else None


    def close(self):
        self.__client.close()

    @property
    def addr(self):
        return self.__addr


class Server:
    """The base class for other server classes
    Calls the callback function when a new client is connected, callback must be non-blocking
    Callback function must have two arguments: clientObject"""
    def __init__(self, listener_port, listener_ip, callback, use_ssl=False, certfile=None, keyfile=None):
        self.__listener_port = listener_port
        self.__listener_ip = listener_ip
        self.__listener = socket(AF_INET, SOCK_STREAM)
        self.__listener.bind((self.__listener_ip, self.__listener_port))
        self.__running = True

        self.__callback = callback
        self.__use_ssl = use_ssl

        if self.__use_ssl:
            # Create SSL context
            print("Using SSL")
            print(certfile)
            print(keyfile)
            self.__ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.__ssl_context.load_cert_chain(certfile=certfile, keyfile=keyfile)

    def __listen(self):
        while self.__running:
            client, addr = self.__listener.accept()
            client.setblocking(False)
            if self.__use_ssl:
                # Wrap the client socket with SSL
                client = self.__ssl_context.wrap_socket(client, server_side=True, do_handshake_on_connect=False)
                clientObject = Client(addr, ssl_client=client)
            else:
                clientObject = Client(addr, client=client)
            self.__callback(clientObject)


    def start(self):
        self.__listener.listen(5)
        self.__listener_thread = Thread(target=self.__listen)
        self.__listener_thread.start()

    def stop(self):
        self.__running = False
        self.__listener.setblocking(False)
        self.__listener.close()
        print("Server stopping")
        self.__listener_thread.join()

