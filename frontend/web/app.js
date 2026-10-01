const API = '/api/v1';
let token = localStorage.getItem('contractsense_token') || '';
let currentUser = null;
let activeContract = null;
let authMode = 'login';
let toastTimer;
const stateLabels = {nda:'NDA',employment:'Employment',vendor:'Vendor / service',consultancy:'Consultancy',saas_it:'SaaS / IT',procurement:'Procurement',lease:'Lease / rental',data_processing:'Data processing',other:'Other'};
const views = {dashboard:'Overview',upload:'Review a contract',contracts:'My contracts',analysis:'Contract analysis',chat:'Ask a question',legal:'Rule coverage',settings:'Settings & privacy'};

function showToast(message, kind='info') { const el=document.getElementById('toast'); el.textContent=message; el.className=`toast show ${kind}`; clearTimeout(toastTimer); toastTimer=setTimeout(()=>el.className='toast',4200); }
async function request(path, options={}) {
  const headers = new Headers(options.headers || {});
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) headers.set('Content-Type','application/json');
  let response;
  try { response = await fetch(`${API}${path}`, {...options, headers}); }
  catch { throw new Error('Could not reach the local service. Check that the API server is running.'); }
  if (response.status === 401 && token) { logout(false); throw new Error('Your session expired. Please sign in again.'); }
  if (!response.ok) {
    let detail=`Request failed (${response.status})`;
    try { const data=await response.json(); detail=data.detail || detail; } catch {}
    throw new Error(detail);
  }
  const contentType=response.headers.get('content-type')||'';
  if (contentType.includes('application/pdf')) return response.blob();
  if (response.status===204) return null;
  return response.json();
}
function authView(mode) {
  authMode=mode; const register=mode==='register';
  document.getElementById('authTitle').textContent=register?'Create your workspace':'Sign in to your workspace';
  document.getElementById('authSubtitle').textContent=register?'Set up a private space for your contract reviews.':'Your contract reviews, together in one place.';
  document.getElementById('authEyebrow').textContent=register?'GET STARTED':'WELCOME BACK';
  document.getElementById('authSubmit').innerHTML=register?'Create account <span>→</span>':'Sign in <span>→</span>';
  document.getElementById('nameField').classList.toggle('hidden',!register);
  document.querySelector('#authForm [name="password"]').autocomplete=register?'new-password':'current-password';
  document.getElementById('authSwitchText').textContent=register?'Already have an account?':'New to ContractSense?';
  document.getElementById('authModeToggle').textContent=register?'Sign in':'Create an account';
}
async function authSubmit(event) {
  event.preventDefault(); const form=new FormData(event.currentTarget);
  const payload={email:String(form.get('email')||''),password:String(form.get('password')||'')};
  if(authMode==='register') payload.full_name=String(form.get('full_name')||'');
  const button=document.getElementById('authSubmit'); button.disabled=true;
  try { const data=await request(`/auth/${authMode==='register'?'register':'login'}`,{method:'POST',body:JSON.stringify(payload)}); token=data.access_token; localStorage.setItem('contractsense_token',token); currentUser=data.user; enterApp(); showToast('Welcome to your private workspace.','success'); }
  catch(err){showToast(err.message,'error');} finally{button.disabled=false;}
}
async function enterApp() {
  try { if(!currentUser) currentUser=await request('/auth/me'); }
  catch { logout(false); return; }
  document.getElementById('authView').classList.add('hidden'); document.getElementById('appView').classList.remove('hidden');
  const name=currentUser.full_name||'there'; document.getElementById('profileName').textContent=name; document.getElementById('profileEmail').textContent=currentUser.email; document.getElementById('greetingName').textContent=name.split(' ')[0]; document.getElementById('settingsName').textContent=name; document.getElementById('settingsEmail').textContent=currentUser.email; document.getElementById('avatarInitials').textContent=name.split(/\s+/).slice(0,2).map(s=>s[0]).join('').toUpperCase();
  await Promise.allSettled([loadDashboard(),loadRules(),loadServiceStatus(),loadChatContracts()]);
}
function logout(notify=true){ token='';currentUser=null;activeContract=null;localStorage.removeItem('contractsense_token');document.getElementById('appView').classList.add('hidden');document.getElementById('authView').classList.remove('hidden');if(notify)showToast('You have signed out.','success'); }
function go(view){
  document.querySelectorAll('.page-section').forEach(x=>x.classList.add('hidden'));
  const target=document.getElementById(`${view}Page`); if(target)target.classList.remove('hidden');
  document.querySelectorAll('.nav-item').forEach(x=>x.classList.toggle('active',x.dataset.view===view));
  document.getElementById('pageTitle').textContent=views[view]||'Overview';
  if(view==='contracts')loadContracts(); if(view==='chat')loadChatContracts();
  if(view==='dashboard')loadDashboard();
  window.scrollTo({top:0,behavior:'smooth'});
}
function formatDate(value){if(!value)return'';try{return new Intl.DateTimeFormat(undefined,{month:'short',day:'numeric',year:'numeric'}).format(new Date(value));}catch{return''}}
function escapeHtml(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function riskTag(level){const value=(level||'').toLowerCase();return `<span class="risk-tag ${['high','medium','low'].includes(value)?value:'neutral'}">${escapeHtml(value||'pending')}</span>`}
function contractRow(item){const state=item.jurisdiction_state?` · ${escapeHtml(item.jurisdiction_state)}`:'';const score=item.overall_risk_score!=null?`${item.overall_risk_score}/100`:'Not analyzed';return `<div class="contract-row" data-contract="${escapeHtml(item.id)}"><div class="file-icon">▤</div><div class="contract-info"><div class="contract-name">${escapeHtml(item.filename)}</div><div class="contract-sub">${escapeHtml(stateLabels[item.contract_type]||item.contract_type)}${state}<span>·</span>${escapeHtml(formatDate(item.created_at))}<span>·</span>${escapeHtml(score)}</div></div>${riskTag(item.overall_risk_level)}<span class="row-chevron">›</span></div>`}
async function loadDashboard(){
 try{const [stats,list]=await Promise.all([request('/dashboard/stats'),request('/contracts')]);document.getElementById('statContracts').textContent=stats.contracts_total;document.getElementById('statAnalyzed').textContent=stats.analyzed_total;document.getElementById('statHigh').textContent=stats.high_priority_total;document.getElementById('statAvg').textContent=stats.analyzed_total?stats.average_risk_score:'—';const items=list.items||[];document.getElementById('recentContracts').innerHTML=items.length?items.slice(0,5).map(contractRow).join(''):`<div class="empty-state compact"><div class="empty-icon">▤</div><h3>Your contract space is ready</h3><p>Upload an NDA, employment, or vendor agreement to see its clauses and review prompts.</p><button class="button button-soft" data-go="upload">Upload a contract</button></div>`;bindContractRows();bindGoButtons();}
 catch(err){showToast(err.message,'error');}}
async function loadContracts(){try{const data=await request('/contracts');const items=data.items||[];document.getElementById('allContracts').innerHTML=items.length?items.map(contractRow).join(''):`<div class="empty-state"><div class="empty-icon">▤</div><h3>No contracts yet</h3><p>Upload a document you’re authorized to use to start a review.</p><button class="button button-primary" data-go="upload">Review a contract</button></div>`;bindContractRows();bindGoButtons();}catch(err){showToast(err.message,'error');}}
function bindContractRows(){document.querySelectorAll('[data-contract]').forEach(row=>row.onclick=()=>openContract(row.dataset.contract));}
function bindGoButtons(){document.querySelectorAll('[data-go]').forEach(btn=>btn.onclick=()=>go(btn.dataset.go));}
async function openContract(id){try{const data=await request(`/contracts/${encodeURIComponent(id)}`);activeContract=data.contract;go('analysis');renderAnalysis(data.contract,data.analysis);if(data.analysis)loadChatContracts();}catch(err){showToast(err.message,'error');}}
function renderAnalysis(contract,result){
 const host=document.getElementById('analysisContent');
 if(!result){
  const stale=Boolean(contract.analysis_stale)||contract.status==='needs_reanalysis';
  const actionLabel=stale?'Re-run analysis':'Run analysis';
  const message=stale?'Contract metadata or review configuration changed since the previous result. Re-run analysis before using clauses, chat, or reports.':'Text extraction is complete. Run the baseline analysis to identify clauses and configured legal review prompts.';
  host.innerHTML=`<div class="analysis-top"><div class="analysis-title"><span class="eyebrow">CONTRACT REVIEW</span><h1>${escapeHtml(contract.filename)}</h1><p class="muted">${escapeHtml(stateLabels[contract.contract_type]||contract.contract_type)} · ${escapeHtml(contract.jurisdiction_state||'State not provided')}</p></div><div class="analysis-actions"><button class="button button-primary" id="runAnalysis">${actionLabel} <span>→</span></button><button class="button button-ghost" id="deleteContract">Delete</button></div></div><div class="panel empty-state"><div class="empty-icon">✳</div><h3>${stale?'Analysis needs refreshing':'This document is ready to review'}</h3><p>${escapeHtml(message)}</p><button class="button button-primary" id="runAnalysis2">${actionLabel} <span>→</span></button></div>`;
  document.getElementById('runAnalysis').onclick=()=>runAnalysis(contract.id);
  document.getElementById('runAnalysis2').onclick=()=>runAnalysis(contract.id);
  document.getElementById('deleteContract').onclick=()=>deleteContract(contract.id);
  return;
 }
 const clauses=result.clauses||[], checks=result.legal_checks||[], coverage=result.coverage_notes||[];
 host.innerHTML=`<div class="analysis-top"><div class="analysis-title"><span class="eyebrow">CONTRACT REVIEW · ${escapeHtml(formatDate(result.analyzed_at))}</span><h1>${escapeHtml(contract.filename)}</h1><p class="muted">${escapeHtml(stateLabels[contract.contract_type]||contract.contract_type)} · ${escapeHtml(contract.jurisdiction_state||'State not provided')} · ${clauses.length} clauses analyzed</p></div><div class="analysis-actions"><button class="button button-soft" id="reportButton">↓ Download report</button><button class="button button-ghost" id="reanalyzeButton">Re-run</button><button class="button button-ghost" id="deleteContract">Delete</button></div></div>
 <div class="analysis-score-panel"><div class="score-ring" style="--score-angle:${Math.max(0,Math.min(100,result.overall_risk_score||0))*3.6}deg"><div class="score-center"><strong>${result.overall_risk_score??0}</strong><small>Review score</small></div></div><div class="analysis-score-copy"><span class="eyebrow">REVIEW PRIORITY · NOT A LEGAL VERDICT</span><h2>${escapeHtml((result.overall_risk_level||'low').replace(/^./,x=>x.toUpperCase()))} priority for review</h2><p>${escapeHtml(result.score_label||'A non-probabilistic prioritization indicator.')} ${escapeHtml(result.disclaimer||'')}</p><div class="score-chips"><span class="score-chip">${clauses.length} clauses</span><span class="score-chip">${checks.length} rule prompts</span><span class="score-chip">${escapeHtml(result.engine?.classifier_engine||'baseline')}</span></div></div></div>
 <div class="analysis-cards"><div class="mini-card"><span>High priority clauses</span><strong>${result.risk_distribution?.high||0}</strong></div><div class="mini-card"><span>Review prompts</span><strong>${checks.length}</strong></div><div class="mini-card"><span>Classifier</span><strong style="font-size:12px">${escapeHtml(result.engine?.classifier_engine||'baseline')}</strong></div></div>
 <div class="analysis-columns"><section class="panel findings-panel"><div class="clause-toolbar"><h2>Clause findings</h2><input id="clauseSearch" class="search-input" placeholder="Search clauses or categories…"></div><div id="clauseList" class="clause-list">${clauses.length?clauses.map(clauseCard).join(''):'<div class="loading-state">No clauses were extracted.</div>'}</div></section>
 <aside class="panel rules-panel"><div class="panel-heading"><div><span class="eyebrow">ISSUE SPOTTING</span><h2>Legal review prompts</h2></div><button class="link-button" data-go="legal">Coverage →</button></div>${checks.length?checks.map(ruleFinding).join(''):'<p class="muted" style="font-size:10px">No configured deterministic review prompt was triggered. This is not a legal clearance.</p>'}<div class="coverage-note">${coverage.map(escapeHtml).join('<br><br>')}</div></aside></div>`;
 document.getElementById('reportButton').onclick=()=>downloadReport(contract.id);document.getElementById('reanalyzeButton').onclick=()=>runAnalysis(contract.id);document.getElementById('deleteContract').onclick=()=>deleteContract(contract.id);document.getElementById('clauseSearch').oninput=e=>filterClauses(e.target.value);bindGoButtons();
}
function clauseCard(c){return `<article class="clause-card" data-clause-search="${escapeHtml((c.category+' '+c.text).toLowerCase())}"><div class="clause-card-top"><div class="clause-labels"><span class="category-pill">${escapeHtml(c.category)}</span><span class="page-pill">Page ${c.page||1} · ${escapeHtml(c.id)}</span></div>${riskTag(c.risk_level)}</div><p>${escapeHtml(c.text)}</p><div class="clause-meta"><span>Baseline confidence ${Math.round((c.confidence||0)*100)}% · not calibrated</span><span class="clause-card-buttons"><button class="mini-action expand-clause">Read more</button><button class="mini-action suggestion-button" data-clause="${escapeHtml(c.id)}">Review wording</button></span></div></article>`}
function sourceLinks(rule){const sources=Array.isArray(rule.source_urls)&&rule.source_urls.length?rule.source_urls:(rule.source_url?[rule.source_url]:[]);const title=escapeHtml(rule.source_title||rule.law||'Official source');return `${sources.map((url,index)=>`<a class="rule-source" title="${title}" target="_blank" rel="noopener" href="${escapeHtml(url)}">${index===0?'View source':'Additional source'} ↗</a>`).join(' ')}${rule.source_checked_on?`<span class="rule-source">Checked ${escapeHtml(rule.source_checked_on)}</span>`:''}`}
function ruleFinding(r){return `<div class="rule-item"><div class="rule-head"><span class="rule-title">${escapeHtml(r.rule_id)}</span>${riskTag(r.severity)}</div><div class="rule-law">${escapeHtml(r.law)} · ${escapeHtml(r.provision)}</div><p>${escapeHtml(r.message)}</p>${sourceLinks(r)}</div>`}
function filterClauses(q){const term=q.toLowerCase();document.querySelectorAll('[data-clause-search]').forEach(el=>el.classList.toggle('hidden',!el.dataset.clauseSearch.includes(term)));}
async function runAnalysis(id){try{const btn=document.getElementById('runAnalysis')||document.getElementById('runAnalysis2')||document.getElementById('reanalyzeButton');if(btn){btn.disabled=true;btn.textContent='Analyzing…'}showToast('Analyzing clauses and checking configured review prompts…');const data=await request(`/contracts/${id}/analyze`,{method:'POST'});activeContract={...(activeContract||{}),id};renderAnalysis(activeContract,data.result);await loadDashboard();await loadChatContracts();showToast('Analysis complete. Review the evidence and coverage notes.','success');}catch(err){showToast(err.message,'error');} }
async function deleteContract(id){if(!confirm('Delete this contract, its analysis, and its stored upload?'))return;try{await request(`/contracts/${id}`,{method:'DELETE'});activeContract=null;go('contracts');await loadDashboard();showToast('Contract deleted.','success');}catch(err){showToast(err.message,'error');}}
async function downloadReport(id){try{const blob=await request(`/contracts/${id}/report`);const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='ContractSense-review.pdf';a.click();URL.revokeObjectURL(url);}catch(err){showToast(err.message,'error');}}
async function uploadSubmit(event){event.preventDefault();const form=event.currentTarget;const file=document.getElementById('contractFile').files[0];if(!file){showToast('Choose a contract file first.','warning');return;}const body=new FormData(form);const progress=document.getElementById('uploadProgress');const button=document.getElementById('uploadSubmit');progress.classList.remove('hidden');button.disabled=true;document.getElementById('progressTitle').textContent='Reading your document';document.getElementById('progressText').textContent='Extracting text and saving it to your private workspace…';try{const uploaded=await request('/contracts/upload',{method:'POST',body});activeContract=uploaded.contract;document.getElementById('progressTitle').textContent='Finding reviewable clauses';document.getElementById('progressText').textContent=`${uploaded.extraction.character_count.toLocaleString()} characters extracted. Running the baseline review…`;const analyzed=await request(`/contracts/${activeContract.id}/analyze`,{method:'POST'});progress.classList.add('hidden');form.reset();document.getElementById('fileLabel').textContent='Drop your contract here';document.getElementById('fileSubtext').innerHTML='or <u>browse files</u> · PDF, DOCX, TXT or image · up to 25 MB';renderAnalysis(activeContract,analyzed.result);go('analysis');await loadDashboard();await loadChatContracts();showToast('Contract review is ready.','success');}catch(err){progress.classList.add('hidden');showToast(err.message,'error');}finally{button.disabled=false;}}
async function loadRules(){try{const data=await request('/rules');document.getElementById('rulesList').innerHTML=(data.rules||[]).map(r=>`<article class="rule-card"><div class="rule-card-top"><h3>${escapeHtml(r.rule_id)}</h3>${riskTag(r.severity)}</div><div class="rule-law">${escapeHtml(r.law)} · ${escapeHtml(r.provision)}</div><p>${escapeHtml(r.message)}</p>${sourceLinks(r)}</article>`).join('');}catch(err){document.getElementById('rulesList').innerHTML=`<div class="loading-state">${escapeHtml(err.message)}</div>`;}}
async function loadServiceStatus(){try{const data=await fetch('/api/v1/health').then(r=>r.json());document.getElementById('serviceStatus').innerHTML=`<div class="service-line"><span>API</span><span>Online</span></div><div class="service-line"><span>Application database</span><span>${escapeHtml(data.database)}</span></div><div class="service-line"><span>Clause classifier</span><span>${escapeHtml(data.classifier?.engine||'baseline')}</span></div><div class="service-line"><span>Retrieval</span><span>${escapeHtml(data.retrieval)}</span></div><div class="service-line"><span>LLM provider</span><span>${escapeHtml(data.llm?.provider||'mock')}</span></div><div class="service-line"><span>Tesseract OCR</span><span>${data.ocr?.tesseract_binary?'Available':'Not installed'}</span></div>`;}catch{document.getElementById('serviceStatus').textContent='API unavailable';}}
async function loadChatContracts(){try{const data=await request('/contracts');const items=(data.items||[]).filter(x=>x.analysis_id);const select=document.getElementById('chatContractSelect');const current=select.value;select.innerHTML='<option value="">Select an analyzed contract</option>'+items.map(x=>`<option value="${escapeHtml(x.id)}">${escapeHtml(x.filename)}</option>`).join('');if(items.some(x=>x.id===current))select.value=current;else if(activeContract&&items.some(x=>x.id===activeContract.id))select.value=activeContract.id;if(select.value)loadChatHistory();}catch{}}
async function loadChatHistory(){const id=document.getElementById('chatContractSelect').value;if(!id)return;try{const data=await request(`/contracts/${id}/chat`);const host=document.getElementById('chatMessages');host.innerHTML=(data.items||[]).map(m=>bubble(m.role,m.content,m.evidence,m.legal_sources,m.provider,m.limitations)).join('')||welcomeHtml();host.scrollTop=host.scrollHeight;}catch(err){showToast(err.message,'error');}}
const welcomeHtml=()=>`<div class="chat-welcome"><div class="chat-orb">◌</div><h2>Ask about the words on the page.</h2><p>Try “What does the termination section say?” or “Which clauses mention payment?”</p></div>`;
function bubble(role,content,evidence=[],legalSources=[],provider='',limitations=''){
 const evidenceMarkup=(evidence||[]).length?`<div>${evidence.map(e=>`<span class="evidence-chip">${escapeHtml(e.clause_id||'Clause')} · p.${escapeHtml(e.page||'?')}</span>`).join('')}</div>`:'';
 const providerLabel=provider==='evidence_only_fallback'?'EVIDENCE-ONLY · NO LLM':provider?`AI-GENERATED · ${escapeHtml(provider.toUpperCase())}`:'CONTRACTSENSE';
 const limitationMarkup=role!=='user'&&limitations?`<div class="chat-limitation">${escapeHtml(limitations)}</div>`:'';
 const sourcesMarkup=role!=='user'&&(legalSources||[]).length?`<div class="chat-sources"><span class="chat-author">RELATED LEGAL SOURCES</span>${legalSources.slice(0,4).map(source=>`<div class="chat-source-item"><span>${escapeHtml(source.source_title||source.law||'Legal source')}</span>${sourceLinks(source)}</div>`).join('')}</div>`:'';
 return `<div class="chat-bubble ${role==='user'?'user':'assistant'}"><span class="chat-author">${role==='user'?'YOU':providerLabel}</span>${escapeHtml(content)}${limitationMarkup}${evidenceMarkup}${sourcesMarkup}</div>`;
}
async function chatSubmit(event){event.preventDefault();const id=document.getElementById('chatContractSelect').value;const input=document.getElementById('chatInput');const message=input.value.trim();if(!id){showToast('Choose an analyzed contract first.','warning');return;}if(!message)return;const host=document.getElementById('chatMessages');host.innerHTML+=bubble('user',message);input.value='';host.scrollTop=host.scrollHeight;const pending=document.createElement('div');pending.className='chat-bubble assistant';pending.innerHTML='<span class="chat-author">CONTRACTSENSE</span>Retrieving relevant contract text…';host.appendChild(pending);try{const data=await request(`/contracts/${id}/chat`,{method:'POST',body:JSON.stringify({message})});pending.outerHTML=bubble('assistant',data.answer,data.evidence,data.legal_sources,data.provider,data.limitations);host.scrollTop=host.scrollHeight;}catch(err){pending.remove();showToast(err.message,'error');}}
async function requestSuggestion(clauseId){if(!activeContract?.id)return;try{const data=await request(`/contracts/${activeContract.id}/suggestions`,{method:'POST',body:JSON.stringify({message:clauseId})});alert(`${data.category} review prompt\n\n${data.suggestion}\n\n${data.disclaimer}`);}catch(err){showToast(err.message,'error');}}

function init(){
 authView('login');
 document.getElementById('authForm').addEventListener('submit',authSubmit);
 document.getElementById('authModeToggle').onclick=()=>authView(authMode==='login'?'register':'login');
 document.querySelectorAll('.nav-item').forEach(btn=>btn.onclick=()=>go(btn.dataset.view));
 document.querySelectorAll('[data-go]').forEach(btn=>btn.onclick=()=>go(btn.dataset.go));
 document.getElementById('uploadForm').addEventListener('submit',uploadSubmit);
 document.getElementById('contractFile').addEventListener('change',e=>{const f=e.target.files[0];if(f){document.getElementById('fileLabel').textContent=f.name;document.getElementById('fileSubtext').textContent=`${(f.size/1024/1024).toFixed(2)} MB · ready to upload`;}});
 const drop=document.getElementById('dropzone');['dragenter','dragover'].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.add('dragover')}));['dragleave','drop'].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.remove('dragover')}));drop.addEventListener('drop',e=>{const f=e.dataTransfer.files[0];if(f){const input=document.getElementById('contractFile');const dt=new DataTransfer();dt.items.add(f);input.files=dt.files;input.dispatchEvent(new Event('change'));}});
 document.getElementById('chatForm').addEventListener('submit',chatSubmit);document.getElementById('chatContractSelect').addEventListener('change',loadChatHistory);
 document.getElementById('profileButton').onclick=()=>document.getElementById('profileMenu').classList.toggle('hidden');document.getElementById('signOutButton').onclick=()=>logout();document.getElementById('settingsSignOut').onclick=()=>logout();
 document.getElementById('helpButton').onclick=()=>showToast('Issue-spotting only. Always check the cited clause and consult a qualified lawyer.');
 document.body.addEventListener('click',e=>{if(e.target.classList.contains('expand-clause')){const card=e.target.closest('.clause-card');card.classList.toggle('expanded');e.target.textContent=card.classList.contains('expanded')?'Show less':'Read more';}const suggestion=e.target.closest('.suggestion-button');if(suggestion)requestSuggestion(suggestion.dataset.clause);});
 if(token)enterApp();else document.getElementById('authView').classList.remove('hidden');
}
document.addEventListener('DOMContentLoaded',init);
