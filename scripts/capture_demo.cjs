/* Capture real local HTML interactions and actual dry-run output for an edited demo.
 * Run from repository root. Requires frontend npm ci; no model/CodeQL calls.
 */
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {execFileSync} = require('node:child_process');
const puppeteer = require('../frontend/node_modules/puppeteer-core');
const root = path.resolve(__dirname, '..');
const output = path.join(root, 'tmp/video');
fs.mkdirSync(output, {recursive:true});
const frames = [];
const escape = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const python = process.env.AUDIT_PYTHON || 'python';
const common = ['--workflow','config/workflow.audit.example.json','--target','config/target.openharmony.abstract.json'];
// Each recording uses a fresh run directory so existing task state is not overwritten.
const runRoot = 'tmp/video/run-' + Date.now();
function run(args){
  const stdout = execFileSync(python,['-m','openharmony_audit','workflow',...args], {
    cwd:root, encoding:'utf8', env:{...process.env,PYTHONUTF8:'1',PYTHONIOENCODING:'utf-8',PYTHONPATH:path.join(root,'src')}
  });
  return JSON.parse(stdout);
}
(async()=>{
  const browser = await puppeteer.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{channel:'chrome'})});
  try {
    const page = await browser.newPage();
    await page.setViewport({width:1440,height:900});
    await page.emulateMediaFeatures([{name:'prefers-reduced-motion',value:'reduce'}]);
    const capture = async (title, caption, duration=8) => {
      const file = String(frames.length+1).padStart(2,'0')+'.png';
      await page.screenshot({path:path.join(output,file)});
      frames.push({file,title,caption,duration});
    };
    const card = async (title, body) => {
      await page.setContent(`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><style>
      *{box-sizing:border-box}body{margin:0;background:#101d25;color:#e9eee7;font:23px/1.8 "Microsoft YaHei",sans-serif;padding:65px 80px}.label{color:#a9ddc6;font-size:15px;letter-spacing:3px}h1{font-size:40px;font-weight:500;margin:25px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#09171c;padding:26px;border:1px solid #2c4147;font:20px/1.65 Consolas,"Microsoft YaHei",monospace}p{color:#b2c7c5}li{margin:12px 0}</style><div class="label">OPENHARMONY AUDIT AGENT / 工程原型操作演示</div><h1>${escape(title)}</h1>${body}</html>`);
    };
    await card('源码审计工作流与按需辅助验证', '<p>题目一 · 交付件 3 · 字幕版 DEMO</p><ul><li>环境与实际命令：配置校验、任务规划、任务准备、状态读取</li><li>交互演示：角色调查、候选交接、辅助核查、检查点恢复</li><li>原理说明：不变量、反证、独立复核与经验回写</li></ul><p>画面由实际操作截图剪辑组成。案例为抽象示例，未运行真实漏洞扫描。</p>');
    await capture('演示内容','本视频展示工程原型。主体负责审计，CodeQL-AI 根据具体问题提供辅助验证。',10);
    await card('运行环境与安装', '<ul><li>HTML：现代浏览器，离线打开，无需密钥。</li><li>主体准备：Python 3.10+，从源码目录安装基础包。</li><li>实际审计：Claude Code、可用模型与认证、真实源码。</li><li>辅助验证：按需配置 CodeQL、FastMCP、angr 和相应目标产物。</li></ul><pre>python -m venv .venv\n.\\.venv\\Scripts\\python.exe -m pip install -e .</pre><p>以下命令使用已配置的 Python 环境，仅执行抽象目标 dry-run。</p>');
    await capture('依赖与安装','基础准备不需要 CodeQL。实际运行 Agent 需要另行配置源码、模型与认证。',12);
    const valid=run(['validate',...common]);
    await card('01 / 校验目标和工作流', '<pre>python -m openharmony_audit workflow validate\n  --workflow config/workflow.audit.example.json\n  --target config/target.openharmony.abstract.json</pre><pre>'+escape(JSON.stringify(valid,null,2))+'</pre><p>以上为本次命令的实际输出。抽象路径只做结构校验。</p>');
    await capture('实际命令 · validate','配置校验返回 VALID。当前目标包含抽象组件，没有绑定真实 OpenHarmony 源码。',9);
    const plan=run(['plan',...common]);
    const planSummary='schema: '+plan.schema+'\n\n'+plan.workers.map(w=>w.id+': '+w.units.map(u=>u.id).join(', ')).join('\n\n');
    await card('02 / 生成任务计划', '<pre>python -m openharmony_audit workflow plan\n  --workflow config/workflow.audit.example.json\n  --target config/target.openharmony.abstract.json</pre><pre>'+escape(planSummary)+'</pre><p>画面摘取实际计划中的 schema 和 worker 分配字段。</p>');
    await capture('实际命令 · plan','总控把分析单元分给 worker。规划阶段只生成分工，不调用模型。',9);
    run(['prepare',...common,'--run-root',runRoot,'--allow-missing-source']);
    const files=[];
    function list(dir){for(const e of fs.readdirSync(dir,{withFileTypes:true})){const f=path.join(dir,e.name);if(e.isDirectory())list(f);else files.push(path.relative(path.join(root,runRoot),f).replace(/\\/g,'/'));}}
    list(path.join(root,runRoot));
    await card('03 / 准备 worker 任务包', '<pre>python -m openharmony_audit workflow prepare\n  --workflow config/workflow.audit.example.json\n  --target config/target.openharmony.abstract.json\n  --run-root &lt;独立运行目录&gt; --allow-missing-source</pre><pre>'+escape(files.filter(f=>/plan.json|worker-1/.test(f)).slice(0,10).join('\n'))+'</pre><p>列表来自本次实际生成的目录。worker-2 同样有独立任务包。</p>');
    await capture('实际命令 · prepare','准备结果包含任务分配、总控提示词、角色协议和检查点提示词。',10);
    const status=run(['status','--run-root',runRoot]);
    const statusSummary='campaignId: '+status.campaignId+'\n\n'+status.workers.map(w=>w.worker+': '+JSON.stringify(w.status)).join('\n\n');
    await card('04 / 查看任务状态', '<pre>python -m openharmony_audit workflow status\n  --run-root &lt;独立运行目录&gt;</pre><pre>'+escape(statusSummary)+'</pre><p>NOT_STARTED 表示尚未启动模型审计。真实任务使用 workflow run 启动。</p>');
    await capture('实际命令 · status','两个 worker 尚未启动。这里完成的是任务准备，不是一次漏洞扫描。',10);
    await page.goto(pathToFileURL(path.join(root,'frontend/demo.html')).href);
    const choose=async n=>{await page.click(`[data-chapter="${n-1}"]`);await page.evaluate(()=>scrollTo(0,0));};
    await capture('HTML / 审计主体','主体从源码、攻击边界和安全不变量出发，组织角色调查并生成候选。',8);
    await choose(2);
    await capture('任务拆分','总控固定目标快照，安排各 worker 的范围。源码审计可以独立开始。',8);
    await page.click('[data-flow="roles"]');
    await capture('角色协作','入口、数据流和反证角色各自调查。总控合并材料，冻结候选 DEMO-001 的 r1 版本。',9);
    await page.click('[data-flow="call"]');
    await capture('按需调用辅助工具','遇到保护函数或路径约束问题时，再为当前候选发起具体的辅助检查。',9);
    await page.click('#flow-return');
    await capture('证据回写 / 页面模拟','点击“演示证据返回”，新增 DEMO-E01。候选标识与版本保持一致，结果交由主体复核。',9);
    await page.click('[data-flow="checkpoint"]');
    await page.click('#flow-save');
    await capture('保存与中断 / 页面模拟','保存候选、证据引用和剩余工作后中断。这个交互状态只存于页面内存。',8);
    await page.click('#flow-resume');
    await capture('恢复继续 / 页面模拟','点击恢复继续。候选 DEMO-001/r1 和已返回证据仍然保留。',8);
    await page.click('[data-flow="map"]');
    await capture('分工与结构','审计工作流控制调查和复核。CodeQL-AI 的经验、函数与路径检查作为可选辅助。',9);
    await choose(3);
    const steps=[
      ['入口调查','抽象 Parcel 示例中，角色调查长度参数由谁提供，以及它经过哪些边界。'],
      ['数据流分析','沿调用关系核对长度和目标容量。这里的安全不变量是复制长度不能超过容量。'],
      ['候选冻结','总控固定代码位置、调用链和待核查条件，交给后续角色复核。'],
      ['反证与辅助','主动查找容量检查、调用方限制和权限条件；需要时用辅助工具核对保护是否有效。'],
      ['独立复核','独立角色重建路径。当前抽象案例保留 STATIC_ONLY，没有运行真实 PoC。']
    ];
    for(let i=0;i<steps.length;i++){if(i)await page.click('#next');await capture(...steps[i],9);}
    await choose(4);
    await capture('局部验证问题','长度设为 96，目标容量为 64。示例模型中，危险条件可以满足。',8);
    const length=async n=>page.$eval('#length',(el,n)=>{el.value=n;el.dispatchEvent(new Event('input',{bubbles:true}));},n);
    await length(32);
    await capture('单个安全输入的范围','长度改为 32 时，本次输入满足容量。但整个输入域仍然包含超过 64 的值。',8);
    await length(96);await page.click('#guard');
    await capture('补充完整的容量检查','开启检查后，玩具域内的危险路径被阻断。页面枚举有限整数，没有调用真实符号执行引擎。',10);
    await choose(5);
    for(const [key,title,caption] of [
      ['needs','证据不足','基础事实缺失时保留 NEEDS_EVIDENCE，并指出还需要查什么。'],
      ['static','源码与静态证据','调用链和不变量已有依据，但确定性验证尚缺时保留 STATIC_ONLY。'],
      ['confirmed','确认所需条件','CONFIRMED 要有独立复核及有效的确定性验证材料。点击卡片只展示规则。'],
      ['rejected','决定性反证','已有证据否定关键前提时可以 REJECTED；超时或工具失败不构成反证。']
    ]){await page.click(`[data-verdict="${key}"]`);await capture(title,caption,8);}
    await choose(6);
    await capture('经验反馈','经复核的误报和保护模式形成候选经验，保留来源、版本和适用条件。',8);
    await page.click('#cycle-next');
    await capture('回归验证','使用正反例检查经验；保护有效与保护失效的情形都要覆盖。',8);
    await page.click('#cycle-next');
    await capture('限定范围复用','经过回归的经验仍需匹配当前源码和条件。相似文字不能直接消除告警。',8);
    await choose(7);
    await capture('如何检验辅助工具的收益','主体独立运行作为主要基线，再比较主体加按需辅助。固定快照、预算与复核标准。',10);
    await choose(8);
    await capture('当前交付范围','交付源码、技术说明、使用说明和原型视频。真实漏洞材料由团队补充。',9);
    await card('性能说明与后续实测', '<ul><li>已有数据：1,000 / 10,000 / 50,000 个合成分析单元的规划开销。</li><li>这项测量没有读取源码，没有调用模型或 CodeQL。</li><li>正式大规模扫描需记录源码快照、规模、总耗时与采样内存。</li></ul><pre>python scripts/measure_command.py\n  --output reports/audit-measurement.json\n  --scope source-audit --snapshot YOUR_COMMIT --\n  python -m openharmony_audit workflow run --run-root &lt;真实任务目录&gt;</pre><p>测量入口已提供。执行最后一条命令会启动真实 Agent。</p>');
    await capture('性能数据的范围','当前规划数据不能替代大规模漏洞扫描性能。正式测量需要实际任务和完整运行记录。',12);
    fs.writeFileSync(path.join(output,'frames.json'),JSON.stringify({kind:'edited-operation-screenshots',frames},null,2));
    console.log(`Captured ${frames.length} operation frames; ${frames.reduce((n,f)=>n+f.duration,0)} seconds.`);
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
