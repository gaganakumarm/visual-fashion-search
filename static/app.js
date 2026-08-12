const API = '';
const tabs = document.querySelectorAll('.console-tab');
const panels = {text:document.getElementById('panel-text'),image:document.getElementById('panel-image')};
const area = document.getElementById('resultsArea');
let previewUrl = null;

tabs.forEach(tab=>tab.addEventListener('click',()=>selectTab(tab.dataset.tab)));
function selectTab(name){
  tabs.forEach(tab=>{const active=tab.dataset.tab===name;tab.classList.toggle('active',active);tab.setAttribute('aria-selected',String(active));});
  Object.entries(panels).forEach(([key,panel])=>panel.classList.toggle('active',key===name));
}

function escapeHtml(value){
  return String(value??'').replace(/[&<>'"]/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
}

function renderGrid(products){
  if(!products.length){area.innerHTML='<div class="empty">No matching vectors found</div>';return;}
  area.innerHTML='<div class="grid"></div>';
  const grid=area.querySelector('.grid');
  products.forEach(product=>{
    const card=document.createElement('article');
    card.className='card-item';
    const score=product.score!==undefined?`<div class="score">${Math.round(product.score*100)}% match</div>`:'';
    card.innerHTML=`<div class="thumb"><img src="${escapeHtml(product.image_url)}" loading="lazy" alt="${escapeHtml(product.name)}">${score}</div><div class="meta"><div class="product-id">ID / ${escapeHtml(product.id)}</div><p class="name">${escapeHtml(product.name)}</p><div class="tags"><span>${escapeHtml(product.baseColour)}</span><span>${escapeHtml(product.subCategory)}</span><span>${escapeHtml(product.usage)}</span></div></div>`;
    grid.appendChild(card);
  });
}

function hideScan(){document.getElementById('scanPanel').classList.remove('show');}
function showScan(tags){
  const labels={masterCategory:'Category',subCategory:'Sub-type',baseColour:'Colour',season:'Season',usage:'Occasion'};
  const list=document.getElementById('attributeList');
  list.innerHTML='';
  Object.entries(tags).forEach(([key,data])=>{
    const confidence=Math.max(0,Math.min(1,Number(data.confidence)||0));
    const row=document.createElement('div');
    row.className='attribute';
    row.innerHTML=`<div class="attribute-top"><span class="attribute-key">${escapeHtml(labels[key]||key)}</span><span class="attribute-value">${escapeHtml(data.value)}</span><span class="attribute-confidence">${Math.round(confidence*100)}%</span></div><div class="confidence-track"><div class="confidence-fill" style="width:${confidence*100}%"></div></div>`;
    list.appendChild(row);
  });
  document.getElementById('scanPanel').classList.add('show');
}

async function loadStats(){
  try{const res=await fetch(API+'/api/stats');if(!res.ok)throw new Error();const data=await res.json();document.getElementById('statLine').textContent=`${Number(data.total_products).toLocaleString()} items indexed`;}
  catch{document.getElementById('statLine').textContent='Index unavailable';}
}
async function loadRandom(){
  area.innerHTML='<div class="loading">Initialising catalogue</div>';
  try{const res=await fetch(API+'/api/random?n=16');if(!res.ok)throw new Error();const data=await res.json();document.getElementById('resultsTitle').textContent='Live catalogue';document.getElementById('resultsCount').textContent=`${data.length} sample items`;renderGrid(data);}
  catch{area.innerHTML='<div class="empty">Catalogue connection failed</div>';}
}
async function runTextSearch(query){
  const q=query.trim();if(!q)return;
  hideScan();area.innerHTML='<div class="loading">Running semantic search</div>';
  document.getElementById('resultsTitle').textContent='Query results';document.getElementById('resultsCount').textContent=`“${q}”`;
  const button=document.getElementById('textBtn');button.disabled=true;
  try{const res=await fetch(API+'/api/search/text',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:q,k:18})});if(!res.ok)throw new Error();const data=await res.json();document.getElementById('resultsCount').textContent=`${data.length} ranked matches`;renderGrid(data);document.querySelector('.results-section').scrollIntoView({behavior:'smooth'});}
  catch{area.innerHTML='<div class="empty">Search request failed</div>';}
  finally{button.disabled=false;}
}

document.getElementById('textBtn').addEventListener('click',()=>runTextSearch(document.getElementById('textInput').value));
document.getElementById('textInput').addEventListener('keydown',event=>{if(event.key==='Enter')runTextSearch(event.target.value);});
document.querySelectorAll('.chip').forEach(chip=>chip.addEventListener('click',()=>{document.getElementById('textInput').value=chip.dataset.q;selectTab('text');runTextSearch(chip.dataset.q);}));

const dropzone=document.getElementById('dropzone');
const fileInput=document.getElementById('fileInput');
dropzone.addEventListener('click',()=>fileInput.click());
dropzone.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();fileInput.click();}});
dropzone.addEventListener('dragover',event=>{event.preventDefault();dropzone.classList.add('drag');});
dropzone.addEventListener('dragleave',()=>dropzone.classList.remove('drag'));
dropzone.addEventListener('drop',event=>{event.preventDefault();dropzone.classList.remove('drag');if(event.dataTransfer.files.length)handleImageFile(event.dataTransfer.files[0]);});
fileInput.addEventListener('change',event=>{if(event.target.files.length)handleImageFile(event.target.files[0]);});

async function handleImageFile(file){
  if(!file.type.startsWith('image/')){area.innerHTML='<div class="empty">Unsupported file type</div>';return;}
  if(previewUrl)URL.revokeObjectURL(previewUrl);
  previewUrl=URL.createObjectURL(file);
  const preview=document.getElementById('imgPreview');preview.src=previewUrl;preview.style.display='block';
  document.getElementById('scanImage').src=previewUrl;
  area.innerHTML='<div class="loading">Analysing visual features</div>';document.getElementById('resultsTitle').textContent='Visual matches';document.getElementById('resultsCount').textContent='Processing input';hideScan();
  const form=new FormData();form.append('file',file);form.append('k',18);
  try{const res=await fetch(API+'/api/search/image',{method:'POST',body:form});if(!res.ok)throw new Error();const data=await res.json();showScan(data.predicted_tags);document.getElementById('resultsCount').textContent=`${data.similar_products.length} ranked matches`;renderGrid(data.similar_products);document.getElementById('scanPanel').scrollIntoView({behavior:'smooth',block:'start'});}
  catch{area.innerHTML='<div class="empty">Image analysis failed · try another file</div>';document.getElementById('resultsCount').textContent='';}
}

loadStats();
loadRandom();

(() => {
  const trigger = document.getElementById('vcHelpTrigger');
  const backdrop = document.getElementById('vcHelpBackdrop');
  const modal = document.getElementById('vcHelpModal');
  const closeButton = document.getElementById('vcHelpClose');
  const samplesGrid = document.getElementById('vcHelpSamples');
  const resultPanel = document.getElementById('vcHelpResult');
  let samplesLoaded = false;

  const escapeValue = value => String(value ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
  const focusableSelector = 'button:not([disabled]), [href], input:not([disabled]), [tabindex]:not([tabindex="-1"])';

  function openHelp() {
    backdrop.classList.add('vc-help-open');
    backdrop.setAttribute('aria-hidden', 'false');
    trigger.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
    closeButton.focus();
    if (!samplesLoaded) loadSamples();
  }

  function closeHelp() {
    backdrop.classList.remove('vc-help-open');
    backdrop.setAttribute('aria-hidden', 'true');
    trigger.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
    trigger.focus();
  }

  async function loadSamples() {
    samplesGrid.innerHTML = '<div class="vc-help-state">Loading test samples</div>';
    try {
      const response = await fetch('/api/samples?n=12');
      if (!response.ok) throw new Error('Sample request failed');
      const samples = await response.json();
      if (!samples.length) {
        samplesGrid.innerHTML = '<div class="vc-help-state">No samples available</div>';
        return;
      }
      samplesGrid.innerHTML = '';
      samples.forEach(sample => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'vc-help-sample';
        button.setAttribute('aria-label', `Use ${sample.name} as a test photo`);
        button.innerHTML = `<img src="${escapeValue(sample.image_url)}" alt="${escapeValue(sample.name)}" loading="lazy"><span>Use this photo →</span>`;
        button.addEventListener('click', () => runSample(sample, button));
        samplesGrid.appendChild(button);
      });
      samplesLoaded = true;
    } catch {
      samplesGrid.innerHTML = '<div class="vc-help-state">Could not load samples · try again</div>';
      samplesLoaded = false;
    }
  }

  async function runSample(sample, sourceButton) {
    resultPanel.classList.add('vc-help-result-show');
    resultPanel.innerHTML = '<div class="vc-help-state">Running image analysis</div>';
    sourceButton.disabled = true;
    try {
      const imageResponse = await fetch(sample.image_url);
      if (!imageResponse.ok) throw new Error('Image request failed');
      const imageBlob = await imageResponse.blob();
      const form = new FormData();
      form.append('file', imageBlob, `${sample.id}.jpg`);
      form.append('k', '4');
      const searchResponse = await fetch('/api/search/image', {method:'POST', body:form});
      if (!searchResponse.ok) throw new Error('Image search failed');
      const data = await searchResponse.json();
      const labels = {masterCategory:'Category',subCategory:'Sub-type',baseColour:'Colour',season:'Season',usage:'Occasion'};
      const tags = Object.entries(data.predicted_tags).map(([key, item]) => `<div class="vc-help-tag"><span class="vc-help-tag-label">${escapeValue(labels[key] || key)}</span><span class="vc-help-tag-value">${escapeValue(item.value)}</span></div>`).join('');
      const matches = data.similar_products.slice(0, 4).map(item => `<div class="vc-help-match"><img src="${escapeValue(item.image_url)}" alt="${escapeValue(item.name)}" loading="lazy"><span>${escapeValue(item.name)}</span></div>`).join('');
      resultPanel.innerHTML = `<h3 class="vc-help-section-title">Test result</h3><p class="vc-help-section-sub">Predicted attributes and top visual matches</p><div class="vc-help-result-grid"><div class="vc-help-tag-list">${tags}</div><div class="vc-help-matches">${matches || '<div class="vc-help-state">No matches returned</div>'}</div></div>`;
      resultPanel.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth', block:'nearest'});
    } catch {
      resultPanel.innerHTML = '<div class="vc-help-state">Test failed · choose another sample</div>';
    } finally {
      sourceButton.disabled = false;
    }
  }

  function trapFocus(event) {
    if (event.key === 'Escape') { closeHelp(); return; }
    if (event.key !== 'Tab') return;
    const focusable = [...modal.querySelectorAll(focusableSelector)].filter(element => element.offsetParent !== null);
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }

  trigger.addEventListener('click', openHelp);
  closeButton.addEventListener('click', closeHelp);
  backdrop.addEventListener('click', event => { if (event.target === backdrop) closeHelp(); });
  document.addEventListener('keydown', event => { if (backdrop.classList.contains('vc-help-open')) trapFocus(event); });
})();
