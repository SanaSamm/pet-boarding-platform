let activeConvoId = null;
let pollInterval = null;
let currentUser = null;
let searchTimer = null;

function initialsFromName(name){
  if (!name) return '';
  const parts = String(name).trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return '';
  if (parts.length === 1) return parts[0][0].toUpperCase();
  return (parts[0][0] + parts[1][0]).toUpperCase();
}

function avatarInitial(role, name){
  const initials = initialsFromName(name);
  if (initials) return initials;
  return (role[0] || '?').toUpperCase();
}
function avatarColor(id){
  // deterministic pastel color from id
  const colors = ['#f39c12','#16a085','#8e44ad','#e74c3c','#3498db','#2ecc71'];
  return colors[id % colors.length];
}

async function apiFetch(path, opts = {}){
  const token = localStorage.getItem('access_token');
  opts.headers = opts.headers || {};
  opts.headers['Content-Type'] = 'application/json';
  if (token) opts.headers['Authorization'] = 'Bearer ' + token;
  const res = await fetch(path, opts);
  if (!res.ok) throw await res.json();
  return res.json();
}

async function loadCurrentUser(){
  const token = localStorage.getItem('access_token');
  if (!token) return null;
  try{
    const res = await fetch('/me', { headers: { Authorization: 'Bearer ' + token } });
    if (!res.ok) return null;
    return await res.json();
  } catch (e){
    return null;
  }
}

async function loadConversations(){
  try{
    const convos = await apiFetch('/conversations');
    const el = document.getElementById('convoList');
    el.innerHTML = '';
    if (!convos.length) el.innerHTML = '<p>No conversations yet</p>';
    convos.forEach(c => {
      const div = document.createElement('div');
      div.className = 'convo-item';
      if (activeConvoId && Number(c.id) === Number(activeConvoId)) {
        div.classList.add('active');
      }

      const av = document.createElement('div');
      av.className = 'avatar';
      av.style.background = avatarColor(c.id);
      const otherName = currentUser && currentUser.role === 'owner' ? c.provider_name : c.owner_name;
      const otherRole = currentUser && currentUser.role === 'owner' ? 'provider' : 'owner';
      av.textContent = avatarInitial(otherRole, otherName);

      const meta = document.createElement('div');
      meta.style.flex = '1';
      const titleRow = document.createElement('div');
      titleRow.style.display = 'flex';
      titleRow.style.alignItems = 'center';
      titleRow.style.justifyContent = 'space-between';
      titleRow.style.gap = '0.5rem';
      const titleText = otherName ? otherName : `Conversation #${c.id}`;
      titleRow.innerHTML = `<span style="font-weight:700">${titleText}</span>`;
      if (c.unread_count && Number(c.unread_count) > 0){
        const badge = document.createElement('span');
        badge.className = 'badge';
        badge.textContent = String(c.unread_count);
        titleRow.appendChild(badge);
      }
      const sub = document.createElement('div');
      sub.style.fontSize = '0.85rem';
      sub.style.color = '#666';
      const ownerLabel = c.owner_name ? `Owner ${c.owner_name}` : `Owner ${c.owner_id}`;
      const providerLabel = c.provider_name ? `Provider ${c.provider_name}` : `Provider ${c.provider_id}`;
      sub.textContent = `${ownerLabel} • ${providerLabel}`;
      meta.appendChild(titleRow);
      meta.appendChild(sub);

      div.appendChild(av);
      div.appendChild(meta);

      div.onclick = async () => {
        // clear active
        document.querySelectorAll('.convo-item').forEach(el=>el.classList.remove('active'));
        div.classList.add('active');
        await openConversation(c.id);
      };

      el.appendChild(div);
    });
  } catch(err){
    console.error(err);
    alert('Error loading conversations. Make sure you are logged in.');
  }
}

async function openConversation(convoId){
  activeConvoId = convoId;
  document.getElementById('threadTitle').textContent = `Conversation #${convoId}`;
  document.getElementById('sendMessageForm').style.display = 'flex';
  await loadMessages();
  await loadConversations();
  if (pollInterval) clearInterval(pollInterval);
  pollInterval = setInterval(loadMessages, 3000);
}

function formatTs(iso){
  try{
    const d = new Date(iso);
    return d.toLocaleString();
  }catch(e){ return iso; }
}

async function loadMessages(){
  if (!activeConvoId) return;
  try{
    const messages = await apiFetch(`/conversations/${activeConvoId}/messages`);
    const area = document.getElementById('messagesArea');
    area.innerHTML = '';
    messages.forEach(m => {
      const row = document.createElement('div');
      row.className = 'message-row ' + (m.sender_role === 'owner' ? 'owner' : 'provider');

      const av = document.createElement('div');
      av.className = 'avatar';
      av.style.background = avatarColor(m.sender_id);
      av.textContent = avatarInitial(m.sender_role, m.sender_name);

      const bubbleWrap = document.createElement('div');
      const bubble = document.createElement('div');
      bubble.className = 'message-bubble ' + (m.sender_role === 'owner' ? 'owner' : 'provider');
      bubble.textContent = m.content;

      const meta = document.createElement('div');
      meta.className = 'message-meta';
      const nameLabel = m.sender_name || m.sender_role;
      meta.textContent = `${nameLabel} • ${formatTs(m.created_at)}`;

      bubbleWrap.appendChild(bubble);
      bubbleWrap.appendChild(meta);

      if (m.sender_role === 'owner'){
        row.appendChild(bubbleWrap);
        row.appendChild(av);
      } else {
        row.appendChild(av);
        row.appendChild(bubbleWrap);
      }

      area.appendChild(row);
    });
    area.scrollTop = area.scrollHeight;
    await loadConversations();
  } catch(err){
    console.error(err);
  }
}

document.getElementById('sendMessageForm').addEventListener('submit', async (e)=>{
  e.preventDefault();
  const input = document.getElementById('messageInput');
  const content = input.value.trim();
  if (!content) return;
  try{
    await apiFetch(`/conversations/${activeConvoId}/messages`, {method:'POST', body: JSON.stringify({content})});
    input.value = '';
    loadMessages();
  } catch(err){
    console.error(err);
    alert('Failed to send message');
  }
});

function renderProviderResults(items){
  const results = document.getElementById('providerResults');
  results.innerHTML = '';
  if (!items.length){
    results.innerHTML = '<div class="new-convo-status">No providers found.</div>';
    return;
  }
  items.forEach(p => {
    const row = document.createElement('div');
    row.className = 'provider-result';

    const av = document.createElement('div');
    av.className = 'avatar';
    av.style.background = avatarColor(p.id);
    av.textContent = avatarInitial('p', p.id);

    const meta = document.createElement('div');
    meta.innerHTML = `<div class="provider-name">${p.name}</div>` +
      (p.bio ? `<div class="provider-bio">${p.bio}</div>` : '');

    row.appendChild(av);
    row.appendChild(meta);

    row.addEventListener('click', async ()=>{
      try{
        const payload = (currentUser && currentUser.role === 'provider')
          ? { owner_id: Number(p.id) }
          : { provider_id: Number(p.id) };
        const convo = await apiFetch('/conversations', {method:'POST', body: JSON.stringify(payload)});
        await loadConversations();
        await openConversation(convo.id);
        document.getElementById('newConvoPanel').style.display = 'none';
      } catch (err){
        console.error(err);
        alert('Failed to start conversation');
      }
    });

    results.appendChild(row);
  });
}

async function handleProviderSearch(query){
  const results = document.getElementById('providerResults');
  if (query.length < 2){
    results.innerHTML = '';
    return;
  }
  try{
    const endpoint = (currentUser && currentUser.role === 'provider') ? 'owners' : 'providers';
    const data = await apiFetch(`/${endpoint}?q=${encodeURIComponent(query)}`);
    renderProviderResults(data);
  } catch (err){
    console.error(err);
    results.innerHTML = '<div class="new-convo-status">Search failed.</div>';
  }
}

// New conversation (owner: search provider, provider: prompt owner id)
document.getElementById('newConvoBtn').addEventListener('click', async ()=>{
  const panel = document.getElementById('newConvoPanel');
  const status = document.getElementById('newConvoStatus');
  const searchInput = document.getElementById('providerSearchInput');

  if (!currentUser){
    status.textContent = 'Log in to start a conversation.';
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    return;
  }

  if (currentUser.role === 'owner'){
    status.textContent = 'Search providers to start a conversation.';
    searchInput.disabled = false;
    searchInput.placeholder = 'Search providers by name';
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    if (panel.style.display === 'block'){
      searchInput.focus();
    }
    return;
  }

  if (currentUser.role === 'provider'){
    status.textContent = 'Search owners to start a conversation.';
    searchInput.disabled = false;
    searchInput.placeholder = 'Search owners by name';
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    if (panel.style.display === 'block'){
      searchInput.focus();
    }
  }
});

// initial load: load conversations, then open if ?open=id is present
(async ()=>{
  currentUser = await loadCurrentUser();
  await loadConversations();
  const params = new URLSearchParams(window.location.search);
  const open = params.get('open');
  if (open){
    // attempt to open conversation; if it fails the user will see the placeholder
    try { openConversation(Number(open)); } catch(e){ console.error(e); }
  }
})();

window.addEventListener('beforeunload', ()=>{ if (pollInterval) clearInterval(pollInterval); });

const searchInput = document.getElementById('providerSearchInput');
if (searchInput){
  searchInput.addEventListener('input', (e)=>{
    const query = e.target.value.trim();
    if (searchTimer) clearTimeout(searchTimer);
    searchTimer = setTimeout(()=> handleProviderSearch(query), 250);
  });
}
