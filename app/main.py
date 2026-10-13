"""HTTP adapter. Authorization and lifecycle rules remain server-side."""
import csv
import hmac
import io
import os
import sqlite3
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from . import db, schemas as S, security, service

ROOT = Path(__file__).resolve().parent.parent

def create_app(database=None, seed_demo=True):
    database = Path(database or os.environ.get('REQFLOW_DB', ROOT / 'data/reqflow.db'))

    @asynccontextmanager
    async def lifespan(app):
        db.initialize(database)
        if seed_demo:
            from .seed import seed
            seed(database)
        yield

    app = FastAPI(title='ReqFlow 需求管理系统', version='1.0.0', lifespan=lifespan)
    app.state.database = database
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=['localhost','127.0.0.1','testserver'])
    login_attempts = defaultdict(deque)
    limiter_lock = Lock()

    @app.middleware('http')
    async def boundaries(request: Request, call_next):
        if request.method in ('POST','PATCH','PUT','DELETE'):
            origin = request.headers.get('origin')
            if origin and origin != str(request.base_url).rstrip('/'):
                return JSONResponse({'detail':'请求来源与本站不一致'}, status_code=403)
            limit = 256 * 1024
            chunks, size = [], 0
            async for chunk in request.stream():
                size += len(chunk)
                if size > limit:
                    return JSONResponse({'detail':'请求内容超过256KB限制'}, status_code=413)
                chunks.append(chunk)
            # Starlette's cached request replays this bounded body to the router.
            request._body = b''.join(chunks)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'same-origin'
        if not request.url.path.startswith(('/docs','/redoc')):
            response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        if request.url.path.startswith('/api'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request, exc):
        # Only field paths are returned; passwords and user input never echoed.
        fields = ', '.join('.'.join(str(v) for v in e['loc'][1:]) for e in exc.errors())
        return JSONResponse({'detail':f'输入校验失败，请检查：{fields}'}, status_code=422)

    @app.exception_handler(sqlite3.IntegrityError)
    async def database_constraint(request, exc):
        return JSONResponse({'detail':'操作与唯一性、关联或历史不可变约束冲突'}, status_code=409)

    def connection():
        c = db.connect(database)
        try:
            yield c
        finally:
            c.close()

    def current_user(request: Request, c=Depends(connection)):
        token = request.cookies.get('reqflow_session', '')
        row = c.execute('SELECT u.*,s.csrf FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>?', (security.token_hash(token),time.time())).fetchone()
        if not row:
            raise HTTPException(401, '请先登录，或会话已过期')
        if request.method in ('POST','PUT','PATCH','DELETE'):
            submitted = request.headers.get('x-csrf-token','')
            if not submitted.isascii() or len(submitted) > 128 or not hmac.compare_digest(submitted, row['csrf']):
                raise HTTPException(403, '安全校验失败，请刷新页面后重试')
        return dict(row)

    def admin(u):
        if not u['is_admin']:
            raise HTTPException(403, '此操作仅限系统管理员')

    def log(c,u,p,action,entity,eid,detail):
        c.execute('INSERT INTO audit_logs(project_id,actor_id,action,entity_type,entity_id,detail,created_at) VALUES(?,?,?,?,?,?,?)',
                  (p,u['id'],action,entity,eid,detail,datetime.now(timezone.utc).isoformat()))

    @app.post('/api/auth/login')
    def login(body:S.Login, request:Request, response:Response, c=Depends(connection)):
        key = request.client.host if request.client else 'local'
        with limiter_lock:
            attempts = login_attempts[key]
            now = time.monotonic()
            while attempts and now-attempts[0] > 60:
                attempts.popleft()
            if len(attempts) >= 30:
                raise HTTPException(429, '登录尝试过于频繁，请稍后再试')
            attempts.append(now)
        row = c.execute('SELECT * FROM users WHERE username=?',(body.username,)).fetchone()
        if not row or not security.verify_password(body.password,row['password_hash']):
            raise HTTPException(401,'用户名或密码错误')
        with db.transaction(c):
            old = request.cookies.get('reqflow_session')
            if old:
                c.execute('DELETE FROM sessions WHERE token_hash=?',(security.token_hash(old),))
            token,csrf = security.new_session(c,row['id'])
        response.set_cookie('reqflow_session',token,httponly=True,samesite='strict',secure=request.url.scheme=='https',max_age=8*3600,path='/')
        return {'user':security.public_user(row),'csrf':csrf}

    @app.get('/api/auth/me')
    def me(u=Depends(current_user)):
        return {'user':security.public_user(u),'csrf':u['csrf']}

    @app.post('/api/auth/logout')
    def logout(request:Request,response:Response,u=Depends(current_user),c=Depends(connection)):
        with db.transaction(c):
            c.execute('DELETE FROM sessions WHERE token_hash=?',(security.token_hash(request.cookies.get('reqflow_session','')),))
        response.delete_cookie('reqflow_session',path='/')
        return {'ok':True}

    @app.get('/api/users')
    def users(u=Depends(current_user),c=Depends(connection)):
        admin(u)
        return [security.public_user(x) for x in c.execute('SELECT * FROM users ORDER BY id')]

    @app.post('/api/users',status_code=201)
    def create_user(body:S.UserBody,u=Depends(current_user),c=Depends(connection)):
        admin(u)
        with db.transaction(c):
            uid = c.execute('INSERT INTO users(username,name,password_hash,is_admin) VALUES(?,?,?,?)', (body.username,body.name,security.hash_password(body.password),int(body.is_admin))).lastrowid
            log(c,u,None,'创建用户','user',uid,body.username)
        return security.public_user(c.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone())

    @app.get('/api/projects')
    def projects(u=Depends(current_user),c=Depends(connection)):
        return [dict(x) for x in c.execute('SELECT p.*,m.role FROM projects p JOIN members m ON m.project_id=p.id WHERE m.user_id=? ORDER BY p.id',(u['id'],))]

    @app.post('/api/projects',status_code=201)
    def create_project(body:S.ProjectBody,u=Depends(current_user),c=Depends(connection)):
        admin(u)
        with db.transaction(c):
            pid=c.execute('INSERT INTO projects(name,description) VALUES(?,?)',(body.name,body.description)).lastrowid
            c.execute('INSERT INTO members VALUES(?,?,?)',(pid,u['id'],'admin'))
            log(c,u,pid,'创建项目','project',pid,body.name)
        return {'id':pid,**body.model_dump(),'role':'admin'}

    @app.get('/api/projects/{p}/members')
    def members(p:int,u=Depends(current_user),c=Depends(connection)):
        service.access(c,u,p)
        return [dict(x) for x in c.execute('SELECT m.user_id,m.role,u.username,u.name FROM members m JOIN users u ON u.id=m.user_id WHERE m.project_id=? ORDER BY m.user_id',(p,))]

    @app.put('/api/projects/{p}/members/{uid}')
    def set_member(p:int,uid:int,body:S.MemberBody,u=Depends(current_user),c=Depends(connection)):
        admin(u)
        with db.transaction(c):
            service.access(c,u,p)
            if not c.execute('SELECT id FROM users WHERE id=?',(uid,)).fetchone():
                raise HTTPException(404,'用户不存在')
            c.execute('INSERT INTO members VALUES(?,?,?) ON CONFLICT(project_id,user_id) DO UPDATE SET role=excluded.role',(p,uid,body.role))
            log(c,u,p,'更新成员角色','member',uid,body.role)
        return {'user_id':uid,'role':body.role}

    @app.get('/api/projects/{p}/documents')
    def documents(p:int,u=Depends(current_user),c=Depends(connection)):
        service.access(c,u,p)
        return [dict(x) for x in c.execute('SELECT * FROM documents WHERE project_id=? ORDER BY id',(p,))]

    @app.post('/api/projects/{p}/documents',status_code=201)
    def create_document(p:int,body:S.DocumentBody,u=Depends(current_user),c=Depends(connection)):
        with db.transaction(c):
            service.access(c,u,p,('admin','analyst'))
            did=c.execute('INSERT INTO documents(project_id,title,description) VALUES(?,?,?)',(p,body.title,body.description)).lastrowid
            log(c,u,p,'创建需求文档','document',did,body.title)
        return {'id':did,'project_id':p,**body.model_dump()}

    @app.get('/api/projects/{p}/dashboard')
    def dashboard(p:int,u=Depends(current_user),c=Depends(connection)):
        return service.dashboard(c,u,p)

    @app.get('/api/projects/{p}/requirements')
    def requirements(p:int,q:str='',status:str='',type:str='',priority:str='',u=Depends(current_user),c=Depends(connection)):
        return service.list_requirements(c,u,p,dict(q=q,status=status,type=type,priority=priority))

    @app.post('/api/projects/{p}/requirements',status_code=201)
    def create_requirement(p:int,body:S.RequirementCreate,u=Depends(current_user),c=Depends(connection)):
        return service.create_requirement(c,u,p,body.model_dump())

    @app.get('/api/requirements/{rid}')
    def requirement(rid:int,u=Depends(current_user),c=Depends(connection)):
        return service.get_requirement(c,u,rid)

    @app.patch('/api/requirements/{rid}')
    def update_requirement(rid:int,body:S.RequirementUpdate,u=Depends(current_user),c=Depends(connection)):
        return service.update_requirement(c,u,rid,body.model_dump())

    @app.post('/api/requirements/{rid}/archive')
    def archive(rid:int,body:S.RevisionBody,u=Depends(current_user),c=Depends(connection)):
        return service.archive_requirement(c,u,rid,body.expected_revision)

    @app.post('/api/requirements/{rid}/submit')
    def submit(rid:int,body:S.SubmitBody,u=Depends(current_user),c=Depends(connection)):
        return service.submit_review(c,u,rid,body.model_dump())

    @app.get('/api/projects/{p}/reviews')
    def reviews(p:int,u=Depends(current_user),c=Depends(connection)):
        return service.list_reviews(c,u,p)

    @app.post('/api/reviews/{rid}/decide')
    def decide_review(rid:int,body:S.DecisionBody,u=Depends(current_user),c=Depends(connection)):
        return service.decide_review(c,u,rid,body.model_dump())

    @app.get('/api/projects/{p}/links')
    def links(p:int,u=Depends(current_user),c=Depends(connection)):
        return service.list_links(c,u,p)

    @app.post('/api/projects/{p}/links',status_code=201)
    def create_link(p:int,body:S.LinkBody,u=Depends(current_user),c=Depends(connection)):
        return service.create_link(c,u,p,body.model_dump())

    @app.delete('/api/links/{lid}')
    def delete_link(lid:int,u=Depends(current_user),c=Depends(connection)):
        return service.delete_link(c,u,lid)

    @app.get('/api/projects/{p}/artifacts')
    def artifacts(p:int,u=Depends(current_user),c=Depends(connection)):
        return service.list_artifacts(c,u,p)

    @app.post('/api/projects/{p}/artifacts',status_code=201)
    def create_artifact(p:int,body:S.ArtifactBody,u=Depends(current_user),c=Depends(connection)):
        return service.save_artifact(c,u,p,body.model_dump())

    @app.patch('/api/artifacts/{aid}')
    def update_artifact(aid:int,body:S.ArtifactUpdate,u=Depends(current_user),c=Depends(connection)):
        row=c.execute('SELECT project_id FROM artifacts WHERE id=?',(aid,)).fetchone()
        if not row: raise HTTPException(404,'验证项不存在')
        return service.save_artifact(c,u,row['project_id'],body.model_dump(),artifact_id=aid)

    @app.get('/api/projects/{p}/trace')
    def trace(p:int,u=Depends(current_user),c=Depends(connection)):
        return service.trace(c,u,p)

    @app.get('/api/projects/{p}/baselines')
    def baselines(p:int,u=Depends(current_user),c=Depends(connection)):
        return service.list_baselines(c,u,p)

    @app.post('/api/projects/{p}/baselines',status_code=201)
    def create_baseline(p:int,body:S.BaselineBody,u=Depends(current_user),c=Depends(connection)):
        return service.create_baseline(c,u,p,body.model_dump())

    @app.get('/api/baselines/{bid}')
    def baseline(bid:int,u=Depends(current_user),c=Depends(connection)):
        return service.get_baseline(c,u,bid)

    @app.get('/api/baselines/{bid}/compare')
    def compare(bid:int,u=Depends(current_user),c=Depends(connection)):
        return service.compare_baseline(c,u,bid)

    @app.get('/api/projects/{p}/changes')
    def changes(p:int,u=Depends(current_user),c=Depends(connection)):
        return service.list_changes(c,u,p)

    @app.post('/api/requirements/{rid}/changes',status_code=201)
    def create_change(rid:int,body:S.ChangeBody,u=Depends(current_user),c=Depends(connection)):
        return service.create_change(c,u,rid,body.model_dump())

    @app.get('/api/requirements/{rid}/impact')
    def impact(rid:int,u=Depends(current_user),c=Depends(connection)):
        return service.impact(c,u,rid)

    @app.post('/api/changes/{cid}/decide')
    def decide_change(cid:int,body:S.DecisionBody,u=Depends(current_user),c=Depends(connection)):
        return service.decide_change(c,u,cid,body.model_dump())

    @app.get('/api/projects/{p}/audit')
    def audit(p:int,u=Depends(current_user),c=Depends(connection)):
        return service.audit_list(c,u,p)

    @app.get('/api/projects/{p}/export')
    def export(p:int,kind:str='requirements',u=Depends(current_user),c=Depends(connection)):
        result=service.export_csv(c,u,p,kind)
        return Response(content='\ufeff'+result,media_type='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="reqflow-{kind}.csv"'})

    @app.get('/api/health')
    def health():
        return {'status':'ok','version':'1.0.0'}

    static=Path(__file__).parent/'static'
    static.mkdir(exist_ok=True)
    app.mount('/static',StaticFiles(directory=static),name='static')

    @app.get('/')
    def index():
        return FileResponse(static/'index.html')

    return app

app=create_app()
