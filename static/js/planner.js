const menuToggle = document.querySelector('.menu-toggle');
const primaryNav = document.querySelector('#primary-nav');
const startDate = document.querySelector('#start_date');
const endDate = document.querySelector('#end_date');
const form = document.querySelector('.planner-form');

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

if (startDate && endDate) {
  startDate.addEventListener('change', () => {
    if (startDate.value) endDate.min = startDate.value;
    if (endDate.value && endDate.value < startDate.value) endDate.value = startDate.value;
  });
}

if (form) {
  const fieldIds = {
    destination: 'destination-error',
    starting_location: 'starting-location-error',
    start_date: 'start-date-error',
    end_date: 'end-date-error',
    travelers: 'travelers-error',
    preferences: 'preferences-error',
    accommodation: 'accommodation-error',
    transportation: 'transportation-error',
    budget: 'budget-error',
  };

  let errorSummary = document.querySelector('.form-error-summary');
  if (!errorSummary) {
    errorSummary = document.createElement('div');
    errorSummary.className = 'form-error-summary';
    errorSummary.setAttribute('role', 'alert');
    errorSummary.setAttribute('tabindex', '-1');
    errorSummary.innerHTML = '<strong>Please check your trip details.</strong><span>Correct the highlighted fields and try again.</span>';
    errorSummary.hidden = true;
    form.parentElement.insertBefore(errorSummary, form);
  }

  const setError = (key, message) => {
    const error = document.getElementById(fieldIds[key]);
    const field = key === 'preferences'
      ? form.querySelector('input[name="preferences"]')
      : form.elements.namedItem(key);
    if (error) error.textContent = message;
    if (field && field.setAttribute) field.setAttribute('aria-invalid', message ? 'true' : 'false');
  };

  const clearErrors = () => Object.keys(fieldIds).forEach((key) => setError(key, ''));

  form.addEventListener('input', (event) => {
    if (event.target.name === 'preferences') setError('preferences', '');
    else if (event.target.name && fieldIds[event.target.name]) setError(event.target.name, '');
  });
  form.addEventListener('change', (event) => {
    if (event.target.name === 'preferences' && form.querySelector('input[name="preferences"]:checked')) {
      setError('preferences', '');
    }
  });

  form.addEventListener('submit', (event) => {
    clearErrors();
    const errors = {};
    const destination = form.elements.namedItem('destination').value;
    const start = form.elements.namedItem('start_date').value;
    const end = form.elements.namedItem('end_date').value;
    const location = form.elements.namedItem('starting_location').value.trim();
    const travelers = Number(form.elements.namedItem('travelers').value);
    const budget = Number(form.elements.namedItem('budget').value);
    const checkedPreferences = form.querySelectorAll('input[name="preferences"]:checked');

    if (!destination) errors.destination = 'Choose a destination from the list.';
    if (location.length < 2 || location.length > 80) errors.starting_location = 'Enter a starting city or town (80 characters or fewer).';
    if (!start) errors.start_date = 'Choose a start date.';
    else if (start < new Date().toISOString().slice(0, 10)) errors.start_date = 'Start date cannot be in the past.';
    if (!end) errors.end_date = 'Choose an end date.';
    else if (start && end < start) errors.end_date = 'End date must be the same day or after your start date.';
    else if (start && (Date.parse(`${end}T00:00:00`) - Date.parse(`${start}T00:00:00`)) / 86400000 >= 30) {
      errors.end_date = 'For this planner, choose a trip of 30 days or fewer.';
    }
    if (!Number.isInteger(travelers) || travelers < 1 || travelers > 20) errors.travelers = 'Choose between 1 and 20 travelers.';
    if (!checkedPreferences.length) errors.preferences = 'Choose at least one travel preference.';
    if (!form.elements.namedItem('accommodation').value) errors.accommodation = 'Choose an accommodation preference.';
    if (!form.elements.namedItem('transportation').value) errors.transportation = 'Choose a transportation preference.';
    if (!Number.isInteger(budget) || budget < 1 || budget > 50000000) errors.budget = 'Enter a budget greater than zero (up to ₹5,00,00,000).';

    if (Object.keys(errors).length || !form.checkValidity()) {
      event.preventDefault();
      Object.entries(errors).forEach(([key, message]) => setError(key, message));
      errorSummary.hidden = false;
      errorSummary.focus();
      const firstInvalid = Object.keys(errors)[0];
      const firstField = firstInvalid === 'preferences'
        ? form.querySelector('input[name="preferences"]')
        : form.elements.namedItem(firstInvalid);
      if (firstField) firstField.focus();
      return;
    }

    const submitButton = form.querySelector('.generate-button');
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.setAttribute('aria-busy', 'true');
      const label = submitButton.querySelector('.generate-label');
      const loading = submitButton.querySelector('.generate-loading');
      if (label) label.hidden = true;
      if (loading) loading.hidden = false;
    }
  });
}

const serverErrorSummary = document.querySelector('.form-error-summary:not([hidden])');
if (serverErrorSummary) serverErrorSummary.focus();
