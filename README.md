# ReqFlow 需求管理系统

面向课程项目的完整本地需求管理应用。浏览器界面连接真实 FastAPI API，数据持久化到 SQLite。示例需求集是校园实验室预约系统；该需求集中的初始审批状态和测试项结果均为教学样例，项目自动化测试结果位于 evidence。

## 启动

需要 Python 3.12 或以上版本。Windows 双击 `run.bat`，或在项目目录运行 `powershell -File run.ps1`。首次启动创建 `.venv` 并按 `requirements.lock` 安装依赖，随后访问 http://127.0.0.1:8765 。Ctrl+C 停止。首次访问自动建立 `data/reqflow.db` 并写入演示数据，之后重启保留修改。

其他平台可使用：

```sh
python -m venv .venv
# 激活环境后
python -m pip install -r requirements.lock
python -m uvicorn app.main:app --host 127.0.0.1 --port 8765
```

API说明在 `/docs`；健康检查在 `/api/health`。通过 `REQFLOW_DB` 环境变量可选择独立数据库文件。请在服务停止后备份数据库；保留默认库即可保留演示修改。

## 演示账号

| 用户名 | 密码 | 职责 |
|---|---|---|
| analyst | AnalystDemo2026! | 需求创建、编辑、提交、追踪、基线、变更申请 |
| reviewer | ReviewDemo2026! | 需求评审与变更审批 |
| admin | AdminDemo2026! | 全局用户/项目成员管理，并作为演示项目管理员 |
| viewer | ViewerDemo2026! | 只读浏览与导出 |

以上账号仅用于这个本地教学实例。服务绑定回环地址。界面提供演示角色填入按钮，切换角色仍通过真实登录验证。全局管理员的数据访问也遵守项目成员资格。

## 完整操作示例

1. 以 analyst 登录，在需求库中新建需求，填写来源和验收标准。
2. 添加需求关联，并在追踪模块创建测试验证项、关联该需求。
3. 在详情提交给 reviewer，退出后以 reviewer 登录，批准该需求。
4. 切回 analyst，为已批准需求建立基线。可选全部已批准需求或明确指定需求集合。
5. 对已批准需求提出修改申请，查看受影响的下游需求和验证项。
6. 以 reviewer 批准变更。需求产生新版本，原基线仍保持原内容。
7. 查看基线比较、追踪矩阵和审计日志，导出CSV。

提交人和审批人必须不同。待评审内容不可编辑；批准内容通过变更申请修改。每次内容或生命周期状态变化都会生成不可变版本。归档仅适用于草稿。过期版本操作返回409并提示刷新。

## 验证

本次交付的实际验证：50项自动化测试通过，Python语句覆盖率94.20%；Microsoft Edge浏览器16项界面验收通过。已脱敏的验证记录与截图在 `evidence/final`，修订前失败证据、问题原因和处理过程见 `docs/quality-review.md`。覆盖率不包含前端JavaScript，浏览器验收与API测试分别计数。

```sh
python -m pytest tests -q --cov=app --cov-report=term
```

浏览器验证需要 Microsoft Edge。脚本通过真实界面创建和修改数据，会操作它所连接的服务，因此应先在独立终端启动专用验证库：

```powershell
$env:REQFLOW_DB = Join-Path (Get-Location) '.test-tmp\browser-check.db'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8766
```

再在另一终端执行：

```powershell
.\.venv\Scripts\python.exe scripts/browser_check.py --base-url http://127.0.0.1:8766 --output evidence/browser-recheck
```

完成后停止专用服务。脚本通过Playwright控制真实界面，输出JSON验收结果和截图。API测试则为每个用例建立独立临时数据库，不操作默认演示库。

Windows受限执行环境下，若 pytest 临时目录不可写，可新建 `.test-tmp` 并指定 `--basetemp=.test-tmp/run-日期时间`；若沙箱阻止TestClient事件循环，需在允许本机测试运行的终端执行。环境启动错误与代码断言失败在证据中分别保存。

## 架构与约束

- `app/main.py`：路由、会话、HTTP输入及安全边界。
- `app/service.py`：项目权限、状态机、追踪遍历、事务和业务规则。
- `app/db.py`：表结构、外键、历史不可变触发器、事务。
- `app/schemas.py`：请求类型、长度、枚举及拒绝多余字段。
- `app/security.py`：scrypt口令摘要、随机会话及过期。
- `app/static/`：中文页面、布局和同源API调用。
- `tests/`：正常流程、安全边界、数据不变量和审查回归。
- `docs/`：接口契约、代码审查、迭代与协作记录。

本项目不包含公网部署、SSO、外部代码库同步或工业级高并发承诺。追踪覆盖率表示“已关联测试项的有效需求比例”，不等于测试通过率或需求正确率。变更影响结果基于已经录入的关系图，无法推断尚未建立的关联。

## AI辅助开发说明

grill 与 architect 来自 SethGammon/Citadel v1.4.2。grill用于澄清业务选择，实际确认了禁止自审；architect用于技术选型比较、文件结构、数据模型和分阶段验收设计。通过本会话的多智能体工具完成研究、业务实现、界面实现、独立审查和报告制作。没有运行Citadel的Archon/Fleet编排框架，应用运行时也不需要模型API。

分析对象 StrictDoc 的事实、与本系统的区别及引用见本地课程交付的作业2-1报告（不包含在此公开仓库）。用户权限、独立审批、基线和变更流程为本系统自主设计。

## 公开仓库内容

需求说明见 [PRD](docs/planning/prd-reqflow.md)，架构设计见 [架构文档](docs/planning/architecture-reqflow.md)。本仓库包含应用、自动化测试、浏览器验证脚本和开发审查记录；启动时由代码生成教学数据，不需要下载数据库。截图中的“林同学”“陈同学”及演示账号均为教学 fixture。

公开验证证据仅对本机绝对路径和 JUnit 计算机名进行脱敏，测试结果、覆盖率、时间、失败断言、浏览器步骤和截图未作改写；详见 [证据说明](evidence/README.md)。运行数据库、会话、虚拟环境和缓存均未发布。源码快照与其原始 SHA256 清单保留，用于复现修订前行为；清单对应各自快照，不是公开目录当前文件的校验清单。
