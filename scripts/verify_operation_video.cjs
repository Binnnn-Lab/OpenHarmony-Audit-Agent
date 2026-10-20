const fs=require('node:fs');
const path=require('node:path');
const os=require('node:os');
const assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url');
const {spawnSync}=require('node:child_process');
const puppeteer=require('../frontend/node_modules/puppeteer-core');
process.chdir(path.resolve(__dirname,'..'));
const timeline=JSON.parse(fs.readFileSync('tmp/operation-video/timeline.json','utf8'));
const ffmpeg=process.env.FFMPEG_PATH||path.resolve('tmp/media-deps/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe');
(async()=>{
 const isolated=fs.mkdtempSync(path.join(os.tmpdir(),'audit-video-'));
 for(const name of ['03-operation-demo.mp4','03-operation-replay.html','03-operation-voiceover.html'])fs.copyFileSync(path.resolve('deliverables',name),path.join(isolated,name));
 const browser=await puppeteer.launch({headless:true,channel:'chrome'});
 const errors=[];
 try{
 const page=await browser.newPage();await page.setViewport({width:1440,height:1000});
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))errors.push(r.url());});
 await page.goto(pathToFileURL(path.join(isolated,'03-operation-voiceover.html')).href);
 await page.waitForFunction(()=>document.querySelector('video').readyState>=1);
 const metadata=await page.$eval('video',v=>({duration:v.duration,width:v.videoWidth,height:v.videoHeight}));
 assert.equal(metadata.width,1920);assert.equal(metadata.height,1080);assert.ok(Math.abs(metadata.duration-timeline.totalSeconds)<.15);
 assert.equal(await page.$$eval('article section',es=>es.length),18);
 await page.click('article section:nth-child(10) button');
 await page.waitForFunction(t=>Math.abs(document.querySelector('video').currentTime-t)<.15,{},timeline.scenes[9].start);
 await page.screenshot({path:'tmp/operation-video/voiceover-qa.png'});
 await page.goto(pathToFileURL(path.join(isolated,'03-operation-replay.html')).href);
 for(let i=0;i<18;i++){await page.evaluate(n=>player.show(n),i);assert.equal(await page.$eval('#title',e=>e.textContent),timeline.scenes[i].title);}
 await page.setViewport({width:390,height:844});await page.evaluate(()=>player.show(0));
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.screenshot({path:'tmp/operation-video/mobile-qa.png',fullPage:true});
 assert.deepEqual(errors,[]);
 }finally{await browser.close();fs.rmSync(isolated,{recursive:true,force:true});}
 const probe=spawnSync(ffmpeg,['-hide_banner','-i',path.resolve('deliverables/03-operation-demo.mp4')],{encoding:'utf8',windowsHide:true});
 assert.match(probe.stderr,/Video: h264/);assert.doesNotMatch(probe.stderr,/Audio:/);
 const decode=spawnSync(ffmpeg,['-v','error','-i',path.resolve('deliverables/03-operation-demo.mp4'),'-f','null','-'],{encoding:'utf8',windowsHide:true});
 assert.equal(decode.status,0,decode.stderr);assert.equal(decode.stderr,'');
 for(const index of [0,5,9,11,15,16,17]){
   const s=timeline.scenes[index];
   const r=spawnSync(ffmpeg,['-v','error','-y','-ss',String(s.start+Math.floor(s.duration*.65)),'-i',path.resolve('deliverables/03-operation-demo.mp4'),'-frames:v','1',path.resolve(`tmp/operation-video/final-${index+1}.png`)],{encoding:'utf8',windowsHide:true});
   assert.equal(r.status,0,r.stderr);
 }
 console.log('PASS: 514s H.264 silent video decoded in full; 1080p playback; 18 timed voiceover segments; seek; offline replay; responsive layout; no external requests or browser errors.');
})().catch(e=>{console.error(e);process.exitCode=1});
