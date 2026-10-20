/* Record browser interactions over the factual run replay, then edit each clip
 * to its voiceover slot. No model calls are made during rendering. */
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {spawn,spawnSync}=require('node:child_process');
const puppeteer=require('../frontend/node_modules/puppeteer-core');
const root=path.resolve(__dirname,'..');process.chdir(root);
const out=path.join(root,'tmp/operation-video');
const ffmpeg=process.env.FFMPEG_PATH||path.join(root,'tmp/media-deps/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe');
const data=JSON.parse(fs.readFileSync(path.join(out,'timeline.json'),'utf8'));
const wait=ms=>new Promise(r=>setTimeout(r,ms));
function command(args){return new Promise((resolve,reject)=>{const p=spawn(ffmpeg,args,{windowsHide:true});let err='';p.stderr.on('data',b=>err+=b);p.on('error',reject);p.on('exit',c=>c?reject(new Error(err.slice(-3000))):resolve());});}
function duration(file){const r=spawnSync(ffmpeg,['-hide_banner','-i',file],{encoding:'utf8',windowsHide:true});const m=r.stderr.match(/Duration: (\d+):(\d+):(\d+(?:\.\d+)?)/);if(!m)throw new Error(r.stderr);return +m[1]*3600 + +m[2]*60 + +m[3];}
(async()=>{
 const browser=await puppeteer.launch({headless:true,channel:'chrome'});
 const errors=[];
 try{
 const page=await browser.newPage();await page.setViewport({width:1920,height:1080});
 await page.emulateMediaFeatures([{name:'prefers-reduced-motion',value:'reduce'}]);
 page.on('pageerror',e=>errors.push(e.message));
 page.on('request',r=>{if(/^https?:/.test(r.url()))errors.push('External request: '+r.url());});
 const url=pathToFileURL(path.join(root,'deliverables/03-operation-replay.html')).href;
 await page.goto(url);
 const cursor=async(x,y,click=false)=>page.evaluate(({x,y,click})=>{const el=document.querySelector('#cursor');if(el){el.style.display='block';el.style.left=x+'px';el.style.top=y+'px';el.style.transition='left .18s, top .18s';el.classList.toggle('click',click);}},{x,y,click});
 const clips=[];
 for(let i=0;i<data.scenes.length;i++){
   const s=data.scenes[i],name=String(i+1).padStart(2,'0');
   const raw=path.join(out,name+'.webm'),clip=path.join(out,name+'.mp4');
   if(process.env.RESUME_VIDEO==='1'&&fs.existsSync(clip)){clips.push(clip);continue;}
   if(s.demo){
     await page.goto(pathToFileURL(path.join(root,'deliverables/03-recording-demo.html')).href+'#chapter-4');
     await page.click('[data-chapter="3"]');
     await page.evaluate(()=>{const marker=document.createElement('div');marker.id='cursor';marker.style.cssText='position:fixed;width:24px;height:24px;border:2px solid #d6f6e5;background:#9edabb44;border-radius:50%;z-index:99;pointer-events:none;display:none';document.body.append(marker);});
   }else{
     if(!page.url().startsWith(url.split('#')[0]))await page.goto(url);
     await page.evaluate(i=>player.show(i,{animate:!!player.scenes[i].command}),i);
   }
   const recorder=await page.screencast({path:raw,ffmpegPath:ffmpeg,format:'webm',fps:24,quality:26});
   const start=Date.now(),target=s.duration*220;
   await cursor(1680,955);await wait(350);
   if(s.demo){
     await wait(target*.23);
     for(const [sel,delay] of [['[data-length="32"]',.23],['[data-length="96"]',.07],['#guard',.23]]){
       const box=await page.$eval(sel,e=>{const b=e.getBoundingClientRect();return{x:b.x+b.width/2,y:b.y+b.height/2};});
       await cursor(box.x,box.y);await wait(250);await page.click(sel);await cursor(box.x,box.y,true);await wait(200);await cursor(box.x,box.y);await wait(target*delay);
     }
   }else{
     if(s.command){
       await cursor(650,380);
       const chunks=12;
       for(let k=1;k<=chunks;k++){await page.evaluate(t=>player.type(t),s.command.slice(0,Math.ceil(s.command.length*k/chunks)));await wait(65);}
       await wait(200);await page.evaluate(()=>player.reveal());
     }
     await cursor(1000,520);await wait(300);
     await page.screenshot({path:path.join(out,'scene-'+name+'.png')});
     const overflowing=await page.$eval('#body',b=>b.scrollHeight>b.clientHeight+5);
     if(s.scroll||overflowing){await wait(target*.35);await cursor(1650,790);await page.evaluate(()=>{const b=document.querySelector('#body');b.scrollTop=b.scrollHeight;});}
   }
   await wait(Math.max(300,target-(Date.now()-start)));
   await page.screenshot({path:path.join(out,'end-'+name+'.png')});
   await recorder.stop();
   const seekable=path.join(out,name+'-seekable.webm');
   await command(['-hide_banner','-loglevel','error','-y','-i',raw,'-c','copy',seekable]);
   const rawSeconds=duration(seekable);
   await command(['-hide_banner','-loglevel','error','-y','-i',seekable,'-vf',`setpts=${s.duration/rawSeconds}*PTS,fps=24,tpad=stop_mode=clone:stop_duration=1`,
     '-t',String(s.duration),'-an','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',clip]);
   clips.push(clip);console.log(`Recorded ${name}/${data.scenes.length}: ${s.title} (${s.duration}s)`);
 }
 if(errors.length)throw new Error(errors.join('\n'));
 fs.writeFileSync(path.join(out,'concat.txt'),clips.map(p=>`file '${path.basename(p)}'`).join('\n'));
 await command(['-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',path.join(out,'concat.txt'),'-c','copy','-movflags','+faststart',path.join(root,'deliverables/03-operation-demo.mp4')]);
 const finalDuration=duration(path.join(root,'deliverables/03-operation-demo.mp4'));
 if(Math.abs(finalDuration-data.totalSeconds)>.15)throw new Error('Video duration does not match voiceover: '+finalDuration);
 console.log(`Completed: ${finalDuration}s, 1920x1080, 24fps, silent MP4; no browser errors or network requests.`);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
