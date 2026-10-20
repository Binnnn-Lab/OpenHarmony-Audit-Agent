/* Small dependency-free Markdown reader for this repository's documentation. */
const fs=require('node:fs');
function esc(s){return s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');}
function inline(s){return esc(s).replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\[([^\]]+)\]\(([^)]+)\)/g,'<a href="$2">$1</a>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');}
function render(source,output,title,reading=false){
 const sections=[];let i=0;
 const content=fs.readFileSync(source,'utf8').split(/\r?\n\r?\n/).filter(Boolean).map(block=>{
  if(block.startsWith('```'))return '<pre><code>'+esc(block.replace(/^```[^\n]*\n/,'').replace(/\n```\s*$/,''))+'</code></pre>';
  const h=block.match(/^(#{1,3}) (.+)$/);if(h){const id='part-'+i++;if(h[1].length===2)sections.push([id,h[2]]);return `<h${h[1].length} id="${id}">${inline(h[2])}</h${h[1].length}>`;}
  if(block.startsWith('> '))return '<aside>'+inline(block.slice(2))+'</aside>';
  if(block.startsWith('|')){const rows=block.split('\n').filter(row=>!/^\|[-: |]+\|$/.test(row.trim()));return '<div class="table-wrap"><table>'+rows.map((r,index)=>'<tr>'+r.trim().replace(/^\||\|$/g,'').split('|').map(c=>`<${index?'td':'th'}>${inline(c.trim())}</${index?'td':'th'}>`).join('')+'</tr>').join('')+'</table></div>';}
  if(block.startsWith('- '))return '<ul>'+block.split('\n').map(l=>'<li>'+inline(l.replace(/^- /,''))+'</li>').join('')+'</ul>';
  return '<p>'+inline(block)+'</p>';
 }).join('\n');
 const html=`<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)}</title><style>
*{box-sizing:border-box}body{margin:0;overflow-wrap:anywhere;background:#f4f6f1;color:#20353c;font:16px/1.85 "Segoe UI","Microsoft YaHei",sans-serif}header{background:#12232b;color:#d4e7dc;padding:24px max(24px,calc((100vw - 1000px)/2));font-size:14px;line-height:2}header a{color:#b8e7d1;margin-right:20px}main{max-width:1056px;margin:auto;padding:28px}nav{display:flex;gap:8px 22px;flex-wrap:wrap;font-size:14px;border-bottom:1px solid #cbd9d0;padding-bottom:24px}a{color:#23624e;text-underline-offset:4px}h1{font-size:32px;line-height:1.5}h2{font-size:26px;margin-top:44px;padding-top:22px;border-top:1px solid #cad7ce;scroll-margin-top:20px}h3{font-size:22px}p{margin:18px 0;${reading?'font-size:22px;line-height:1.95;':''}}aside{font-size:15px;line-height:1.85;background:#e5eee6;border-left:3px solid #659378;color:#4e6458;padding:14px 18px;margin:24px 0}code{font-family:Consolas,monospace;font-size:.88em;overflow-wrap:anywhere}pre{background:#12232b;color:#e3eee5;overflow:auto;padding:20px;font:13px/1.8 Consolas,monospace}pre code{font-size:inherit;overflow-wrap:normal}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;vertical-align:top;border-bottom:1px solid #cbd9d0;padding:12px}th{background:#e4ece5}li{margin:8px 0}footer{font-size:13px;border-top:1px solid #cad7ce;padding:24px 0;margin-top:40px;color:#566b64}@media(max-width:600px){main{padding:20px}p{font-size:${reading?'19':'16'}px}h1{font-size:27px}h2{font-size:23px}}@media print{header,nav{display:none}body{background:white}main{max-width:none;padding:0}p{font-size:11pt}h2,h3{break-after:avoid}tr,aside{break-inside:avoid}pre{white-space:pre-wrap;background:#eee;color:#222}a{color:inherit}}
</style></head><body><header>OpenHarmony Audit Agent · 主体审计 / 按需辅助验证<br><a href="demo.html" target="_blank" rel="noopener">原理 DEMO</a><a href="manual.html">使用说明书</a><a href="narration.html">逐页讲稿</a><a href="performance.html">性能说明</a></header><main><nav aria-label="文档目录">${sections.map(([id,s])=>`<a href="#${id}">${esc(s)}</a>`).join('')}</nav>${content}<footer>${reading?'正文可直接朗读，浅绿色操作提示不用读。录屏建议只选择演示窗口。':'本文依据当前工程实现编写，实际运行结果与抽象演示分别标注。'}</footer></main></body></html>\n`;
 fs.writeFileSync(output,html);
 console.log(output);
}
module.exports = render;
if (require.main === module) {
 render('docs/user-manual.md','frontend/manual.html','工具使用说明书');
 render('frontend/NARRATION.md','frontend/narration.html','逐页录屏讲解稿',true);
 if(fs.existsSync('docs/performance.md'))render('docs/performance.md','frontend/performance.html','工具性能说明');
}
