const API_BASE = 'http://127.0.0.1:8000';

const rows = document.getElementById('storeRows');
const message = document.getElementById('message');

function setMessage(text, isError = false) {
  message.innerText = text;
  message.style.color = isError ? '#b00020' : '#007700';
}

function statusClass(status) {
  const normalized = (status || '').toLowerCase();
  if (normalized === 'ready') return 'status-ready';
  if (normalized === 'failed') return 'status-failed';
  return 'status-provisioning';
}

async function loadStores() {
  rows.innerHTML = '';
  const res = await fetch(`${API_BASE}/stores`);
  const stores = await res.json();

  for (const store of stores) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${store.name}</td>
      <td>${store.engine}</td>
      <td class="${statusClass(store.status)}">${store.status}</td>
      <td><a href="${store.url}" target="_blank">${store.url}</a></td>
      <td>${store.created_at ?? '-'}</td>
      <td><button data-name="${store.name}">Delete</button></td>
    `;

    const btn = tr.querySelector('button');
    btn.onclick = async () => {
      setMessage(`Deleting ${store.name}...`);
      const response = await fetch(`${API_BASE}/stores/${store.name}`, { method: 'DELETE' });
      if (!response.ok) {
        const body = await response.json();
        setMessage(body.detail || 'Delete failed', true);
        return;
      }
      setMessage(`Deleted ${store.name}`);
      await loadStores();
    };

    rows.appendChild(tr);
  }
}

document.getElementById('createBtn').onclick = async () => {
  const name = document.getElementById('storeName').value.trim();
  const engine = document.getElementById('engine').value;

  if (!name) {
    setMessage('Store name is required', true);
    return;
  }

  setMessage(`Provisioning ${name}...`);
  const response = await fetch(`${API_BASE}/stores/${name}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ engine }),
  });

  if (!response.ok) {
    const body = await response.json();
    setMessage(body.detail || 'Creation failed', true);
    return;
  }

  setMessage(`Provisioning started for ${name}`);
  document.getElementById('storeName').value = '';
  await loadStores();
};

document.getElementById('refreshBtn').onclick = loadStores;

loadStores().catch((err) => setMessage(err.message, true));
