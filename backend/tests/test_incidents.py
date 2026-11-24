from types import SimpleNamespace
from datetime import datetime, timedelta
from backend.app.services.analysis import duplicate_candidates

def item(**changes):
    return SimpleNamespace(**({'id':'one','title':'Water pipe issue','text':'Water pipe broken near school','area':'Mirpur','latitude':23.8,'longitude':90.36,'occurred_at':datetime(2026,1,1),'status':'Submitted'}|changes))

def test_different_places_are_excluded():
    assert duplicate_candidates(item(),[item(id='two',latitude=23.9)]) == []

def test_same_text_nearby_requires_review():
    result=duplicate_candidates(item(),[item(id='two',latitude=23.8001)])
    assert len(result)==1 and result[0]['requires_review']

def test_old_or_resolved_incidents_are_excluded():
    assert duplicate_candidates(item(),[item(id='two',occurred_at=datetime(2026,1,10)),item(id='three',status='Resolved')]) == []

def test_missing_location_different_areas_are_excluded():
    assert duplicate_candidates(item(latitude=None,longitude=None),[item(id='two',area='Dhanmondi')]) == []
