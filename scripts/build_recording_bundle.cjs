/* Build one offline HTML with embedded operating guide and page-by-page speech. */
const fs = require('node:fs');
const path = require('node:path');
const render = require('./build_reading_pages.cjs');
process.chdir(path.resolve(__dirname, '..'));
fs.mkdirSync('tmp', {recursive:true});
fs.mkdirSync('deliverables', {recursive:true});
render('frontend/NARRATION.md','frontend/narration.html','逐页录屏讲解稿',true);
render('frontend/RECORDING-GUIDE.md','tmp/recording-guide.html','环境与操作');
function mainContent(file) {
  const html = fs.readFileSync(file,'utf8');
  const main = html.match(/<main>([\s\S]*?)<\/main>/);
  if (!main) throw new Error('Missing main: '+file);
  return main[1].replace(/<footer>[\s\S]*?<\/footer>/g,'');
}
const content = `<template id="guide-template">${mainContent('tmp/recording-guide.html')}</template>\n<template id="speech-template">${mainContent('frontend/narration.html')}</template>`;
let demo = fs.readFileSync('frontend/demo.html','utf8');
const marker = /<!-- RECORDING_CONTENT_START -->[\s\S]*?<!-- RECORDING_CONTENT_END -->/;
if (!marker.test(demo)) throw new Error('Recording template marker is missing');
demo = demo.replace(marker, '<!-- RECORDING_CONTENT_START -->\n'+content+'\n<!-- RECORDING_CONTENT_END -->');
fs.writeFileSync('frontend/demo.html',demo);
fs.writeFileSync('deliverables/工具原理与流程交互说明.html',demo);
let speech = fs.readFileSync('frontend/narration.html','utf8');
speech = speech.replace(/<header>[\s\S]*?<\/header>/,'<header>OpenHarmony Audit Agent · 逐页录屏讲稿<br>正文直接朗读 · 绿色框为操作提示 · 章节与演示网页一一对应</header>');
fs.writeFileSync('deliverables/03-narration.html',speech);
fs.copyFileSync('frontend/NARRATION.md','deliverables/03-narration.md');
console.log('Built standalone demo and narration. All reading material is embedded.');
