'''
Created on 2 févr. 2014

@author: inso
'''

import re
import math

class Coin(object):
    '''
    A coin parsing a regex to read its value
    '''


    def __init__(self, coin_id):
        # Regex to parse the coin id
        regex = "/^([A-Z\d]{40})-(\d+)-(\d)-(\d+)-((A|F|D)-\d+))$/"
        m = re.search(regex, coin_id)
        self.issuer = m.group(0)
        self.number = int(m.group(1))
        self.base = int(m.group(2))
        self.power = int(m.group(3))
        self.origin = m.group(4)

    def value(self):
        return math.pow(self.base, self.power)

    def getId(self):
        return self.issuer + "-" \
            + str(self.number) + "-" \
            + str(self.base) + "-" \
            + str(self.power) + "-" \
            + self.origin


