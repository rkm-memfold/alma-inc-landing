(()=>{
'use strict';
const canvas=document.querySelector('#ambient'),ctx=canvas.getContext('2d'),buffer=document.createElement('canvas'),sample=buffer.getContext('2d',{willReadFrequently:true});
const theme=matchMedia('(prefers-color-scheme: light)'),motion=matchMedia('(prefers-reduced-motion: reduce)');
const W=1600,H=900,CW=10,CH=12,COLS=160,ROWS=75;
buffer.width=COLS;buffer.height=ROWS;
const atmosphere=document.createElement('canvas');atmosphere.width=COLS;atmosphere.height=ROWS;
const fog=atmosphere.getContext('2d',{willReadFrequently:true});
const reference=new Image();reference.src='/page/alma-art-ref.png';
const specimens=[{x:1015,y:465,size:700,phase:0,alpha:1},{x:278,y:204,size:300,phase:1,alpha:.93},{x:417,y:739,size:330,phase:3,alpha:.8},{x:1420,y:97,size:165,phase:5,alpha:.58},{x:80,y:570,size:200,phase:2,alpha:.68},{x:652,y:80,size:132,phase:4,alpha:.50}];
const hash=n=>{const v=Math.sin(n*127.1+311.7)*43758.5453;return v-Math.floor(v)};
let t=0,last=0,frame=0;
function resize(){const r=canvas.getBoundingClientRect(),d=Math.min(devicePixelRatio,2);canvas.width=Math.round(r.width*d);canvas.height=Math.round(r.height*d);draw()}
function draw(){
if(!canvas.width||!reference.complete||!reference.naturalWidth)return;
const light=false;
sample.fillStyle='#000';sample.fillRect(0,0,COLS,ROWS);
sample.save();sample.scale(COLS/W,ROWS/H);sample.globalCompositeOperation='screen';
for(const s of specimens){sample.save();sample.translate(s.x+Math.sin(t*.12+s.phase)*7,s.y+Math.sin(t*.19+s.phase)*9);sample.rotate(Math.sin(t*.18+s.phase)*.045);
let breath=Math.sin(t*1.12+s.phase*.7),size=s.size*(1+breath*.065);
// Slow asymmetric expansion and contraction, like a bell pushing water.
sample.scale(1+breath*.024,1-breath*.018);
sample.globalAlpha=s.alpha*(.94+breath*.06);
sample.drawImage(reference,-size/2,-size/2,size,size);sample.restore()}
sample.restore();
const pixels=sample.getImageData(0,0,COLS,ROWS).data;
// Diffuse the image in the sampling field, then translate the blur back to glyphs.
fog.clearRect(0,0,COLS,ROWS);fog.filter='blur(2.5px)';fog.drawImage(buffer,0,0);fog.filter='none';
const haze=fog.getImageData(0,0,COLS,ROWS).data;
ctx.setTransform(canvas.width/W,0,0,canvas.height/H,0,0);ctx.fillStyle=light?'#eeedf3':'#05030d';ctx.fillRect(0,0,W,H);
ctx.font='bold 13px "Courier New",monospace';ctx.textAlign='center';ctx.textBaseline='middle';
const tick=Math.floor(t*5),grainTick=Math.floor(t*9);
for(let row=0;row<ROWS;row++)for(let col=0;col<COLS;col++){
let index=row*COLS+col,p=index*4,r=pixels[p],g=pixels[p+1],b=pixels[p+2],peak=Math.max(r,g,b),brightness=(r*.25+g*.45+b*.3)/255,seed=hash(index),x=col*CW+CW/2,y=row*CH+CH/2;
let hr=haze[p],hg=haze[p+1],hb=haze[p+2];
let soft=Math.max(hr,hg,hb)/255,grain=hash(index+grainTick*11939);
// Alternate focused and diffused regions rather than blurring the whole organism.
let focus=.5+.5*Math.sin(col*.045+row*.055+t*.22);
let diffusion=.07+focus*.15;
r=r*(1-diffusion)+hr*diffusion;g=g*(1-diffusion)+hg*diffusion;b=b*(1-diffusion)+hb*diffusion;
brightness=(r*.25+g*.45+b*.3)/255;
let active=peak>35;
if(active){
// Sample the actual brand image, so the ASCII retains its exact internal anatomy.
let ramp='.:+x*%#@',strength=Math.min(1,brightness*1.7),char=ramp[Math.min(7,Math.floor(strength*7+hash(index+tick)*1.3))];
if(light){let a=Math.min(1,.68+Math.pow(brightness,.5)*.4);
// Deep cobalt and violet preserve the reference anatomy on a pale background.
let violet=r>g*1.12;
ctx.fillStyle=violet?`rgba(78,24,151,${a})`:`rgba(16,53,151,${a})`;
ctx.shadowColor=violet?'rgba(93,35,165,.25)':'rgba(35,75,171,.22)';ctx.shadowBlur=brightness>.4?1.5:0}
else{let boost=1.24+(grain-.5)*.19;ctx.fillStyle=`rgba(${Math.min(255,Math.round(r*boost))},${Math.min(255,Math.round(g*boost))},${Math.min(255,Math.round(b*boost))},${Math.min(1,.5+brightness)})`;ctx.shadowColor=`rgb(${r},${g},${b})`;ctx.shadowBlur=brightness>.35?3+focus*5:1}
ctx.fillText(char,x,y);
}else{
ctx.shadowBlur=0;
let warpedCol=col+Math.sin(row*.11+t*.2)*8,warpedRow=row+Math.cos(col*.05-t*.16)*6;
let wave=(Math.sin(warpedCol*.10+warpedRow*.12-t*.14)+Math.sin(warpedCol*.035-warpedRow*.16+t*.1))*.25+.5;
let ribbon=Math.pow(.5+.5*Math.sin(warpedRow*.13+Math.sin(warpedCol*.037+t*.16)*2.8-t*.24),14);
let ghost=Math.pow(.5+.5*Math.sin(Math.hypot(col-92,row-37)*.19-t*.35),24)*.22;
let chars='..::;+=/x*#',ch=chars[Math.min(9,Math.floor(wave*4+seed*2+ribbon*2+soft*4))];
if(grain>.986)ch=':+*'[Math.floor(seed*3)];
let opacity=.075+wave*.115+ribbon*.13+ghost*.13+soft*.48+(grain-.5)*.075;
ctx.fillStyle=light?`rgba(91,77,121,${opacity*.30})`:`rgba(${Math.round(94+hr*.5+ribbon*30)},${Math.round(77+hg*.55)},${Math.round(150+hb*.4)},${Math.min(.7,opacity)})`;
if(soft>.08){ctx.shadowColor=light?'#b4a6d1':'#7960cd';ctx.shadowBlur=5}else if(ribbon>.6){ctx.shadowColor=light?'#a3a0bc':'#64609f';ctx.shadowBlur=3}
ctx.fillText(ch,x,y);
}
}
ctx.shadowBlur=0;
}
reference.onload=resize;new ResizeObserver(resize).observe(canvas);theme.addEventListener('change',draw);motion.addEventListener('change',draw);
function loop(now){let dt=last?Math.min((now-last)/1000,.05):0;last=now;if(!motion.matches&&!document.hidden){t+=dt;if(frame++%2===0)draw()}requestAnimationFrame(loop)}requestAnimationFrame(loop);
})();
