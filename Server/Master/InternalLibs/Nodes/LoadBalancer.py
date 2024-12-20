import sys
import os

# Ajouter le répertoire parent au sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class Balancer:
    def __init__(self):
        self.nodes = {}

    def add_node(self, node):
        self.nodes[node.uid] = node

    def remove_node(self, node):
        del self.nodes[node.uid]

    def sortnodes(self): # return a list of nodes uid sorted by load
        list = []
        for node in self.nodes:
            list.append(node)
        # we sort them with their cpu and ram load : {"cpu": cpu, "mem": mem}
        list.sort(key=lambda x: self.nodes[x][0].load["cpu"] + self.nodes[x][0].load["mem"]*2)


        return list


    def choose_node(self, required_packages):
        nodes = self.sortnodes()
        possibles = []

        # if the first and second have a very close load, we choose a random one

        for node in nodes:
            if self.nodes[node][0].has_packages(required_packages):
                usercnt = self.nodes[node][0].user_count()
                if usercnt["count"] < usercnt["absolute_max"]:
                    possibles.append((self.nodes[node],usercnt))
                else:
                    print("Node", node, "is full, it has", usercnt["count"], "users", "max is", usercnt["absolute_max"])

        if len(possibles) == 0:
            return None
        else:
            for node in possibles:
                if node[1]["count"] < node[1]["max"]:
                    return node[0]

            # at this point, we choose the one with the lowest load
            return possibles[0][0]
        # return nodes[0] # TO BE CHANGED


