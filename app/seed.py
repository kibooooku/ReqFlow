"""Labeled demonstration fixtures; results below are examples, not real tests."""
import json
from datetime import datetime, timezone
from . import db, security

def seed(path):
    c=db.connect(path)
    try:
        with db.transaction(c):
            if c.execute('SELECT COUNT(*) FROM users').fetchone()[0]:
                return
            accounts=[('admin','系统管理员','AdminDemo2026!',1),('analyst','需求分析员 · 林同学','AnalystDemo2026!',0),('reviewer','需求评审员 · 陈同学','ReviewDemo2026!',0),('viewer','只读观察员','ViewerDemo2026!',0)]
            for username,name,password,admin in accounts:
                c.execute('INSERT INTO users(username,name,password_hash,is_admin) VALUES(?,?,?,?)',(username,name,security.hash_password(password),admin))
            c.execute('INSERT INTO projects(name,description) VALUES(?,?)',('校园实验室预约系统','演示需求集：管理预约业务的需求、评审、基线与追踪；所有初始数据均为教学示例。'))
            for uid,role in [(1,'admin'),(2,'analyst'),(3,'reviewer'),(4,'viewer')]:
                c.execute('INSERT INTO members VALUES(1,?,?)',(uid,role))
            c.execute('INSERT INTO documents(project_id,title,description) VALUES(1,?,?)',('业务与功能需求','预约、资格校验、取消与消息通知'))
            c.execute('INSERT INTO documents(project_id,title,description) VALUES(1,?,?)',('质量与约束需求','性能、数据保护与可访问性'))
            samples=[
                ('REQ-001','统一身份登录','学生应使用校园统一身份进行登录，系统识别学生编号。','functional','must','approved','有效身份可进入预约页面；无效身份返回明确错误。',1,None),
                ('REQ-002','实验室可用时段查询','学生可按日期和实验室查询可预约时段。','functional','must','approved','返回所选日期的空闲时段；已满时段不可预约。',1,None),
                ('REQ-003','创建实验室预约','已登录学生可选择一个空闲时段提交预约。','functional','must','approved','同一实验室同一时段不可重复预约，预约成功生成唯一编号。',1,None),
                ('REQ-004','取消预约规则','学生可在开始时间前30分钟取消本人预约。','functional','must','approved','提前30分钟及以上允许取消；少于30分钟拒绝取消并说明原因。',1,3),
                ('REQ-005','预约结果通知','预约成功或取消后，在站内显示确认信息。','functional','should','draft','成功创建或取消预约后，显示对应预约编号及结果。',1,3),
                ('REQ-006','预约冲突校验','并发预约同一时段时，只允许一条预约成功。','functional','must','in_review','两个请求同时预约同一时段，成功记录数为1。',1,3),
                ('REQ-007','页面响应时间','在约定的校园测试环境中，查询接口95%请求响应不超过2秒。','nonfunctional','should','draft','100并发、1000次请求中，P95不超过2秒；记录测试环境。',2,None),
                ('REQ-008','个人信息访问控制','学生只能查看与取消自己的预约，管理员按授权查看。','constraint','must','approved','普通账号访问他人预约返回无权限，管理员授权访问成功。',2,None),
                ('REQ-009','键盘可访问性','核心预约流程应支持仅使用键盘操作。','nonfunctional','could','draft','登录、选择时段、确认与取消均可用Tab及Enter完成。',2,None)]
            now=datetime.now(timezone.utc).isoformat()
            for uid,title,statement,kind,priority,status,acceptance,doc,parent in samples:
                c.execute('INSERT INTO requirements(project_id,document_id,uid,parent_id,title,statement,source,rationale,type,priority,status,owner_id,acceptance,tags,revision,created_by,updated_at) VALUES(1,?,?,?,?,?,?,?,?,?,?,2,?,?,1,2,?)',
                          (doc,uid,parent,title,statement,'校园实验室业务访谈（教学示例）','提高预约流程的可验证性',kind,priority,status,acceptance,json.dumps(['教学示例'],ensure_ascii=False),now))
                row=dict(c.execute('SELECT * FROM requirements WHERE uid=?',(uid,)).fetchone()); row['tags']=json.loads(row['tags'])
                c.execute('INSERT INTO requirement_versions(requirement_id,revision,snapshot,created_by,created_at) VALUES(?,1,?,2,?)',(row['id'],json.dumps(row,ensure_ascii=False),now))
            for src,target,kind in [(3,1,'depends'),(3,2,'depends'),(4,3,'refines'),(5,3,'refines'),(6,3,'refines'),(3,8,'depends')]:
                c.execute('INSERT INTO links(project_id,source_id,target_id,kind) VALUES(1,?,?,?)',(src,target,kind))
            fixtures=[('design','预约业务状态图','DESIGN-01','not_run',[3,4]),('test','正常预约验收用例','TC-001','passed',[1,2,3]),('test','取消预约时间边界用例','TC-002','not_run',[4]),('test','越权取消预约用例','TC-003','passed',[8]),('test','预约冲突并发用例','TC-004','not_run',[6])]
            for kind,title,ref,result,reqs in fixtures:
                aid=c.execute('INSERT INTO artifacts(project_id,kind,title,reference,result) VALUES(1,?,?,?,?)',(kind,title,ref,result)).lastrowid
                for rid in reqs:c.execute('INSERT INTO artifact_links VALUES(?,?)',(rid,aid))
            c.execute('INSERT INTO reviews(requirement_id,revision,submitted_by,reviewer_id,created_at) VALUES(6,1,2,3,?)',(now,))
            c.execute('INSERT INTO audit_logs(project_id,actor_id,action,entity_type,entity_id,detail,created_at) VALUES(1,1,?,?,?,?,?)',('初始化教学示例','project',1,'初始需求状态及验证项结果均为示例数据，不是本系统实测结论',now))
    finally:
        c.close()
