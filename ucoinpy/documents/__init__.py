'''
Created on 3 déc. 2014

@author: inso
'''
import base58
import time
from ..key import Base58Encoder


class Document:
    def __init__(self, version):
        self.version = version

    def content(self):
        return ""

    def sign(self, key):
        return key.sign(self.content(), encoder=Base58Encoder)

    def signed(self, key):
        return "{0}\n{1}\n".format(self.content(), self.sign(key))
