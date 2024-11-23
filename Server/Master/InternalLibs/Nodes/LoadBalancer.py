class Balancer:
    def __init__(self, pipe):
        self.nodes = []
        self.__pipe = pipe

    def add_node(self, node):
        self.nodes.append(node)

    def remove_node(self, node):
        self.nodes.remove(node)

    def best_node(self):
        """Returns the node uid with the lower load"""
        pass

