'use strict';

(() => {
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const attr = esc;
  const icons = {
    dashboard:'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    document:'<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h6"/>',
    review:'<path d="M9 4H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-4"/><rect x="9" y="2" width="6" height="4" rx="1"/><path d="m8 13 3 3 5-6"/>',
    trace:'<rect x="9" y="2" width="6" height="5" rx="1"/><rect x="2" y="17" width="6" height="5" rx="1"/><rect x="16" y="17" width="6" height="5" rx="1"/><path d="M12 7v5M5 17v-5h14v5"/>',
    baseline:'<path d="m12 3 10 5-10 5L2 8l10-5zM2 12l10 5 10-5M2 16l10 5 10-5"/>',
    change:'<path d="M20 7H7l4-4M4 17h13l-4 4M20 7l-4 4M4 17l4-4"/>',
    audit:'<path d="M3 12a9 9 0 1 0 3-7M3 3v5h5M12 7v5l3 2"/>',
    users:'<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M22 21v-2a4 4 0 0 0-3-3.87"/><circle cx="9" cy="7" r="4"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    plus:'<path d="M12 5v14M5 12h14"/>', search:'<circle cx="10.5" cy="10.5" r="7.5"/><path d="m16 16 5 5"/>',
    down:'<path d="m6 9 6 6 6-6"/>', arrow:'<path d="M5 12h14m-5-5 5 5-5 5"/>', chevron:'<path d="m9 5 7 7-7 7"/>',
    download:'<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>',
    check:'<path d="m5 12 4 4L19 6"/>', circlecheck:'<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    link:'<path d="M10 13a5 5 0 0 0 7 .1l3-3a5 5 0 0 0-7-7l-1.7 1.7M14 11a5 5 0 0 0-7-.1l-3 3a5 5 0 0 0 7 7l1.7-1.7"/>',
    folder:'<path d="M3 7V5a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z"/>',
    info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
    edit:'<path d="m15 5 4 4M4 16l12-12a2.8 2.8 0 0 1 4 4L8 20l-5 1z"/>',
    empty:'<path d="m3 7 9-4 9 4v11l-9 4-9-4V7zM3 7l9 4 9-4M12 11v11M7 5l10 4"/>',
    close:'<path d="m6 6 12 12M6 18 18 6"/>', menu:'<path d="M3 6h18M3 12h18M3 18h18"/>',
    test:'<path d="M9 3h6M10 3v6L4 19a1.4 1.4 0 0 0 1.2 2h13.6a1.4 1.4 0 0 0 1.2-2L14 9V3M7 15h10"/>',
    shield:'<path d="m12 2 9 4v6c0 5-9 10-9 10S3 17 3 12V6zM8 12l3 3 5-6"/>',
    logout:'<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
    archive:'<path d="M3 3h18v5H3zM5 8v13h14V8M10 12h4"/>',
  };
  const icon = name => `<svg viewBox="0 0 24 24" aria-hidden="true">${icons[name] || icons.document}</svg>`;
  const labels = {draft:'草稿',in_review:'评审中',approved:'已批准',archived:'已归档',pending:'待处理',rejected:'已退回',passed:'通过',failed:'失败',not_run:'未执行',functional:'功能需求',nonfunctional:'非功能需求',constraint:'约束',must:'必须',should:'应有',could:'可选',admin:'管理员',analyst:'分析员',reviewer:'评审员',viewer:'观察员',refines:'分解',depends:'依赖',conflicts:'冲突',design:'设计项',test:'测试项',unchanged:'未变化',modified:'已修改',added:'新增加'};
  const titleOf = key => labels[key] || key || '—';
  const badge = key => `<span class="badge ${attr(Object.hasOwn(labels,key) ? key : 'draft')}">${esc(titleOf(key))}</span>`;
  const priority = key => `<span class="priority ${attr(['must','should','could'].includes(key) ? key : '')}"><i></i>${esc(titleOf(key))}</span>`;
  const fmtDate = (value, short = false) => { if (!value) return '—'; const d = new Date(value); return Number.isNaN(d.getTime()) ? esc(value) : d.toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',month:'2-digit',day:'2-digit',...(short ? {} : {year:'numeric'}),hour:'2-digit',minute:'2-digit',hour12:false}); };
  const state = {user:null,csrf:null,projects:[],project:null,view:'dashboard',members:[],documents:[],requirements:[],artifacts:[],links:[],reviews:[],changes:[],baselines:[],docFilter:'',filters:{q:'',status:'',type:'',priority:''},traceTab:'matrix',reviewFilter:'pending',changeFilter:'pending',modalContext:null,loadSequence:0};
  const navItems = [['dashboard','dashboard','总览仪表盘'],['requirements','document','需求管理'],['reviews','review','需求评审'],['trace','trace','追踪与验证'],['baselines','baseline','版本基线'],['changes','change','变更控制'],['audit','audit','审计记录'],['members','users','项目成员']];
  const currentProject = () => state.projects.find(p => Number(p.id) === Number(state.project));
  const role = () => currentProject()?.role || 'viewer';
  const canWrite = () => ['admin','analyst'].includes(role());
  const canReview = () => ['admin','reviewer'].includes(role());
  const endpoint = name => `/projects/${state.project}/${name}`;
  const btn = (text,action,id='',kind='btn',ico='') => `<button type="button" class="${kind}" data-action="${attr(action)}"${!text ? ` aria-label="${attr({'new-document':'新建需求文档','mobile-menu':'展开导航'}[action] || action)}"` : ''}${id === '' ? '' : ` data-id="${attr(id)}"`}>${ico ? icon(ico) : ''}${esc(text)}</button>`;
  const exportBtn = (kind='requirements') => `<a class="btn" href="/api/projects/${Number(state.project)}/export?kind=${attr(kind)}" download>${icon('download')}导出 CSV</a>`;
  const empty = (title,description='',action='') => `<div class="empty">${icon('empty')}<strong>${esc(title)}</strong><p>${esc(description)}</p>${action}</div>`;
  const loading = () => '<div class="loading"><span class="spinner"></span>正在加载数据…</div>';
  const reqLink = (r, extra='') => `<button type="button" class="btn-link req-title ${extra}" data-action="requirement-detail" data-id="${Number(r.id)}">${esc(r.title)}</button>`;
  const statusPill = (text,cls='draft') => `<span class="badge ${attr(cls)}">${esc(text)}</span>`;
  const option = (value,text,current) => `<option value="${attr(value)}"${String(value) === String(current ?? '') ? ' selected' : ''}>${esc(text)}</option>`;
  const options = (list,current) => list.map(key => option(key,titleOf(key),current)).join('');

  async function api(path,method='GET',body) {
    const headers = {'Accept':'application/json'};
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (method !== 'GET' && state.csrf) headers['X-CSRF-Token'] = state.csrf;
    const response = await fetch(`/api${path}`,{method,headers,credentials:'same-origin',...(body === undefined ? {} : {body:JSON.stringify(body)})});
    let data;
    try { data = await response.json(); } catch { data = null; }
    if (!response.ok) {
      if (response.status === 401 && path !== '/auth/login' && path !== '/auth/me') {
        state.user = null;
        closeModal();
        renderLogin('登录已过期，请重新登录。');
      }
      const detail = data?.detail;
      const message = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(d => `${d.loc?.slice(1).join('.') || '字段'}：${d.msg}`).join('；') : `请求失败（${response.status}），请稍后重试。`;
      throw new Error(message);
    }
    return data;
  }
  function toast(message,error=false) {
    const item = document.createElement('div');
    item.className = `toast${error ? ' error' : ''}`;
    item.innerHTML = `${icon(error ? 'info' : 'circlecheck')}<span>${esc(message)}</span>`;
    $('#toast-container').append(item);
    while ($('#toast-container').children.length > 3) $('#toast-container').firstElementChild.remove();
    setTimeout(() => item.remove(),5000);
  }
  function pageHead(eyebrow,title,description,actions='') {
    return `<header class="page-head"><div><div class="eyebrow">${esc(eyebrow)}</div><h1>${esc(title)}</h1><p class="page-description">${esc(description)}</p></div><div class="head-actions">${actions}</div></header>`;
  }
  function panelHead(title,ico='',action='',subtitle='') {
    return `<div class="panel-head"><div><div class="panel-title">${ico ? icon(ico) : ''}${esc(title)}</div>${subtitle ? `<p class="panel-subtitle">${esc(subtitle)}</p>` : ''}</div>${action}</div>`;
  }
  function renderLogin(message='') {
    state.loadSequence++;
    $('#toast-container').replaceChildren();
    document.title = '登录 · ReqFlow';
    $('#app').innerHTML = `<main class="login-page"><section class="login-story"><div class="login-brand"><span class="brand-mark">R</span><div><div class="brand-name">ReqFlow</div><div class="brand-caption">REQUIREMENTS IN FLOW</div></div></div><div class="login-story-content"><div class="login-kicker">从一个需求，到每一次交付</div><h1>让需求清晰，<br>让变更<span>有迹可循。</span></h1><p>连接需求、评审与验证，在同一个工作空间里，管理软件需求的完整生命周期。</p><div class="flow-illustration"><div class="flow-node">${icon('document')}定义需求</div><span>→</span><div class="flow-node">${icon('review')}独立评审</div><span>→</span><div class="flow-node">${icon('baseline')}冻结基线</div><span>→</span><div class="flow-node">${icon('trace')}追踪验证</div></div></div><div class="login-story-footer">系统分析与设计 · 本地演示环境</div></section><section class="login-form-area"><div class="login-form-box"><div class="eyebrow">WELCOME BACK</div><h2>登录需求工作台</h2><p>管理需求的每一个版本，记录每一次决定。</p><form id="login-form"><div class="form-error">${esc(message)}</div><div class="field"><label for="username">用户名</label><input id="username" name="username" autocomplete="username" value="analyst" required maxlength="80"></div><div class="field"><label for="password">密码</label><input id="password" name="password" type="password" autocomplete="current-password" value="AnalystDemo2026!" required maxlength="200"></div><button class="btn btn-primary login-submit" type="submit">登录工作台 ${icon('arrow')}</button></form><div class="demo-accounts"><p>本地演示账号 · 选择角色自动填入账号密码</p><div class="demo-grid">${[['analyst','分析员'],['reviewer','评审员'],['admin','管理员'],['viewer','观察员']].map(([name,label]) => `<button type="button" class="demo-account${name === 'analyst' ? ' active' : ''}" data-action="demo-account" data-id="${name}">${label}<small>${name}</small></button>`).join('')}</div><div class="login-note">演示账号共用同一工作空间。需求与变更由不同成员审批，可退出登录后切换角色体验。</div></div></div></section></main>`;
  }
  async function startSession(data) {
    state.user = data.user; state.csrf = data.csrf;
    state.projects = await api('/projects');
    if (!state.projects.some(p => Number(p.id) === Number(state.project))) state.project = state.projects[0]?.id || null;
    renderShell();
    await loadView();
  }
  function renderShell() {
    document.title = `${navItems.find(n => n[0] === state.view)?.[2] || '工作台'} · ReqFlow`;
    $('#app').innerHTML = `<div class="app-shell"><aside class="sidebar"><div class="brand"><span class="brand-mark">R</span><div><div class="brand-name">ReqFlow</div><div class="brand-caption">REQUIREMENTS IN FLOW</div></div></div><div class="workspace-label">当前工作空间</div><div class="workspace-select"><span class="project-tag">PROJECT</span><label class="sr-only" for="project-select" hidden>切换项目</label><select id="project-select" aria-label="切换工作空间">${state.projects.map(p => option(p.id,p.name,state.project)).join('')}</select></div><nav class="nav" aria-label="主导航">${navItems.map(([view,ico,label],index) => `${index === 6 ? '<div class="nav-separator"></div>' : ''}<button type="button" class="nav-button${view === state.view ? ' active' : ''}" data-action="navigate" data-id="${view}">${icon(ico)}<span>${label}</span></button>`).join('')}</nav><div class="sidebar-bottom"><div class="local-badge"><span class="dot"></span>本地演示环境</div><p>定义 · 评审 · 追踪 · 演进</p></div></aside><div class="main-shell"><header class="topbar"><div class="breadcrumb">${btn('','mobile-menu','','btn btn-ghost icon-button mobile-menu','menu')}<span>工作空间</span>${icon('chevron')}<strong id="breadcrumb-current">${esc(navItems.find(n => n[0] === state.view)?.[2])}</strong></div><div class="top-actions"><span class="environment"><span class="dot"></span>数据实时保存</span><div class="account"><div class="avatar">${esc(state.user.name?.slice(-2) || state.user.username?.slice(0,2))}</div><div><div class="account-name">${esc(state.user.name || state.user.username)}</div><div class="account-role">${esc(titleOf(role()))}</div></div></div>${btn('退出','logout','','signout')}</div></header><main class="content" id="content">${loading()}</main></div></div>`;
  }
  async function navigate(view) {
    if (!navItems.some(n => n[0] === view)) return;
    state.view = view;
    $$('.nav-button').forEach(button => button.classList.toggle('active',button.dataset.id === view));
    $('.sidebar')?.classList.remove('open');
    $('#breadcrumb-current').textContent = navItems.find(n => n[0] === view)[2];
    document.title = `${navItems.find(n => n[0] === view)[2]} · ReqFlow`;
    await loadView();
  }
  async function loadView() {
    const seq = ++state.loadSequence;
    const host = $('#content');
    if (!host || !state.user) return;
    host.innerHTML = loading();
    if (!state.project) {
      host.innerHTML = empty('还没有可访问的工作空间','请联系管理员添加项目成员。',state.user.is_admin ? btn('创建工作空间','new-project','','btn btn-primary','plus') : '');
      return;
    }
    try {
      let html = '';
      if (state.view === 'dashboard') {
        const [data,reqs] = await Promise.all([api(endpoint('dashboard')),api(endpoint('requirements'))]);
        state.requirements = reqs; html = renderDashboard(data,reqs);
      } else if (state.view === 'requirements') {
        const params = new URLSearchParams(Object.entries(state.filters).filter(([,value]) => value));
        const [reqs,docs,members] = await Promise.all([api(`${endpoint('requirements')}?${params}`),api(endpoint('documents')),api(endpoint('members'))]);
        state.requirements = reqs; state.documents = docs; state.members = members; html = renderRequirements();
      } else if (state.view === 'reviews') {
        state.reviews = await api(endpoint('reviews')); html = renderReviews();
      } else if (state.view === 'trace') {
        const [trace,links,artifacts,reqs] = await Promise.all([api(endpoint('trace')),api(endpoint('links')),api(endpoint('artifacts')),api(endpoint('requirements'))]);
        state.trace = trace; state.links = links; state.artifacts = artifacts; state.requirements = reqs; html = renderTrace();
      } else if (state.view === 'baselines') {
        state.baselines = await api(endpoint('baselines')); html = renderBaselines();
      } else if (state.view === 'changes') {
        state.changes = await api(endpoint('changes')); html = renderChanges();
      } else if (state.view === 'audit') {
        const audit = await api(endpoint('audit')); html = renderAudit(audit);
      } else if (state.view === 'members') {
        state.members = await api(endpoint('members')); html = renderMembers();
      }
      if (seq !== state.loadSequence || !state.user) return;
      host.innerHTML = html + `<footer class="footer"><span>ReqFlow · ${esc(currentProject()?.name || '需求管理系统')}</span><span>让每一次变更，都有依据。</span></footer>`;
    } catch (error) {
      if (seq !== state.loadSequence || !state.user) return;
      host.innerHTML = `<div class="error-panel">${icon('info')}<span>${esc(error.message)}</span>${btn('重新加载','refresh','','btn btn-small')}</div>`;
    }
  }

  function renderDashboard(data,reqs) {
    const counts = data.counts || {}; const total = Number(counts.total || 0);
    const approved = Number(counts.approved || 0); const inReview = Number(counts.in_review || 0);
    const rate = total ? Math.round(approved/total*100) : 0;
    const coverage = data.coverage || {linked:0,total:0,percent:0};
    const active = reqs.filter(r => r.status !== 'archived').sort((a,b) => String(b.updated_at).localeCompare(String(a.updated_at))).slice(0,6);
    const metric = (name,value,ico,tone,note) => `<div class="metric"><div class="metric-top"><span>${name}</span><span class="metric-icon ${tone}">${icon(ico)}</span></div><div class="metric-value">${esc(value)}</div><div class="metric-bottom">${note}</div></div>`;
    return pageHead('PROJECT OVERVIEW','需求概览','从需求定义到变更闭环，掌握工作空间的最新进展。',exportBtn() + (canWrite() ? btn('新建需求','new-requirement','','btn btn-primary','plus') : '')) +
      `<section class="cards">${metric('需求总数',total,'document','',`<b>${esc(counts.draft || 0)} 项草稿</b><span>等待完善与提交</span>`)}${metric('已批准需求',approved,'circlecheck','green',`<b>${rate}%</b><span>需求已完成评审</span>`)}${metric('待处理评审',data.pending_reviews || 0,'review','amber',`<span>提交与批准由不同成员完成</span>`)}${metric('待审批变更',data.pending_changes || 0,'change','purple',`<span>已建立 ${esc(data.baselines || 0)} 个需求基线</span>`)}</section>` +
      `<div class="dashboard-grid"><div><section class="panel">${panelHead('最近更新的需求','document',btn('全部需求 →','navigate','requirements','btn-link'))}${active.length ? `<div class="table-wrap"><table class="compact-table"><thead><tr><th>需求 / 标识</th><th>优先级</th><th>状态</th><th>版本</th></tr></thead><tbody>${active.map(r => `<tr><td>${reqLink(r)}<div class="cell-sub req-id">${esc(r.uid)}</div></td><td>${priority(r.priority)}</td><td>${badge(r.status)}</td><td><span class="small-note">v${esc(r.revision)}</span></td></tr>`).join('')}</tbody></table></div><div class="table-foot"><span>按最近更新时间排序</span><span>共 ${total} 项需求</span></div>` : empty('从第一条需求开始','录入清晰的需求描述和验收标准。',canWrite() ? btn('创建需求','new-requirement','','btn btn-primary btn-small','plus') : '')}</section><section class="panel">${panelHead('需求管理流程','trace')}<div class="panel-body"><div class="chip-group">${[['01','定义需求'],['02','独立评审'],['03','建立基线'],['04','变更控制'],['05','追踪验证']].map(([i,t],index) => `<span class="file-pill"><span style="color:#29a187">${i}</span> ${t}</span>${index < 4 ? '<span class="small-note" style="padding:3px">→</span>' : ''}`).join('')}</div><p class="help-text" style="margin-top:13px">批准后的需求通过变更流程更新；基线保留当时的版本、关联与验证信息。</p></div></section></div><div class="dashboard-right"><section class="panel">${panelHead('需求状态分布','dashboard')}<div class="status-summary"><div class="ring" style="background:conic-gradient(#008a7c 0deg ${rate*3.6}deg,#e5b749 ${rate*3.6}deg ${total ? (approved+inReview)/total*360 : 0}deg,#d5e1ea ${total ? (approved+inReview)/total*360 : 0}deg 360deg)"><div class="ring-inner"><div class="ring-number">${total}</div><div class="ring-caption">全部需求</div></div></div><div class="legend"><div class="legend-line"><i class="legend-dot"></i>已批准<b>${approved}</b></div><div class="legend-line"><i class="legend-dot amber"></i>评审中<b>${inReview}</b></div><div class="legend-line"><i class="legend-dot gray"></i>草稿<b>${esc(counts.draft || 0)}</b></div>${counts.archived ? `<div class="legend-line"><i class="legend-dot muted"></i>已归档<b>${esc(counts.archived)}</b></div>` : ''}</div></div><div class="coverage"><div class="coverage-top"><span>需求验证覆盖率</span><strong>${esc(coverage.percent)}%</strong></div><div class="progress-bar"><span style="width:${Math.min(100,Math.max(0,Number(coverage.percent) || 0))}%"></span></div><p class="coverage-note">${esc(coverage.linked)} / ${esc(coverage.total)} 项需求已关联测试项</p></div></section><section class="panel">${panelHead('最近动态','audit',btn('查看全部','navigate','audit','btn-link'))}<div class="panel-body" style="padding-top:7px;padding-bottom:9px">${renderActivity((data.recent || []).slice(0,4))}</div></section><div class="next-step">${icon('shield')}<div><h3>每个决定，都有完整记录</h3><p>关联验收标准与测试项，让需求变更的影响看得见。</p>${btn('查看追踪矩阵 →','navigate','trace','btn-link')}</div></div></div></div>`;
  }
  const actionLabels = {create:'创建',update:'更新',archive:'归档',submit:'提交评审',approve:'批准',reject:'退回',login:'登录',logout:'退出',create_requirement:'创建需求',update_requirement:'更新需求',submit_review:'提交评审',approve_review:'批准评审',reject_review:'退回评审',create_baseline:'创建基线',create_change:'提交变更',approve_change:'批准变更',reject_change:'退回变更',requirement_created:'创建需求',requirement_updated:'更新需求',review_submitted:'提交评审',review_approved:'批准评审',review_rejected:'退回评审',baseline_created:'创建基线',change_created:'提交变更',change_approved:'批准变更',change_rejected:'退回变更',member_updated:'更新成员',artifact_created:'创建验证项',artifact_updated:'更新验证项',link_created:'建立关联',link_deleted:'移除关联'};
  const actionLabel = action => actionLabels[action] || ({'requirement.created':'创建需求','requirement.updated':'更新需求','requirement.archived':'归档需求','review.submitted':'提交评审','review.approved':'批准评审','review.rejected':'退回评审','link.created':'建立关联','link.deleted':'移除关联','artifact.created':'创建验证项','artifact.updated':'更新验证项','baseline.created':'创建基线','change.submitted':'提交变更','change.approved':'批准变更','change.rejected':'退回变更'}[action]) || action;
  const entityLabel = entity => ({requirement:'需求',review:'评审',baseline:'基线',change:'变更',link:'追踪关系',artifact:'验证项',member:'成员',user:'用户',document:'文档',project:'项目',auth:'会话'}[entity] || entity || '记录');
  function renderActivity(rows) {
    return rows.length ? `<ul class="activity-list">${rows.map(row => `<li class="activity"><span class="activity-icon">${icon('check')}</span><div class="activity-content"><div class="activity-title"><b>${esc(row.actor_name || '系统')}</b> ${esc(actionLabel(row.action))}<br><span class="small-note">${esc(entityLabel(row.entity_type))} #${esc(row.entity_id ?? '—')}</span></div><div class="activity-time">${fmtDate(row.created_at,true)}</div></div></li>`).join('')}</ul>` : empty('暂无操作记录','完成需求操作后，动态将在这里展示。');
  }
  function renderRequirements() {
    const reqs = state.requirements.filter(r => !state.docFilter || String(r.document_id) === state.docFilter);
    return pageHead('REQUIREMENT LIBRARY','需求管理','用清晰的属性、验收标准和版本记录组织每一条需求。',exportBtn() + (canWrite() ? btn('新建需求','new-requirement','','btn btn-primary','plus') : '')) +
      `<div class="requirements-layout"><aside class="document-panel"><div class="document-head">需求文档${canWrite() ? btn('','new-document','','btn btn-ghost icon-button','plus') : ''}</div><div class="document-list"><button type="button" class="document-item${!state.docFilter ? ' active' : ''}" data-action="filter-document" data-id="">${icon('folder')}<span>全部需求</span></button>${state.documents.map(doc => `<button type="button" class="document-item${String(doc.id) === state.docFilter ? ' active' : ''}" data-action="filter-document" data-id="${Number(doc.id)}">${icon('document')}<span>${esc(doc.title)}</span></button>`).join('')}</div></aside><section class="panel requirement-panel"><div class="toolbar"><form id="requirements-filter" class="filter-form"><div class="search-box">${icon('search')}<input name="q" aria-label="搜索需求" placeholder="搜索编号、标题或需求描述…" value="${attr(state.filters.q)}"></div><div class="filters"><select name="status" aria-label="筛选需求状态">${option('','所有状态',state.filters.status)}${options(['draft','in_review','approved','archived'],state.filters.status)}</select><select name="priority" aria-label="筛选优先级">${option('','所有优先级',state.filters.priority)}${options(['must','should','could'],state.filters.priority)}</select><select name="type" aria-label="筛选需求类型">${option('','所有类型',state.filters.type)}${options(['functional','nonfunctional','constraint'],state.filters.type)}</select><button class="btn btn-small" type="submit">筛选</button>${Object.values(state.filters).some(Boolean) || state.docFilter ? btn('重置','reset-filter','','btn btn-ghost btn-small') : ''}</div></form></div>${reqs.length ? `<div class="table-wrap"><table><thead><tr><th>需求标识</th><th>标题 / 类型</th><th>优先级</th><th>状态</th><th>负责人</th><th>版本</th><th>操作</th></tr></thead><tbody>${reqs.map(r => `<tr><td><span class="req-id">${esc(r.uid)}</span></td><td>${reqLink(r)}<div class="cell-sub">${esc(titleOf(r.type))}${r.parent_id ? ' · 子需求' : ''}</div></td><td>${priority(r.priority)}</td><td>${badge(r.status)}</td><td><span class="muted">${esc(r.owner_name || '未分配')}</span></td><td class="no-wrap"><span class="small-note">v${esc(r.revision)}</span></td><td>${btn('查看','requirement-detail',r.id,'btn-link')}</td></tr>`).join('')}</tbody></table></div><div class="table-foot"><span>当前显示 ${reqs.length} 条需求</span><span>需求内容与历史版本独立保存</span></div>` : empty('没有符合条件的需求','调整筛选条件，或创建一条新的需求。',canWrite() ? btn('新建需求','new-requirement','','btn btn-primary btn-small','plus') : '')}</section></div>`;
  }
  function canDecideReview(r) { return canReview() && r.status === 'pending' && Number(r.submitted_by) !== Number(state.user.id) && Number(r.reviewer_id) === Number(state.user.id); }
  function renderReviews() {
    const list = state.reviews.filter(r => state.reviewFilter === 'all' || r.status === state.reviewFilter);
    return pageHead('REVIEW WORKFLOW','需求评审','围绕指定需求版本开展评审，让批准结果与实际内容保持一致。',btn('刷新队列','refresh','','btn','audit')) +
      `<div class="inline-notice">${icon('shield')}<span>评审只能由指定的评审人处理，提交人不能批准自己的申请。若需求版本发生变化，原评审将无法批准。</span></div><div class="review-status-bar">${[['pending','待处理'],['approved','已批准'],['rejected','已退回'],['all','全部']].map(([key,title]) => `<button type="button" class="status-filter${state.reviewFilter === key ? ' active' : ''}" data-action="review-filter" data-id="${key}">${title}<span>${key === 'all' ? state.reviews.length : state.reviews.filter(r => r.status === key).length}</span></button>`).join('')}</div><section class="card-list">${list.length ? list.map(r => `<article class="item-card"><div class="item-card-icon">${icon('review')}</div><div class="item-card-body"><div class="item-card-head"><div><div class="req-id" style="margin-bottom:4px">${esc(r.uid)} · v${esc(r.revision)}</div><h3>${esc(r.title)}</h3></div>${badge(r.status)}</div><div class="item-card-meta"><span>提交人：${esc(r.submitter_name)}</span><span>评审人：${esc(r.reviewer_name)}</span><span>${fmtDate(r.created_at)}</span></div>${r.comment ? `<p style="margin-top:10px">评审意见：${esc(r.comment)}</p>` : ''}<div class="item-card-actions">${btn('查看需求','requirement-detail',r.requirement_id,'btn btn-small','document')}${canDecideReview(r) ? btn('批准','review-approve',r.id,'btn btn-primary btn-small','check') + btn('退回修改','review-reject',r.id,'btn btn-small') : r.status === 'pending' ? `<span class="small-note" style="align-self:center">${Number(r.submitted_by) === Number(state.user.id) ? '由其他成员独立评审' : Number(r.reviewer_id) !== Number(state.user.id) ? '等待指定评审人处理' : '当前角色无审批权限'}</span>` : ''}</div></div></article>`).join('') : `<div class="panel">${empty('当前没有评审记录','在需求详情中提交草稿后，这里会出现对应版本的评审申请。')}</div>`}</section><div style="height:20px"></div>`;
  }
  function renderTrace() {
    const tabs = [['matrix','追踪矩阵'],['links','需求关联'],['artifacts','设计与测试']];
    const headActions = exportBtn('trace') + (canWrite() ? state.traceTab === 'links' ? btn('新建关联','new-link','','btn btn-primary','plus') : btn('新建验证项','new-artifact','','btn btn-primary','plus') : '');
    let body = '';
    if (state.traceTab === 'matrix') body = state.trace.length ? `<div class="table-wrap"><table class="matrix-table"><thead><tr><th>需求</th><th>上游 / 父需求</th><th>下游 / 子需求</th><th>设计与测试</th><th>测试覆盖</th></tr></thead><tbody>${state.trace.map(row => `<tr><td>${reqLink(row)}<div class="cell-sub req-id">${esc(row.uid)} · v${esc(row.revision)}</div></td><td>${(row.parents || []).map(p => `<span class="tag" title="${attr(p.title)}">${esc(p.uid)}</span>`).join('') || '<span class="small-note">—</span>'}</td><td>${(row.children || []).map(c => `<span class="tag" title="${attr(c.title)}">${esc(c.uid)}</span>`).join('') || '<span class="small-note">—</span>'}</td><td>${(row.artifacts || []).map(a => `<div><span class="tag">${esc(titleOf(a.kind))}</span><span class="small-note">${esc(a.title)}</span>${a.kind === 'test' ? ` ${badge(a.result)}` : ''}</div>`).join('') || '<span class="small-note">尚未关联</span>'}</td><td><span class="trace-indicator${row.covered ? '' : ' missing'}">${icon(row.covered ? 'circlecheck' : 'info')}${row.covered ? '已覆盖' : '待补充'}</span></td></tr>`).join('')}</tbody></table></div><div class="table-foot"><span>共 ${state.trace.length} 条需求 · ${state.trace.filter(r => r.covered).length} 条已关联测试</span><span>覆盖表示存在关联测试，不等同于测试通过</span></div>` : empty('还没有可追踪的需求','创建需求并关联设计项和测试项。');
    if (state.traceTab === 'links') body = state.links.length ? `<div class="table-wrap"><table><thead><tr><th>来源需求</th><th>关系</th><th>目标需求</th>${canWrite() ? '<th>操作</th>' : ''}</tr></thead><tbody>${state.links.map(link => `<tr><td><span class="req-id">${esc(link.source_uid)}</span><div class="cell-sub">${esc(link.source_title)}</div></td><td><span class="tag">${esc(titleOf(link.kind))} →</span></td><td><span class="req-id">${esc(link.target_uid)}</span><div class="cell-sub">${esc(link.target_title)}</div></td>${canWrite() ? `<td>${btn('移除','delete-link',link.id,'btn-link')}</td>` : ''}</tr>`).join('')}</tbody></table></div>` : empty('尚未建立需求关联','建立分解、依赖或冲突关系，用于追踪和影响分析。',canWrite() ? btn('新建关联','new-link','','btn btn-primary btn-small','plus') : '');
    if (state.traceTab === 'artifacts') body = state.artifacts.length ? `<div class="table-wrap"><table><thead><tr><th>验证项</th><th>类型</th><th>引用位置</th><th>执行结果</th><th>关联需求</th>${canWrite() ? '<th>操作</th>' : ''}</tr></thead><tbody>${state.artifacts.map(a => `<tr><td><span class="req-title">${esc(a.title)}</span></td><td><span class="tag">${esc(titleOf(a.kind))}</span></td><td><span class="small-note truncate" title="${attr(a.reference)}">${esc(a.reference || '—')}</span></td><td>${badge(a.result)}</td><td>${(a.requirement_ids || []).map(id => `<span class="tag">${esc(state.requirements.find(r => Number(r.id) === Number(id))?.uid || `#${id}`)}</span>`).join('') || '<span class="small-note">未关联</span>'}</td>${canWrite() ? `<td>${btn('编辑','edit-artifact',a.id,'btn-link')}</td>` : ''}</tr>`).join('')}</tbody></table></div>` : empty('尚未创建验证项','通过设计项与测试项建立需求到交付证据的关联。',canWrite() ? btn('新建验证项','new-artifact','','btn btn-primary btn-small','plus') : '');
    return pageHead('TRACEABILITY','追踪与验证','把需求、设计和测试连接起来，发现覆盖缺口与变更影响。',headActions) + `<div class="inline-notice">${icon('info')}<span>分解关系用于需求层级，依赖与冲突关系用于分析关联。系统阻止自关联、重复关联和分解环。</span></div><section class="panel"><div class="tabs">${tabs.map(([key,title]) => `<button type="button" class="tab${state.traceTab === key ? ' active' : ''}" data-action="trace-tab" data-id="${key}">${title}</button>`).join('')}</div>${body}</section>`;
  }
  function renderBaselines() {
    return pageHead('VERSION BASELINES','版本基线','冻结已批准的需求版本，为后续变更提供稳定的比较依据。',canWrite() ? btn('创建基线','new-baseline','','btn btn-primary','plus') : '') +
      `<div class="inline-notice">${icon('baseline')}<span>基线保存创建时的需求内容、版本、追踪关系与验证项快照。后续编辑不会改变已有基线。</span></div><section class="baseline-grid">${state.baselines.length ? state.baselines.map(b => `<article class="baseline-card"><div class="item-card-icon">${icon('baseline')}</div><h3>${esc(b.name)}</h3><p>${esc(b.creator_name || '—')} 创建于 ${fmtDate(b.created_at)}</p><div class="baseline-count">${esc(b.item_count)}<span>项已批准需求</span></div><div class="row-actions">${btn('查看快照','baseline-detail',b.id,'btn-link')}${btn('对比当前','baseline-compare',b.id,'btn btn-small','change')}</div></article>`).join('') : `<div class="panel" style="grid-column:1/-1">${empty('还没有需求基线','完成需求评审后，将已批准的版本冻结为一个基线。',canWrite() ? btn('创建第一个基线','new-baseline','','btn btn-primary btn-small','plus') : '')}</div>`}</section><div style="height:25px"></div>`;
  }
  function canDecideChange(c) { return canReview() && c.status === 'pending' && Number(c.submitted_by) !== Number(state.user.id); }
  function renderChanges() {
    const list = state.changes.filter(c => state.changeFilter === 'all' || c.status === state.changeFilter);
    return pageHead('CHANGE CONTROL','变更控制','先了解影响，再决定变更。已批准需求通过申请更新版本。',canWrite() ? btn('发起变更','new-change','','btn btn-primary','plus') : '') +
      `<div class="review-status-bar">${[['pending','待审批'],['approved','已批准'],['rejected','已退回'],['all','全部']].map(([key,title]) => `<button type="button" class="status-filter${state.changeFilter === key ? ' active' : ''}" data-action="change-filter" data-id="${key}">${title}<span>${key === 'all' ? state.changes.length : state.changes.filter(c => c.status === key).length}</span></button>`).join('')}</div><section class="card-list">${list.length ? list.map(c => `<article class="item-card"><div class="item-card-icon">${icon('change')}</div><div class="item-card-body"><div class="item-card-head"><h3>${esc(c.title)}</h3>${badge(c.status)}</div><div class="req-id">${esc(c.uid)} · 基于 v${esc(c.base_revision)} · ${esc(c.requirement_title)}</div><p style="margin-top:9px">${esc(c.reason)}</p><div class="item-card-meta"><span>申请人：${esc(c.submitter_name)}</span><span>${fmtDate(c.created_at)}</span></div>${c.decision_comment ? `<p style="margin-top:9px">审批意见：${esc(c.decision_comment)}</p>` : ''}<div class="item-card-actions">${btn('变更详情','change-detail',c.id,'btn btn-small','document')}${btn('影响分析','impact',c.requirement_id,'btn btn-small','trace')}${canDecideChange(c) ? btn('批准变更','change-approve',c.id,'btn btn-primary btn-small','check') + btn('退回','change-reject',c.id,'btn btn-small') : c.status === 'pending' && Number(c.submitted_by) === Number(state.user.id) ? '<span class="small-note" style="align-self:center">等待其他成员独立审批</span>' : ''}</div></div></article>`).join('') : `<div class="panel">${empty('当前没有变更申请','选择一条已批准的需求，说明变更原因和拟修改内容。',canWrite() ? btn('发起变更','new-change','','btn btn-primary btn-small','plus') : '')}</div>`}</section><div style="height:20px"></div>`;
  }
  function formatDetail(detail) { if (detail == null) return '—'; if (typeof detail === 'string') return detail; return JSON.stringify(detail); }
  function renderAudit(rows) {
    return pageHead('AUDIT TRAIL','审计记录','按时间回溯成员操作、需求版本和审批决定。',btn('刷新记录','refresh','','btn','audit')) + `<section class="panel">${panelHead('操作记录','audit',`<span class="count-label">${rows.length} 条记录</span>`)}${rows.length ? `<div class="table-wrap"><table class="audit-table"><thead><tr><th>操作时间</th><th>操作人</th><th>操作</th><th>对象</th><th>详情</th></tr></thead><tbody>${rows.map(a => `<tr><td class="no-wrap">${fmtDate(a.created_at)}</td><td>${esc(a.actor_name || '系统')}</td><td><span class="tag">${esc(actionLabel(a.action))}</span></td><td class="no-wrap">${esc(entityLabel(a.entity_type))} #${esc(a.entity_id ?? '—')}</td><td class="audit-detail"><span class="small-note">${esc(formatDetail(a.detail))}</span></td></tr>`).join('')}</tbody></table></div>` : empty('暂无审计记录','需求及相关对象的操作将自动记录在这里。')}</section>`;
  }
  function renderMembers() {
    return pageHead('WORKSPACE MEMBERS','项目成员','以角色分配职责，让需求维护、评审与只读查看各司其职。',state.user.is_admin ? btn('新增用户','new-user','','btn','plus') + btn('添加成员','add-member','','btn btn-primary','users') : '') +
      `<div class="inline-notice">${icon('shield')}<span>分析员维护需求并提交申请；评审员批准或退回；观察员只读查看；管理员管理成员。所有角色都必须遵守禁止自审规则。</span></div><section class="panel">${panelHead('工作空间成员','users',`<span class="count-label">${state.members.length} 位成员</span>`)}<div class="table-wrap"><table><thead><tr><th>成员</th><th>用户名</th><th>项目角色</th><th>职责</th>${state.user.is_admin ? '<th>管理</th>' : ''}</tr></thead><tbody>${state.members.map(m => `<tr><td><div class="account"><div class="avatar">${esc(m.name?.slice(-2) || m.username?.slice(0,2))}</div><span class="req-title">${esc(m.name)}${Number(m.user_id) === Number(state.user.id) ? '<span class="tag" style="margin-left:7px">当前</span>' : ''}</span></div></td><td><span class="small-note">${esc(m.username)}</span></td><td><span class="tag">${esc(titleOf(m.role))}</span></td><td><span class="small-note">${esc({admin:'维护、审批与成员管理',analyst:'维护需求、追踪与提交申请',reviewer:'需求评审与变更审批',viewer:'浏览与导出需求信息'}[m.role] || '查看项目')}</span></td>${state.user.is_admin ? `<td>${btn('调整角色','edit-member',m.user_id,'btn-link')}</td>` : ''}</tr>`).join('')}</tbody></table></div></section>${state.user.is_admin ? `<div class="panel">${panelHead('工作空间管理','folder')}<div class="panel-body"><p class="help-text" style="margin-bottom:12px">通过独立工作空间组织不同的需求集合与成员权限。</p>${btn('创建工作空间','new-project','','btn btn-small','plus')}</div></div>` : ''}`;
  }

  function openModal(title,subtitle,body,footer='',wide=false) {
    const dialog = $('#modal');
    dialog.classList.toggle('wide',wide);
    dialog.innerHTML = `<div class="modal-inner"><div class="modal-head"><div><h2 id="modal-title">${esc(title)}</h2>${subtitle ? `<p>${esc(subtitle)}</p>` : ''}</div><button type="button" class="modal-close" data-action="close-modal" aria-label="关闭弹窗">×</button></div><div class="modal-body">${body}</div>${footer ? `<div class="modal-footer">${footer}</div>` : ''}</div>`;
    if (!dialog.open) dialog.showModal();
    $('.modal-inner',dialog).scrollTop = 0;
  }
  function closeModal() { $('#modal').close(); state.modalContext = null; }
  function formModal(id,title,subtitle,fields,submitText='保存',wide=false,notice='') {
    const body = `${notice}<form id="${id}"><div class="form-error"></div><div class="form-grid">${fields}</div></form>`;
    const footer = btn('取消','close-modal','','btn') + `<button class="btn btn-primary" type="submit" form="${id}">${esc(submitText)}</button>`;
    openModal(title,subtitle,body,footer,wide);
  }
  const field = (name,label,input,full=false,hint='') => `<div class="field${full ? ' full' : ''}"><label for="field-${attr(name)}">${esc(label)}</label>${input}${hint ? `<p class="hint">${esc(hint)}</p>` : ''}</div>`;
  const textField = (name,label,value='',required=false,full=false,placeholder='',max=500) => field(name,label,`<input id="field-${attr(name)}" name="${attr(name)}" value="${attr(value)}"${required ? ' required' : ''}${name === 'uid' ? ' pattern="[A-Za-z0-9_-]+" title="需求编号只允许字母、数字、下划线和连字符"' : name === 'username' ? ' pattern="[A-Za-z0-9_.-]+" minlength="2" title="用户名至少2位，只允许字母、数字、下划线、点和连字符"' : ''} maxlength="${max}" placeholder="${attr(placeholder)}">`,full);
  const textareaField = (name,label,value='',required=false,full=true,placeholder='',max=12000) => field(name,label,`<textarea id="field-${attr(name)}" name="${attr(name)}"${required ? ' required' : ''} maxlength="${max}" placeholder="${attr(placeholder)}">${esc(value)}</textarea>`,full);
  const selectField = (name,label,content,full=false,hint='') => field(name,label,`<select id="field-${attr(name)}" name="${attr(name)}">${content}</select>`,full,hint);
  async function loadEditingResources() {
    const [reqs,docs,members] = await Promise.all([api(endpoint('requirements')),api(endpoint('documents')),api(endpoint('members'))]);
    state.requirements = reqs; state.documents = docs; state.members = members;
  }
  function requirementFields(r={},isNew=false) {
    return (isNew ? textField('uid','需求编号（可选）','',false,false,'留空由系统生成',60) : '') + textField('title','需求标题 *',r.title || '',true,isNew ? false : true,'用一句话描述需求目标',200) +
      textareaField('statement','需求描述 *',r.statement || '',true,true,'明确系统应在什么条件下提供什么行为。') +
      selectField('document_id','所属文档',option('','未分类',r.document_id) + state.documents.map(d => option(d.id,d.title,r.document_id)).join('')) +
      selectField('parent_id','父需求',option('','无父需求',r.parent_id) + state.requirements.filter(x => Number(x.id) !== Number(r.id) && x.status !== 'archived').map(x => option(x.id,`${x.uid} · ${x.title}`,r.parent_id)).join('')) +
      selectField('type','需求类型',options(['functional','nonfunctional','constraint'],r.type || 'functional')) + selectField('priority','优先级',options(['must','should','could'],r.priority || 'should')) +
      selectField('owner_id','负责人',option('','未分配',r.owner_id) + state.members.map(m => option(m.user_id,m.name,r.owner_id)).join('')) + textField('tags','标签',(r.tags || []).join(', '),false,false,'用逗号分隔，例如：预约, 核心流程',1000) +
      textField('source','需求来源',r.source || '',false,true,'例如：实验室管理员访谈、管理制度',1000) + textareaField('rationale','需求理由',r.rationale || '',false,true,'为什么需要这条需求？',4000) +
      textareaField('acceptance','验收标准 *',r.acceptance || '',true,true,'写出可以验证的输入、步骤和预期结果。',8000);
  }
  async function showRequirementForm(id=null) {
    await loadEditingResources();
    const r = id ? await api(`/requirements/${id}`) : {};
    state.modalContext = {kind:'requirement',requirement:r};
    formModal('requirement-form',id ? '编辑需求' : '新建需求',id ? `${r.uid} · 当前版本 v${r.revision} · 保存后生成新版本` : '先定义清晰的内容，再提交独立评审。',requirementFields(r,!id),id ? '保存新版本' : '创建需求',true);
  }
  async function showRequirement(id) {
    const r = await api(`/requirements/${id}`);
    state.modalContext = {kind:'detail',requirement:r};
    const owner = r.owner_name || '未分配';
    const actions = (canWrite() && r.status === 'draft' ? btn('编辑需求','edit-requirement',r.id,'btn btn-small','edit') + btn('提交评审','submit-review',r.id,'btn btn-primary btn-small','review') : '') +
      (canWrite() && r.status === 'approved' ? btn('发起变更','change-for-requirement',r.id,'btn btn-primary btn-small','change') : '') + btn('影响分析','impact',r.id,'btn btn-small','trace') +
      (canWrite() && r.status === 'draft' ? btn('归档','archive-requirement',r.id,'btn btn-ghost btn-small','archive') : '');
    const info = (label,value) => `<div><div class="detail-label">${label}</div><div class="detail-value">${value}</div></div>`;
    const body = `<div class="detail-actions">${badge(r.status)}${actions}</div><div class="details-grid">${info('需求类型',esc(titleOf(r.type)))}${info('优先级',priority(r.priority))}${info('负责人',esc(owner))}${info('当前版本',`v${esc(r.revision)}`)}${info('需求来源',esc(r.source || '未填写'))}${info('更新时间',fmtDate(r.updated_at))}</div><h3 class="subsection">需求描述</h3><div class="prose">${esc(r.statement)}</div><h3 class="subsection">需求理由</h3><div class="prose">${esc(r.rationale || '未填写')}</div><h3 class="subsection">验收标准</h3><div class="prose">${esc(r.acceptance || '未填写')}</div>${r.tags?.length ? `<h3 class="subsection">标签</h3>${r.tags.map(tag => `<span class="tag">${esc(tag)}</span>`).join('')}` : ''}<h3 class="subsection">追踪关系与验证项</h3><div class="chip-group">${(r.links || []).map(link => `<span class="file-pill">${esc(link.source_uid)} ${esc(titleOf(link.kind))} → ${esc(link.target_uid)}</span>`).join('')}${(r.artifacts || []).map(a => `<span class="file-pill">${icon(a.kind === 'test' ? 'test' : 'document')}${esc(a.title)} · ${esc(titleOf(a.result))}</span>`).join('')}${!r.links?.length && !r.artifacts?.length ? '<span class="small-note">尚未建立关联，可在“追踪与验证”中添加。</span>' : ''}</div><h3 class="subsection">历史版本 · ${(r.versions || []).length} 个</h3>${(r.versions || []).slice().sort((a,b) => b.revision-a.revision).map(v => `<div class="revision-line"><div class="revision-heading"><strong>v${esc(v.revision)}</strong><span class="small-note">${fmtDate(v.created_at)}</span></div><details><summary>查看该版本内容</summary><div class="revision-content"><div class="req-title">${esc(v.snapshot?.title || r.title)}</div><div class="prose" style="margin-top:7px">${esc(v.snapshot?.statement || '')}</div><div class="detail-label" style="margin-top:10px">验收标准</div><div class="prose">${esc(v.snapshot?.acceptance || '—')}</div><div class="detail-label" style="margin-top:10px">版本属性</div><div class="prose">${esc(titleOf(v.snapshot?.type))} · ${esc(titleOf(v.snapshot?.priority))} · ${esc(titleOf(v.snapshot?.status))}</div></div></details></div>`).join('') || '<span class="small-note">暂无历史版本</span>'}${r.reviews?.length ? `<h3 class="subsection">评审记录</h3>${r.reviews.map(rv => `<div class="revision-content" style="margin-bottom:8px"><div class="row-actions">v${esc(rv.revision)} ${badge(rv.status)} <span class="small-note">${fmtDate(rv.created_at)}</span></div><p class="prose">${esc(rv.comment || '暂无评审意见')}</p></div>`).join('')}` : ''}`;
    openModal(r.title,`${r.uid} · 需求详情`,body,btn('关闭','close-modal','','btn'),true);
  }
  async function showSubmitReview(id) {
    const [r,members] = await Promise.all([api(`/requirements/${id}`),api(endpoint('members'))]);
    const reviewers = members.filter(m => ['admin','reviewer'].includes(m.role) && Number(m.user_id) !== Number(state.user.id));
    if (!reviewers.length) { toast('当前没有可用的独立评审人，请管理员添加评审员。',true); return; }
    state.modalContext = {requirement:r};
    formModal('submit-review-form','提交需求评审',`${r.uid} · ${r.title} · v${r.revision}`,selectField('reviewer_id','指定评审人',reviewers.map(m => option(m.user_id,`${m.name}（${titleOf(m.role)}）`)).join(''),true),'提交评审',false,`<div class="inline-notice">${icon('info')}<span>提交后当前版本将锁定编辑。评审批准前，需求保持“评审中”状态。</span></div>`);
  }
  function showDecision(kind,id,decision) {
    const isReview = kind === 'review';
    const item = (isReview ? state.reviews : state.changes).find(r => Number(r.id) === Number(id));
    state.modalContext = {kind,id:Number(id),decision};
    formModal('decision-form',`${decision === 'approved' ? '批准' : '退回'}${isReview ? '需求评审' : '变更申请'}`,item?.title || '',textareaField('comment','审批意见', '',decision === 'rejected',true,decision === 'rejected' ? '请说明需要修改的内容。' : '记录本次批准的依据或补充说明。',2000),decision === 'approved' ? '确认批准' : '确认退回',false,isReview ? '' : `<div class="inline-notice warning">${icon('info')}<span>${decision === 'approved' ? '批准后，系统将核对原版本并原子更新需求内容。已有基线仍保留原快照。' : '退回后不会更新需求内容。'}</span></div>`);
  }
  async function showLinkForm() {
    state.requirements = await api(endpoint('requirements'));
    const reqs = state.requirements.filter(r => r.status !== 'archived');
    if (reqs.length < 2) { toast('至少需要两条有效需求才能建立关联。',true); return; }
    formModal('link-form','建立需求关联','关联用于追踪需求分解、依赖关系及变更影响。',selectField('source_id','来源需求',reqs.map(r => option(r.id,`${r.uid} · ${r.title}`)).join(''),true) + selectField('kind','关联类型',options(['refines','depends','conflicts'],'depends'),true) + selectField('target_id','目标需求',reqs.map(r => option(r.id,`${r.uid} · ${r.title}`,reqs[1]?.id)).join(''),true),'建立关联',false,`<div class="inline-notice">${icon('info')}<span>分解关系表示“来源需求是目标需求的细化”；依赖关系表示“来源需求依赖目标需求”。</span></div>`);
  }
  async function showArtifactForm(id=null) {
    state.requirements = await api(endpoint('requirements'));
    const a = id ? state.artifacts.find(x => Number(x.id) === Number(id)) || {} : {};
    state.modalContext = {artifact:a};
    const fields = textField('title','验证项名称 *',a.title || '',true,true,'例如：重复预约冲突测试',200) + selectField('kind','类型',options(['test','design'],a.kind || 'test')) + selectField('result','执行结果',options(['not_run','passed','failed'],a.result || 'not_run')) + textField('reference','引用位置',a.reference || '',false,true,'例如：tests/test_booking.py::test_conflict',2000) + field('requirement_ids','关联需求',`<div class="checkbox-list">${state.requirements.filter(r => r.status !== 'archived').map(r => `<label class="checkbox-option"><input type="checkbox" name="requirement_ids" value="${Number(r.id)}"${(a.requirement_ids || []).map(Number).includes(Number(r.id)) ? ' checked' : ''}><span>${esc(r.uid)} · ${esc(r.title)}</span></label>`).join('') || '<span class="small-note">当前没有可关联的需求。</span>'}</div>`,true,'至少关联一条需求，以便形成可追踪的验证证据。');
    formModal('artifact-form',id ? '编辑验证项' : '新建设计 / 测试项','关联验证证据，并记录当前执行结果。',fields,'保存验证项');
  }
  async function showBaselineForm() {
    const reqs = await api(endpoint('requirements')+'?status=approved');
    if (!reqs.length) { toast('没有已批准的需求，请先完成需求评审。',true); return; }
    const fields = textField('name','基线名称 *','',true,true,'例如：V1.0 需求评审基线',150) + field('requirement_ids','选择需求',`<div class="checkbox-list">${reqs.map(r => `<label class="checkbox-option"><input type="checkbox" name="requirement_ids" value="${Number(r.id)}" checked><span>${esc(r.uid)} · v${esc(r.revision)}<br>${esc(r.title)}</span></label>`).join('')}</div>`,true,'默认选择全部已批准需求；至少保留一项。');
    formModal('baseline-form','创建需求基线','创建后将固定本次需求、追踪关系与验证项快照。',fields,'创建并冻结');
  }
  async function showBaseline(id,compare=false) {
    const b = await api(`/baselines/${id}${compare ? '/compare' : ''}`);
    if (compare) {
      openModal('基线与当前状态比较',b.name,`<div class="comparison-info"><span class="tag">追踪关系：${b.links_changed ? '已变化' : '未变化'}</span><span class="tag">验证项：${b.artifacts_changed ? '已变化' : '未变化'}</span></div>${b.rows?.length ? `<div class="table-wrap"><table><thead><tr><th>需求</th><th>基线版本</th><th>当前版本</th><th>比较结果</th></tr></thead><tbody>${b.rows.map(r => `<tr><td><span class="req-id">${esc(r.uid)}</span><div class="req-title">${esc(r.title)}</div></td><td>${r.baseline_revision ? `v${esc(r.baseline_revision)}` : '—'}</td><td>${r.current_revision ? `v${esc(r.current_revision)}` : '—'}</td><td>${badge(r.change)}</td></tr>`).join('')}</tbody></table></div>` : empty('暂无可比较的需求')}`,btn('关闭','close-modal','','btn'),true);
    } else {
      const items = b.items || [];
      openModal('基线快照',`${b.name} · ${fmtDate(b.created_at)}`,`<div class="inline-notice">${icon('shield')}<span>以下内容来自创建基线时的不可变快照，共 ${items.length} 条需求、${(b.links || []).length} 条关联、${(b.artifacts || []).length} 个验证项。</span></div>${items.map(item => `<div class="revision-content" style="margin-bottom:12px"><div class="revision-heading"><strong>${esc(item.snapshot?.uid || `#${item.requirement_id}`)} · ${esc(item.snapshot?.title)}</strong><span>v${esc(item.revision)}</span></div><details style="margin-top:9px"><summary class="small-note" style="cursor:pointer">查看冻结内容</summary><p class="prose" style="margin-top:9px">${esc(item.snapshot?.statement)}</p><div class="detail-label" style="margin-top:10px">验收标准</div><p class="prose">${esc(item.snapshot?.acceptance || '—')}</p><div class="detail-label" style="margin-top:10px">需求属性</div><p class="prose">${esc(titleOf(item.snapshot?.type))} · ${esc(titleOf(item.snapshot?.priority))} · ${esc(titleOf(item.snapshot?.status))}</p><div class="detail-label" style="margin-top:10px">需求来源与理由</div><p class="prose">${esc(item.snapshot?.source || '—')}<br>${esc(item.snapshot?.rationale || '—')}</p><div class="chip-group" style="margin-top:10px">${(item.snapshot?.tags || []).map(tag => `<span class="tag">${esc(tag)}</span>`).join('')}</div></details></div>`).join('')}<h3 class="subsection">冻结的追踪关系</h3>${b.links?.length ? `<div class="chip-group">${b.links.map(link => `<span class="file-pill">${esc(link.source_uid || `#${link.source_id}`)} ${esc(titleOf(link.kind))} → ${esc(link.target_uid || `#${link.target_id}`)}</span>`).join('')}</div>` : '<p class="help-text">创建时没有相关追踪关系。</p>'}<h3 class="subsection">冻结的设计与测试项</h3>${b.artifacts?.length ? b.artifacts.map(a => `<div class="revision-content" style="margin-bottom:8px"><span class="tag">${esc(titleOf(a.kind))}</span><span class="req-title">${esc(a.title)}</span> ${badge(a.result)}<p class="small-note" style="margin-top:6px">${esc(a.reference || '未填写引用位置')}</p></div>`).join('') : '<p class="help-text">创建时没有关联的验证项。</p>'}`,btn('对比当前','baseline-compare',b.id,'btn btn-primary','change') + btn('关闭','close-modal','','btn'),true);
    }
  }
  async function selectChangeRequirement() {
    const reqs = await api(endpoint('requirements')+'?status=approved');
    if (!reqs.length) { toast('只有已批准的需求可以发起变更。',true); return; }
    formModal('select-change-form','选择变更对象','从已批准的需求开始，说明变更原因和拟修改内容。',selectField('requirement_id','需要变更的需求',reqs.map(r => option(r.id,`${r.uid} · ${r.title} · v${r.revision}`)).join(''),true),'下一步：填写变更');
  }
  function impactHtml(data) {
    return `<div class="inline-notice">${icon('trace')}<span>从 ${esc(data.requirement?.uid || '')} 出发，发现 ${(data.requirements || []).length} 条关联需求、${(data.artifacts || []).length} 个设计 / 测试项。请结合关联方向判断具体影响。</span></div><h3 class="subsection">关联需求</h3>${data.requirements?.length ? data.requirements.map(r => `<div class="revision-content" style="margin-bottom:8px"><span class="req-id">${esc(r.uid)}</span><span class="req-title" style="margin-left:12px">${esc(r.title)}</span></div>`).join('') : '<p class="help-text">没有发现其他关联需求。</p>'}<h3 class="subsection">设计与测试</h3>${data.artifacts?.length ? data.artifacts.map(a => `<div class="revision-content" style="margin-bottom:8px"><span class="tag">${esc(titleOf(a.kind))}</span> ${esc(a.title)} ${badge(a.result)}</div>`).join('') : '<p class="help-text">没有发现关联的设计或测试项。</p>'}`;
  }
  async function showImpact(id) {
    const data = await api(`/requirements/${id}/impact`);
    openModal('变更影响分析',`${data.requirement?.uid || ''} · ${data.requirement?.title || ''}`,impactHtml(data),btn('关闭','close-modal','','btn'),true);
  }
  async function showChangeForm(id) {
    await loadEditingResources();
    const [r,impact] = await Promise.all([api(`/requirements/${id}`),api(`/requirements/${id}/impact`)]);
    state.modalContext = {requirement:r};
    const fields = textField('change_title','变更申请标题 *','',true,true,'例如：调整预约提前量规则',200) + textareaField('change_reason','变更原因 *','',true,true,'说明业务原因、预期效果和影响。',4000) + `<div class="field full"><hr class="soft-divider"><h3 style="margin-bottom:5px">拟修改的需求内容</h3><p class="help-text">下方已填入当前版本，调整需要变更的字段。批准后生成新版本。</p></div>` + requirementFields(r);
    formModal('change-form','发起需求变更',`${r.uid} · 基于版本 v${r.revision} · 需其他成员审批`,fields,'提交变更申请',true,`<details style="margin-bottom:20px"><summary class="help-text" style="cursor:pointer;color:var(--accent)">查看影响范围：${(impact.requirements || []).length} 条关联需求、${(impact.artifacts || []).length} 个验证项</summary>${impactHtml(impact)}</details>`);
  }
  async function showChange(id) {
    if (!state.changes.length) state.changes = await api(endpoint('changes'));
    const c = state.changes.find(x => Number(x.id) === Number(id));
    if (!c) throw new Error('未找到该变更申请。');
    const proposed = c.proposed || {};
    const names = {title:'标题',statement:'需求描述',source:'需求来源',rationale:'需求理由',type:'需求类型',priority:'优先级',owner_id:'负责人编号',acceptance:'验收标准',tags:'标签',document_id:'所属文档编号',parent_id:'父需求编号'};
    const body = `<div class="detail-actions">${badge(c.status)}<span class="tag">基于 v${esc(c.base_revision)}</span></div><div class="two-column-definition"><dt>变更对象</dt><dd>${esc(c.uid)} · ${esc(c.requirement_title)}</dd><dt>申请人</dt><dd>${esc(c.submitter_name)}</dd><dt>变更原因</dt><dd class="prose">${esc(c.reason)}</dd><dt>提交时间</dt><dd>${fmtDate(c.created_at)}</dd>${c.decision_comment ? `<dt>审批意见</dt><dd>${esc(c.decision_comment)}</dd>` : ''}</div><h3 class="subsection">拟更新内容</h3>${Object.entries(proposed).filter(([key]) => Object.hasOwn(names,key)).map(([key,value]) => `<div class="changed-field"><div class="detail-label">${esc(names[key])}</div><div class="prose">${esc(Array.isArray(value) ? value.join('、') : ['type','priority'].includes(key) ? titleOf(value) : value ?? '无')}</div></div>`).join('')}`;
    openModal(c.title,'变更申请详情',body,btn('影响分析','impact',c.requirement_id,'btn','trace') + (canDecideChange(c) ? btn('批准变更','change-approve',c.id,'btn btn-primary','check') + btn('退回','change-reject',c.id,'btn') : '') + btn('关闭','close-modal','','btn'),true);
  }
  async function showMemberForm(id=null) {
    const users = await api('/users');
    const member = id ? state.members.find(m => Number(m.user_id) === Number(id)) : null;
    const candidates = member ? users.filter(u => Number(u.id) === Number(id)) : users.filter(u => !state.members.some(m => Number(m.user_id) === Number(u.id)));
    if (!candidates.length) { toast('所有现有用户都已加入项目，请先新增用户。',true); return; }
    formModal('member-form',id ? '调整成员角色' : '添加项目成员','角色变更立即影响该成员在项目内的操作权限。',selectField('user_id','用户',candidates.map(u => option(u.id,`${u.name}（${u.username}）`,id)).join(''),true) + selectField('role','项目角色',options(['analyst','reviewer','viewer','admin'],member?.role || 'viewer'),true),'保存成员');
  }
  function confirmation(title,message,action,id) {
    openModal(title,'请确认操作内容',`<p class="prose">${esc(message)}</p><div class="form-error"></div>`,btn('取消','close-modal','','btn') + btn('确认','confirm-action',id,'btn btn-primary'));
    state.modalContext = {action,id};
  }
  async function finishWrite(message) { closeModal(); toast(message); await loadView(); }
  function readRequirement(form) {
    const data = new FormData(form); const number = name => data.get(name) ? Number(data.get(name)) : null;
    const tags = [...new Set(String(data.get('tags') || '').split(/[,，]/).map(t => t.trim()).filter(Boolean))];
    if(tags.length > 20 || tags.some(tag => tag.length > 40)) throw new Error('标签最多 20 个，每个标签不超过 40 字。');
    return {title:String(data.get('title') || '').trim(),statement:String(data.get('statement') || '').trim(),source:String(data.get('source') || '').trim(),rationale:String(data.get('rationale') || '').trim(),type:data.get('type'),priority:data.get('priority'),owner_id:number('owner_id'),acceptance:String(data.get('acceptance') || '').trim(),tags,document_id:number('document_id'),parent_id:number('parent_id')};
  }
  const actions = {
    navigate: id => navigate(id), refresh: () => loadView(),
    'mobile-menu': () => $('.sidebar').classList.toggle('open'),
    'close-modal': () => closeModal(),
    'demo-account': (id,target) => { const passwords={admin:'AdminDemo2026!',analyst:'AnalystDemo2026!',reviewer:'ReviewDemo2026!',viewer:'ViewerDemo2026!'}; if (!Object.hasOwn(passwords,id)) return; $('#username').value=id; $('#password').value=passwords[id]; $$('.demo-account').forEach(button => button.classList.toggle('active',button === target)); },
    logout: async () => { await api('/auth/logout','POST',{}); state.user=null;state.csrf=null;state.project=null;state.view='dashboard';closeModal();renderLogin(); },
    'new-requirement': () => showRequirementForm(), 'edit-requirement': id => showRequirementForm(Number(id)), 'requirement-detail': id => showRequirement(Number(id)),
    'filter-document': id => {state.docFilter=id; return loadView();},
    'reset-filter': () => {state.filters={q:'',status:'',type:'',priority:''};state.docFilter='';return loadView();},
    'new-document': () => formModal('document-form','新建需求文档','通过文档组织一个业务领域或一组相关需求。',textField('title','文档名称 *','',true,true,'例如：预约与审批需求',150) + textareaField('description','文档说明','',false,true,'说明文档范围与读者。',2000),'创建文档'),
    'submit-review': id => showSubmitReview(Number(id)),
    'review-filter': id => {state.reviewFilter=id;return loadView();},
    'review-approve': id => showDecision('review',id,'approved'), 'review-reject': id => showDecision('review',id,'rejected'),
    'trace-tab': id => {state.traceTab=id;return loadView();},
    'new-link': () => showLinkForm(), 'delete-link': id => confirmation('移除追踪关系','移除后该关联不再参与当前追踪与影响分析，已有基线中的快照仍然保留。','delete-link',Number(id)),
    'new-artifact': () => showArtifactForm(), 'edit-artifact': id => showArtifactForm(Number(id)),
    'new-baseline': () => showBaselineForm(), 'baseline-detail': id => showBaseline(Number(id)), 'baseline-compare': id => showBaseline(Number(id),true),
    'new-change': () => selectChangeRequirement(), 'change-for-requirement': id => showChangeForm(Number(id)),
    'change-filter': id => {state.changeFilter=id;return loadView();}, 'change-detail': id => showChange(Number(id)),
    'change-approve': id => showDecision('change',id,'approved'), 'change-reject': id => showDecision('change',id,'rejected'), impact: id => showImpact(Number(id)),
    'archive-requirement': async id => {const r=await api(`/requirements/${id}`);confirmation('归档需求',`归档 ${r.uid}「${r.title}」后，该需求保留历史记录，但退出有效需求集合。`,'archive-requirement',Number(id));state.modalContext.revision=r.revision;},
    'new-user': () => formModal('user-form','新增系统用户','新用户创建后，可通过“添加成员”分配项目角色。',textField('username','用户名 *','',true,false,'英文、数字或下划线',60) + textField('name','显示名称 *','',true,false,'成员姓名',80) + field('password','初始密码','<input type="password" id="field-password" name="password" required minlength="10" maxlength="200" autocomplete="new-password" placeholder="至少 10 位，建议包含字母、数字与符号">',true),'创建用户'),
    'add-member': () => showMemberForm(), 'edit-member': id => showMemberForm(Number(id)),
    'new-project': () => formModal('project-form','创建工作空间','工作空间用于隔离需求集合及成员权限。',textField('name','工作空间名称 *','',true,true,'例如：校园图书馆服务需求',100) + textareaField('description','工作空间说明','',false,true,'描述该需求集合的业务范围。',2000),'创建工作空间'),
    'confirm-action': async () => {const ctx=state.modalContext;if (ctx.action === 'delete-link') {await api(`/links/${ctx.id}`,'DELETE');await finishWrite('追踪关系已移除。');} else if (ctx.action === 'archive-requirement') {await api(`/requirements/${ctx.id}/archive`,'POST',{expected_revision:ctx.revision});await finishWrite('需求已归档，历史记录已保留。');}}
  };
  document.addEventListener('click',async event => {
    const button = event.target.closest('[data-action]');
    if (!button || button.disabled || button.dataset.busy) return;
    const action = actions[button.dataset.action];
    if (!action) return;
    event.preventDefault(); button.dataset.busy = 'true';
    try { await action(button.dataset.id,button); } catch (error) { toast(error.message || '操作失败，请稍后重试。',true); } finally { delete button.dataset.busy; }
  });
  document.addEventListener('change',async event => {
    if (event.target.id === 'project-select') {
      closeModal();state.project=Number(event.target.value);state.docFilter='';state.filters={q:'',status:'',type:'',priority:''};state.requirements=[];state.members=[];state.changes=[];state.reviews=[];
      renderShell();await loadView();
    }
  });
  document.addEventListener('submit',async event => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) return;
    event.preventDefault();
    if (!form.reportValidity() || form.dataset.busy) return;
    const errorBox = $('.form-error',form);
    if (errorBox) errorBox.textContent='';
    const submitters = $$(`[form="${form.id}"]`).concat($$('button[type="submit"]',form));
    form.dataset.busy='true'; submitters.forEach(button => {button.disabled=true;});
    const data = new FormData(form); const value = name => String(data.get(name) || '').trim();
    try {
      if (form.id === 'login-form') {
        const result = await api('/auth/login','POST',{username:value('username'),password:String(data.get('password') || '')});
        await startSession(result);
      } else if (form.id === 'requirements-filter') {
        state.filters={q:value('q'),status:value('status'),type:value('type'),priority:value('priority')};await loadView();
      } else if (form.id === 'requirement-form') {
        const r=state.modalContext.requirement;const body=readRequirement(form);
        if (!body.title || !body.statement || !body.acceptance) throw new Error('请填写标题、需求描述与验收标准。');
        if (r.id) {body.expected_revision=r.revision;await api(`/requirements/${r.id}`,'PATCH',body);} else {if(value('uid'))body.uid=value('uid');await api(endpoint('requirements'),'POST',body);}
        await finishWrite(r.id ? '需求已更新，新的历史版本已保存。' : '需求已创建，可以继续完善并提交评审。');
      } else if (form.id === 'document-form') {
        await api(endpoint('documents'),'POST',{title:value('title'),description:value('description')});await finishWrite('需求文档已创建。');
      } else if (form.id === 'submit-review-form') {
        const r=state.modalContext.requirement;await api(`/requirements/${r.id}/submit`,'POST',{expected_revision:r.revision,reviewer_id:Number(data.get('reviewer_id'))});await finishWrite('已提交评审，等待指定成员处理。');
      } else if (form.id === 'decision-form') {
        const ctx=state.modalContext;await api(`/${ctx.kind === 'review' ? 'reviews' : 'changes'}/${ctx.id}/decide`,'POST',{decision:ctx.decision,comment:value('comment')});await finishWrite(ctx.decision === 'approved' ? '审批已通过，记录已保存。' : '申请已退回，意见已记录。');
      } else if (form.id === 'link-form') {
        if(data.get('source_id') === data.get('target_id')) throw new Error('来源需求和目标需求不能相同。');
        await api(endpoint('links'),'POST',{source_id:Number(data.get('source_id')),target_id:Number(data.get('target_id')),kind:value('kind')});await finishWrite('需求关联已建立。');
      } else if (form.id === 'artifact-form') {
        const a=state.modalContext.artifact;const ids=data.getAll('requirement_ids').map(Number);if(!ids.length)throw new Error('请至少关联一条需求。');
        await api(a.id ? `/artifacts/${a.id}` : endpoint('artifacts'),a.id ? 'PATCH' : 'POST',{title:value('title'),kind:value('kind'),reference:value('reference'),result:value('result'),requirement_ids:ids,...(a.id ? {expected_revision:a.revision} : {})});await finishWrite('验证项与需求关联已保存。');
      } else if (form.id === 'baseline-form') {
        const ids=data.getAll('requirement_ids').map(Number);if(!ids.length)throw new Error('请至少选择一条已批准需求。');
        await api(endpoint('baselines'),'POST',{name:value('name'),requirement_ids:ids});await finishWrite('基线已创建，快照内容已冻结。');
      } else if (form.id === 'select-change-form') {
        await showChangeForm(Number(data.get('requirement_id')));
      } else if (form.id === 'change-form') {
        const r=state.modalContext.requirement;const proposed=readRequirement(form);if(!proposed.title || !proposed.statement || !proposed.acceptance)throw new Error('请填写拟修改需求的标题、描述与验收标准。');
        await api(`/requirements/${r.id}/changes`,'POST',{expected_revision:r.revision,title:value('change_title'),reason:value('change_reason'),proposed});await finishWrite('变更申请已提交，等待其他成员审批。');
      } else if (form.id === 'user-form') {
        await api('/users','POST',{username:value('username'),name:value('name'),password:String(data.get('password') || ''),is_admin:false});await finishWrite('用户已创建，可将该用户添加为项目成员。');
      } else if (form.id === 'member-form') {
        await api(`${endpoint('members')}/${Number(data.get('user_id'))}`,'PUT',{role:value('role')});state.projects=await api('/projects');renderShell();await finishWrite('项目成员角色已保存。');
      } else if (form.id === 'project-form') {
        const p=await api('/projects','POST',{name:value('name'),description:value('description')});state.projects=await api('/projects');state.project=p.id;state.view='dashboard';state.docFilter='';renderShell();await finishWrite('工作空间已创建。');
      }
    } catch(error) {
      if (errorBox && form.isConnected) errorBox.textContent=error.message || '操作失败，请稍后重试。'; else toast(error.message || '操作失败，请稍后重试。',true);
    } finally {
      delete form.dataset.busy;submitters.forEach(button => {button.disabled=false;});
    }
  });
  $('#modal').addEventListener('click',event => {if(event.target === $('#modal')){const rect=$('#modal').getBoundingClientRect();if(event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)closeModal();}});
  $('#modal').addEventListener('cancel',() => {state.modalContext=null;});
  async function boot() {
    try {const session=await api('/auth/me');await startSession(session);} catch(error) {renderLogin();}
  }
  boot();
})();
