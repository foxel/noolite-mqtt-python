#!/usr/bin/python3
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# this is a dummy test showing that code compiles
def test_compile():
    from noolite_mqtt import NooLiteMQTT

    assert NooLiteMQTT is not None
