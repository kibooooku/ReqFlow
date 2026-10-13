import pytest
from fastapi.testclient import TestClient
from conftest import fields,created,approve

def test_anonymous_cannot_read(actors):
    with TestClient(actors['app']) as c:
        assert c.get('/api/projects').status_code==401
        assert c.get('/api/requirements/1').status_code==401

def test_wrong_password_and_cookie_flags(actors):
    with TestClient(actors['app']) as c:
        assert c.post('/api/auth/login',json={'username':'analyst','password':'wrong'}).status_code==401
        r=c.post('/api/auth/login',json={'username':'analyst','password':'AnalystDemo2026!'})
        cookie=r.headers['set-cookie'].lower()
        assert 'httponly' in cookie and 'samesite=strict' in cookie
        assert 'password' not in str(r.json()['user'])

def test_csrf_missing_or_invalid_rejected(actors):
    c=actors['analyst'].client
    for headers in ({},{'x-csrf-token':'wrong'}):
        assert c.post('/api/projects/1/requirements',json=fields(),headers=headers).status_code==403

def test_cross_origin_write_rejected(actors):
    a=actors['analyst']
    r=a.client.post('/api/projects/1/requirements',json=fields(),headers={'X-CSRF-Token':a.csrf,'Origin':'https://evil.example'})
    assert r.status_code==403

@pytest.mark.parametrize('endpoint,body',[('/projects/1/requirements',fields()),('/projects/1/documents',{'title':'拒绝写入'}),('/projects/1/baselines',{'name':'拒绝基线'})])
def test_viewer_cannot_write(actors,endpoint,body):
    assert actors['viewer'].post(endpoint,body).status_code==403

def test_cross_project_access_and_link_rejected(actors):
    admin=actors['admin']; a=actors['analyst']
    pid=admin.post('/projects',{'name':'私有项目'}).json()['id']
    assert a.get(f'/projects/{pid}/requirements').status_code in (403,404)
    foreign=admin.post(f'/projects/{pid}/requirements',fields(owner_id=1,document_id=None)).json()
    assert a.get(f"/requirements/{foreign['id']}").status_code in (403,404)
    r=a.post('/projects/1/links',{'source_id':1,'target_id':foreign['id'],'kind':'depends'})
    assert r.status_code in (400,403,404,422)

def test_submitter_cannot_choose_self_as_reviewer(actors):
    admin=actors['admin']
    req=admin.post('/projects/1/requirements',fields()).json()
    assert admin.post(f"/requirements/{req['id']}/submit",{'expected_revision':req['revision'],'reviewer_id':1}).status_code in (400,403,422)

def test_only_assigned_reviewer_can_decide(actors):
    req=created(actors); a=actors['analyst']
    assert a.post(f"/requirements/{req['id']}/submit",{'expected_revision':req['revision'],'reviewer_id':3}).status_code==200
    review=next(x for x in a.get('/projects/1/reviews').json() if x['requirement_id']==req['id'])
    for name in ('analyst','admin','viewer'):
        assert actors[name].post(f"/reviews/{review['id']}/decide",{'decision':'approved'}).status_code==403

def test_admin_cannot_approve_own_change(actors):
    req=approve(actors,created(actors)['id']); admin=actors['admin']
    change=admin.post(f"/requirements/{req['id']}/changes",{'expected_revision':req['revision'],'title':'管理员提交变更','reason':'自审规则','proposed':fields(title='管理员申请的新标题')})
    assert change.status_code==201,change.text
    assert admin.post(f"/changes/{change.json()['id']}/decide",{'decision':'approved'}).status_code==403

def test_logout_invalidates_session(actors):
    a=actors['analyst']; cookies=dict(a.client.cookies)
    assert a.post('/auth/logout').status_code==200
    a.client.cookies.update(cookies)
    assert a.get('/auth/me').status_code==401

def test_sql_injection_search_is_data(actors):
    r=actors['analyst'].get('/projects/1/requirements',params={'q':"' OR 1=1 --"})
    assert r.status_code==200 and r.json()==[]
    assert actors['analyst'].get('/projects/1/requirements').status_code==200

def test_input_fields_cannot_set_status_or_privilege(actors):
    assert actors['analyst'].post('/projects/1/requirements',fields(status='approved')).status_code==422
    assert actors['analyst'].post('/users',{'username':'hacker','name':'账号','password':'Password123!','is_admin':True}).status_code==403

def test_csv_formula_injection_neutralized(actors):
    created(actors,title='=HYPERLINK("https://example.invalid")')
    text=actors['analyst'].get('/projects/1/export?kind=requirements').text
    import csv,io
    rows=list(csv.reader(io.StringIO(text.lstrip('\ufeff'))))
    assert any(cell.startswith("'=HYPERLINK") for row in rows for cell in row)

def test_login_rate_limit(actors):
    with TestClient(actors['app']) as c:
        status=[c.post('/api/auth/login',json={'username':'missing','password':'wrong'}).status_code for _ in range(31)]
        assert status[-1]==429

def test_oversized_payload_rejected(actors):
    a=actors['analyst']
    r=a.client.post('/api/projects/1/requirements',content=b'x'*(256*1024+1),headers={'x-csrf-token':a.csrf,'content-type':'application/json'})
    assert r.status_code==413
