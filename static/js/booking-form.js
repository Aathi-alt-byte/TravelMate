const form = document.querySelector('#booking-form');
const output = document.querySelector('#booking-estimate');
if (form && output) {
  const updateEstimate = () => {
    const start = new Date(form.elements.start_date.value);
    const end = new Date(form.elements.end_date.value);
    const travelers = Number(form.elements.travelers.value || 0);
    if (!form.elements.start_date.value || !form.elements.end_date.value || end < start || !travelers) {
      output.textContent = 'Enter valid trip dates and traveller count to see an estimate.';
      return;
    }
    const days = Math.round((end - start) / 86400000) + 1;
    const total = (Number(form.dataset.daily) * days + Number(form.dataset.travel)) * travelers;
    output.textContent = `Estimated total: ₹${new Intl.NumberFormat('en-IN').format(total)} (estimate; server recalculates before payment).`;
  };
  form.addEventListener('input', updateEstimate);
  updateEstimate();
}
