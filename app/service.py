"""ReqFlow business rules. Authorization and version checks run inside writes.

Requirement revisions record both content and lifecycle transitions. Trace links
and verification evidence have their own audit trail; a baseline freezes all
three so that later evidence updates never rewrite a released baseline.
"""
import csv
import io
import json
import sqlite3
from datetime import datetime, timezone

from fastapi import HTTPException

from . import db


EDITORS = ('admin', 'analyst')
APPROVERS = ('admin', 'reviewer')
FIELDS = (
    'document_id', 'parent_id', 'title', 'statement', 'source', 'rationale',
    'type', 'priority', 'owner_id', 'acceptance', 'tags',
)
REQ_SELECT = """SELECT r.*, u.name AS owner_name FROM requirements r
LEFT JOIN users u ON u.id=r.owner_id"""


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _error(status, message):
    raise HTTPException(status_code=status, detail=message)


def _execute(c, sql, params=()):
    try:
        return c.execute(sql, params)
    except sqlite3.IntegrityError:
        _error(409, '数据约束冲突：编号、名称或关联重复，或引用对象已失效')


def access(c, u, p, roles=None):
    """Return the project role; global administration is not membership."""
    membership = c.execute(
        'SELECT role FROM members WHERE project_id=? AND user_id=?',
        (p, u['id']),
    ).fetchone()
    if membership is None:
        _error(403, '你不是该项目的成员')
    role = membership['role']
    if roles is not None and role not in roles:
        _error(403, '当前项目角色没有此操作权限')
    return role


def _req(c, rid):
    row = c.execute(REQ_SELECT + ' WHERE r.id=?', (rid,)).fetchone()
    if row is None:
        _error(404, '需求不存在')
    result = dict(row)
    result['tags'] = json.loads(result['tags'])
    return result


def _audit(c, u, p, action, entity, eid, detail):
    _execute(c, '''INSERT INTO audit_logs
        (project_id,actor_id,action,entity_type,entity_id,detail,created_at)
        VALUES (?,?,?,?,?,?,?)''',
        (p, u['id'], action, entity, eid, _json(detail), now()))


def _version(c, u, rid):
    snapshot = _req(c, rid)
    # Display names are deliberately omitted: mutable user labels are not
    # requirement content. Identity is kept through owner_id and created_by.
    snapshot.pop('owner_name', None)
    _execute(c, '''INSERT INTO requirement_versions
        (requirement_id,revision,snapshot,created_by,created_at) VALUES (?,?,?,?,?)''',
        (rid, snapshot['revision'], _json(snapshot), u['id'], snapshot['updated_at']))


def _expected(req, revision):
    if req['revision'] != revision:
        _error(409, '需求版本已变化，请刷新后重新操作')


def _assert_live(req):
    if req['status'] == 'archived':
        _error(409, '已归档需求不能继续修改或建立关联')


def _would_cycle(c, p, source, target, replacing_parent=False):
    """Parent, refines and depends share a child/dependent-to-parent graph."""
    if source == target:
        return True
    graph = {}
    for row in c.execute('SELECT id,parent_id FROM requirements WHERE project_id=?', (p,)):
        if row['parent_id'] is not None and not (replacing_parent and row['id'] == source):
            graph.setdefault(row['id'], set()).add(row['parent_id'])
    for row in c.execute("SELECT source_id,target_id FROM links WHERE project_id=? AND kind IN ('refines','depends')", (p,)):
        graph.setdefault(row['source_id'], set()).add(row['target_id'])
    pending, visited = [target], set()
    while pending:
        item = pending.pop()
        if item == source:
            return True
        if item not in visited:
            visited.add(item)
            pending.extend(graph.get(item, ()))
    return False


def _fields(c, p, data, rid=None):
    values = {name: data[name] for name in FIELDS}
    if values['document_id'] is not None:
        row = c.execute('SELECT project_id FROM documents WHERE id=?', (values['document_id'],)).fetchone()
        if row is None or row['project_id'] != p:
            _error(422, '需求文档必须属于当前项目')
    if values['owner_id'] is not None:
        row = c.execute('SELECT 1 FROM members WHERE project_id=? AND user_id=?', (p, values['owner_id'])).fetchone()
        if row is None:
            _error(422, '需求负责人必须是当前项目成员')
    if values['parent_id'] is not None:
        row = c.execute('SELECT project_id,status FROM requirements WHERE id=?', (values['parent_id'],)).fetchone()
        if row is None or row['project_id'] != p:
            _error(422, '上位需求必须属于当前项目')
        if row['status'] == 'archived':
            _error(409, '不能选择已归档的上位需求')
        if rid is not None and _would_cycle(c, p, rid, values['parent_id'], replacing_parent=True):
            _error(409, '上位需求会造成分解或依赖环')
    return values


def _quality(values):
    if not values['source'].strip() or not values['acceptance'].strip():
        _error(422, '提交评审或批准内容必须填写需求来源与验收标准')


def _replace(c, u, req, fields=None, status=None):
    values = dict(fields or {})
    if status is not None:
        values['status'] = status
    values['revision'] = req['revision'] + 1
    values['updated_at'] = now()
    if 'tags' in values:
        values['tags'] = _json(values['tags'])
    # Keys originate exclusively in the fixed FIELDS tuple and literals above.
    sql = 'UPDATE requirements SET ' + ','.join(f'{key}=?' for key in values)
    cur = _execute(c, sql + ' WHERE id=? AND revision=?',
                   (*values.values(), req['id'], req['revision']))
    if cur.rowcount != 1:
        _error(409, '需求版本已变化，请刷新后重新操作')
    _version(c, u, req['id'])
    return _req(c, req['id'])


@db.consistent_read
def list_requirements(c, u, p, filters):
    access(c, u, p)
    predicates, args = ['r.project_id=?'], [p]
    for key in ('status', 'type', 'priority'):
        if filters.get(key):
            predicates.append(f'r.{key}=?')
            args.append(filters[key])
    if filters.get('q'):
        predicates.append('(r.uid LIKE ? OR r.title LIKE ? OR r.statement LIKE ? OR r.tags LIKE ?)')
        args.extend([f"%{filters['q']}%"] * 4)
    rows = c.execute(REQ_SELECT + ' WHERE ' + ' AND '.join(predicates) + ' ORDER BY r.id', args)
    result = []
    for row in rows:
        item = dict(row)
        item['tags'] = json.loads(item['tags'])
        result.append(item)
    return result


@db.consistent_read
def get_requirement(c, u, rid):
    req = _req(c, rid)
    access(c, u, req['project_id'])
    req['versions'] = []
    for row in c.execute('SELECT revision,snapshot,created_by,created_at FROM requirement_versions WHERE requirement_id=? ORDER BY revision DESC', (rid,)):
        item = dict(row)
        item['snapshot'] = json.loads(item['snapshot'])
        req['versions'].append(item)
    req['links'] = [x for x in list_links(c, u, req['project_id']) if rid in (x['source_id'], x['target_id'])]
    req['artifacts'] = [x for x in list_artifacts(c, u, req['project_id']) if rid in x['requirement_ids']]
    req['reviews'] = [x for x in list_reviews(c, u, req['project_id']) if x['requirement_id'] == rid]
    return req


def create_requirement(c, u, p, data):
    with db.transaction(c):
        access(c, u, p, EDITORS)
        values = _fields(c, p, data)
        uid = data.get('uid')
        if not uid:
            number = c.execute('SELECT COALESCE(MAX(id),0)+1 FROM requirements').fetchone()[0]
            uid = f'REQ-{number:04d}'
            while c.execute('SELECT 1 FROM requirements WHERE project_id=? AND uid=?', (p, uid)).fetchone():
                number += 1
                uid = f'REQ-{number:04d}'
        values['tags'] = _json(values['tags'])
        keys = ['project_id', 'uid', *FIELDS, 'status', 'created_by', 'updated_at']
        args = [p, uid, *(values[x] for x in FIELDS), 'draft', u['id'], now()]
        cur = _execute(c, 'INSERT INTO requirements (' + ','.join(keys) + ') VALUES (' + ','.join('?' for _ in keys) + ')', args)
        rid = cur.lastrowid
        _version(c, u, rid)
        _audit(c, u, p, 'requirement.created', 'requirement', rid, {'uid': uid, 'revision': 1})
        return _req(c, rid)


def update_requirement(c, u, rid, data):
    with db.transaction(c):
        req = _req(c, rid)
        access(c, u, req['project_id'], EDITORS)
        _expected(req, data['expected_revision'])
        if req['status'] != 'draft':
            _error(409, '仅草稿可直接编辑；已批准需求请提交变更申请')
        fields = _fields(c, req['project_id'], data, rid)
        updated = _replace(c, u, req, fields)
        _audit(c, u, req['project_id'], 'requirement.updated', 'requirement', rid,
               {'from_revision': req['revision'], 'to_revision': updated['revision']})
        return updated


def archive_requirement(c, u, rid, revision):
    with db.transaction(c):
        req = _req(c, rid)
        access(c, u, req['project_id'], EDITORS)
        _expected(req, revision)
        _assert_live(req)
        if req['status'] != 'draft':
            _error(409, '本版仅允许归档草稿，待评审或已批准需求不能直接归档')
        if c.execute("SELECT 1 FROM changes WHERE requirement_id=? AND status='pending'", (rid,)).fetchone():
            _error(409, '需求还有待处理变更，不能归档')
        result = _replace(c, u, req, status='archived')
        _audit(c, u, req['project_id'], 'requirement.archived', 'requirement', rid,
               {'from_revision': req['revision'], 'to_revision': result['revision']})
        return result


def submit_review(c, u, rid, data):
    with db.transaction(c):
        req = _req(c, rid)
        p = req['project_id']
        access(c, u, p, EDITORS)
        _expected(req, data['expected_revision'])
        if req['status'] != 'draft':
            _error(409, '只有草稿可以提交评审')
        _quality(req)
        reviewer = c.execute('SELECT role FROM members WHERE project_id=? AND user_id=?', (p, data['reviewer_id'])).fetchone()
        if reviewer is None or reviewer['role'] not in APPROVERS:
            _error(422, '指定评审人必须是当前项目评审员或管理员')
        if data['reviewer_id'] == u['id']:
            _error(403, '提交人与评审人必须是不同成员，禁止自审')
        updated = _replace(c, u, req, status='in_review')
        cur = _execute(c, '''INSERT INTO reviews
            (requirement_id,revision,submitted_by,reviewer_id,created_at) VALUES (?,?,?,?,?)''',
            (rid, updated['revision'], u['id'], data['reviewer_id'], now()))
        _audit(c, u, p, 'review.submitted', 'review', cur.lastrowid,
               {'requirement_id': rid, 'revision': updated['revision'], 'reviewer_id': data['reviewer_id']})
        return dict(c.execute('SELECT * FROM reviews WHERE id=?', (cur.lastrowid,)).fetchone())


@db.consistent_read
def list_reviews(c, u, p):
    access(c, u, p)
    return [dict(row) for row in c.execute('''SELECT v.*, r.uid, r.title,
        a.name AS submitter_name, b.name AS reviewer_name FROM reviews v
        JOIN requirements r ON r.id=v.requirement_id JOIN users a ON a.id=v.submitted_by
        JOIN users b ON b.id=v.reviewer_id WHERE r.project_id=? ORDER BY v.id DESC''', (p,))]


def decide_review(c, u, review_id, data):
    with db.transaction(c):
        row = c.execute('SELECT * FROM reviews WHERE id=?', (review_id,)).fetchone()
        if row is None:
            _error(404, '评审不存在')
        req = _req(c, row['requirement_id'])
        access(c, u, req['project_id'], APPROVERS)
        if row['submitted_by'] == u['id'] or row['reviewer_id'] != u['id']:
            _error(403, '只有指定的独立评审人可以作出决定')
        if row['status'] != 'pending' or req['status'] != 'in_review':
            _error(409, '评审已处理或需求不再处于待评审状态')
        _expected(req, row['revision'])
        decision = data['decision']
        if decision not in ('approved', 'rejected'):
            _error(422, '评审决定无效')
        if decision == 'approved':
            _quality(req)
        _execute(c, 'UPDATE reviews SET status=?,comment=?,decided_at=? WHERE id=?',
                 (decision, data.get('comment', ''), now(), review_id))
        _replace(c, u, req, status='approved' if decision == 'approved' else 'draft')
        _audit(c, u, req['project_id'], 'review.' + decision, 'review', review_id,
               {'requirement_id': req['id'], 'reviewed_revision': row['revision'], 'comment': data.get('comment', '')})
        return dict(c.execute('SELECT * FROM reviews WHERE id=?', (review_id,)).fetchone())


@db.consistent_read
def list_links(c, u, p):
    access(c, u, p)
    return [dict(row) for row in c.execute('''SELECT l.*, s.uid AS source_uid,
        s.title AS source_title, t.uid AS target_uid, t.title AS target_title
        FROM links l JOIN requirements s ON s.id=l.source_id
        JOIN requirements t ON t.id=l.target_id WHERE l.project_id=? ORDER BY l.id''', (p,))]


def create_link(c, u, p, data):
    with db.transaction(c):
        access(c, u, p, EDITORS)
        if data['source_id'] == data['target_id']:
            _error(409, '需求不能关联自身')
        for rid in (data['source_id'], data['target_id']):
            row = c.execute('SELECT project_id,status FROM requirements WHERE id=?', (rid,)).fetchone()
            if row is None or row['project_id'] != p:
                _error(422, '关联两端必须是当前项目需求')
            _assert_live(row)
        if data['kind'] in ('refines', 'depends') and _would_cycle(c, p, data['source_id'], data['target_id']):
            _error(409, '关联将造成分解或依赖环')
        if data['kind'] == 'conflicts' and c.execute(
                "SELECT 1 FROM links WHERE source_id=? AND target_id=? AND kind='conflicts'",
                (data['target_id'], data['source_id'])).fetchone():
            _error(409, '这两个需求已经存在冲突关联')
        cur = _execute(c, 'INSERT INTO links(project_id,source_id,target_id,kind) VALUES (?,?,?,?)',
                       (p, data['source_id'], data['target_id'], data['kind']))
        _audit(c, u, p, 'link.created', 'link', cur.lastrowid, data)
        return next(x for x in list_links(c, u, p) if x['id'] == cur.lastrowid)


def delete_link(c, u, lid):
    with db.transaction(c):
        row = c.execute('SELECT * FROM links WHERE id=?', (lid,)).fetchone()
        if row is None:
            _error(404, '关联不存在')
        access(c, u, row['project_id'], EDITORS)
        _execute(c, 'DELETE FROM links WHERE id=?', (lid,))
        _audit(c, u, row['project_id'], 'link.deleted', 'link', lid, dict(row))
        return {'ok': True}


@db.consistent_read
def list_artifacts(c, u, p):
    access(c, u, p)
    associations = {}
    for row in c.execute('''SELECT al.artifact_id,al.requirement_id FROM artifact_links al
        JOIN artifacts a ON a.id=al.artifact_id WHERE a.project_id=? ORDER BY al.requirement_id''', (p,)):
        associations.setdefault(row['artifact_id'], []).append(row['requirement_id'])
    result = []
    for row in c.execute('SELECT * FROM artifacts WHERE project_id=? ORDER BY id', (p,)):
        item = dict(row)
        item['requirement_ids'] = associations.get(row['id'], [])
        result.append(item)
    return result


def save_artifact(c, u, p, data, artifact_id=None):
    with db.transaction(c):
        access(c, u, p, EDITORS)
        if artifact_id is not None:
            row = c.execute('SELECT project_id,revision FROM artifacts WHERE id=?', (artifact_id,)).fetchone()
            if row is None or row['project_id'] != p:
                _error(404, '当前项目的验证项不存在')
            if data.get('expected_revision') != row['revision']:
                _error(409, '验证项版本已变化，请刷新后重新编辑')
        requirement_ids = sorted(set(data['requirement_ids']))
        for rid in requirement_ids:
            row = c.execute('SELECT project_id,status FROM requirements WHERE id=?', (rid,)).fetchone()
            if row is None or row['project_id'] != p:
                _error(422, '验证项只能关联当前项目的需求')
            _assert_live(row)
        args = (data['kind'], data['title'], data.get('reference', ''), data.get('result', 'not_run'))
        if artifact_id is None:
            cur = _execute(c, 'INSERT INTO artifacts(project_id,kind,title,reference,result) VALUES (?,?,?,?,?)', (p, *args))
            artifact_id = cur.lastrowid
            action = 'artifact.created'
        else:
            _execute(c, 'UPDATE artifacts SET kind=?,title=?,reference=?,result=?,revision=revision+1 WHERE id=? AND revision=?', (*args, artifact_id, data['expected_revision']))
            _execute(c, 'DELETE FROM artifact_links WHERE artifact_id=?', (artifact_id,))
            action = 'artifact.updated'
        for rid in requirement_ids:
            _execute(c, 'INSERT INTO artifact_links(requirement_id,artifact_id) VALUES (?,?)', (rid, artifact_id))
        _audit(c, u, p, action, 'artifact', artifact_id, {'requirement_ids': requirement_ids, 'result': args[3]})
        return next(x for x in list_artifacts(c, u, p) if x['id'] == artifact_id)


@db.consistent_read
def trace(c, u, p):
    reqs = list_requirements(c, u, p, {})
    links, artifacts = list_links(c, u, p), list_artifacts(c, u, p)
    indexed = {x['id']: x for x in reqs}
    parents, children = {}, {}
    for req in reqs:
        if req['parent_id'] in indexed:
            parents.setdefault(req['id'], set()).add(req['parent_id'])
            children.setdefault(req['parent_id'], set()).add(req['id'])
    for link in links:
        if link['kind'] in ('refines', 'depends'):
            parents.setdefault(link['source_id'], set()).add(link['target_id'])
            children.setdefault(link['target_id'], set()).add(link['source_id'])
    result = []
    for req in reqs:
        associated = [a for a in artifacts if req['id'] in a['requirement_ids']]
        info = {key: req[key] for key in ('id', 'uid', 'title', 'status', 'revision')}
        for name, mapping in (('parents', parents), ('children', children)):
            info[name] = [{key: indexed[rid][key] for key in ('id', 'uid', 'title')}
                          for rid in sorted(mapping.get(req['id'], ())) if rid in indexed]
        info['artifacts'] = associated
        info['covered'] = any(a['kind'] == 'test' for a in associated)
        result.append(info)
    return result


def _context(c, u, p, ids):
    ids = set(ids)
    links = [x for x in list_links(c, u, p) if x['source_id'] in ids or x['target_id'] in ids]
    artifacts = []
    for item in list_artifacts(c, u, p):
        linked = sorted(ids.intersection(item['requirement_ids']))
        if linked:
            artifacts.append({**item, 'requirement_ids': linked})
    return links, artifacts


@db.consistent_read
def list_baselines(c, u, p):
    access(c, u, p)
    return [dict(row) for row in c.execute('''SELECT b.*, u.name AS creator_name,
        (SELECT COUNT(*) FROM baseline_items i WHERE i.baseline_id=b.id) AS item_count
        FROM baselines b JOIN users u ON u.id=b.created_by WHERE b.project_id=? ORDER BY b.id DESC''', (p,))]


def create_baseline(c, u, p, data):
    with db.transaction(c):
        access(c, u, p, EDITORS)
        ids = sorted(set(data.get('requirement_ids', [])))
        scope = 'selected' if ids else 'project'
        if not ids:
            ids = [x['id'] for x in c.execute("SELECT id FROM requirements WHERE project_id=? AND status='approved' ORDER BY id", (p,))]
        if not ids:
            _error(422, '没有可纳入基线的已批准需求')
        reqs = []
        for rid in ids:
            row = c.execute('SELECT project_id,status FROM requirements WHERE id=?', (rid,)).fetchone()
            if row is None or row['project_id'] != p or row['status'] != 'approved':
                _error(422, '基线只能包含当前项目的已批准需求')
            reqs.append(_req(c, rid))
        links, artifacts = _context(c, u, p, ids)
        cur = _execute(c, 'INSERT INTO baselines(project_id,name,scope,created_by,created_at) VALUES (?,?,?,?,?)',
                       (p, data['name'], scope, u['id'], now()))
        bid = cur.lastrowid
        for req in reqs:
            version = c.execute('SELECT snapshot FROM requirement_versions WHERE requirement_id=? AND revision=?', (req['id'], req['revision'])).fetchone()
            if version is None:
                _error(409, '需求版本记录不完整，无法建立基线')
            _execute(c, 'INSERT INTO baseline_items(baseline_id,requirement_id,revision,snapshot) VALUES (?,?,?,?)',
                     (bid, req['id'], req['revision'], version['snapshot']))
        _execute(c, 'INSERT INTO baseline_snapshots(baseline_id,links_json,artifacts_json) VALUES (?,?,?)',
                 (bid, _json(links), _json(artifacts)))
        _audit(c, u, p, 'baseline.created', 'baseline', bid,
               {'name': data['name'], 'requirement_ids': ids, 'links': len(links), 'artifacts': len(artifacts)})
        return get_baseline(c, u, bid)


@db.consistent_read
def get_baseline(c, u, bid):
    row = c.execute('SELECT * FROM baselines WHERE id=?', (bid,)).fetchone()
    if row is None:
        _error(404, '基线不存在')
    access(c, u, row['project_id'])
    result = dict(row)
    result['items'] = []
    for item in c.execute('SELECT requirement_id,revision,snapshot FROM baseline_items WHERE baseline_id=? ORDER BY requirement_id', (bid,)):
        record = dict(item)
        record['snapshot'] = json.loads(record['snapshot'])
        result['items'].append(record)
    context = c.execute('SELECT links_json,artifacts_json FROM baseline_snapshots WHERE baseline_id=?', (bid,)).fetchone()
    result['links'] = json.loads(context['links_json']) if context else []
    result['artifacts'] = json.loads(context['artifacts_json']) if context else []
    return result


@db.consistent_read
def compare_baseline(c, u, bid):
    baseline = get_baseline(c, u, bid)
    current = {x['id']: x for x in list_requirements(c, u, baseline['project_id'], {})}
    ids = {item['requirement_id'] for item in baseline['items']}
    rows = []
    for item in baseline['items']:
        req = current.get(item['requirement_id'])
        snapshot = item['snapshot']
        change = ('archived' if req is None or req['status'] == 'archived'
                  else 'modified' if req['revision'] != item['revision'] else 'unchanged')
        rows.append({'requirement_id': item['requirement_id'], 'uid': snapshot['uid'],
                     'title': snapshot['title'], 'baseline_revision': item['revision'],
                     'current_revision': req['revision'] if req else None, 'change': change})
    # Only project-wide baselines compare membership against today's approved set.
    for req in current.values():
        if baseline['scope'] == 'project' and req['id'] not in ids and req['status'] == 'approved':
            rows.append({'requirement_id': req['id'], 'uid': req['uid'], 'title': req['title'],
                         'baseline_revision': None, 'current_revision': req['revision'], 'change': 'added'})
    links, artifacts = _context(c, u, baseline['project_id'], ids)
    return {'baseline_id': bid, 'name': baseline['name'], 'scope': baseline['scope'], 'rows': rows,
            'links_changed': _json(links) != _json(baseline['links']),
            'artifacts_changed': _json(artifacts) != _json(baseline['artifacts'])}


@db.consistent_read
def list_changes(c, u, p):
    access(c, u, p)
    result = []
    for row in c.execute('''SELECT ch.*, r.uid, r.title AS requirement_title,
        u.name AS submitter_name FROM changes ch JOIN requirements r ON r.id=ch.requirement_id
        JOIN users u ON u.id=ch.submitted_by WHERE r.project_id=? ORDER BY ch.id DESC''', (p,)):
        item = dict(row)
        item['proposed'] = json.loads(item.pop('proposed_json'))
        result.append(item)
    return result


def create_change(c, u, rid, data):
    with db.transaction(c):
        req = _req(c, rid)
        p = req['project_id']
        access(c, u, p, EDITORS)
        _expected(req, data['expected_revision'])
        if req['status'] != 'approved':
            _error(409, '仅已批准需求可以提交变更申请')
        proposed = _fields(c, p, data['proposed'], rid)
        _quality(proposed)
        if all(proposed[key] == req[key] for key in FIELDS):
            _error(422, '变更内容与当前版本相同')
        cur = _execute(c, '''INSERT INTO changes
            (requirement_id,base_revision,title,reason,proposed_json,submitted_by,created_at)
            VALUES (?,?,?,?,?,?,?)''',
            (rid, req['revision'], data['title'], data['reason'], _json(proposed), u['id'], now()))
        _audit(c, u, p, 'change.submitted', 'change', cur.lastrowid,
               {'requirement_id': rid, 'base_revision': req['revision'], 'reason': data['reason']})
        return next(x for x in list_changes(c, u, p) if x['id'] == cur.lastrowid)


@db.consistent_read
def impact(c, u, rid):
    req = _req(c, rid)
    p = req['project_id']
    access(c, u, p)
    reqs = list_requirements(c, u, p, {})
    indexed = {x['id']: x for x in reqs}
    graph = {}
    for item in reqs:
        if item['parent_id'] is not None:
            graph.setdefault(item['parent_id'], set()).add(item['id'])
    for link in list_links(c, u, p):
        graph.setdefault(link['target_id'], set()).add(link['source_id'])
        if link['kind'] == 'conflicts':
            graph.setdefault(link['source_id'], set()).add(link['target_id'])
    visited, pending = {rid}, [rid]
    while pending:
        for next_id in graph.get(pending.pop(), ()):
            if next_id not in visited and next_id in indexed:
                visited.add(next_id)
                pending.append(next_id)
    fields = ('id', 'uid', 'title')
    return {'requirement': {key: req[key] for key in fields},
            'requirements': [{key: indexed[item][key] for key in fields} for item in sorted(visited - {rid})],
            'artifacts': [a for a in list_artifacts(c, u, p) if visited.intersection(a['requirement_ids'])]}


def decide_change(c, u, cid, data):
    with db.transaction(c):
        row = c.execute('SELECT * FROM changes WHERE id=?', (cid,)).fetchone()
        if row is None:
            _error(404, '变更申请不存在')
        req = _req(c, row['requirement_id'])
        p = req['project_id']
        access(c, u, p, APPROVERS)
        if row['submitted_by'] == u['id']:
            _error(403, '变更提交人不能批准或退回自己的申请')
        if row['status'] != 'pending':
            _error(409, '变更申请已经处理')
        decision = data['decision']
        if decision not in ('approved', 'rejected'):
            _error(422, '变更决定无效')
        if decision == 'approved':
            _expected(req, row['base_revision'])
            if req['status'] != 'approved':
                _error(409, '目标需求不再处于已批准状态')
            proposed = _fields(c, p, json.loads(row['proposed_json']), req['id'])
            _quality(proposed)
            _replace(c, u, req, proposed, status='approved')
        _execute(c, 'UPDATE changes SET status=?,decision_comment=?,decided_at=? WHERE id=?',
                 (decision, data.get('comment', ''), now(), cid))
        _audit(c, u, p, 'change.' + decision, 'change', cid,
               {'requirement_id': req['id'], 'base_revision': row['base_revision'],
                'new_revision': req['revision'] + 1 if decision == 'approved' else None,
                'comment': data.get('comment', '')})
        return next(x for x in list_changes(c, u, p) if x['id'] == cid)


@db.consistent_read
def audit_list(c, u, p):
    access(c, u, p)
    return [dict(row) for row in c.execute('''SELECT a.*, u.name AS actor_name
        FROM audit_logs a LEFT JOIN users u ON u.id=a.actor_id
        WHERE a.project_id=? ORDER BY a.id DESC LIMIT 500''', (p,))]


@db.consistent_read
def dashboard(c, u, p):
    reqs = list_requirements(c, u, p, {})
    counts = {'total': len(reqs), 'draft': 0, 'in_review': 0, 'approved': 0, 'archived': 0}
    for req in reqs:
        counts[req['status']] += 1
    traced = [x for x in trace(c, u, p) if x['status'] != 'archived']
    total, linked = len(traced), sum(1 for x in traced if x['covered'])
    return {'counts': counts,
            'pending_reviews': sum(1 for x in list_reviews(c, u, p) if x['status'] == 'pending'),
            'pending_changes': sum(1 for x in list_changes(c, u, p) if x['status'] == 'pending'),
            'baselines': len(list_baselines(c, u, p)),
            'coverage': {'linked': linked, 'total': total, 'percent': round(linked * 100 / total, 1) if total else 0},
            'recent': audit_list(c, u, p)[:12]}


def _csv_cell(value):
    text = '' if value is None else str(value)
    # Spreadsheet importers may ignore leading spaces/control characters before
    # interpreting a formula. Neutralize both the raw and trimmed first token.
    stripped = text.lstrip(' \t\r\n\v\f\ufeff')
    if text.startswith(('\t', '\r', '\n')) or stripped.startswith(('=', '+', '-', '@')):
        return "'" + text
    return text


@db.consistent_read
def export_csv(c, u, p, kind):
    access(c, u, p)
    out = io.StringIO(newline='')
    writer = csv.writer(out)
    if kind == 'requirements':
        writer.writerow(['编号', '标题', '描述', '来源', '理由', '类型', '优先级', '状态', '负责人', '验收标准', '标签', '版本'])
        for req in list_requirements(c, u, p, {}):
            values = [req[k] for k in ('uid', 'title', 'statement', 'source', 'rationale', 'type', 'priority', 'status', 'owner_name', 'acceptance')]
            values.extend([','.join(req['tags']), req['revision']])
            writer.writerow([_csv_cell(value) for value in values])
    elif kind == 'trace':
        writer.writerow(['编号', '标题', '状态', '版本', '上游需求', '下游需求', '设计项', '测试项', '测试已关联'])
        for item in trace(c, u, p):
            values = [item['uid'], item['title'], item['status'], item['revision'],
                      '; '.join(x['uid'] for x in item['parents']), '; '.join(x['uid'] for x in item['children']),
                      '; '.join(x['title'] for x in item['artifacts'] if x['kind'] == 'design'),
                      '; '.join(x['title'] for x in item['artifacts'] if x['kind'] == 'test'),
                      '是' if item['covered'] else '否']
            writer.writerow([_csv_cell(value) for value in values])
    else:
        _error(422, '导出类型必须为 requirements 或 trace')
    # The HTTP adapter adds a single UTF-8 BOM for spreadsheet compatibility.
    return out.getvalue()
