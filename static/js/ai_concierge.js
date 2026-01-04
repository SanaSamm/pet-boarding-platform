async function askConcierge(){
  const input = document.getElementById('conciergeInput');
  const answerEl = document.getElementById('conciergeAnswer');
  const resultsEl = document.getElementById('conciergeResults');
  if (!input || !answerEl || !resultsEl) return;

  const query = input.value.trim();
  if (!query) return;

  answerEl.textContent = 'Searching...';
  resultsEl.innerHTML = '';

  try{
    const res = await fetch('/ai/concierge', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    if (!res.ok){
      const err = await res.json().catch(()=> ({}));
      answerEl.textContent = err.message || 'Request failed';
      return;
    }
    const data = await res.json();
    answerEl.textContent = data.answer || 'Here are some options:';
    if (!data.results || !data.results.length){
      resultsEl.innerHTML = '<div class="concierge-result">No matching providers found. Try another search.</div>';
      return;
    }
    data.results.forEach(r => {
      const card = document.createElement('div');
      card.className = 'concierge-result';
      const price = r.price_per_day !== null && r.price_per_day !== undefined ? `${r.price_per_day} TND/day` : 'Price on request';
      const distance = r.distance_km != null ? ` • ${r.distance_km.toFixed(1)} km` : '';
      const providerLink = r.provider_id ? `<a href="/provider?id=${r.provider_id}">View provider profile</a>` : '';
      const highlights = r.highlights ? `<div style="color:#666; font-size:0.9rem; margin-top:4px;">${r.highlights}</div>` : '';
      card.innerHTML = `<strong>${r.name}</strong> — ${r.location}<br>${price}${distance}${highlights}<br>${providerLink}`;
      resultsEl.appendChild(card);
    });
  } catch (e){
    answerEl.textContent = 'Network error';
  }
}

document.addEventListener('DOMContentLoaded', ()=>{
  const btn = document.getElementById('conciergeBtn');
  const input = document.getElementById('conciergeInput');
  if (btn) btn.addEventListener('click', askConcierge);
  if (input) input.addEventListener('keydown', (e)=>{ if (e.key === 'Enter') askConcierge(); });
});
