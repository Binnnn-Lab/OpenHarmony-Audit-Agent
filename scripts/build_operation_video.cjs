/* Build the operation replay, timed voiceover and subtitles from real run records. */
const fs=require('node:fs');
const path=require('node:path');
process.chdir(path.resolve(__dirname,'..'));
const dir='reports/operation-demo';
const load=n=>JSON.parse(fs.readFileSync(`${dir}/${n}.json`,'utf8'));
const meta=load('session'),review=load('source-review'),measurement=load('measurement'),state=load('worker-state'),checkpoint=load('checkpoint');
if(state.state!=='COMPLETE'||!state.terminal||measurement.returncode!==0)throw new Error('A completed real run is required');
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const pre=s=>'<pre>'+esc(typeof s==='string'?s:JSON.stringify(s,null,2))+'</pre>';
const rows=a=>a.map(([k,v])=>`<div class="row"><b>${esc(k)}</b>　${esc(v)}</div>`).join('');
const metric=(v,l)=>`<div class="metric"><strong>${esc(v)}</strong><span>${esc(l)}</span></div>`;
const base='python -m openharmony_audit workflow';
const options='--workflow tmp/operation-demo/workflow.json\n  --target tmp/operation-demo/target.json';
const runroot='tmp/operation-demo/run';
const checks=review.checks.slice(0,3);
const scenes=[];
function add(stage,label,title,subtitle,file,command,html,note,speech,extra={}){
 const spoken=speech.replace(/[A-Za-z_]/g,'').replace(/\s/g,'').length;
 scenes.push({stage,label,title,subtitle,file,command,html,note,speech,duration:Math.max(18,Math.ceil(spoken/4.4)+6),...extra});
}
add(0,'START','从配置到结果，跑一次源码审计','OpenHarmony 官方 c_utils 组件 · 本次任务记录','任务概览','',
 rows([['分析对象','Parcel 的缓冲区写入与容量检查'],['主体','审计工作流：范围、任务、源码调查、结果保存'],['运行时','Codex / '+meta.model],['本次产物','源码记录、检查报告、检查点、任务状态']]),
 '画面使用本次命令输出和实际文件，运行等待段经过剪辑。',
 '大家好，这段视频演示我们的 OpenHarmony 代码审计工具。我会从运行环境和目标配置开始，接着展示任务怎样启动，以及完成后怎样查看结果。选用的是官方基础工具库里的 Parcel 代码，重点看缓冲区写入和容量检查。画面中的命令和文件都来自这次运行，等待过程做了剪辑。');
add(0,'WORKFLOW','主体组织调查，辅助工具回答具体问题','源码审计 → 候选与证据 → 复核与报告','工作流分工','',
 rows([['任务准备','固定源码版本、划分分析范围、生成 worker 任务包'],['源码调查','入口参数 → 数据流与容量 → 已有保护条件'],['按需辅助','CodeQL-AI：函数保护、静态路径、误报经验'],['结果保存','源码位置、检查依据、后续问题、状态与检查点']]),
 '本次配置：一个 worker，顺序检查三个视角。',
 '我们的主体是审计工作流。它负责安排调查范围、组织源码检查，并把结果保存下来。CodeQL-AI 用于辅助核对具体的函数和路径。本次用一个工作单元，按入口参数、数据流和保护条件这三个视角顺序检查，便于看清任务的输入和输出。');
add(1,'ENVIRONMENT','检查环境，安装工具','Python 基础包 + Codex 命令行','环境与安装 · 本次输出',
 'python --version\ncodex --version\npython -m pip install -e . --no-deps',
 pre(load('01-environment').stdout.trim()+'\n'+load('03-codex-version').stdout.trim()+'\n\n'+load('02-install').stdout.split('\n').filter(l=>/Successfully|Building editable|Created wheel/.test(l)).join('\n')),
 '最低 Python 版本：3.10；本次使用 '+esc(meta.python)+'。模型认证由本机已有 Codex 配置提供。',
 '工具主体需要 Python 三点十及以上版本。这次机器上的版本显示在这里。安装时，在源码根目录执行 pip install，装好后就可以使用统一命令入口。这次选择 Codex 调用模型，所以也检查了 Codex 的版本，并使用本机已经配置好的模型认证。');
add(1,'TARGET','确定源码版本和检查范围','每次任务都带上确定的代码版本','target.json · 关键字段','',
 pre({id:meta.target.id,source:{adapter:'git-repository',root:'<PROJECT>/tmp/demo-source-c-utils',revision:meta.revision},units:meta.target.units}),
 '源码来源：github.com/openharmony/commonlibrary_c_utils',
 '目标配置里，最重要的是源码位置、代码版本和检查范围。这次使用官方工具库的一个固定提交，主要检查三个函数：写入缓冲区、保证可写容量，以及实际复制数据的函数。它们都在同一个源文件里。相关的直接辅助函数，也会随着调用关系一起查看。');
add(1,'RUNTIME','选择 Codex，保留工作流的任务接口','同一套 validate / plan / prepare / run / status 命令','workflow.json · 运行设置','',
 pre({runtime:{adapter:'codex',model:meta.model,outputFormat:'jsonl',maxCycles:1},parallelism:{rootWorkers:1,subagentsPerWorker:1},phases:meta.workflow.phases.map(p=>p.id)}),
 '认证信息由运行环境提供；任务配置保存模型名和运行设置。',
 '工作流配置决定用哪个运行时、哪个模型，以及安排多少工作单元。这里选的是 Codex，模型名称和并发设置都可以看到。后面的命令保持一致，换目标时，主要调整源码配置和分析范围。每次任务也会保存这些设置，方便之后核对。');
add(2,'VALIDATE','校验配置与实际源码目录','检查提示词、目标路径和分析单元','04-validate.json · 标准输出',
 base+' validate\n  '+options+' --strict-source',pre(load('04-validate').stdout),
 '退出码：0 · strict-source 检查实际目录和文件是否存在。',
 '配置写好后，运行 validate。这里加上 strict-source，检查实际源码目录和文件。命令返回 VALID，表示当前配置和路径检查通过，可以进入任务准备。路径或者配置有问题时，就在这一步根据错误信息修改。');
const plan=JSON.parse(load('05-plan').stdout);
add(2,'PLAN','查看任务分配','本次分析单元分给 worker-1','plan · 分配字段',
 base+' plan\n  '+options,
 pre({schema:plan.schema,campaignId:plan.campaignId,workers:plan.workers}),
 '画面摘取本次 plan 输出中的任务分配字段。',
 '接着运行 plan，看任务怎么分。当前只有一个分析单元，所以分给 worker 一。这里列出了文件位置、关注的函数和角色设置。目标规模扩大后，可以配置更多分析单元，由规划器分配给不同工作单元。');
add(2,'PREPARE','生成任务包，查看交接文件','assignment.json 固定范围，prompt.md 携带执行说明','本次生成的 worker 目录',
 base+' prepare\n  '+options+'\n  --run-root '+runroot,
 pre('run/\n  plan.json\n  workers/worker-1/\n    assignment.json\n    prompt.md\n    roles.md\n    blind-verifier.md\n    checkpoint-prompt.md\n  shared/\n    candidates/\n    verification/\n    reports/'),
 '文件由本次 prepare 命令生成。',
 'prepare 会把计划变成实际文件。每个工作单元都有自己的任务分配、总控提示词、角色说明和检查点提示词。任务启动后，就从这些文件读取范围和要求。这样，配置、执行和后续检查都能对上同一份任务。');
add(2,'READY','启动前查看状态','任务包已生成，worker 等待运行','07-status-before.json · 标准输出',
 base+' status --run-root '+runroot,pre(load('07-status-before').stdout),
 'NOT_STARTED：当前任务尚未启动。',
 '启动前可以用 status 看一下状态。这里显示 NOT_STARTED，说明任务包已经准备好，工作单元还在等待执行。后面仍然用这条命令查看进度和完成状态。');
const events=load('events');
const commands=events.filter(e=>e.type==='command.completed');
add(3,'RUN','启动任务，记录运行过程','Codex 读取任务与源码，检查结果写入 worker 目录','08-run.json / events.json',
 base+' run --run-root '+runroot,
 rows([['运行入口','workflow run'],['已记录的命令操作',commands.length+' 次'],['运行事件',events.filter(e=>/thread.started|turn.started|turn.completed/.test(e.type)).map(e=>e.type).join(' → ')],['已完成的输出文件',state.artifacts.join('、')]])+
 '<p class="small" style="margin-top:22px">日志保存于 controller-001.stream.jsonl；本页摘取事件类型和产物名称。</p>',
 '运行等待段已剪辑。完整测量时长见后面的性能记录。',
 '现在进入 run。工作流启动 Codex，读取任务包和目标源码。运行期间，事件会保存到日志里，文件操作和最后的状态也能查到。这次从指定的写入入口沿调用关系检查，随后把源码记录、报告和检查点写进工作单元目录。');
add(3,'COMPLETE','任务完成，核对产物','状态文件与实际输出对应','worker-state.json · 字段节选',
 base+' status --run-root '+runroot,
 pre({state:state.state,terminal:state.terminal,scope:state.scope,completed_units:state.completed_units,artifacts:state.artifacts,candidate_count:state.candidate_count}),
 '本次结果：限定范围源码检查完成，候选数量 '+review.candidate_count+'。',
 '运行结束后，再看一次状态。现在显示 COMPLETE，下面列出了已经生成的四份文件。本次候选数量是零。接下来打开检查记录，看它读了哪些函数、查到了哪些保护条件，以及留下了哪些需要继续核对的问题。');
const excerpt=load('source-excerpt');
add(4,'SOURCE','对照源码看检查依据','WriteBuffer：参数、补齐长度和写入顺序','base/src/parcel.cpp · 409–432 行','',
 '<pre>'+excerpt.lines.map(l=>`<span class="code-line ${[411,419,423,424,427].includes(l.number)?'hot':''}"><span class="line-number">${l.number}</span>${esc(l.text)}</span>`).join('')+'</pre>',
 '源码节选来源：OpenHarmony c_utils · Apache-2.0 · '+meta.revision.slice(0,12),
 '看一下实际源码。写入函数会检查空指针和零长度，然后计算补齐后的容量需求。高亮的位置检查加法是否回绕。继续往下，容量准备成功后才复制数据，复制成功后才处理补齐。记录里引用的行号，就对应这里的这些条件。',
 {scroll:true});
add(4,'CHECKS','查看函数级检查记录','三个目标函数，以及沿调用关系检查的四个辅助函数','source-review.json · checks 节选','',
 checks.map(c=>`<div class="check"><b>${esc(c.function)}</b><p>${esc(c.observation)}</p><p class="small">${esc(c.location)}</p></div>`).join(''),
 '总计 '+review.scope.length+' 个函数；观察事实、保护条件和后续问题分别保存。',
 '检查记录按函数整理。写入入口记录参数和补齐检查；容量函数记录可写状态、扩容条件和分配结果；复制函数记录剩余容量以及复制失败时的处理。每条都有源码位置，后续复核的人可以直接回到对应代码。');
add(4,'REPORT','打开检查报告','将源码位置和检查结果整理为可读记录','review-report.md · 前三项节选','',
 pre(fs.readFileSync(`${dir}/review-report.md`,'utf8').split(/\r?\n\r?\n/).slice(0,5).join('\n\n')),
 '本次生成的报告文件，可与 source-review.json 交叉查看。',
 '这份 Markdown 文件把检查结果整理成了文字报告。开头记录源码版本，后面按函数列出已检查的条件和后续问题。结构化记录方便程序继续处理，文字报告方便人工阅读。两份材料引用的是同一份代码和同一轮任务。',
 {scroll:true});
add(4,'CHECKPOINT','查看检查点，保留工作进度','已完成函数、文件位置和下一步事项一起保存','checkpoint.json · 字段节选','',
 pre({state:checkpoint.state,completed_functions:checkpoint.completed_functions,artifacts:checkpoint.artifacts,next_actions:checkpoint.next_actions}),
 '检查点由本次审计任务实际写入。',
 '检查点里保存了已经看过的函数、对应文件，以及后续可以继续做的事。这次任务已经完成，记录仍然保留下来。对于时间较长的审计，这类信息能帮助恢复进度，也方便其他成员接手时了解工作做到哪里。');
add(5,'PRINCIPLE','用容量示例解释路径检查','改变输入长度，观察保护条件怎样影响复制操作','教学交互 · 容量约束','',
 rows([['目标容量','64'],['输入长度 96','超过容量 32'],['输入长度 32','当前输入在容量以内'],['加入检查','到达复制要求 n ≤ 64；越界要求 n > 64']]),
 '这一段使用教学模型说明原理；前面的源码检查结果保存在本次任务文件中。',
 '这里穿插一个容量检查的教学例子。长度是九十六，容量是六十四，就会超出三十二。把长度改成三十二，这次输入落在容量以内。再加上完整的长度检查，超过容量就直接返回。路径核对要解决的，就是这些条件能否同时满足。主体把问题写清楚，再按需要交给辅助工具检查。',
 {demo:true,duration:42});
const seconds=measurement.wall_seconds.toFixed(2),memory=(measurement.sampled_peak_process_tree_rss_bytes/1048576).toFixed(2);
add(5,'MEASUREMENT','查看本次运行的耗时和内存','测量范围：本地工作流与 Codex 进程树','measurement.json · 本次实测','',
 '<div class="metric-grid">'+metric(seconds+' s','任务墙钟时间')+metric(memory+' MiB','进程树 RSS 最大采样值')+metric(String(review.scope.length),'实际检查的函数')+metric('20 ms','配置的内存采样间隔')+'</div>',
 '小范围 Parcel 源码检查；RSS 统计本地父子进程，远端模型资源另计。',
 '最后看运行记录。这次小范围检查耗时大约一百三十秒，本地进程树采样到的峰值内存大约三百八十五兆字节。测量文件同时保存了代码版本、机器环境和退出码。后续换成更大的代码范围，可以沿用这套记录方式，再按目标规模和配置比较运行成本。');
add(5,'FINISH','从同一份任务，找到配置、过程和结果','环境 → 目标 → 准备 → 执行 → 源码记录 → 检查报告','操作演示结束','',
 rows([['配置与计划','固定源码版本、函数范围和模型设置'],['执行与进度','run 启动，status 查看状态，日志保留过程'],['本次结果','7 个函数的源码检查记录，候选数量为 0'],['审计分工','主体组织调查；CodeQL-AI 按需提供辅助依据']]),
 'OpenHarmony Audit Agent · 工具使用与源码检查演示',
 '这次演示完成了环境检查、目标配置、任务准备、实际运行和结果查看。使用时，可以从同一份任务找到配置、源码位置、检查记录和报告。后续接入具体漏洞案例时，再沿着对应候选补充复核和复现材料。以上就是本次操作演示，谢谢大家。');
let time=0;for(const s of scenes){s.start=time;time+=s.duration;s.end=time;}
const data={revision:meta.revision,totalSeconds:time,scenes};
fs.mkdirSync('tmp/operation-video',{recursive:true});
fs.writeFileSync('tmp/operation-video/timeline.json',JSON.stringify(data,null,2));
fs.writeFileSync('deliverables/03-operation-replay.html',fs.readFileSync('frontend/operation-player.template.html','utf8').replace('/*SESSION_DATA*/',JSON.stringify(data).replaceAll('<','\\u003c')));
const tc=n=>`${String(Math.floor(n/60)).padStart(2,'0')}:${String(n%60).padStart(2,'0')}`;
const stamp=n=>`${String(Math.floor(n/3600)).padStart(2,'0')}:${String(Math.floor(n%3600/60)).padStart(2,'0')}:${String(n%60).padStart(2,'0')},000`;
const md='# 操作演示视频配音稿\n\n> 对应 03-operation-demo.mp4，总时长 '+tc(time)+'。正文可以直接读；每段开头留有约两秒停顿，末尾留有换气时间。建议按段录音，再按时间码放入剪辑软件。\n\n'+scenes.map((s,i)=>`## ${String(i+1).padStart(2,'0')} · ${tc(s.start)}–${tc(s.end)} ${s.title}\n\n> 画面：${s.file}。本段 ${s.duration} 秒。\n\n${s.speech}`).join('\n\n')+'\n';
fs.writeFileSync('deliverables/03-operation-voiceover.md',md);
let captions=[],idx=1;
for(const s of scenes){const sentences=s.speech.match(/[^。！？]+[。！？]?/g)||[s.speech];const total=sentences.reduce((a,x)=>a+x.length,0);let consumed=0;for(const sentence of sentences){const start=s.start+2+Math.round(consumed/total*(s.duration-4));consumed+=sentence.length;const end=s.start+2+Math.round(consumed/total*(s.duration-4));captions.push(`${idx++}\n${stamp(start)} --> ${stamp(end)}\n${sentence.trim()}\n`);}}
fs.writeFileSync('deliverables/03-operation-voiceover.srt',captions.join('\n'));
const voice=`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>操作演示 · 配音稿</title><style>*{box-sizing:border-box}body{margin:0;background:#f3f5ef;color:#1e353a;font:19px/1.9 'Microsoft YaHei',sans-serif}header{padding:26px 5vw;background:#11252d;color:#e2eee5}h1{font-size:29px;margin:0}header p{font-size:15px;margin:10px 0}.layout{max-width:1560px;margin:auto;padding:28px;display:grid;grid-template-columns:1fr 1fr;gap:35px}.preview{position:sticky;top:24px;align-self:start}video{width:100%;background:#101d25;border-radius:8px}.tip{padding:18px;background:#e2ece1;font-size:15px}section{padding:22px 0;border-bottom:1px solid #bdcfc4}h2{font-size:22px;margin:0 0 12px}button{font:14px inherit;background:#d8e9df;border:1px solid #9bbda9;padding:7px 12px;cursor:pointer;border-radius:4px}.action{font-size:14px;color:#5e766a}section p{font-size:23px;margin:16px 0}section.active{background:#e4eee3;padding:22px 16px;border-left:3px solid #72a388}a{color:#27634a}@media(max-width:850px){.layout{grid-template-columns:1fr}.preview{position:static}section p{font-size:20px}}@media print{header,.preview,button{display:none}.layout{display:block;padding:0}section p{font-size:12pt}section{break-inside:avoid}}</style><header><h1>操作演示视频 · 逐段配音稿</h1><p>${scenes.length} 段 · ${tc(time)} · 正文直接读 · 画面提示不用读</p></header><div class="layout"><div class="preview"><video id="video" controls preload="metadata" src="03-operation-demo.mp4"></video><p class="tip">把本 HTML 和 MP4 放在同一文件夹，即可边看边录音。点击段落的时间按钮可跳到对应画面。每段前后留有停顿，可分段录制后对齐时间码。</p><p><a href="03-operation-voiceover.md">可编辑讲稿</a> · <a href="03-operation-voiceover.srt">字幕文件</a> · <a href="03-operation-replay.html">离线操作记录回放</a></p></div><article>${scenes.map((s,i)=>`<section data-start="${s.start}" data-end="${s.end}"><h2>${String(i+1).padStart(2,'0')} · ${esc(s.title)}</h2><button onclick="document.querySelector('video').currentTime=${s.start}">${tc(s.start)}–${tc(s.end)} · ${s.duration} 秒</button><div class="action">画面：${esc(s.file)}</div><p>${esc(s.speech)}</p></section>`).join('')}</article></div><script>document.querySelector('video').addEventListener('timeupdate',e=>document.querySelectorAll('section').forEach(s=>s.classList.toggle('active',e.target.currentTime>=+s.dataset.start&&e.target.currentTime<+s.dataset.end)))</script></html>`;
fs.writeFileSync('deliverables/03-operation-voiceover.html',voice);
console.log(`Built ${scenes.length} scenes / ${tc(time)} voiceover and portable replay.`);
