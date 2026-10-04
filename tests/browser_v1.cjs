// Deterministic desktop/mobile acceptance. No scientific service or paid AI calls.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const {chromium} = require('playwright');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const record = {id:'pubmed:123456',source:'pubmed',type:'publication',title:'Fixture ovarian research',
  summary:'Fixture evidence for browser behavior; not a scientific claim.',url:'https://pubmed.ncbi.nlm.nih.gov/123456/',
  metadata:{abstract_available:true,retrieved_at:'2026-10-04T12:00:00Z'},year:'2025',authors:[]};
const candidate = {title:'Review ovarian outcomes',question:'Is ovarian reserve associated with outcomes?',
  population:'Unknown',exposure:'Ovarian reserve',outcome:'Reproductive outcomes',design:'Unknown',
  required_data:'Verify dataset',feasibility:'Unknown',uncertainties:'Verify with mentor',
  rationale:'Provisional fixture direction [pubmed:123456].',citations:[record.id]};
function result(payload){return {next_step:'Review the population for '+payload.query+' [pubmed:123456].',
  tip:'Check outcome availability before selecting a design.',refined_query:'ovarian reserve outcomes',
  explanation:'The retrieved record motivates a provisional direction [pubmed:123456].',candidate_question:candidate,
  citations:[{id:record.id,title:record.title,url:record.url}],evidence_ids:[record.id],
  model:'gpt-6.1-sol',prompt_version:'rei-evidence-1.1',generated_at:'2026-10-04T12:01:00Z',evidence_snapshot:payload};}
const server=http.createServer((req,res)=>{
  const name=new URL(req.url,'http://localhost').pathname.replace(/^\/hosted\//,'/');
  if(name==='/'||name==='/index.html'){
    res.setHeader('Content-Type','text/html; charset=utf-8');
    res.end(req.url.startsWith('/hosted/')?html.replace('<head>','<head><meta name="rei-hosted-demo" content="github-pages">'):html);
  }else if(['/README.md','/HELP.md','/CHANGELOG.md'].includes(name))res.end(fs.readFileSync(path.join(root,name.slice(1))));
  else{res.statusCode=404;res.end('Not available');}
});
let browser, base, passed=0;
const pageErrors=[];
async function scenario(name,options,run){
  const context=await browser.newContext({viewport:options.viewport||{width:1365,height:950},reducedMotion:'reduce'});
  const page=await context.newPage();page.on('pageerror',e=>pageErrors.push(name+': '+e.message));
  const calls={guidance:[],api:[],queries:[]};
  await page.route('**/api/**',async route=>{
    const req=route.request(),url=new URL(req.url());calls.api.push(url.pathname);
    const json=async body=>route.fulfill({contentType:'application/json',body:JSON.stringify(body)});
    if(url.pathname==='/api/health')return json({version:'1.0.0',ai:{configured:options.connected!==false,model:'gpt-6.1-sol'}});
    if(url.pathname==='/api/ai/check')return json({accessible:true,model:'gpt-6.1-sol',message:'Fixture access verified'});
    if(url.pathname==='/api/search'){
      const payload=req.postDataJSON();calls.queries.push(payload.query);
      const records=options.empty?[]:Array.from({length:options.count||1},(_,i)=>({...record,id:'pubmed:'+(123456+i),url:'https://pubmed.ncbi.nlm.nih.gov/'+(123456+i)+'/'}));
      return json({query:payload.query,records,demo:false,
        interpretation:{type:'topic',term:payload.query},retrieved_at:'2026-10-04T12:00:00Z',
        coverage:payload.sources.map(source=>({source,status:source==='pubmed'?'ok':'skipped',total:source==='pubmed'?records.length:null,
          retrieved:source==='pubmed'?records.length:0,truncated:false,query:payload.query,retrieved_at:'2026-10-04T12:00:00Z'}))});
    }
    if(url.pathname==='/api/ai'){
      const payload=req.postDataJSON();
      if(payload.action!=='guidance')return json({text:'Fixture explanation [pubmed:123456].',citations:[record],candidate_questions:[candidate],model:'gpt-6.1-sol'});
      calls.guidance.push(payload);
      if(options.delay)await new Promise(resolve=>setTimeout(resolve,options.delay(payload,calls.guidance.length)));
      if(options.fail&&calls.guidance.length===1)return route.fulfill({status:502,contentType:'application/json',body:JSON.stringify({detail:'AI temporarily unavailable. Retry suggestions.'})});
      if(options.malformed)return json({text:'Unsupported guidance'});
      return json(result(payload));
    }
    return route.fulfill({status:404,body:'Not available'});
  });
  try{
    await page.goto(base+(options.hosted?'/hosted/':'/'));
    await page.waitForFunction(()=>document.querySelector('#connection-label').textContent!== 'Checking AI');
    if(options.connected!==false&&!options.hosted)await page.waitForFunction(()=>document.querySelector('#connection-button').dataset.state==='ready');
    const search=async query=>{await page.locator('#query').fill(query);await page.locator('#search-button').click();await page.waitForFunction(()=>!document.querySelector('#result-actions').hidden);};
    const guided=async()=>page.waitForFunction(()=>document.querySelector('#guidance-phase').textContent==='AI guidance');
    await run({page,calls,search,guided});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth),false,'No horizontal overflow');
    passed++;console.log('PASS '+name);
  }finally{await context.close();}
}
(async()=>{
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));base='http://127.0.0.1:'+server.address().port;
  browser=await chromium.launch({headless:true});fs.mkdirSync(path.join(root,'test-results'),{recursive:true});
  for(const width of [1365,390,320])await scenario('compact layout and sticky controls '+width,{count:8,viewport:{width,height:950}},async({page,search,guided})=>{
    assert.equal(await page.locator('#ai-connection-panel').count(),0);
    assert.equal(await page.locator('#connection-label').textContent(),'AI connected to GPT-6.1 Sol · key verified.');
    const position=await page.evaluate(()=>({source:document.querySelector('#source-strip').getBoundingClientRect().bottom,search:document.querySelector('.search-surface').getBoundingClientRect().top}));
    assert.ok(position.source<=position.search,'Sources above search');
    await search('ovarian aging');await guided();
    assert.equal(await page.locator('#search-button').getAttribute('class'),'');
    assert.ok((await page.locator('#suggest-questions').getAttribute('class')).includes('primary'));
    assert.equal(await page.locator('#make-question').isVisible(),false);
    await page.locator('#research-more summary').click();assert.equal(await page.locator('#make-question').isVisible(),true);
    await page.keyboard.press('Escape');
    await page.evaluate(()=>window.scrollTo(0,400));
    const dock=await page.evaluate(()=>({source:document.querySelector('#source-strip').getBoundingClientRect(),actions:document.querySelector('#result-actions').getBoundingClientRect()}));
    assert.ok(dock.source.top>=0&&dock.source.top<=13);assert.ok(dock.actions.top>=dock.source.bottom);
    await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:path.join(root,'test-results','v1-'+width+'.png'),fullPage:true});
    if(width<650){assert.equal(await page.locator('#connection-short-label').isVisible(),true);await page.locator('#connection-button').click();assert.match(await page.locator('#ai-setup-note').textContent(),/gpt-6.1-sol.*key verified/);}
  });
  await scenario('guidance cache, changed context and no keystroke calls',{},async({page,calls,search,guided})=>{
    await search('ovarian aging');await guided();assert.equal(calls.guidance.length,1);
    await page.locator('#query').fill('different topic');assert.equal(calls.guidance.length,1);assert.match(await page.locator('#guidance-phase').textContent(),/search again/);
    await page.locator('#query').fill('ovarian aging');assert.equal(await page.locator('#guidance-phase').textContent(),'AI guidance');
    await search('ovarian aging');await guided();assert.equal(calls.guidance.length,1,'Reuse same evidence/context');
    await page.locator('#constraints summary').click();await page.locator('#constraint-data').fill('Clinic registry');await page.locator('#constraint-data').blur();await guided();
    assert.equal(calls.guidance.length,2);assert.equal(calls.guidance[1].constraints.data,'Clinic registry');
    await page.locator('#guidance-refresh').click();await guided();assert.equal(calls.guidance.length,3);
    await page.locator('#guidance-why summary').click();assert.equal(await page.locator('#guidance-citations a').getAttribute('href'),record.url);
  });
  await scenario('save proposal, add note and preserve both audits',{},async({page,calls,search,guided})=>{
    await search('ovarian aging');await guided();await page.locator('#guidance-save').click();
    assert.equal(await page.locator('#brief-question').inputValue(),candidate.question);
    await page.locator('#brief-form button[type=submit]').click();await guided();
    assert.equal(calls.guidance.at(-1).questions[0].question,candidate.question);
    await page.locator('#guidance-add').click();await page.locator('#next-step-briefs button').filter({hasText:candidate.title}).click();
    assert.match(await page.locator('#brief-notes').inputValue(),/AI next step/);
    await page.locator('#brief-form button[type=submit]').click();await guided();
    const workspace=await page.evaluate(()=>JSON.parse(localStorage.getItem('rei-research-workspace-v1')));
    assert.equal(workspace.app_version,'1.0.0');assert.equal(workspace.questions[0].ai_audit.action,'guidance');
    assert.equal(workspace.questions[0].guidance_audits.length,1);assert.equal(workspace.questions[0].guidance_audits[0].evidence_snapshot.records[0].id,record.id);
    await page.locator('#guidance-query').click();await guided();assert.equal(calls.queries.at(-1),'ovarian reserve outcomes');
  });
  await scenario('automatic guidance off and explicit refresh',{},async({page,calls,search,guided})=>{
    await page.locator('#ai-connect-action').click();await page.locator('#automatic-guidance').uncheck();await page.locator('[data-close="help-dialog"]').click();
    await search('ovarian aging');assert.equal(calls.guidance.length,0);assert.match(await page.locator('#guidance-phase').textContent(),/manual guidance/);
    await page.locator('#guidance-refresh').click();await guided();assert.equal(calls.guidance.length,1);
  });
  await scenario('AI failure preserves evidence and manual brief; retry works',{fail:true},async({page,calls,search,guided})=>{
    await search('ovarian aging');await page.waitForFunction(()=>document.querySelector('#guidance-phase').textContent.includes('retry'));
    assert.equal(await page.locator('.record').count(),1);assert.equal(await page.locator('#guidance-actions').isVisible(),false);
    await page.locator('#research-more summary').click();await page.locator('#make-question').click();assert.equal(await page.locator('#brief-dialog').isVisible(),true);
    await page.getByRole('button',{name:'Close research brief',exact:true}).click();await page.locator('#guidance-refresh').click();await guided();assert.equal(calls.guidance.length,2);
  });
  await scenario('malformed guidance uses labeled fallback',{malformed:true},async({page,search})=>{
    await search('ovarian aging');await page.waitForFunction(()=>document.querySelector('#guidance-phase').textContent.includes('retry'));
    assert.equal(await page.locator('#guidance-actions').isVisible(),false);assert.equal(await page.locator('.record').count(),1);
  });
  await scenario('stale and canceled guidance cannot replace current context',{delay:(p,n)=>n===2?20:700},async({page,calls,search,guided})=>{
    await search('ovarian aging');await page.waitForFunction(()=>document.querySelector('#guidance-cancel').hidden===false);
    await search('PCOS');await guided();assert.match(await page.locator('#guidance-next').textContent(),/PCOS/);
    await page.waitForTimeout(750);assert.match(await page.locator('#guidance-next').textContent(),/PCOS/);
    await page.locator('#guidance-refresh').click();await page.locator('#guidance-cancel').click();
    assert.match(await page.locator('#guidance-next').textContent(),/cancelled/);assert.equal(await page.locator('#guidance-actions').isVisible(),false);
  });
  await scenario('missing key and illustrative evidence never trigger AI',{connected:false},async({page,calls,search})=>{
    await search('ovarian aging');assert.equal(calls.guidance.length,0);assert.match(await page.locator('#guidance-phase').textContent(),/unavailable/);
    await page.locator('#guidance-refresh').click();assert.equal(await page.locator('#ai-setup-dialog').isVisible(),true);await page.locator('[data-close="ai-setup-dialog"]').click();
    await page.locator('#demo-button').click();assert.equal(calls.guidance.length,0);assert.match(await page.locator('#guidance-phase').textContent(),/example mode/);assert.equal(await page.locator('#suggest-questions').isDisabled(),true);
  });
  await scenario('empty search never generates scientific guidance',{empty:true},async({page,calls,search})=>{
    await search('ovarian aging');assert.equal(calls.guidance.length,0);assert.match(await page.locator('#guidance-phase').textContent(),/no evidence/);
  });
  await scenario('hosted demo has fallback and no backend/key requests',{hosted:true},async({page,calls})=>{
    assert.equal(calls.api.length,0);await page.locator('#ai-connect-action').click();
    assert.equal(await page.locator('#ai-setup-form').isVisible(),false);await page.locator('#ai-connection-help').click();
    assert.match(await page.locator('#help-content').textContent(),/private local backend/);
    await page.locator('[data-close="help-dialog"]').click();await page.locator('#demo-button').click();assert.equal(calls.api.length,0);
  });
  assert.deepEqual(pageErrors,[]);console.log(`${passed} browser scenarios passed; no page errors.`);
})().catch(error=>{console.error(error);process.exitCode=1;}).finally(async()=>{await browser?.close();server.close();});
