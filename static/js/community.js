const ROOM_NAME = 'owners'; // we will create/fetch first room called 'owners'
let roomId = null;
let pollInterval = null;

function avatarInitial(role, id){ return (role[0]||'?').toUpperCase() + String(id); }
function avatarColor(id){ const colors = ['#f39c12','#16a085','#8e44ad','#e74c3c','#3498db','#2ecc71']; return colors[id % colors.length]; }

async function apiFetch(path, opts = {}){
  const token = localStorage.getItem('access_token');
  opts.headers = opts.headers || {};
  opts.headers['Content-Type'] = 'application/json';
  if (token) opts.headers['Authorization'] = 'Bearer ' + token;
  const res = await fetch(path, opts);
  if (!res.ok) throw await res.json();
  return res.json();
}

async function findOrCreateOwnersRoom(){
  const rooms = await apiFetch('/chat/rooms');
  let room = rooms.find(r => r.name === ROOM_NAME);
  if (!room){
    room = await apiFetch('/chat/rooms', {method:'POST', body: JSON.stringify({name:ROOM_NAME, description:'Shared chat for pet owners'})});
  }
  roomId = room.id;
}

function formatTs(iso){ try { const d = new Date(iso); return d.toLocaleString(); } catch(e){ return iso; } }

async function loadMessages(){
  if (!roomId) return;
  try{
    const messages = await apiFetch(`/chat/rooms/${roomId}/messages`);
    const area = document.getElementById('messagesArea');
    area.innerHTML = '';
    messages.forEach(m => {
      const row = document.createElement('div');
      row.className = 'message-row';

      const av = document.createElement('div');
      av.className = 'avatar';
      av.style.background = avatarColor(m.sender_id);
      av.textContent = avatarInitial('owner', m.sender_id);

      const bubbleWrap = document.createElement('div');
      const bubble = document.createElement('div');
      bubble.className = 'message-bubble owner';
      bubble.textContent = m.content;

      const meta = document.createElement('div');
      meta.className = 'message-meta';
      meta.textContent = `owner • ${formatTs(m.created_at)}`;

      bubbleWrap.appendChild(bubble);
      bubbleWrap.appendChild(meta);

      row.appendChild(av);
      row.appendChild(bubbleWrap);

      area.appendChild(row);
    });
    area.scrollTop = area.scrollHeight;
  } catch(err){
    console.error(err);
  }
}

document.getElementById('sendForm').addEventListener('submit', async (e)=>{
  e.preventDefault();
  const input = document.getElementById('messageInput');
  const content = input.value.trim();
  if (!content) return;
  try{
    await apiFetch(`/chat/rooms/${roomId}/messages`, {method:'POST', body: JSON.stringify({content})});
    input.value = '';
    loadMessages();
  } catch(err){
    console.error(err);
    alert('Failed to send message. Are you logged in as an owner?');
  }
});

(async ()=>{
  try{
    await findOrCreateOwnersRoom();
    await loadMessages();
    pollInterval = setInterval(loadMessages, 3000);
  } catch(err){
    console.error(err);
    alert('Failed to initialize community chat.');
  }
})();

window.addEventListener('beforeunload', ()=>{ if (pollInterval) clearInterval(pollInterval); });