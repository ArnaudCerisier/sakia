'''
Created on 1 févr. 2014

@author: inso
'''

import ucoinpy as ucoin

class Node(object):
    '''
    classdocs
    '''
    def __init__(self, server, port):
        '''
        Constructor
        '''
        self.server = server
        self.port = port


    def __eq__(self, other):
        return ( self.server == other.server and self.port == other.port )

class MainNode(Node):

    def downstreamPeers(self):
        ucoin.settings['server'] = self.server
        ucoin.settings['port'] = self.port

        peers = []
        for peer in ucoin.ucg.peering.peers.DownStream().get()['peers']:
            node = Node(peer['ipv4'], peer['port'])
            print(node.server + ":" + node.port)
            peers.append(node)
