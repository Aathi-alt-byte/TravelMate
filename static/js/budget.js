const form = document.querySelector('#budget-form');
const expenseFields = [
  ['transportation', document.querySelector('#cost-transportation'), 'Transportation cost', 'transportation-error'],
  ['local_transportation', document.querySelector('#cost-local'), 'Local travel cost', 'local-error'],
  ['accommodation', document.querySelector('#cost-accommodation'), 'Accommodation cost', 'accommodation-error'],
  ['food', document.querySelector('#cost-food'), 'Food expenses', 'food-error'],
  ['activities', document.querySelector('#cost-activities'), 'Sightseeing and activity costs', 'activities-error'],
  ['other', document.querySelector('#cost-other'), 'Other expenses', 'other-error'],
];
const travelersInput = document.querySelector('#budget-travelers');
const daysInput = document.querySelector('#budget-days');
const limitInput = document.querySelector('#budget-limit');
const saveButton = document.querySelector('#save-budget');
const saveStatus = document.querySelector('#save-status');
const destinationSelect = document.querySelector('#budget-destination');
const money = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 });
const storageKey = 'travelmate.budget.v1';

function setError(input, errorId, message) {
  const error = document.querySelector(`#${errorId}`);
  error.textContent = message;
  input.setAttribute('aria-invalid', String(Boolean(message)));
}

function readInteger(input, { minimum, maximum, label, errorId, deferEmptyError = false, unit = 'rupees' }) {
  const raw = input.value.trim();
  const value = Number(raw);
  let message = '';
  if (raw === '') message = deferEmptyError && !input.dataset.touched ? '' : `Enter ${label.toLowerCase()}.`;
  else if (!Number.isFinite(value)) message = `Enter ${label.toLowerCase()}.`;
  else if (!Number.isInteger(value)) message = `${label} must be a whole number of ${unit}.`;
  else if (value < minimum) message = `${label} cannot be negative${minimum === 1 ? ' or zero' : ''}.`;
  else if (value > maximum) message = `${label} must be ${unit === 'rupees' ? money.format(maximum) : `${maximum} ${unit}`} or less.`;
  if (errorId) setError(input, errorId, message);
  else input.setAttribute('aria-invalid', String(Boolean(message)));
  return { value, valid: raw !== '' && !message };
}

function updateCalculator() {
  const travelerResult = readInteger(travelersInput, { minimum: 1, maximum: 20, label: 'Travelers', errorId: 'travelers-error', unit: 'people' });
  const dayResult = readInteger(daysInput, { minimum: 1, maximum: 365, label: 'Trip duration', errorId: 'days-error', unit: 'days' });
  const budgetResult = readInteger(limitInput, { minimum: 1, maximum: 50000000, label: 'Your total budget', errorId: 'budget-error', deferEmptyError: true });
  const categories = {};
  let inputsValid = travelerResult.valid && dayResult.valid;

  expenseFields.forEach(([key, input, label, errorId]) => {
    const result = readInteger(input, { minimum: 0, maximum: 5000000, label, errorId });
    categories[key] = result.valid ? result.value : 0;
    inputsValid = inputsValid && result.valid;
  });

  const travelers = travelerResult.valid ? travelerResult.value : 1;
  const days = dayResult.valid ? dayResult.value : 1;
  const dailyPerPerson = Object.values(categories).reduce((sum, amount) => sum + amount, 0);
  const estimatedTotal = dailyPerPerson * travelers * days;
  const costPerPerson = travelers > 0 ? dailyPerPerson * days : 0;
  const comparison = document.querySelector('#budget-comparison');

  document.querySelector('#total-cost').textContent = money.format(estimatedTotal);
  document.querySelector('#per-person-cost').textContent = money.format(costPerPerson);
  document.querySelector('#results-duration').textContent = `${days} ${days === 1 ? 'day' : 'days'}`;
  document.querySelector('.results-footnote').textContent = `Calculated from your daily estimates × ${travelers} ${travelers === 1 ? 'traveler' : 'travelers'} × ${days} ${days === 1 ? 'day' : 'days'}.`;

  const chartTotal = Object.values(categories).reduce((sum, amount) => sum + amount * travelers * days, 0);
  expenseFields.forEach(([key]) => {
    const item = document.querySelector(`.breakdown-item[data-key="${key}"]`);
    const categoryTotal = categories[key] * travelers * days;
    item.querySelector('strong').textContent = money.format(categoryTotal);
    item.querySelector('.breakdown-track i').style.width = chartTotal > 0 ? `${(categoryTotal / chartTotal) * 100}%` : '0%';
    item.setAttribute('aria-label', `${key}: ${money.format(categoryTotal)}, ${chartTotal > 0 ? Math.round((categoryTotal / chartTotal) * 100) : 0}% of estimated total`);
  });

  if (!budgetResult.valid) {
    comparison.dataset.state = limitInput.value.trim() ? 'invalid' : 'unset';
    document.querySelector('#comparison-title').textContent = limitInput.value.trim() ? 'Check your budget limit' : 'Add a budget to compare';
    document.querySelector('#comparison-copy').textContent = limitInput.value.trim() ? 'Enter a whole amount from ₹1 to ₹5,00,00,000.' : 'Your estimate updates as you edit.';
  } else {
    const withinBudget = estimatedTotal <= budgetResult.value;
    const difference = Math.abs(budgetResult.value - estimatedTotal);
    comparison.dataset.state = withinBudget ? 'within' : 'over';
    document.querySelector('#comparison-title').textContent = withinBudget ? 'Within your budget' : 'Over your budget';
    document.querySelector('#comparison-copy').textContent = withinBudget ? `${money.format(difference)} left in your budget.` : `${money.format(difference)} above your budget limit.`;
  }

  saveButton.disabled = !inputsValid || !budgetResult.valid;
  return { inputsValid, budgetValid: budgetResult.valid, categories, travelers, days, budget: budgetResult.value, estimatedTotal, costPerPerson };
}

function collectState() {
  const totals = updateCalculator();
  return {
    inputsValid: totals.inputsValid,
    budgetValid: totals.budgetValid,
    destination: destinationSelect.value,
    transportation: totals.categories.transportation,
    local_transportation: totals.categories.local_transportation,
    accommodation: totals.categories.accommodation,
    food: totals.categories.food,
    activities: totals.categories.activities,
    other: totals.categories.other,
    travelers: totals.travelers,
    days: totals.days,
    budget: totals.budget,
    estimatedTotal: totals.estimatedTotal,
    costPerPerson: totals.costPerPerson,
  };
}

function applyState(state) {
  if (state.destination && [...destinationSelect.options].some((option) => option.value === state.destination)) destinationSelect.value = state.destination;
  for (const [key, input] of expenseFields) {
    if (Number.isFinite(Number(state[key]))) input.value = String(state[key]);
  }
  if (Number.isFinite(Number(state.travelers))) travelersInput.value = String(state.travelers);
  if (Number.isFinite(Number(state.days))) daysInput.value = String(state.days);
  if (Number.isFinite(Number(state.budget)) && Number(state.budget) > 0) limitInput.value = String(state.budget);
}

for (const input of [...form.querySelectorAll('input'), destinationSelect]) {
  input.addEventListener('input', () => {
    input.dataset.touched = 'true';
    if (saveButton.dataset.saved === 'true') {
      saveButton.innerHTML = 'Save Budget';
      delete saveButton.dataset.saved;
      saveStatus.textContent = '';
    }
    updateCalculator();
  });
  input.addEventListener('change', () => {
    if (saveButton.dataset.saved === 'true') {
      saveButton.innerHTML = 'Save Budget';
      delete saveButton.dataset.saved;
      saveStatus.textContent = '';
    }
    updateCalculator();
  });
}
limitInput.addEventListener('blur', () => {
  limitInput.dataset.touched = 'true';
  updateCalculator();
});

destinationSelect.addEventListener('change', () => {
  const option = destinationSelect.selectedOptions[0];
  const dailyCost = Number(option.dataset.dailyCost || 0);
  if (dailyCost > 0) {
    const values = {
      transportation: Math.floor(dailyCost * 8 / 100),
      local_transportation: Math.floor(dailyCost * 10 / 100),
      accommodation: Math.floor(dailyCost * 40 / 100),
      food: Math.floor(dailyCost * 25 / 100),
      activities: Math.floor(dailyCost * 14 / 100),
    };
    values.other = dailyCost - Object.values(values).reduce((sum, amount) => sum + amount, 0);
    for (const [key, input] of expenseFields) input.value = String(values[key]);
  }
  updateCalculator();
  document.querySelector('#results-destination').childNodes[0].textContent = destinationSelect.value || 'Your getaway';
});

const initialParams = new URLSearchParams(window.location.search);
if (!initialParams.size) {
  try {
    const saved = localStorage.getItem(storageKey);
    if (saved) applyState(JSON.parse(saved));
  } catch {
    saveStatus.textContent = 'Saved budget could not be loaded in this browser.';
  }
}

const backLink = document.querySelector('#back-to-plan');
const backParams = new URLSearchParams();
for (const key of ['destination', 'starting_location', 'start_date', 'end_date', 'travelers', 'accommodation', 'transportation', 'budget']) {
  const value = initialParams.get(key);
  if (value) backParams.set(key, value);
}
for (const preference of initialParams.getAll('preferences')) backParams.append('preferences', preference);
if (destinationSelect.value) backParams.set('destination', destinationSelect.value);
if (!backParams.has('travelers')) backParams.set('travelers', travelersInput.value);
if (!backParams.has('budget') && limitInput.value) backParams.set('budget', limitInput.value);
backLink.href = `/plan?${backParams.toString()}`;

saveButton.addEventListener('click', () => {
  const state = collectState();
  if (!state.inputsValid || !state.budgetValid) {
    if (!limitInput.value.trim()) setError(limitInput, 'budget-error', 'Enter your total budget.');
    saveStatus.textContent = 'Correct the highlighted values and add a budget limit before saving.';
    if (!limitInput.value.trim()) limitInput.focus();
    return;
  }
  try {
    localStorage.setItem(storageKey, JSON.stringify({ ...state, savedAt: new Date().toISOString() }));
    saveStatus.textContent = `Budget saved on this device · ${new Date().toLocaleString()}`;
    saveButton.dataset.saved = 'true';
    saveButton.innerHTML = '<span aria-hidden="true">✓</span> Saved';
  } catch {
    saveStatus.textContent = 'This browser could not save the budget. Check local storage settings and try again.';
  }
});

const menuToggle = document.querySelector('.menu-toggle');
const primaryNav = document.querySelector('#primary-nav');
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

updateCalculator();