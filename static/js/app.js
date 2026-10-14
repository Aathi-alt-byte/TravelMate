const searchForm = document.querySelector('#destination-search');
const queryInput = document.querySelector('#destination-query');
const resultsPanel = document.querySelector('#search-results');
const menuToggle = document.querySelector('.menu-toggle');
const primaryNav = document.querySelector('#primary-nav');

if (menuToggle && primaryNav) {
  menuToggle.addEventListener('click', () => {
    const isOpen = menuToggle.getAttribute('aria-expanded') === 'true';
    menuToggle.setAttribute('aria-expanded', String(!isOpen));
    primaryNav.classList.toggle('is-open', !isOpen);
  });

  primaryNav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      menuToggle.setAttribute('aria-expanded', 'false');
      primaryNav.classList.remove('is-open');
    });
  });
}

if (searchForm && queryInput && resultsPanel) {
  searchForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const query = queryInput.value.trim();
    resultsPanel.hidden = false;
    resultsPanel.setAttribute('aria-busy', 'true');
    resultsPanel.innerHTML = '<p class="search-empty search-loading">Looking for your next stop...</p>';

    try {
      const response = await fetch(`/api/destinations?q=${encodeURIComponent(query)}`);
      if (!response.ok) throw new Error('Search request failed');
      const destinations = await response.json();
      resultsPanel.setAttribute('aria-busy', 'false');

      if (!destinations.length) {
        resultsPanel.innerHTML = '<p class="search-empty">No match just yet. Try Ooty, Goa, Munnar, Kodaikanal, or Manali.</p>';
        return;
      }

      resultsPanel.replaceChildren(...destinations.map((destination) => {
        const result = document.createElement('a');
        result.className = 'search-result';
        result.href = '#destinations';
        const name = document.createElement('strong');
        name.textContent = destination.name;
        const region = document.createElement('span');
        region.textContent = destination.region;
        result.append(name, region);
        result.addEventListener('click', () => {
          queryInput.value = destination.name;
          resultsPanel.hidden = true;
        });
        return result;
      }));
    } catch {
      resultsPanel.setAttribute('aria-busy', 'false');
      resultsPanel.innerHTML = '<p class="search-empty">Search is unavailable right now. Please try again.</p>';
    }
  });

  document.addEventListener('click', (event) => {
    if (!searchForm.contains(event.target)) resultsPanel.hidden = true;
  });
}