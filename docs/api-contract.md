# ReqFlow API contract v1

Base /api. JSON requests/responses. Errors {detail: string}. IDs integers. Auth cookie plus csrf in X-CSRF-Token for all POST/PATCH/DELETE except login. Same origin. login returns {user:{id,username,name,is_admin},csrf}; GET /auth/me same. All array endpoints return arrays directly.

## Final contract amendments

CSRF applies to PUT as well. Every content change or lifecycle transition increments requirement revision; always use current server revision. Global admin also needs project membership to read project data. Archive is draft-only.
Artifacts include integer `revision`; PATCH /artifacts/{id} requires `expected_revision` plus all editable ArtifactBody fields. Stale writes return 409.
Baselines include `scope` (`selected` for explicit IDs, `project` for an empty ID list at creation). The selected scope compares only frozen members; project scope can also report newly approved members as added. compare returns scope too. Coverage means test-item linkage, not execution success.

- POST /auth/login {username,password}; POST /auth/logout {}; GET /auth/me
- GET /users -> [{id,username,name,is_admin}]; POST /users {username,name,password,is_admin:false} admin only
- GET /projects -> [{id,name,description,role}]; POST /projects {name,description}
- GET /projects/{p}/members -> [{user_id,username,name,role}]; PUT /projects/{p}/members/{u} {role} global admin
- GET /projects/{p}/dashboard -> {counts:{total,draft,in_review,approved,archived},pending_reviews,pending_changes,baselines,coverage:{linked,total,percent},recent:[audit]}
- GET /projects/{p}/documents -> [{id,title,description}]; POST same {title,description}
- GET /projects/{p}/requirements?q=&status=&type=&priority= -> array; POST same body as below
- GET /requirements/{id} -> requirement plus versions:[{revision,snapshot,created_by,created_at}],links:[link with source_uid,target_uid,source_title,target_title],artifacts:[artifact],reviews:[review]
- PATCH /requirements/{id} body as below + expected_revision. Only draft mutable.
- POST /requirements/{id}/archive {expected_revision}; POST /requirements/{id}/submit {expected_revision,reviewer_id}
- GET /projects/{p}/reviews -> [{id,requirement_id,uid,title,revision,submitted_by,submitter_name,reviewer_id,reviewer_name,status,comment,created_at}]
- POST /reviews/{id}/decide {decision:'approved'|'rejected',comment:''}
- GET /projects/{p}/links -> array; POST same {source_id,target_id,kind:'refines'|'depends'|'conflicts'}; DELETE /links/{id}
- GET /projects/{p}/artifacts -> [{id,kind:'design'|'test',title,reference,result:'not_run'|'passed'|'failed',requirement_ids:[]}]
- POST /projects/{p}/artifacts {kind,title,reference,result,requirement_ids:[]}; PATCH /artifacts/{id} same
- GET /projects/{p}/trace -> [{id,uid,title,status,revision,parents:[{uid,title}],children:[{uid,title}],artifacts:[artifact],covered:bool}]
- GET /projects/{p}/baselines -> [{id,name,created_at,creator_name,item_count}]; POST same {name,requirement_ids:[]} empty means all approved
- GET /baselines/{id} -> {id,name,project_id,created_at,items:[{requirement_id,revision,snapshot}],links:[],artifacts:[]}
- GET /baselines/{id}/compare -> {baseline_id,name,rows:[{requirement_id,uid,title,baseline_revision,current_revision,change:'unchanged'|'modified'|'added'|'archived'}],links_changed:bool,artifacts_changed:bool}
- GET /projects/{p}/changes -> [{id,requirement_id,uid,requirement_title,base_revision,title,reason,proposed,submitted_by,submitter_name,status,decision_comment,created_at}]
- POST /requirements/{id}/changes {expected_revision,title,reason,proposed:{title,statement,source,rationale,type,priority,owner_id,acceptance,tags,document_id,parent_id}} approved only
- GET /requirements/{id}/impact -> {requirement:{id,uid,title},requirements:[{id,uid,title}],artifacts:[artifact]}
- POST /changes/{id}/decide {decision:'approved'|'rejected',comment:''}
- GET /projects/{p}/audit -> [{id,actor_name,action,entity_type,entity_id,detail,created_at}]
- GET /projects/{p}/export?kind=requirements|trace -> CSV download (cookie auth)

Requirement: {id,project_id,document_id,uid,parent_id,title,statement,source,rationale,type:'functional'|'nonfunctional'|'constraint',priority:'must'|'should'|'could',status:'draft'|'in_review'|'approved'|'archived',owner_id,owner_name,acceptance,tags:[],revision,created_by,updated_at}. POST accepts uid (optional generated),document_id(optional),parent_id(optional),title,statement,source,rationale,type,priority,owner_id(optional),acceptance,tags. For PATCH use complete editable fields; revision in expected_revision. Reviews separate author/submitter and approver: submitted_by != current user and reviewer_id == current user; global admin role does not bypass self review. Reviewer role may create change? analyst/admin create, reviewer/admin decide.

Demo users: admin / AdminDemo2026!, analyst / AnalystDemo2026!, reviewer / ReviewDemo2026!, viewer / ViewerDemo2026!. Initial login recommended analyst. Global admin assigned project admin; analyst and reviewer independent. Browser login must be actual login, no fake frontend auth. Every write persistent, server checked, escaped UI content. Network loading/error/empty states required.
