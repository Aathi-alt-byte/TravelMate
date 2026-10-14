const searchInput=document.querySelector('#browse-query');
const cards=[...document.querySelectorAll('.explore-card')];
const stateFilter=document.querySelector('#filter-state');
const typeFilter=document.querySelector('#filter-type');
const budgetFilter=document.querySelector('#filter-budget');
const durationFilter=document.querySelector('#filter-duration');
const sortSelect=document.querySelector('#sort-destinations');
const resultCount=document.querySelector('#result-count');
const emptyState=document.querySelector('#empty-state');
const clearButton=document.querySelector('#clear-all-filters');
const oldClear=document.querySelector('#clear-filters');
const loadMore=document.querySelector('#load-more');
const pageSize=9;
let visibleLimit=pageSize;
const menuToggle=document.querySelector('.menu-toggle');
const primaryNav=document.querySelector('#primary-nav');

function matchesDuration(card,value){
 if(!value)return true;
 const days=Number(card.dataset.duration||3);
 return value==='5+'?days>=5:value==='1-2'?days<=2:days>=3&&days<=4;
}
function updateResults(){
 const query=(searchInput.value||'').trim().toLocaleLowerCase();
 const visible=[];
 cards.forEach(card=>{
  const ok=card.dataset.name.includes(query)
   &&(!stateFilter.value||card.dataset.region===stateFilter.value)
   &&(!typeFilter.value||card.dataset.category===typeFilter.value)
   &&(!budgetFilter.value||Number(card.dataset.cost)<=Number(budgetFilter.value))
   &&matchesDuration(card,durationFilter.value);
  card.dataset.matches=String(ok);
  if(ok)visible.push(card);
 });
 visible.sort((a,b)=>sortSelect.value==='cost'
  ?Number(a.dataset.cost)-Number(b.dataset.cost)
  :a.dataset.name.localeCompare(b.dataset.name));
 const grid=document.querySelector('#explore-grid');
 visible.forEach(card=>grid.append(card));
 cards.filter(card=>!visible.includes(card)).forEach(card=>{card.hidden=true});
 visible.forEach((card,index)=>{card.hidden=index>=visibleLimit});
 resultCount.textContent=`${visible.length} ${visible.length===1?'destination':'destinations'}`;
 emptyState.hidden=visible.length!==0;
 loadMore.hidden=visible.length<=visibleLimit;
}
[searchInput,stateFilter,typeFilter,budgetFilter,durationFilter,sortSelect].forEach(el=>el.addEventListener('input',()=>{visibleLimit=pageSize;updateResults()}));
clearButton.addEventListener('click',()=>{searchInput.value='';stateFilter.value='';typeFilter.value='';budgetFilter.value='';durationFilter.value='';sortSelect.value='name';visibleLimit=pageSize;updateResults()});
oldClear.addEventListener('click',()=>clearButton.click());
loadMore.addEventListener('click',()=>{visibleLimit+=pageSize;updateResults()});
document.addEventListener('keydown',event=>{if(event.key==='/'&&!['INPUT','TEXTAREA'].includes(document.activeElement.tagName)){event.preventDefault();searchInput.focus()}});
if(menuToggle&&primaryNav){menuToggle.addEventListener('click',()=>{const open=menuToggle.getAttribute('aria-expanded')==='true';menuToggle.setAttribute('aria-expanded',String(!open));primaryNav.classList.toggle('is-open',!open)});primaryNav.querySelectorAll('a').forEach(link=>link.addEventListener('click',()=>{menuToggle.setAttribute('aria-expanded','false');primaryNav.classList.remove('is-open')}))}
updateResults();