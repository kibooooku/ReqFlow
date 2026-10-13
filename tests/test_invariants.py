import sqlite3
import pytest
from app import db
from conftest import fields,created,approve

def test_stale_revision_cannot_overwrite(actors):
    req=created(actors); a=actors['analyst']; url=f"/requirements/{req['id']}"
    assert a.patch(url,fields(title='第一次修改',expected_revision=req['revision'])).status_code==200
    assert a.patch(url,fields(title='过期覆盖',expected_revision=req['revision'])).status_code==409
    assert a.get(url).json()['title']=='第一次修改'

def test_reviewed_content_cannot_be_edited(actors):
    req=created(actors); a=actors['analyst']; rid=req['id']
    assert a.post(f'/requirements/{rid}/submit',{'expected_revision':req['revision'],'reviewer_id':3}).status_code==200
    current=a.get(f'/requirements/{rid}').json()
    assert a.patch(f'/requirements/{rid}',fields(expected_revision=current['revision'])).status_code==409
    approved=approve_existing(actors,rid)
    assert a.patch(f'/requirements/{rid}',fields(expected_revision=approved['revision'])).status_code==409

def approve_existing(actors,rid):
    review=next(x for x in actors['reviewer'].get('/projects/1/reviews').json() if x['requirement_id']==rid and x['status']=='pending')
    assert actors['reviewer'].post(f"/reviews/{review['id']}/decide",{'decision':'approved'}).status_code==200
    return actors['analyst'].get(f'/requirements/{rid}').json()

def test_duplicate_decision_rejected(actors):
    a=actors['analyst']; r=actors['reviewer']; req=created(actors)
    a.post(f"/requirements/{req['id']}/submit",{'expected_revision':req['revision'],'reviewer_id':3})
    review=next(x for x in r.get('/projects/1/reviews').json() if x['requirement_id']==req['id'])
    url=f"/reviews/{review['id']}/decide"
    assert r.post(url,{'decision':'approved'}).status_code==200
    assert r.post(url,{'decision':'approved'}).status_code==409

@pytest.mark.parametrize('kind',['depends','refines'])
def test_directed_link_cycles_rejected(actors,kind):
    a=actors['analyst']; r1=created(actors); r2=created(actors); r3=created(actors)
    for src,dst in [(r1,r2),(r2,r3)]:
        r=a.post('/projects/1/links',{'source_id':src['id'],'target_id':dst['id'],'kind':kind})
        assert r.status_code==201,r.text
    r=a.post('/projects/1/links',{'source_id':r3['id'],'target_id':r1['id'],'kind':kind})
    assert r.status_code in (400,409,422)

def test_self_and_duplicate_links_rejected(actors):
    a=actors['analyst']; req=created(actors)
    assert a.post('/projects/1/links',{'source_id':req['id'],'target_id':req['id'],'kind':'depends'}).status_code in (400,409,422)
    body={'source_id':req['id'],'target_id':1,'kind':'depends'}
    assert a.post('/projects/1/links',body).status_code==201
    assert a.post('/projects/1/links',body).status_code==409

def test_parent_hierarchy_cycle_rejected(actors):
    first=created(actors); second=created(actors,parent_id=first['id'])
    response=actors['analyst'].patch(f"/requirements/{first['id']}",fields(parent_id=second['id'],expected_revision=first['revision']))
    assert response.status_code in (400,409,422)

def test_transitive_impact(actors):
    a=actors['analyst']; x=created(actors); y=created(actors); z=created(actors)
    for src,dst in [(x,y),(y,z)]:
        assert a.post('/projects/1/links',{'source_id':src['id'],'target_id':dst['id'],'kind':'depends'}).status_code==201
    affected=a.get(f"/requirements/{z['id']}/impact").json()
    assert {x['id'],y['id']}.issubset({v['id'] for v in affected['requirements']})

def test_baseline_rejects_unapproved_requirement(actors):
    req=created(actors)
    r=actors['analyst'].post('/projects/1/baselines',{'name':'非法基线','requirement_ids':[req['id']]})
    assert r.status_code in (400,409,422)

def test_historical_tables_are_immutable(actors):
    a=actors['analyst']
    r=a.post('/projects/1/baselines',{'name':'保护基线','requirement_ids':[1]})
    assert r.status_code==201,r.text
    c=db.connect(actors['db'])
    try:
        for table in ('requirement_versions','baseline_items','baseline_snapshots','baselines','audit_logs'):
            with pytest.raises(sqlite3.IntegrityError):c.execute(f'DELETE FROM {table}')
        with pytest.raises(sqlite3.IntegrityError):c.execute("UPDATE requirement_versions SET snapshot='{}'")
    finally:c.close()

def test_stale_change_rejected_atomically(actors):
    a=actors['analyst']; r=actors['reviewer']; req=approve(actors,created(actors)['id'])
    bodies=[{'expected_revision':req['revision'],'title':f'变更{i}','reason':'并发情况','proposed':fields(title=f'变更后的标题{i}')} for i in (1,2)]
    changes=[a.post(f"/requirements/{req['id']}/changes",b).json() for b in bodies]
    assert r.post(f"/changes/{changes[0]['id']}/decide",{'decision':'approved'}).status_code==200
    assert r.post(f"/changes/{changes[1]['id']}/decide",{'decision':'approved'}).status_code==409
    assert a.get(f"/requirements/{req['id']}").json()['title']=='变更后的标题1'

def test_approved_cannot_directly_archive(actors):
    req=approve(actors,created(actors)['id'])
    assert actors['analyst'].post(f"/requirements/{req['id']}/archive",{'expected_revision':req['revision']}).status_code==409

def test_design_link_is_not_test_coverage(actors):
    req=created(actors); a=actors['analyst']
    assert a.post('/projects/1/artifacts',{'kind':'design','title':'设计图','reference':'D-1','result':'not_run','requirement_ids':[req['id']]}).status_code==201
    row=next(x for x in a.get('/projects/1/trace').json() if x['id']==req['id'])
    assert row['covered'] is False

def test_foreign_document_and_owner_rejected(actors):
    a=actors['admin']; p=a.post('/projects',{'name':'隔离文档'}).json()['id']
    doc=a.post(f'/projects/{p}/documents',{'title':'其他项目文档'}).json()
    assert actors['analyst'].post('/projects/1/requirements',fields(document_id=doc['id'])).status_code in (400,403,404,422)
    user=a.post('/users',{'username':'outsider','name':'非成员','password':'OutsiderPassword!'}).json()
    assert actors['analyst'].post('/projects/1/requirements',fields(owner_id=user['id'])).status_code in (400,403,404,422)
