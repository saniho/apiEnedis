import pytest
from custom_components.apiEnedis import sensorEnedis

def test_get_init():
    se = sensorEnedis.manageSensorState()
    assert se.getInit() == False, "not False !! "
