"""Exercise the real UI with independent analyst/reviewer sessions.

Usage: .venv/Scripts/python scripts/browser_check.py --base-url http://127.0.0.1:8765
Requires the server to be running with demo users. Uses installed Microsoft Edge;
no browser download, browser storage injection, or direct API mutations.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]


def run(base_url: str, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    suffix = datetime.now(timezone.utc).strftime("%H%M%S") + uuid4().hex[:4]
    uid = f"UI-{suffix}"
    title = f"设备借用预约验收 · {suffix}"
    baseline_name = f"浏览器验收基线 · {suffix}"
    change_title = f"调整设备预约提前量 · {suffix}"
    artifact_title = f"设备预约边界验证 · {suffix}"
    started = datetime.now(timezone.utc).isoformat()
    result = {
        "started_at": started,
        "base_url": base_url,
        "browser": "Microsoft Edge (headless, Playwright)",
        "requirement_uid": uid,
        "steps": [],
        "console_errors": [],
        "http_errors": [],
        "screenshots": [],
        "passed": False,
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1000}, locale="zh-CN")
        page = context.new_page()
        page.set_default_timeout(15000)
        page.on("pageerror", lambda error: result["console_errors"].append(str(error)))

        def track_http(response):
            if response.status >= 400 and "/api/" in response.url:
                # Anonymous boot probes /auth/me by design.
                if response.status == 401 and response.url.endswith("/api/auth/me"):
                    return
                result["http_errors"].append({"status": response.status, "url": response.url})

        page.on("response", track_http)

        def step(name):
            result["steps"].append({"name": name, "passed": True, "at": datetime.now(timezone.utc).isoformat()})

        def screenshot(name):
            path = output / name
            expect(page.locator(".toast")).to_have_count(0, timeout=8000)
            modal_open = page.locator("#modal").is_visible()
            page.screenshot(path=str(path), full_page=not modal_open, animations="disabled")
            result["screenshots"].append(str(path.relative_to(ROOT)))

        def nav(view, heading):
            if page.viewport_size["width"] <= 760:
                page.get_by_role("button", name="展开导航", exact=True).click()
            page.locator(f'.nav-button[data-id="{view}"]').click()
            expect(page.get_by_role("heading", name=heading, exact=True)).to_be_visible()

        def login(role):
            if page.locator('[data-action="logout"]').count():
                page.get_by_role("button", name="退出", exact=True).click()
            expect(page.get_by_role("heading", name="登录需求工作台", exact=True)).to_be_visible()
            page.locator(f'[data-action="demo-account"][data-id="{role}"]').click()
            page.get_by_role("button", name="登录工作台", exact=True).click()
            expect(page.get_by_role("heading", name="需求概览", exact=True)).to_be_visible()

        def modal_closed():
            expect(page.locator("#modal")).not_to_be_visible()

        def req_row():
            return page.locator("tbody tr").filter(has=page.locator(".req-id", has_text=uid))

        try:
            page.goto(base_url, wait_until="networkidle")
            expect(page.get_by_role("heading", name="登录需求工作台", exact=True)).to_be_visible()
            screenshot("00-login.png")
            login("analyst")
            screenshot("01-dashboard.png")
            step("分析员登录真实后端，仪表盘加载成功")

            nav("requirements", "需求管理")
            page.get_by_role("button", name="新建需求", exact=True).first.click()
            page.locator('#requirement-form [name="uid"]').fill(uid)
            page.locator('#requirement-form [name="title"]').fill(title)
            page.locator('#requirement-form [name="statement"]').fill("学生应至少提前30分钟预约可借用设备，预约成功后生成唯一预约编号。")
            page.locator('#requirement-form [name="source"]').fill("浏览器端到端验收场景")
            page.locator('#requirement-form [name="rationale"]').fill('让设备准备时间和预约规则可以被独立验证。转义验收：<img src=x onerror=alert(1)>')
            page.locator('#requirement-form [name="acceptance"]').fill("提前30分钟可预约；提前29分钟应拒绝，并显示时间要求。")
            page.locator('#requirement-form [name="tags"]').fill("浏览器验收,预约规则")
            page.get_by_role("button", name="创建需求", exact=True).click()
            modal_closed()
            expect(req_row()).to_be_visible()
            expect(req_row()).to_contain_text("草稿")
            step("通过需求表单创建草稿并确认列表持久化")

            req_row().get_by_role("button", name=title, exact=True).click()
            page.get_by_role("button", name="提交评审", exact=True).click()
            reviewer_select = page.locator('#submit-review-form [name="reviewer_id"]')
            expect(reviewer_select).to_be_visible()
            reviewer_label = next(x for x in reviewer_select.locator("option").all_text_contents() if "（评审员）" in x)
            reviewer_select.select_option(label=reviewer_label)
            page.locator('button[form="submit-review-form"]').click()
            modal_closed()
            expect(req_row()).to_contain_text("评审中")
            screenshot("02-requirements.png")
            step("草稿提交给独立评审员，列表显示评审中")

            nav("reviews", "需求评审")
            own_review = page.locator(".item-card").filter(has=page.get_by_role("heading", name=title, exact=True))
            expect(own_review).to_contain_text("由其他成员独立评审")
            expect(own_review.get_by_role("button", name="批准", exact=True)).to_have_count(0)
            step("提交人界面没有自审按钮")

            login("reviewer")
            nav("reviews", "需求评审")
            review_card = page.locator(".item-card").filter(has=page.get_by_role("heading", name=title, exact=True))
            review_card.get_by_role("button", name="查看需求", exact=True).click()
            expect(page.locator("#modal")).to_contain_text("提前30分钟可预约")
            expect(page.locator("#modal")).to_contain_text("<img src=x onerror=alert(1)>")
            expect(page.locator("#modal img")).to_have_count(0)
            step("需求中的HTML样式输入按普通文字呈现，不执行或创建标签")
            page.get_by_role("button", name="关闭", exact=True).click()
            review_card.get_by_role("button", name="批准", exact=True).click()
            page.locator('#decision-form [name="comment"]').fill("验收边界清晰，批准进入基线。")
            page.get_by_role("button", name="确认批准", exact=True).click()
            modal_closed()
            page.locator('[data-action="review-filter"][data-id="approved"]').click()
            expect(page.locator(".item-card").filter(has=page.get_by_role("heading", name=title, exact=True))).to_contain_text("已批准")
            screenshot("03-independent-review.png")
            step("切换指定评审员，查看需求后独立批准")

            login("analyst")
            nav("trace", "追踪与验证")
            page.get_by_role("button", name="新建验证项", exact=True).first.click()
            page.locator('#artifact-form [name="title"]').fill(artifact_title)
            page.locator('#artifact-form [name="reference"]').fill("TEST-UI-BOUNDARY")
            page.locator('#artifact-form [name="result"]').select_option("passed")
            page.locator("#artifact-form .checkbox-option").filter(has_text=uid).get_by_role("checkbox").check()
            page.get_by_role("button", name="保存验证项", exact=True).click()
            modal_closed()
            expect(page.locator("tbody tr").filter(has_text=uid)).to_contain_text("已覆盖")
            step("新建关联测试项，追踪矩阵显示覆盖证据")

            # Editing verifies that the client sends the artifact revision token.
            page.get_by_role("button", name="设计与测试", exact=True).click()
            artifact_row = page.locator("tbody tr").filter(has_text=artifact_title)
            artifact_row.get_by_role("button", name="编辑", exact=True).click()
            page.locator('#artifact-form [name="reference"]').fill("TEST-UI-BOUNDARY-UPDATED")
            page.get_by_role("button", name="保存验证项", exact=True).click()
            modal_closed()
            expect(artifact_row).to_contain_text("TEST-UI-BOUNDARY-UPDATED")
            screenshot("04-traceability.png")
            step("编辑验证项并使用版本号完成乐观锁更新")

            nav("baselines", "版本基线")
            page.get_by_role("button", name="创建基线", exact=True).first.click()
            page.locator('#baseline-form [name="name"]').fill(baseline_name)
            for checkbox in page.locator('#baseline-form input[type="checkbox"]').all():
                checkbox.uncheck()
            page.locator("#baseline-form .checkbox-option").filter(has_text=uid).get_by_role("checkbox").check()
            page.get_by_role("button", name="创建并冻结", exact=True).click()
            modal_closed()
            baseline_card = page.locator(".baseline-card").filter(has=page.get_by_role("heading", name=baseline_name, exact=True))
            expect(baseline_card).to_be_visible()
            baseline_card.get_by_role("button", name="对比当前", exact=True).click()
            expect(page.locator("#modal tbody tr")).to_have_count(1)
            expect(page.locator("#modal tbody tr")).to_contain_text("未变化")
            page.get_by_role("button", name="关闭", exact=True).click()
            step("冻结指定批准需求基线，未误报其他既存需求为新增")

            nav("changes", "变更控制")
            page.get_by_role("button", name="发起变更", exact=True).first.click()
            change_select = page.locator('#select-change-form [name="requirement_id"]')
            expect(change_select).to_be_visible()
            requirement_label = next(x for x in change_select.locator("option").all_text_contents() if x.startswith(uid + " ·"))
            change_select.select_option(label=requirement_label)
            page.get_by_role("button", name="下一步：填写变更", exact=True).click()
            page.locator('#change-form [name="change_title"]').fill(change_title)
            page.locator('#change-form [name="change_reason"]').fill("设备准备需增加检查时间，将提前量从30分钟调整为60分钟。")
            page.locator('#change-form [name="statement"]').fill("学生应至少提前60分钟预约可借用设备，预约成功后生成唯一预约编号。")
            page.locator('#change-form [name="acceptance"]').fill("提前60分钟可预约；提前59分钟应拒绝，并显示时间要求。")
            page.get_by_role("button", name="提交变更申请", exact=True).click()
            modal_closed()
            change_card = page.locator(".item-card").filter(has=page.get_by_role("heading", name=change_title, exact=True))
            expect(change_card).to_contain_text("待处理")
            expect(change_card.get_by_role("button", name="批准变更", exact=True)).to_have_count(0)
            change_card.get_by_role("button", name="影响分析", exact=True).click()
            expect(page.locator("#modal")).to_contain_text(artifact_title)
            screenshot("05-change-impact.png")
            page.get_by_role("button", name="关闭", exact=True).click()
            step("提交变更并查看关联测试影响；提交人没有自批入口")

            login("reviewer")
            nav("changes", "变更控制")
            change_card = page.locator(".item-card").filter(has=page.get_by_role("heading", name=change_title, exact=True))
            change_card.get_by_role("button", name="变更详情", exact=True).click()
            expect(page.locator("#modal")).to_contain_text("提前60分钟可预约")
            page.locator("#modal").get_by_role("button", name="批准变更", exact=True).click()
            page.locator('#decision-form [name="comment"]').fill("同意提前量调整，后续重新执行边界测试。")
            page.get_by_role("button", name="确认批准", exact=True).click()
            modal_closed()
            page.locator('[data-action="change-filter"][data-id="approved"]').click()
            expect(page.locator(".item-card").filter(has=page.get_by_role("heading", name=change_title, exact=True))).to_contain_text("已批准")
            step("另一成员审查拟修改内容并批准变更")

            nav("baselines", "版本基线")
            baseline_card = page.locator(".baseline-card").filter(has=page.get_by_role("heading", name=baseline_name, exact=True))
            baseline_card.get_by_role("button", name="对比当前", exact=True).click()
            expect(page.locator("#modal tbody tr")).to_have_count(1)
            expect(page.locator("#modal tbody tr")).to_contain_text("已修改")
            screenshot("06-baseline-comparison.png")
            page.get_by_role("button", name="关闭", exact=True).click()
            baseline_card.get_by_role("button", name="查看快照", exact=True).click()
            page.locator("#modal details summary").first.click()
            expect(page.locator("#modal")).to_contain_text("提前30分钟可预约")
            expect(page.locator("#modal")).not_to_contain_text("提前60分钟可预约")
            page.get_by_role("button", name="关闭", exact=True).click()
            step("比较显示版本已修改，原基线仍保留30分钟验收标准")

            nav("requirements", "需求管理")
            req_row().get_by_role("button", name=title, exact=True).click()
            expect(page.locator("#modal")).to_contain_text("提前60分钟可预约")
            expect(page.locator("#modal")).to_contain_text("历史版本")
            screenshot("07-version-history.png")
            page.get_by_role("button", name="关闭", exact=True).click()
            with page.expect_download() as download_info:
                page.get_by_role("link", name="导出 CSV", exact=True).click()
            download = download_info.value
            csv_path = output / "browser-requirements.csv"
            download.save_as(str(csv_path))
            if uid not in csv_path.read_text(encoding="utf-8-sig"):
                raise AssertionError("Downloaded CSV does not contain the new requirement")
            step("当前需求显示新版本，CSV导出包含真实新增记录")

            login("viewer")
            nav("requirements", "需求管理")
            expect(page.get_by_role("button", name="新建需求", exact=True)).to_have_count(0)
            req_row().get_by_role("button", name=title, exact=True).click()
            expect(page.locator("#modal").get_by_role("button", name="编辑需求", exact=True)).to_have_count(0)
            expect(page.locator("#modal").get_by_role("button", name="发起变更", exact=True)).to_have_count(0)
            page.get_by_role("button", name="关闭", exact=True).click()
            step("观察员能够阅读需求且没有维护或变更操作入口")

            page.set_viewport_size({"width": 390, "height": 844})
            nav("dashboard", "需求概览")
            screenshot("08-mobile-dashboard.png")
            body_width = page.locator("body").bounding_box()["width"]
            if body_width > 390:
                raise AssertionError(f"Mobile body overflows viewport: {body_width}")
            step("390px窄屏导航及仪表盘可用")

            page.set_viewport_size({"width": 1440, "height": 1000})
            nav("audit", "审计记录")
            expect(page.locator("tbody")).to_contain_text("批准变更")
            screenshot("09-audit-trail.png")
            step("审计列表记录完整需求、评审与变更操作")

            if result["console_errors"] or result["http_errors"]:
                raise AssertionError("Browser console or API errors were recorded")
            result["passed"] = True
        except Exception as exc:
            result["failure"] = str(exc) or type(exc).__name__
            result["traceback"] = traceback.format_exc()
            try:
                screenshot("browser-failure.png")
            except Exception:
                pass
        finally:
            result["finished_at"] = datetime.now(timezone.utc).isoformat()
            (output / "browser.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            context.close()
            browser.close()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence" / "final")
    args = parser.parse_args()
    report = run(args.base_url, args.output.resolve())
    print(json.dumps({"passed": report["passed"], "steps": len(report["steps"]), "output": str(args.output), "failure": report.get("failure")}, ensure_ascii=False, indent=2))
    sys.exit(0 if report["passed"] else 1)
