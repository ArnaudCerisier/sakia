'''
Created on 12 déc. 2014

@author: inso
'''
import pytest
from ucoinpy.documents.transaction import Transaction
from mock import Mock

inline_membership = ""

class Test_Membership:
    def test_frominline(self):
        membership = Membership.from_inline(inline_membership)

        