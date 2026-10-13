import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import create_app

class API:
    def __init__(self, client, csrf):
        self.client, self.csrf = client, csrf

    def get(self, url, **kw):
        return self.client.get('/api'+url, **kw)

    def request(self, method, url, data=None):
        return self.client.request(method, '/api'+url, json=data, headers={'X-CSRF-Token':self.csrf})

    def post(self, url, data=None): return self.request('POST',url,data or {})
    def patch(self, url, data): return self.request('PATCH',url,data)
    def put(self, url, data): return self.request('PUT',url,data)
    def delete(self, url): return self.request('DELETE',url)

@pytest.fixture
def actors(tmp_path):
    app=create_app(tmp_path/'test.db')
    clients=[]; result={}
    for name,pw in [('admin','AdminDemo2026!'),('analyst','AnalystDemo2026!'),('reviewer','ReviewDemo2026!'),('viewer','ViewerDemo2026!')]:
        client=TestClient(app); client.__enter__(); clients.append(client)
        r=client.post('/api/auth/login',json={'username':name,'password':pw})
        assert r.status_code==200, r.text
        result[name]=API(client,r.json()['csrf'])
    result['app']=app; result['db']=app.state.database
    yield result
    for client in reversed(clients): client.__exit__(None,None,None)

def fields(**changes):
    return {'title':'新增需求','statement':'系统应验证输入并保存需求。','source':'测试案例','rationale':'验证完整性','type':'functional','priority':'must','owner_id':2,'acceptance':'有效输入成功保存，非法输入拒绝','tags':['测试'],'document_id':1,'parent_id':None,**changes}

def created(actors, **changes):
    r=actors['analyst'].post('/projects/1/requirements',fields(**changes))
    assert r.status_code==201, r.text
    return r.json()

def approve(actors,rid):
    a,r=actors['analyst'],actors['reviewer']
    revision=a.get(f'/requirements/{rid}').json()['revision']
    sent=a.post(f'/requirements/{rid}/submit',{'expected_revision':revision,'reviewer_id':3})
    assert sent.status_code==200,sent.text
    review=next(x for x in r.get('/projects/1/reviews').json() if x['requirement_id']==rid and x['status']=='pending')
    decision=r.post(f"/reviews/{review['id']}/decide",{'decision':'approved','comment':'符合验收标准'})
    assert decision.status_code==200,decision.text
    return a.get(f'/requirements/{rid}').json()
