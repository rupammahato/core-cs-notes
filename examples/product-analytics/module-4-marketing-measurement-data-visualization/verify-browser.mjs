import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {once} from 'node:events';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
const base=path.dirname(fileURLToPath(import.meta.url));
const qa=path.join(base,'outputs/qa');await mkdir(qa,{recursive:true});
const routes={'/':['index.html','text/html'],'/chart.js':['chart.js','text/javascript'],
  '/measurement-output.json':['measurement-output.json','application/json'],
  '/node_modules/d3/dist/d3.min.js':['node_modules/d3/dist/d3.min.js','text/javascript']};
const server=createServer(async(req,res)=>{
  const route=routes[req.url];if(!route){res.writeHead(404);res.end();return;}
  try{res.writeHead(200,{'Content-Type':route[1]});res.end(await readFile(path.join(base,route[0])));}
  catch{res.writeHead(500);res.end();}
});
server.listen(0,'127.0.0.1');await once(server,'listening');const port=server.address().port;assert.notEqual(port,3000);
const origin='http://127.0.0.1:'+port;
let browser;const checks=[],errors=[],external=[];let version;
function check(name,actual,expected){assert.deepEqual(actual,expected,name);checks.push({name,passed:true});}
try{
  browser=await chromium.launch({channel:'chrome',headless:true});version=browser.version();
  const page=await browser.newPage({viewport:{width:1200,height:1000}});
  page.on('pageerror',error=>errors.push(error.message));
  await page.route('**/*',route=>{if(new URL(route.request().url()).origin!==origin){external.push(route.request().url());return route.abort();}return route.continue();});
  await page.goto(origin);await page.waitForFunction(()=>window.demo);
  check('Real D3 version',await page.evaluate(()=>demo.d3Version),'7.9.0');
  check('Initial keyed bars',await page.locator('.campaign-bar').count(),2);
  check('Initial table rows',await page.locator('#values tbody tr').count(),2);
  check('Initial treemap leaves',await page.locator('.tile').count(),2);
  check('Known spend label',await page.locator('#tree-note').textContent(),'Known spend: $150.00. 0 campaign(s) missing spend. Area represents spend, not performance.');
  check('Bar input values',await page.locator('.campaign-bar').evaluateAll(nodes=>nodes.map(n=>Number(n.dataset.value))),[10000,5000]);
  const geometry=await page.locator('.campaign-bar').evaluateAll(nodes=>nodes.map(n=>Number(n.getAttribute('width'))));
  check('Spend width ratio',geometry[0]/geometry[1],2);
  check('Hierarchy sum counts leaves once',await page.evaluate(()=>{
    const root=d3.hierarchy({value:15000,children:[{value:10000},{value:5000}]}).sum(d=>d.children?0:d.value);
    return root.value;
  }),15000);
  check('Unpadded treemap conserves area',await page.evaluate(()=>{
    const r=d3.hierarchy({children:[{value:10000},{value:5000}]}).sum(d=>d.children?0:d.value);
    d3.treemap().size([600,300])(r);return r.leaves().reduce((s,n)=>s+(n.x1-n.x0)*(n.y1-n.y0),0);
  }),180000);
  await page.evaluate(()=>{window.savedA=document.querySelector('[data-key="A"].campaign-bar');demo.setData([...demo.source.platform_report.campaigns].reverse());});
  check('Keyed join retains A DOM identity',await page.evaluate(()=>savedA===document.querySelector('[data-key="A"].campaign-bar')),true);
  check('Reorder changes data order',await page.locator('.campaign-bar').evaluateAll(nodes=>nodes.map(n=>n.dataset.key)),['B','A']);
  await page.selectOption('#metric','reported_roas');
  check('ROAS title has units',await page.locator('#bar-title').textContent(),'Compare reported ROAS (times media spend)');
  check('ROAS uses ratios rather than cents',await page.locator('.campaign-bar').evaluateAll(nodes=>nodes.map(n=>Number(n.dataset.value))),[5,1.5]);
  await page.selectOption('#channel','Search');
  check('Filter removes exited bar',await page.locator('.campaign-bar').count(),1);
  check('Filter removes exited tile',await page.locator('.tile').count(),1);
  check('Filter updates table',await page.locator('#values tbody tr').count(),1);
  await page.selectOption('#channel','All');await page.click('#restore');await page.selectOption('#metric','spend_cents');
  await page.screenshot({path:path.join(qa,'desktop.png'),fullPage:true});
  check('SVG has an accessible name',await page.locator('#bars').getAttribute('aria-labelledby'),'bar-title bar-desc');
  check('Table retains exact ROAS',await page.locator('#values tbody tr').nth(1).textContent(),'Prospecting social$50.001005.00\u00d7');
  await page.keyboard.press('Tab');
  check('Native controls remain focusable',await page.locator('#channel').evaluate(el=>el.tabIndex),0);
  await page.evaluate(()=>{
    const rows=structuredClone(demo.source.platform_report.campaigns);rows[1].spend_cents=null;rows[1].metrics.reported_roas=null;demo.setData(rows);
  });
  check('Missing spend not drawn as zero bar',await page.locator('.campaign-bar').count(),1);
  check('Missing values remain in table',await page.locator('#values tbody tr').nth(1).textContent(),'Prospecting socialUnavailable100Unavailable');
  check('Missing spend audit visible',await page.locator('#tree-note').textContent(),'Known spend: $100.00. 1 campaign(s) missing spend. Area represents spend, not performance.');
  await page.evaluate(()=>{const rows=structuredClone(demo.source.platform_report.campaigns);rows.forEach(r=>r.spend_cents=0);demo.setData(rows);});
  check('Zero spend has no positive area',await page.locator('.tile').count(),0);
  check('Zero widths remain finite',await page.locator('.campaign-bar').evaluateAll(nodes=>nodes.every(n=>Number(n.getAttribute('width'))===0)),true);
  await page.click('#empty');
  check('Empty bars removed',await page.locator('.campaign-bar').count(),0);
  check('Empty table removed',await page.locator('#values tbody tr').count(),0);
  check('Empty state explains absence',await page.locator('#bars text.empty').textContent(),'No known values to compare');
  for(const [name,mutation] of [['Duplicate key',rows=>rows.push({...rows[0]})],['Negative spend',rows=>rows[0].spend_cents=-1],['NaN metric',rows=>rows[0].metrics.reported_roas=NaN]]){
    check(name+' rejected',await page.evaluate(fn=>{const rows=structuredClone(demo.source.platform_report.campaigns);(0,eval)('('+fn+')')(rows);try{demo.setData(rows);return false;}catch{return true;}},mutation.toString()),true);
  }
  await page.click('#restore');await page.setViewportSize({width:390,height:1000});
  await page.waitForFunction(()=>Math.abs(document.querySelector('#bars').viewBox.baseVal.width-Math.max(320,document.querySelector('#bars').clientWidth))<1);
  check('Responsive SVG uses available width',await page.locator('#bars').evaluate(el=>Math.abs(el.viewBox.baseVal.width-Math.max(320,el.clientWidth))<1),true);
  check('Mobile chart text keeps fourteen pixel type',await page.locator('#bars .campaign-label').first().evaluate(el=>getComputedStyle(el).fontSize),'14px');
  check('Mobile document fits viewport',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.screenshot({path:path.join(qa,'mobile.png'),fullPage:true});
  check('No script errors',errors,[]);check('No external network requests',external,[]);
}finally{
  if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));
}
let listening=false;try{await fetch(origin,{signal:AbortSignal.timeout(1000)});listening=true;}catch{}
check('Temporary server closed',listening,false);
const proof={verified_date:'2026-10-18',node:process.version,playwright:'1.62.1',browser:version,d3:'7.9.0',
  total:checks.length,checks,port,server_closed:true,browser_closed:true,external_requests:external,
  screenshots:['outputs/qa/desktop.png','outputs/qa/mobile.png'],
  scope:'Real local Chromium/D3 keyed joins, scales, hierarchy, filters, missing/empty states and mobile overflow; not a full accessibility audit or vendor dashboard parity.'};
await writeFile(path.join(base,'browser-validation.json'),JSON.stringify(proof,null,2)+'\n');
console.log(JSON.stringify({passed:checks.length,browser:version,d3:proof.d3,server_closed:true},null,2));
