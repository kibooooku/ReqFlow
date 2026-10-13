"""Regression cases derived from review of the actual first implementation."""
from conftest import fields,created,approve
from app import db, service

def test_selected_baseline_has_no_false_added_requirements(actors):
    a=actors['analyst']
    baseline=a.post('/projects/1/baselines',{'name':'仅一条需求的基线','requirement_ids':[1]}).json()
    result=a.get(f"/baselines/{baseline['id']}/compare").json()
    assert len(result['rows'])==1
    assert result['rows'][0]['change']=='unchanged'

def test_project_baseline_detects_later_approved_requirement(actors):
    a=actors['analyst']
    baseline=a.post('/projects/1/baselines',{'name':'全项目基线','requirement_ids':[]}).json()
    req=approve(actors,created(actors)['id'])
    rows=a.get(f"/baselines/{baseline['id']}/compare").json()['rows']
    assert next(x for x in rows if x['requirement_id']==req['id'])['change']=='added'

def test_artifact_concurrent_edit_rejected(actors):
    a=actors['analyst']
    item=a.get('/projects/1/artifacts').json()[0]
    original={k:item[k] for k in ('kind','title','reference','result','requirement_ids')}
    url=f"/artifacts/{item['id']}"
    revision=item.get('revision',1)
    first=a.patch(url,{**original,'title':'成员A已修改','expected_revision':revision})
    assert first.status_code==200,first.text
    second=a.patch(url,{**original,'title':'成员B过期覆盖','expected_revision':revision})
    assert second.status_code==409,second.text
    assert next(x for x in a.get('/projects/1/artifacts').json() if x['id']==item['id'])['title']=='成员A已修改'

def test_dashboard_one_snapshot_during_concurrent_write(actors,monkeypatch):
    original=service.list_requirements
    called=False
    def interleaved(c,u,p,filters):
        nonlocal called
        rows=original(c,u,p,filters)
        if not called:
            called=True
            other=db.connect(actors['db'])
            try:
                service.create_requirement(other,{'id':2},1,fields(title='读取中新增需求'))
            finally:other.close()
        return rows
    monkeypatch.setattr(service,'list_requirements',interleaved)
    result=actors['analyst'].get('/projects/1/dashboard')
    assert result.status_code==200,result.text
    data=result.json()
    assert data['counts']['total']-data['counts']['archived']==data['coverage']['total']
