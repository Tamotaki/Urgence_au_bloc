
// Date actuelle
const dateEl = document.getElementById('current-date');
if (dateEl) {
  const now = new Date();
  const opts = { weekday:'long', year:'numeric', month:'long', day:'numeric' };
  dateEl.textContent = now.toLocaleDateString('fr-FR', opts);
}

// Recherche dans le tableau
const searchInput = document.getElementById('search');
const filterSalle = document.getElementById('filter-salle');
const table = document.getElementById('table-resa');

function filterTable() {
  if (!table) return;
  const term = (searchInput?.value || '').toLowerCase();
  const salle = (filterSalle?.value || '').toLowerCase();
  const rows = table.querySelectorAll('tbody tr');
  rows.forEach(row => {
    const text = row.textContent.toLowerCase();
    const rowSalle = row.dataset.salle?.toLowerCase() || '';
    const matchTerm  = !term  || text.includes(term);
    const matchSalle = !salle || rowSalle === salle;
    row.style.display = (matchTerm && matchSalle) ? '' : 'none';
  });
}

searchInput?.addEventListener('input', filterTable);
filterSalle?.addEventListener('change', filterTable);
