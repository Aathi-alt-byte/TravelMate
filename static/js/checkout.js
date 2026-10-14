const payButton = document.querySelector('#pay');
const paymentStatus = document.querySelector('#status');
const processingMessage = document.querySelector('#payment-processing');

if (payButton && paymentStatus) {
  const setBusy = (busy) => {
    payButton.disabled = busy;
    payButton.setAttribute('aria-busy', String(busy));
    const label = payButton.querySelector('.pay-label');
    const loading = payButton.querySelector('.pay-loading');
    if (label) label.hidden = busy;
    if (loading) loading.hidden = !busy;
    if (processingMessage) processingMessage.hidden = !busy;
  };

  payButton.addEventListener('click', () => {
    if (!window.Razorpay) {
      paymentStatus.textContent = 'Secure Checkout is unavailable. Your booking remains unpaid; refresh the page or contact support.';
      return;
    }

    const config = payButton.dataset;
    setBusy(true);
    paymentStatus.textContent = 'Opening Razorpay Checkout…';
    try {
      const checkout = new window.Razorpay({
        key: config.key,
        amount: Number(config.amount),
        currency: 'INR',
        name: 'TravelMate',
        description: `${config.name} · ${config.bookingId}`,
        order_id: config.order,
        prefill: { name: config.name, email: config.email, contact: config.contact },
        notes: { booking_id: config.bookingId },
        handler: (response) => {
          paymentStatus.textContent = 'Payment received by Checkout. Verifying securely with the server…';
          if (processingMessage) processingMessage.hidden = false;
          const form = document.createElement('form');
          form.method = 'post';
          form.action = config.verifyUrl;
          for (const [name, value] of Object.entries({
            _csrf: config.csrf,
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature
          })) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = name;
            input.value = value;
            form.append(input);
          }
          document.body.append(form);
          form.submit();
        },
        modal: {
          ondismiss: () => {
            setBusy(false);
            paymentStatus.textContent = 'Checkout closed. The booking remains unpaid until the server verifies a captured payment.';
          }
        }
      });

      checkout.on('payment.failed', (event) => {
        setBusy(false);
        const reason = event && event.error && event.error.description;
        paymentStatus.textContent = reason
          ? `Payment failed: ${reason}. The booking remains unpaid.`
          : 'Payment failed. The booking remains unpaid; you can try again.';
      });
      checkout.open();
    } catch (error) {
      setBusy(false);
      paymentStatus.textContent = 'Secure Checkout could not start. Your booking remains unpaid; try again.';
    }
  });
}
