function initialsFromName(name){
  if (!name) return '';
  const parts = String(name).trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return '';
  if (parts.length === 1) return parts[0][0].toUpperCase();
  return (parts[0][0] + parts[1][0]).toUpperCase();
}

function buildUserMenu(user){
  const menu = document.getElementById('userMenu');
  if (!menu) return;

  const trigger = document.createElement('button');
  trigger.className = 'user-menu-trigger';
  trigger.type = 'button';
  trigger.title = 'Account';
  trigger.textContent = initialsFromName(user.name) || (user.role ? user.role[0].toUpperCase() : '?');

  const dropdown = document.createElement('div');
  dropdown.className = 'user-menu-dropdown';

  const nameRow = document.createElement('div');
  nameRow.className = 'user-menu-name';
  nameRow.textContent = user.name || (user.role ? user.role.toUpperCase() : 'Account');
  dropdown.appendChild(nameRow);

  if (user.role === 'provider') {
    const profile = document.createElement('a');
    profile.className = 'user-menu-item';
    profile.href = `/provider?id=${encodeURIComponent(user.id)}`;
    profile.textContent = 'My Profile';
    dropdown.appendChild(profile);
  } else if (user.role === 'owner') {
    const pets = document.createElement('a');
    pets.className = 'user-menu-item';
    pets.href = '/my-pets';
    pets.textContent = 'My Pets';
    dropdown.appendChild(pets);
  }

  const logout = document.createElement('a');
  logout.className = 'user-menu-item';
  logout.href = '#';
  logout.textContent = 'Logout';
  logout.addEventListener('click', (e)=>{
    e.preventDefault();
    localStorage.removeItem('access_token');
    window.location.href = '/login';
  });
  dropdown.appendChild(logout);

  menu.appendChild(trigger);
  menu.appendChild(dropdown);

  trigger.addEventListener('click', ()=>{
    dropdown.classList.toggle('open');
  });

  document.addEventListener('click', (e)=>{
    if (!menu.contains(e.target)) dropdown.classList.remove('open');
  });
}

async function initUserMenu(){
  const token = localStorage.getItem('access_token');
  if (!token) return;
  try{
    const res = await fetch('/me', { headers: { Authorization: 'Bearer ' + token } });
    if (!res.ok) return;
    const user = await res.json();
    const loginLink = document.getElementById('loginLink');
    if (loginLink) loginLink.style.display = 'none';
    buildUserMenu(user);
  } catch (e){
    // ignore
  }
}

document.addEventListener('DOMContentLoaded', initUserMenu);
