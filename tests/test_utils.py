# tests/test_utils.py

from core import utils

def test_generate_uuid():
    uid = utils.generate_uuid()
    assert isinstance(uid, str)
    assert len(uid) == 36
    assert uid.count("-") == 4

def test_timestamp_now():
    ts = utils.timestamp_now()
    assert isinstance(ts, str)
    assert "T" in ts
    assert ts.endswith("Z") or "+" in ts
