# ReqFlow 实施架构

PRD：docs/planning/prd-reqflow.md；日期：2026-10-12。
技能：SethGammon/Citadel v1.4.2 architect。用户“开始完成吧”授权架构与开发。使用本会话多智能体工具执行阶段，不声称启用Archon/Fleet。

## 关键方案对比

1. 后端：选择FastAPI + sqlite3，接口定义与请求校验明确、事务易审查；相较纯http.server减少HTTP边界代码；相较Java/Spring降低本机依赖和交付体积。
2. 前端：选择原生HTML/CSS/JavaScript模块，与后端同源；相较React/Vue减少构建依赖，适合有限页面和直接可运行作业；通过公共请求层和渲染函数约束重复。
3. 存储：SQLite适合本地演示与自动化测试，外键、事务、不可变快照保护业务；PostgreSQL更适合高并发服务但增加部署成本；JSON文件缺少事务不采用。
4. 身份：服务端随机会话、HttpOnly SameSite Cookie、CSRF头、scrypt口令摘要。避免浏览器长期保存访问令牌；生产HTTPS等另行部署。
5. 变更：版本号乐观锁 + BEGIN IMMEDIATE事务 + 评审绑定版本；不能仅依靠前端禁用按钮或覆盖更新。

## 文件树

作业2-2/reqflow/
- README.md、requirements.txt、requirements.lock、run.ps1、run.bat、.gitignore
- app/__init__.py、main.py、db.py、security.py、schemas.py、service.py、seed.py
- app/static/index.html、styles.css、app.js
- tests/test_workflow.py、test_security.py、test_invariants.py
- scripts/browser_check.mjs、scripts/verify.ps1
- docs/api-contract.md、docs/quality-review.md、docs/iteration-log.md、docs/agent-collaboration.md
- evidence/initial/、evidence/final/（真实运行输出与截图，具体清单由运行后生成）
- data/reqflow.db（运行生成，不加入源码包）

## 模块与依赖

main.py处理路由/会话/HTTP边界，调用service；service集中业务规则及事务；db管理schema/连接；security只负责哈希和会话；schemas为输入契约；seed通过一致模型生成示例；前端只通过API访问数据。
禁止路由直接绕过业务服务更新需求版本；前端权限仅作体验提示，后端作最终授权。

## 数据模型

- users(id,username,name,password_hash,is_admin)；sessions(token_hash,user_id,csrf,expires_at)。
- projects(id,name,description)；members(project_id,user_id,role)组成多对多。
- documents(id,project_id,title,description)；requirements(id,project_id,document_id,uid,parent_id,title,statement,source,rationale,type,priority,status,owner_id,acceptance,tags,revision,created_by,updated_at)。
- requirement_versions(id,requirement_id,revision,snapshot,created_by,created_at)以(requirement_id,revision)唯一，不可更新或删除。
- links(id,project_id,source_id,target_id,kind)表示有向依赖/细化/冲突；同项目、无自环，细化/依赖无环。
- artifacts(id,project_id,kind,title,reference,result)；artifact_links(requirement_id,artifact_id)为多对多。
- reviews(id,requirement_id,revision,submitted_by,reviewer_id,status,comment,created_at,decided_at)。
- changes(id,requirement_id,base_revision,title,reason,proposed_json,submitted_by,status,decision_comment,created_at)；批准必须基于未变更版本。
- baselines(id,project_id,name,created_by,created_at)；baseline_items(baseline_id,requirement_id,revision,snapshot)；baseline_snapshots(baseline_id,links_json,artifacts_json)固定完整追踪上下文。
- audit_logs(id,project_id,actor_id,action,entity_type,entity_id,detail,created_at)。

## 实施阶段和验收

Phase 1 契约与设计：完成PRD、API契约、模型；禁止自审规则可从用户答复追溯。
Phase 2 后端与界面并行：接口匹配，种子数据可登录，全部模块可操作。
Phase 3 集成与初版冻结：保存源码哈希与初版快照，核心闭环测试，记录真实结果。
Phase 4 独立审查与受控重设计：审查定位原因，保留修订前后证据，新测试覆盖实际发现的缺陷。
Phase 5 最终验证与报告：API测试、浏览器流程、图表与报告一一对应，docx逐页渲染检查，源码包干净且启动说明可复现。

依赖图：Phase 1 -> (后端 + 前端 + StrictDoc研究 + 模板准备) -> Phase 3 -> Phase 4 -> Phase 5。
主控负责架构、后端和集成；前端代理独立实现界面；研究代理核实StrictDoc并在后期独立审查；报告代理负责模板与报告。所有反馈记录实际任务来源，不伪造其他模型回答。

## 风险及处理

- 自审批/跨项目访问：后端身份与项目角色检查，独立账号负向测试。
- 并发覆盖/过期评审：事务内版本比较，返回409，回归测试。
- 基线误引用当前对象：保存不可变JSON快照、数据库触发器保护，修改后对比验收。
- 跨代理接口偏差：共享docs/api-contract.md，契约变更同步通知，不并行修改同一文件。
- 报告与结果脱节：只引用真实测试记录和截图；未取得课件不声称引用。
- 本机渲染环境：使用已解析bundled runtime及Word只读PDF导出，保留模板结构。

## 实施后架构修订

独立审查与浏览器验证后形成八项真实问题，具体见项目docs/quality-review.md。验证项新增revision乐观锁；基线新增scope集合语义；复合查询用可重入WAL只读快照；文档写权限在事务内复核；凭据字段精确保留空白；请求体按流提前限额。每个HTTP请求拥有独立SQLite连接并配置check_same_thread=False，以适配FastAPI同步线程池；连接从不跨请求共享。上述修订同时反映到API契约、前端和回归用例。
实际浏览器脚本为scripts/browser_check.py，替代最初规划的mjs。回归文件扩充test_redesign.py、test_review_findings.py、test_concurrency.py；conftest.py统一构建独立数据库与登录会话；snapshot.py保留真实快照证据。

交付审查另发现并修复PowerShell 5.1首次缺包探测的终止问题Q09。最终交付未另设verify.ps1：README提供可复现pytest命令，browser_check.py独立执行真实界面验收。最终50项自动化与16项浏览器验收通过，实际覆盖率94.20%；源码及证据随完整项目包交付。
