/* Offline demonstration fixtures. No scanner, model, solver or PoC is invoked. */
"use strict";
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const escapeHTML = (value) =>
  String(value).replace(
    /[&<>"']/g,
    (ch) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        ch
      ],
  );
const stages = [
  {
    title: "目标冻结",
    en: "Inventory",
    output: "AuditCampaign",
    role: "planner",
    description:
      "冻结抽象代码快照、分析单元与威胁边界，为每次审计保留同一份上下文。",
    log: "已载入 oh-demo-001；锁定 IPC、NAPI、Native 三个抽象单元。",
  },
  {
    title: "静态发现",
    en: "Discovery",
    output: "Finding × 3",
    role: "codeql",
    description:
      "回放三条预置 SARIF 候选，保留规则、CWE 与 source → sink 路径。",
    log: "已归一化 3 条预置告警；静态告警仍是待审计的线索。",
  },
  {
    title: "语义审计",
    en: "Semantic Audit",
    output: "CandidatePacket",
    role: "audit-roles",
    description: "分析攻击者控制、调用链与安全不变量，记录反证检查并冻结候选。",
    log: "已追加不变量与反证摘要；NAPI 案例仍缺对象生命周期事实。",
  },
  {
    title: "证据增强",
    en: "Enrichment",
    output: "Evidence × 12",
    role: "codeql-ai",
    description:
      "回放误报经验、sanitizer、QL 修补与路径复核建议，全部关联候选 ID。",
    log: "经验只提供分析线索；预置 sanitizer 证据支持排除一个抽象候选。",
  },
  {
    title: "独立复核",
    en: "Decision Gate",
    output: "Decision × 3",
    role: "blind-verifier",
    description: "独立复核后，按目标门禁规则区分静态成立、反证排除和证据不足。",
    log: "演示结果：STATIC_ONLY / REJECTED / NEEDS_EVIDENCE；没有真实漏洞确认。",
  },
  {
    title: "经验反馈",
    en: "Feedback",
    output: "ExperienceRecord",
    role: "experience",
    description:
      "将 sanitizer 模式保存为待验证经验，回归验证后才允许提升状态。",
    log: "已演示经验登记：candidate / low；没有实际写入后端知识库。",
  },
  {
    title: "报告输出",
    en: "Reporting",
    output: "DemoReport.md",
    role: "reporter",
    description:
      "汇总证据引用、候选状态与待验证计划，生成可以导出的中文演示报告。",
    log: "演示回放完成；可导出 Markdown 报告和证据 JSON。",
  },
];
const cases = [
  {
    id: "DEMO-001",
    name: "Parcel 长度与目标容量不一致",
    area: "memory",
    cwe: "CWE-787",
    path: "abstract/ipc/parcel_service.cpp",
    unit: "IPC / Parcel",
    severity: "高风险模式",
    chain: ["Parcel::ReadUint32", "CopyPayload", "memcpy"],
    summary:
      "外部 IPC 长度进入固定容量缓冲区；需要核对每条复制路径是否满足边界约束。",
    invariant: "0 ≤ input.length ≤ destination.capacity",
    lines: [
      "void CopyPayload(Parcel& data) {",
      "  uint32_t length = data.ReadUint32();",
      "  char buffer[CAPACITY];",
      "  // required: length <= sizeof(buffer)",
      "  memcpy(buffer, data.ReadBuffer(length), length);",
      "}",
    ],
    highlight: 4,
    final: "STATIC_ONLY",
    conclusion:
      "静态路径与边界缺失假设已齐备，但没有真实可达性证明或执行复现。",
    next: "在冻结版本上确认 IPC 权限和输入约束，准备隔离环境的边界测试计划。",
    evidence: [
      {
        kind: "static_path",
        title: "预置静态路径",
        producer: "CodeQL / SARIF",
        stage: 1,
        content:
          "示例长度从 Parcel 传播到 memcpy 的 length 参数。路径是手工构造的演示材料。",
      },
      {
        kind: "semantic_invariant",
        title: "容量不变量",
        producer: "dataflow-lifetime",
        stage: 2,
        content:
          "若输入长度大于目标容量且路径可达，则复制操作违反缓冲区边界。这里尚未证明真实程序满足这些前提。",
      },
      {
        kind: "counter_evidence",
        title: "反证检查摘要",
        producer: "counterevidence-history",
        stage: 2,
        content:
          "检查点 1：调用方是否限制长度？检查点 2：IPC 权限是否阻断攻击者？抽象示例假定未发现决定性反证。",
      },
      {
        kind: "poc_plan",
        title: "待执行的复现计划",
        producer: "poc-planner",
        stage: 3,
        content:
          "计划在隔离测试环境检查边界输入和复制约束。本演示不提供实际攻击载荷，也不运行测试。PoC 计划不能升级为 CONFIRMED。",
      },
    ],
  },
  {
    id: "DEMO-002",
    name: "Native 清洗函数未被静态建模",
    area: "boundary",
    cwe: "CWE-120",
    path: "abstract/native/validated_copy.cpp",
    unit: "Native / Sanitizer",
    severity: "边界校验模式",
    chain: ["ExternalInput", "ValidateLength", "CopyChecked"],
    summary:
      "静态规则缺少自定义清洗函数模型；完整路径检查可能提供排除候选的决定性反证。",
    invariant: "ValidateLength(len, cap) 必须支配复制操作",
    lines: [
      "bool CopyChecked(Input input) {",
      "  if (!ValidateLength(input.size, CAPACITY))",
      "    return false;",
      "  // the guard dominates every copy",
      "  memcpy(buffer, input.data, input.size);",
      "  return true;",
      "}",
    ],
    highlight: 1,
    final: "REJECTED",
    conclusion:
      "在设定的抽象路径中，容量检查支配所有复制操作，构成决定性反证；经验匹配本身不作为排除依据。",
    next: "为 sanitizer 建模建议准备正反例回归集，再判断是否纳入 QL 查询。",
    evidence: [
      {
        kind: "static_path",
        title: "预置复制路径",
        producer: "CodeQL / SARIF",
        stage: 1,
        content:
          "规则看到了输入到复制操作的路径，但演示设定中尚未对 ValidateLength 建模。",
      },
      {
        kind: "fp_experience",
        title: "相似误报经验",
        producer: "FP Experience",
        stage: 3,
        content:
          "匹配到自定义长度校验模式。经验为 candidate / low，只提示检查函数实现，不能静默删除候选。",
      },
      {
        kind: "function_sanitizer",
        title: "决定性反证（模拟）",
        producer: "Function Sanitizer",
        stage: 3,
        content:
          "演示前提：ValidateLength 精确检查容量，且该检查支配每条复制路径。这是抽象构造的反证，不是实际程序分析结果。",
      },
      {
        kind: "ql_patch",
        title: "QL 模型修补建议",
        producer: "QL Optimizer",
        stage: 3,
        content:
          "建议将经验证的长度关系建模为 guard。修补应另存、评审并通过回归集，不能单凭模型建议覆盖原始查询。",
      },
    ],
  },
  {
    id: "DEMO-003",
    name: "NAPI 异步回调的对象生命周期",
    area: "memory",
    cwe: "CWE-416",
    path: "abstract/napi/async_callback.cpp",
    unit: "NAPI / Lifetime",
    severity: "高风险模式",
    chain: ["ScheduleCallback", "ReleaseOwner", "Callback::Use"],
    summary:
      "异步回调持有对象引用，但取消机制、引用计数和实际调度顺序仍不明确。",
    invariant: "callback 执行期间 owner 必须保持存活",
    lines: [
      "void Schedule(Owner* owner) {",
      "  Queue([owner] {",
      "    owner->Dispatch();  // lifetime unknown",
      "  });",
      "  ReleaseOwner(owner);",
      "  // cancellation / reference count?",
      "}",
    ],
    highlight: 2,
    final: "NEEDS_EVIDENCE",
    conclusion:
      "静态引用链存在，但对象是否真正释放、回调能否执行尚不明确，不能认定为释放后使用。",
    next: "补充引用计数、取消回调、线程调度与所有权证据，再冻结完整候选。",
    evidence: [
      {
        kind: "static_path",
        title: "预置回调引用链",
        producer: "CodeQL / SARIF",
        stage: 1,
        content:
          "抽象回调捕获 owner，后续出现 ReleaseOwner 调用；该顺序不等同于对象已被释放。",
      },
      {
        kind: "lifetime_assumption",
        title: "未解决的所有权假设",
        producer: "dataflow-lifetime",
        stage: 2,
        content:
          "是否存在引用计数？队列是否保存强引用？这些事实未提供，不变量尚未得到完整支持。",
      },
      {
        kind: "counter_evidence",
        title: "取消机制待检查",
        producer: "counterevidence-history",
        stage: 2,
        content:
          "待检查析构是否取消回调，以及队列是否串行化释放和调用。当前不能形成决定性结论。",
      },
      {
        kind: "verification_plan",
        title: "符号复核前置条件",
        producer: "Symbolic Sanitizer",
        stage: 3,
        content:
          "符号执行前需要明确对象布局、调度抽象和释放语义。这里仅记录缺失条件，没有调用求解器。",
      },
    ],
  },
];
const evidence = cases.flatMap((c) =>
  c.evidence.map((item, index) => ({
    ...item,
    id: `EV-${c.id.slice(-3)}-${String(index + 1).padStart(2, "0")}`,
    candidate_id: c.id,
    source_ref: c.path,
    demo: true,
  })),
);
const labels = {
  STATIC_ONLY: "静态证据成立",
  REJECTED: "反证排除",
  NEEDS_EVIDENCE: "需要更多证据",
  CONFIRMED: "确定性复核成立",
  PENDING: "等待复核",
};
const statusClass = {
  STATIC_ONLY: "static",
  REJECTED: "rejected",
  NEEDS_EVIDENCE: "needs",
  CONFIRMED: "confirmed",
  PENDING: "waiting",
};
const badge = (verdict) =>
  `<span class="status ${statusClass[verdict]}">${verdict}</span>`;
const state = {
  stage: 0,
  selected: cases[0].id,
  filter: "all",
  view: "workspace",
  timer: null,
  seenAt: new Map([[0, new Date().toISOString()]]),
};
function verdict(c) {
  return state.stage >= 4 ? c.final : "PENDING";
}
function showToast(message) {
  $("#toast").textContent = message;
  $("#toast").classList.add("show");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(
    () => $("#toast").classList.remove("show"),
    3000,
  );
}
function navigate(view) {
  if (!["workspace", "principles", "evidence", "report"].includes(view)) return;
  state.view = view;
  $$(".view").forEach((el) => el.classList.toggle("active", el.id === view));
  $$("nav [data-view]").forEach((el) => {
    el.classList.toggle("active", el.dataset.view === view);
    if (el.dataset.view === view) el.setAttribute("aria-current", "page");
    else el.removeAttribute("aria-current");
  });
  $("#breadcrumb").textContent = {
    workspace: "审计工作台",
    principles: "原理实验室",
    evidence: "证据档案",
    report: "演示报告",
  }[view];
  history.replaceState(null, "", `#${view}`);
  window.scrollTo({ top: 0, behavior: "instant" });
}
function renderPipeline() {
  $("#pipeline").innerHTML = stages
    .map(
      (s, i) =>
        `<button class="pipeline-node ${i === state.stage ? "current" : i < state.stage ? "done" : ""}" data-stage="${i}" ${i === state.stage ? 'aria-current="step"' : ""} aria-label="第 ${i + 1} 阶段：${s.title}"><span class="node-symbol">${i < state.stage ? "✓" : String(i + 1).padStart(2, "0")}</span><strong>${s.title}</strong><small>${s.en}</small></button>`,
    )
    .join("");
  const current = stages[state.stage];
  $("#stage-icon").textContent = String(state.stage + 1).padStart(2, "0");
  $("#stage-label").textContent = `${current.title} / ${current.en}`;
  $("#stage-description").textContent = current.description;
  $("#stage-output").textContent = current.output;
  $("#phase-value").textContent = current.title;
  $("#phase-foot").textContent = `0${state.stage + 1} / 07 · ${current.en}`;
  const count = evidence.filter((e) => e.stage <= state.stage).length;
  $("#evidence-count").innerHTML =
    `${String(count).padStart(2, "0")}<span>/ 12</span>`;
  $("#evidence-progress").style.width = `${(count / 12) * 100}%`;
  $("#next").disabled = state.stage === 6;
  $("#play").innerHTML = state.timer
    ? "<span>Ⅱ</span> 暂停回放"
    : state.stage === 6
      ? "<span>↺</span> 重新播放"
      : "<span>▶</span> 播放审计过程";
  $("#event-log").innerHTML = stages
    .slice(0, state.stage + 1)
    .map(
      (s, i) =>
        `<div class="log-row"><time>${String(i + 1).padStart(2, "0")} / 07</time><code>${s.role}</code><span>${s.log}</span></div>`,
    )
    .join("");
  $("#event-log").scrollTop = $("#event-log").scrollHeight;
}
function renderFindings() {
  $("#findings").innerHTML = cases
    .filter((c) => state.filter === "all" || c.area === state.filter)
    .map(
      (c) =>
        `<button class="finding ${c.id === state.selected ? "selected" : ""}" data-candidate="${c.id}" aria-pressed="${c.id === state.selected}"><div class="finding-top"><span class="finding-code">${c.id} · ${c.cwe}</span><span class="severity">${c.severity}</span></div><h3>${c.name}</h3><div class="finding-bottom"><span class="finding-path">${c.unit}</span>${badge(verdict(c))}</div></button>`,
    )
    .join("");
  const c = cases.find((c) => c.id === state.selected);
  $("#candidate-id").textContent = c.id;
  $("#candidate-title").textContent = c.name;
  $("#candidate-status").innerHTML = badge(verdict(c));
  $("#candidate-summary").textContent = c.summary;
  $("#call-chain").innerHTML = c.chain
    .map((n) => `<span class="chain-node">${escapeHTML(n)}</span>`)
    .join('<span class="chain-arrow">→</span>');
  $("#code-filename").textContent = c.path.split("/").pop();
  $("#code-sample").innerHTML = c.lines
    .map(
      (line, i) =>
        `<span class="code-line ${i === c.highlight ? "highlight" : ""}"><span class="line-number">${String(i + 1).padStart(2, "0")}</span><span>${escapeHTML(line)}</span></span>`,
    )
    .join("");
  $("#invariant").textContent = c.invariant;
  $("#evidence-mini").innerHTML = evidence
    .filter((e) => e.candidate_id === c.id)
    .map(
      (e) =>
        `<button class="evidence-chip ${state.stage < e.stage ? "pending" : ""}" data-evidence="${e.id}">${state.stage < e.stage ? "◌" : "✓"} ${e.title}</button>`,
    )
    .join("");
}
function renderEvidence() {
  const filter = $("#evidence-filter").value;
  $("#evidence-table").innerHTML = evidence
    .filter((e) => filter === "all" || e.candidate_id === filter)
    .map(
      (e) =>
        `<tr><td>${e.title}<small>${e.id}</small></td><td>${e.producer}</td><td><code>${e.candidate_id}</code></td><td>${stages[e.stage].title}</td><td><span class="status ${e.stage <= state.stage ? "rejected" : "waiting"}">${e.stage <= state.stage ? "已回放 · 模拟" : "待回放"}</span></td><td><button class="text-button" data-evidence="${e.id}" aria-label="查看 ${e.title}">查看 ↗</button></td></tr>`,
    )
    .join("");
}
function reportMarkdown() {
  return (
    `# OpenHarmony Audit Agent · 演示报告\n\n> DEMO ONLY：全部案例均为手工预置的抽象场景，不是实际扫描结果。\n\n## 目标与范围\n\n快照：oh-demo-001（演示标识）；范围：IPC / Parcel、Native / Sanitizer、NAPI / Lifetime。\n当前回放阶段：${state.stage + 1}/7 ${stages[state.stage].title}。\n已回放证据：${evidence.filter((e) => e.stage <= state.stage).length}/12。\n\n## 候选与证据\n\n` +
    cases
      .map(
        (c) =>
          `### ${c.id} · ${c.name}\n\n- 状态：${verdict(c)}（演示）\n- CWE：${c.cwe}；未分配 CVE\n- 抽象位置：${c.path}\n- 调用链：${c.chain.join(" → ")}\n- 不变量：${c.invariant}\n- 说明：${state.stage >= 4 ? c.conclusion : "尚未回放至决策阶段，不能提前给出结论。"}\n- 已回放证据：${
            evidence
              .filter((e) => e.candidate_id === c.id && e.stage <= state.stage)
              .map((e) => e.id)
              .join(", ") || "无"
          }\n- 后续计划：${c.next}\n`,
      )
      .join("\n") +
    `\n## 验证边界\n\n没有调用 CodeQL、模型 API 或符号执行引擎；没有运行 PoC 或真机测试。案例状态展示目标方法规则，不代表后端运行结果或比赛成绩。Python 后端与此交互前端尚未接入。原理实验室的实验状态不计入本报告。\n`
  );
}
function renderReport() {
  $("#report-paper").innerHTML =
    `<div class="report-kicker">BINNNN LAB / RESEARCH DEMONSTRATION</div><h2>OpenHarmony 源码审计<br>证据链演示报告</h2><div class="report-subtitle">DEMO ONLY · oh-demo-001 · 回放阶段 ${state.stage + 1} / 7</div><h3 id="report-context">01　目标与范围</h3><p>覆盖 IPC / Parcel、Native / Sanitizer、NAPI / Lifetime 三类抽象场景。演示展示统一工作流如何组织证据，不包含真实漏洞结论或实验性能数据。</p><h3 id="report-findings">02　候选与证据</h3><table><thead><tr><th>候选 / CWE</th><th>演示状态</th></tr></thead><tbody>${cases.map((c) => `<tr><td>${c.name}<small>${c.id} · ${c.cwe}</small></td><td>${badge(verdict(c))}</td></tr>`).join("")}</tbody></table>${cases.map((c) => `<h3>${c.id} / ${c.name}</h3><p>${state.stage >= 4 ? c.conclusion : "尚未回放至决策阶段。请继续播放审计流程，查看证据如何支持后续判断。"}</p><p><strong>待验证事项：</strong>${c.next}</p>`).join("")}<h3 id="report-limitations">03　验证边界</h3><p>全部案例均为预置数据。没有调用真实扫描引擎、模型 API 或符号求解器，也没有执行 PoC。当前页面未与 Python 后端接通，演示决策展示目标方法规则，不能作为真实漏洞或比赛成绩提交。</p><div class="report-stamp">ILLUSTRATIVE CASES · NOT VERIFIED FINDINGS</div>`;
}
function render() {
  renderPipeline();
  renderFindings();
  renderEvidence();
  renderReport();
}
function stop() {
  clearInterval(state.timer);
  state.timer = null;
  renderPipeline();
}
function moveTo(stage) {
  state.stage = stage;
  for (let i = 0; i <= stage; i++)
    if (!state.seenAt.has(i)) state.seenAt.set(i, new Date().toISOString());
  for (const i of state.seenAt.keys()) if (i > stage) state.seenAt.delete(i);
  if (stage === 6) {
    clearInterval(state.timer);
    state.timer = null;
  }
  render();
}
function play() {
  if (state.timer) {
    stop();
    return;
  }
  if (state.stage === 6) {
    state.seenAt.clear();
    moveTo(0);
  }
  state.timer = setInterval(() => moveTo(Math.min(6, state.stage + 1)), 2400);
  renderPipeline();
}
function showEvidence(id) {
  const item = evidence.find((e) => e.id === id);
  if (!item) return;
  $("#dialog-title").textContent = item.title;
  const data = {
    demo: true,
    evidence_id: item.id,
    candidate_id: item.candidate_id,
    kind: item.kind,
    producer: item.producer,
    source_ref: item.source_ref,
    input_snapshot: "oh-demo-001 (illustrative)",
    status: item.stage <= state.stage ? "replayed_fixture" : "pending_fixture",
    rule_version: "demo-fixture-v1",
    model_version: null,
    source_created_at: null,
    content_hash: null,
    content: { summary: item.content },
  };
  $("#dialog-content").innerHTML =
    `<p>${escapeHTML(item.content)}</p><pre>${escapeHTML(JSON.stringify(data, null, 2))}</pre><p>空值表示没有真实运行凭证。预置内容不构成可用于确认实际漏洞的证据。</p>`;
  $("#evidence-dialog").showModal();
}
function download(filename, content, type) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  showToast(`已导出 ${filename}`);
}
const architecture = {
  discovery: [
    "CodeQL / 高召回的候选发现",
    "通过规则与数据流近似生成 SARIF，保留 ruleId、CWE、源码位置及 code flow。静态告警是审计输入，不能直接当作最终漏洞。",
  ],
  workflow: [
    "审计工作流 / 统一调度中心",
    "分配入口、数据流、反证等角色，冻结 CandidatePacket，再调用 CodeQL-AI 的复核能力。盲验证仅接收重建所需的事实，避免读取发现阶段结论。",
  ],
  experience: [
    "FP Experience / 可回归的经验",
    "相似经验帮助提出反证假设，但低置信度经验不能直接抑制告警。新经验以 candidate / low 登记，经跨样例回归验证后再提升状态。",
  ],
  sanitizer: [
    "Function Sanitizer / 识别语义上的保护",
    "检查自定义函数是否真正约束输入，以及该约束是否在所有相关路径上成立。函数名字含 Safe 或 Check 并不足以证明安全。",
  ],
  optimizer: [
    "QL Optimizer / 修补分析模型",
    "将经过验证的清洗或 guard 关系写成候选 QL 修补。保留原始查询，通过正反例回归确认误报减少没有引入新的漏报。",
  ],
  symbolic: [
    "Symbolic Sanitizer / 有边界的路径复核",
    "对关键路径施加明确的攻击条件和环境假设。SAT 只证明模型约束内的可达性；UNSAT 也只能排除覆盖范围内的路径，超时或 UNKNOWN 不能视为安全。",
  ],
  gate: [
    "Decision Gate / 由证据决定结论",
    "先看决定性反证，再检查静态路径、不变量、攻击者控制、危险操作和反证覆盖。基础证据完整时为 STATIC_ONLY；有效确定性复核可进一步支持 CONFIRMED。",
  ],
};
function explainArchitecture(key) {
  const [title, text] = architecture[key];
  $("#arch-explanation").innerHTML = `<strong>${title}</strong>${text}`;
  $$("[data-arch]").forEach((el) =>
    el.setAttribute("aria-pressed", el.dataset.arch === key),
  );
}
const gateFields = [
  ["path", "存在静态路径", "静态告警包含可追踪的 source → sink 路径。", true],
  [
    "invariant",
    "不变量与攻击条件明确",
    "包含攻击者控制、危险操作和待证明的不变量。",
    true,
  ],
  ["counter", "反证检查完成", "已检查可能阻断或清洗该路径的条件。", true],
  [
    "deterministic",
    "获得有效的确定性复核",
    "模拟已取得适用范围内的符号可达性或复现证据。",
    false,
  ],
  ["reject", "存在决定性反证", "模拟已证明保护条件覆盖相关路径。", false],
];
function evaluateDemoGate(input) {
  if (input.reject)
    return {
      verdict: "REJECTED",
      reason:
        "决定性反证排除了当前候选。在限定路径和前提下排除，不外推为整个组件安全。",
      missing: "经验匹配本身不能构成决定性反证。",
    };
  const absent = [
    !input.path && "静态路径",
    !input.invariant && "不变量与攻击条件",
    !input.counter && "反证检查",
  ].filter(Boolean);
  if (absent.length)
    return {
      verdict: "NEEDS_EVIDENCE",
      reason:
        "基础证据还没有闭合，即使模型非常确信或勾选了复核，也无法补齐缺失的前提。",
      missing: "仍需补齐：" + absent.join("、"),
    };
  if (input.deterministic)
    return {
      verdict: "CONFIRMED",
      reason:
        "基础证据齐备，且假设已获得范围明确的确定性复核。这个结果只是在当前实验条件下的模拟。",
      missing: "真实任务还需核对证据有效性、输入版本与复核范围。",
    };
  return {
    verdict: "STATIC_ONLY",
    reason:
      "静态与语义证据支持漏洞假设，但缺少确定性复核。保留候选并明确待验证事项。",
    missing: "仍需补齐：有效的符号可达性、PoC 执行或其他确定性复核。",
  };
}
function renderGate() {
  const input = Object.fromEntries(
    gateFields.map(([key]) => [key, $(`#gate-${key}`).checked]),
  );
  const decision = evaluateDemoGate(input);
  $("#gate-verdict").textContent = decision.verdict;
  $("#gate-title").textContent = labels[decision.verdict];
  $("#gate-reason").textContent = decision.reason;
  $("#gate-missing").textContent = decision.missing;
  $("#gate-emblem").textContent = {
    REJECTED: "⊘",
    NEEDS_EVIDENCE: "◌",
    STATIC_ONLY: "◇",
    CONFIRMED: "✓",
  }[decision.verdict];
}
const roles = [
  [
    "入口与边界",
    "entrypoint-boundary",
    "识别外部入口、攻击者控制量和信任边界。",
  ],
  [
    "数据流与生命周期",
    "dataflow-lifetime",
    "追踪容量、类型、所有权与危险操作。",
  ],
  ["反证与历史", "counterevidence-history", "主动寻找能推翻漏洞假设的条件。"],
  ["调用链组合", "chain-composer", "把逐跳事实组合成完整不变量。"],
  ["独立盲验证", "blind-verifier", "隔离发现阶段结论，独立重建证据。"],
  ["复现计划", "poc-planner", "列出复现条件和验证步骤，不自动执行。"],
  ["中文报告", "reporter", "引用证据，说明影响、修复与局限。"],
];
$("#gate-inputs").innerHTML = gateFields
  .map(
    ([key, title, desc, checked]) =>
      `<label class="gate-input"><input type="checkbox" id="gate-${key}" ${checked ? "checked" : ""}><span><strong>${title}</strong><small>${desc}</small></span></label>`,
  )
  .join("");
$("#roles").innerHTML = roles
  .map(
    ([title, role, desc], i) =>
      `<article class="role-card"><small>ROLE / 0${i + 1}</small><h3>${title}</h3><code>${role}</code><p>${desc}</p></article>`,
  )
  .join("");
$("#evidence-filter").insertAdjacentHTML(
  "beforeend",
  cases.map((c) => `<option value="${c.id}">${c.id}</option>`).join(""),
);
document.addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) return;
  if (button.dataset.view) navigate(button.dataset.view);
  if (button.dataset.stage !== undefined) {
    stop();
    moveTo(Number(button.dataset.stage));
  }
  if (button.dataset.candidate) {
    state.selected = button.dataset.candidate;
    renderFindings();
  }
  if (button.dataset.filter) {
    state.filter = button.dataset.filter;
    const visible = cases.filter(
      (c) => state.filter === "all" || c.area === state.filter,
    );
    if (!visible.some((c) => c.id === state.selected))
      state.selected = visible[0].id;
    $$("[data-filter]").forEach((el) => {
      el.classList.toggle("active", el === button);
      el.setAttribute("aria-pressed", String(el === button));
    });
    renderFindings();
  }
  if (button.dataset.evidence) showEvidence(button.dataset.evidence);
  if (button.dataset.arch) explainArchitecture(button.dataset.arch);
});
$("#play").addEventListener("click", play);
$("#next").addEventListener("click", () => {
  stop();
  moveTo(Math.min(6, state.stage + 1));
});
$("#reset").addEventListener("click", () => {
  stop();
  state.seenAt.clear();
  moveTo(0);
  showToast("回放已重置，所有模拟证据恢复待回放状态");
});
$("#evidence-filter").addEventListener("change", renderEvidence);
$("#close-dialog").addEventListener("click", () =>
  $("#evidence-dialog").close(),
);
$("#evidence-dialog").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) {
    const r = e.currentTarget.getBoundingClientRect();
    if (
      e.clientX < r.left ||
      e.clientX > r.right ||
      e.clientY < r.top ||
      e.clientY > r.bottom
    )
      e.currentTarget.close();
  }
});
$("#gate-inputs").addEventListener("change", renderGate);
$("#confidence").addEventListener("input", (event) => {
  $("#confidence-value").textContent = `${event.target.value}%`;
});
$("#reset-lab").addEventListener("click", () => {
  gateFields.forEach(
    ([key, , , checked]) => ($(`#gate-${key}`).checked = checked),
  );
  $("#confidence").value = 95;
  $("#confidence-value").textContent = "95%";
  renderGate();
});
$("#present").addEventListener("click", () => {
  const focused = document.body.classList.toggle("focus-mode");
  $("#present").setAttribute("aria-pressed", String(focused));
  showToast(
    focused ? "已进入专注演示，再次点击右上角可恢复导航" : "已恢复完整工作台",
  );
});
$("#export-report").addEventListener("click", () =>
  download(
    "openharmony-demo-report.md",
    reportMarkdown(),
    "text/markdown;charset=utf-8",
  ),
);
$("#export-json").addEventListener("click", () =>
  download(
    "openharmony-demo-evidence.json",
    JSON.stringify(
      {
        schema: "audit-demo-export-v1",
        demo: true,
        notice:
          "Illustrative fixtures, not backend results or vulnerability evidence",
        exported_at: new Date().toISOString(),
        stage: stages[state.stage].en,
        evidence: evidence
          .filter((e) => e.stage <= state.stage)
          .map((e) => ({
            ...e,
            status: "replayed_fixture",
            rule_version: "demo-fixture-v1",
            model_version: null,
            source_created_at: null,
            content_hash: null,
          })),
        decisions: cases.map((c) => ({
          candidate_id: c.id,
          verdict: verdict(c),
          demo: true,
        })),
      },
      null,
      2,
    ),
    "application/json;charset=utf-8",
  ),
);
document.addEventListener("visibilitychange", () => {
  if (document.hidden && state.timer) stop();
});
window.addEventListener("hashchange", () => {
  const route = location.hash.slice(1);
  if (["workspace", "principles", "evidence", "report"].includes(route))
    navigate(route);
});
explainArchitecture("workflow");
renderGate();
render();
navigate(location.hash.slice(1) || "workspace");
