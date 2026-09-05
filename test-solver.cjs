const assert = require('node:assert/strict');
const fs = require('node:fs');
const {execFileSync} = require('node:child_process');
const path = require('node:path');
const {Worker} = require('node:worker_threads');
const source = fs.readFileSync(path.join(__dirname, 'src.html'), 'utf8');
function load(html) {
  const core = html.match(/<script id="solvercore">([\s\S]*?)<\/script>/)[1];
  const mats = html.match(/const MATS = (\[[\s\S]*?\n\]);/)[1];
  return new Function(`${core}\nreturn {mats:${mats}, solve(sel, p=202, r=15, h=50, ri=null, q=3000, seed=null) { Q=q; LAST=seed; return optimise(sel,p,r,h,ri,false); }, seed:()=>LAST, logsOf, dpOf};`)();
}
const solver = load(source);
const ids = names => names.map(id => solver.mats.find(m => m.id === id));
const cases = [
  ['default', ids(['grey fuzzy','grey holey','duvet'])],
  ['all', solver.mats.filter(m=>!m.untested)],
  ['duvet', ids(['duvet'])],
  ['thin', ids(['soft linen','grey holey'])],
  ['low pressure', ids(['grey fuzzy','grey holey','duvet']), 60],
  ['wide core', ids(['grey fuzzy','grey holey','duvet']), 202, 20, 50, 11],
  ['short', ids(['grey fuzzy','grey holey','duvet']), 202, 15, 15],
];
function check(t, sel, p=202, r=15, h=50, ri=null, q=3000) {
  assert(t && t.bands.length, 'expected a feasible plan');
  assert(t.H>0 && t.H<=h+1e-8);
  assert(Number.isFinite(t.logs));
  assert(t.ro<=r+1e-8);
  if(ri) assert.equal(t.ri,ri);
  let logs=0, dp=0, radius=t.ri;
  const used={};
  for(const b of t.bands){
    assert(sel.some(m=>m.id===b.m.id));
    assert(Math.abs(b.r0-radius)<1e-8);
    assert(b.n>=1-1e-8);
    const f=t.folds[b.m.id];
    if(f.f*b.m.t>=1) assert(Math.abs(b.turns-Math.round(b.turns))<1e-7);
    assert(f.axial>=t.H+t.ro-1e-7);
    used[b.m.id]=(used[b.m.id]||0)+Math.PI*(b.r1**2-b.r0**2)/b.m.t;
    assert(used[b.m.id]<=f.stock+1e-6);
    logs+=solver.logsOf(b.m,b.r0,b.r1,q/(2*Math.PI*t.H));
    dp+=solver.dpOf(b.m,b.r0,b.r1,q/(2*Math.PI*t.H));
    radius=b.r1;
  }
  assert(dp<=p+1e-6, `pressure ${dp} > ${p}`);
  assert(Math.abs(dp-t.dp)<1e-7, 'reported pressure differs from build');
  assert(Math.abs(logs-t.logs)<1e-7, 'reported protection differs from build');
  assert(Math.abs(radius-t.ro)<1e-8);
  for(const [id,amount] of Object.entries(used)) assert(Math.abs(amount-t.used[id])<1e-6);
}
if(require.main===module){
  const legacy=process.argv.includes('--legacy') ? load(execFileSync('git',['show','f0b78245:src.html'],{cwd:__dirname,encoding:'utf8',maxBuffer:2e6})) : null;
  const refs=JSON.parse(fs.readFileSync(path.join(__dirname,'solver-reference.json'),'utf8'));
  const references=[2.384895,3.336411,1.059105,1.406569,1.629367,1.429863,1.695636];
  let worstMs=0;
  for(const [i,[name,...args]] of [...cases,...refs.map((r,i)=>[`varied ${i}`,...r.args])].entries()){
    const start=performance.now(), t=solver.solve(...args), ms=performance.now()-start;
    worstMs=Math.max(worstMs,ms);
    check(t,...args);
    const reference=i<cases.length?references[i]:refs[i-cases.length].logs;
    assert(t.logs>=reference-.006, `${name}: search gap ${reference-t.logs}`);
    let old='';
    if(legacy){const s=performance.now(), b=legacy.solve(...args); old=`; legacy ${b?.logs.toFixed(5)} (${(performance.now()-s).toFixed(0)} ms)`;}
    console.log(`${name}: ${t.logs.toFixed(5)} logs, ${ms.toFixed(0)} ms${old}`);
  }
  assert(worstMs<1000, `slowest solve ${worstMs.toFixed(0)} ms exceeds one second`);
  const sel=cases[0][1], base=solver.solve(sel), seed=structuredClone(solver.seed());
  assert.equal(solver.solve(sel.slice().reverse()).logs,base.logs,'input order changed solution');
  const relaxed=[
    [sel,222.2,15,50], [sel,202,16.5,50], [sel,202,15,55],
    [sel.map(m=>({...m,L:m.L*1.1})),202,15,50],
    [solver.mats.filter(m=>!m.untested),202,15,50]
  ];
  for(const [s,p,r,h] of relaxed){
    const t=solver.solve(s,p,r,h,null,3000,seed);
    check(t,s,p,r,h);
    assert(t.logs>=base.logs-1e-9,'relaxing a constraint lost the previous plan');
  }
  for(const [s,p,r,h,ri,q] of [[sel,80,15,30,null,3300],[sel.map(m=>({...m,t:m.t*1.1})),202,15,50,null,3000]]){
    check(solver.solve(s,p,r,h,ri,q,seed),s,p,r,h,ri,q);
  }
  assert.equal(solver.solve([]),null);
  assert.equal(solver.solve(sel,202,15,50,15),null);
  assert.equal(solver.solve(sel,202,15,50,16),null);
  assert.equal(solver.solve(sel,Infinity),null);
  console.log('Feasibility, reference quality, determinism, seed revalidation and runtime checks passed.');
  // Execute the actual browser worker message handler in a worker thread.
  const core=source.match(/<script id="solvercore">([\s\S]*?)<\/script>/)[1];
  const workerDefinition=source.match(/const WORKER_SRC = ([\s\S]*?);\r?\nlet workerURL/)[1];
  const workerSource=new Function('document',`return ${workerDefinition};`)({getElementById:()=>({textContent:core})});
  const w=new Worker(`const {parentPort}=require('node:worker_threads');
    const postMessage=m=>parentPort.postMessage(m);
    ${workerSource}
    parentPort.on('message',data=>onmessage({data}));`,{eval:true});
  w.once('error',e=>{console.error(e);process.exitCode=1;});
  w.once('message',m=>{
    try{assert.equal(m.id,17);check(m.result,sel);assert(m.seed.bands.length);console.log('Worker message round-trip passed.');}
    catch(e){console.error(e);process.exitCode=1;}
    finally{w.terminate();}
  });
  w.postMessage({id:17,full:true,sel,dpMax:202,roMax:15,Hmax:50,fixedRi:null,q:3000,seed});
}
module.exports={load,solver,cases,check};
