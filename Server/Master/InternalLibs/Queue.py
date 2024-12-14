from multiprocessing import Queue

class BidirectionalQueue:
    def __init__(self):
        self.queue_to_server = Queue()
        self.queue_to_client = Queue()

    def send_to_server(self, data):
        self.queue_to_server.put(data)

    def recv_from_server(self):
        return self.queue_to_client.get()

    def poll_from_server(self, timeout=0):
        return not self.queue_to_client.empty()

    def send_to_client(self, data):
        self.queue_to_client.put(data)

    def recv_from_client(self):
        return self.queue_to_server.get()

    def poll_from_client(self, timeout=0):
        return not self.queue_to_server.empty()