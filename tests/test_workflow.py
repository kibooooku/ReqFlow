from conftest import fields,created,approve

def test_complete_requirement_baseline_change_workflow(actors):
    a,r=actors['analyst'],actors['reviewer']
    req=created(actors,title='预约取消时间')
    rid=req['id']
    artifact=a.post('/projects/1/artifacts',{'kind':'test','title':'30分钟边界','reference':'TC-DEMO','result':'not_run','requirement_ids':[rid]})
    assert artifact.status_code==201,artifact.text
    approved=approve(actors,rid)
    baseline=a.post('/projects/1/baselines',{'name':'测试基线','requirement_ids':[rid]})
    assert baseline.status_code==201,baseline.text
    bid=baseline.json()['id']
    before=a.get(f'/baselines/{bid}').json()
    change=a.post(f'/requirements/{rid}/changes',{'expected_revision':approved['revision'],'title':'改为60分钟','reason':'实验室调度需要','proposed':fields(title='预约取消时间',statement='应提前60分钟取消预约。')})
    assert change.status_code==201,change.text
    impact=a.get(f'/requirements/{rid}/impact').json()
    assert any(x['id']==artifact.json()['id'] for x in impact['artifacts'])
    decision=r.post(f"/changes/{change.json()['id']}/decide",{'decision':'approved','comment':'确认业务变更'})
    assert decision.status_code==200,decision.text
    after=a.get(f'/requirements/{rid}').json()
    assert after['statement']=='应提前60分钟取消预约。'
    assert after['revision']>approved['revision'] and after['status']=='approved'
    assert a.get(f'/baselines/{bid}').json()==before
    compare=a.get(f'/baselines/{bid}/compare').json()
    assert next(x for x in compare['rows'] if x['requirement_id']==rid)['change']=='modified'
    assert len(after['versions'])>=3
    assert any(x['entity_type'] in ('change','requirement') for x in a.get('/projects/1/audit').json())

def test_draft_edit_and_search(actors):
    req=created(actors,title='唯一检索样本')
    a=actors['analyst']
    r=a.patch(f"/requirements/{req['id']}",fields(title='唯一检索样本二',expected_revision=req['revision']))
    assert r.status_code==200,r.text
    found=a.get('/projects/1/requirements?q=唯一检索样本二&status=draft&type=functional&priority=must').json()
    assert len(found)==1 and found[0]['revision']>req['revision']

def test_review_rejection_allows_revision(actors):
    req=created(actors); a=actors['analyst']; r=actors['reviewer']
    assert a.post(f"/requirements/{req['id']}/submit",{'expected_revision':req['revision'],'reviewer_id':3}).status_code==200
    review=next(x for x in r.get('/projects/1/reviews').json() if x['requirement_id']==req['id'])
    assert r.post(f"/reviews/{review['id']}/decide",{'decision':'rejected','comment':'补充验收边界'}).status_code==200
    current=a.get(f"/requirements/{req['id']}").json()
    assert current['status']=='draft'
    assert a.patch(f"/requirements/{req['id']}",fields(expected_revision=current['revision'])).status_code==200

def test_artifact_update_and_trace_coverage(actors):
    req=created(actors); a=actors['analyst']
    artifact=a.post('/projects/1/artifacts',{'kind':'test','title':'测试用例','reference':'TC-X','result':'not_run','requirement_ids':[req['id']]}).json()
    changed=a.patch(f"/artifacts/{artifact['id']}",{'kind':'test','title':'测试用例','reference':'TC-X','result':'passed','requirement_ids':[req['id']],'expected_revision':artifact['revision']})
    assert changed.status_code==200,changed.text
    trace=next(x for x in a.get('/projects/1/trace').json() if x['id']==req['id'])
    assert trace['covered'] is True
    assert any(x['result']=='passed' for x in trace['artifacts'])

def test_dashboard_counts_match_list(actors):
    a=actors['analyst']; dash=a.get('/projects/1/dashboard').json(); reqs=a.get('/projects/1/requirements').json()
    assert dash['counts']['total']==len(reqs)
    for status in ('draft','in_review','approved','archived'):
        assert dash['counts'][status]==sum(x['status']==status for x in reqs)

def test_document_member_and_project_admin_flows(actors):
    a=actors['admin']
    user=a.post('/users',{'username':'new_user','name':'新成员','password':'NewUserPassword!','is_admin':False})
    assert user.status_code==201,user.text
    project=a.post('/projects',{'name':'第二项目','description':'隔离示例'})
    assert project.status_code==201,project.text
    pid=project.json()['id']
    assert a.put(f"/projects/{pid}/members/{user.json()['id']}",{'role':'viewer'}).status_code==200
    assert a.post(f'/projects/{pid}/documents',{'title':'需求规格','description':'说明'}).status_code==201
    assert len(a.get(f'/projects/{pid}/members').json())==2

def test_draft_archive_is_audited(actors):
    req=created(actors); a=actors['analyst']
    response=a.post(f"/requirements/{req['id']}/archive",{'expected_revision':req['revision']})
    assert response.status_code==200,response.text
    assert a.get(f"/requirements/{req['id']}").json()['status']=='archived'

def test_change_rejection_preserves_content(actors):
    a=actors['analyst']; r=actors['reviewer']
    req=approve(actors,created(actors)['id'])
    change=a.post(f"/requirements/{req['id']}/changes",{'expected_revision':req['revision'],'title':'不采纳的变更','reason':'演示','proposed':fields(title='不应生效')}).json()
    assert r.post(f"/changes/{change['id']}/decide",{'decision':'rejected','comment':'当前范围不需要'}).status_code==200
    current=a.get(f"/requirements/{req['id']}").json()
    assert current['title']==req['title'] and current['revision']==req['revision']

def test_exports_are_downloadable(actors):
    for kind in ('requirements','trace'):
        r=actors['viewer'].get('/projects/1/export?kind='+kind)
        assert r.status_code==200 and 'text/csv' in r.headers['content-type']
        assert 'attachment' in r.headers['content-disposition'] and 'REQ-001' in r.text
