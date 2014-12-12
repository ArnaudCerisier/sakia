'''
Created on 2 déc. 2014

@author: inso
'''
import re

from . import Document


class SelfCertification(Document):
    '''
    A document discribing a self certification.
    '''

    re_inline = re.compile("([1-9A-Za-z][^OIl]{43,45}):([A-Za-z0-9+/]+):([0-9]+):([^\n]+)\n")

    def __init__(self, version, currency, pubkey, ts, identifier, signature):
        super(version, currency, [signature])
        self.pubkey = pubkey
        self.timestamp = ts
        self.identifier = identifier

    @classmethod
    def from_inline(cls, version, inline):
        selfcert_data = SelfCertification.re_inline.match(inline)
        pubkey = selfcert_data.group(1)
        signature = selfcert_data.group(2)
        ts = selfcert_data.group(3)
        identifier = selfcert_data.group(4)
        return cls(version, pubkey, ts, identifier, signature)

    @classmethod
    def from_raw(cls, raw):
        #TODO : Parsing
        return cls()

    def ts(self):
        return "META:TS:{0}".format(self.timestamp)

    def uid(self):
        return "UID:{0}".format(self.identifier)

    def raw(self):
        return "{0}\n{1}\n{2}".format(self.uid(), self.ts(), self.signatures[0])


class Certification(Document):
    '''
    A document describing a certification.
    '''

    re_inline = re.compile("([1-9A-Za-z][^OIl]{43,45}):\
    ([A-Za-z0-9+/]+)(==)?:([0-9]+):([0-9a-fA-F]{5,40}):\
    ([0-9]+):([^\n]+)\n")

    def __init__(self, version, currency, pubkey_from, pubkey_to,
                 blockhash, blocknumber, signature):
        '''
        Constructor
        '''
        super(version, currency, signature)
        self.pubkey_from = pubkey_from
        self.pubkey_to = pubkey_to
        self.blockhash = blockhash
        self.blocknumber = blocknumber

    @classmethod
    def from_inline(cls, version, blockhash, inline):
        cert_data = Certification.re_inline.match(inline)
        pubkey_from = cert_data.group(1)
        pubkey_to = cert_data.group(2)
        blocknumber = cert_data.group(3)
        signature = cert_data.group(4)
        return cls(version, pubkey_from, pubkey_to,
                   blockhash, blocknumber, signature)

    def ts(self):
        return "META:TS:{0}-{1}".format(self.blockhash, self.blocknumber)

    def raw(self, selfcert):
        return "{0}\n{1}\n{2}".format(selfcert.raw(), self.ts(), self.signatures[0])
