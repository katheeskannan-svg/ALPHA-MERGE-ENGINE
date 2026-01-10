// Small JS for dynamic bits and a simple contact handler
document.getElementById('year').textContent = new Date().getFullYear();

const form = document.getElementById('contact-form');
form.addEventListener('submit', e => {
  e.preventDefault();
  const email = document.getElementById('email').value.trim();
  const message = document.getElementById('message').value.trim();
  if (!email || !message) return alert('Please fill both fields.');
  // Open default mail client with prefilled subject/body
  const subject = encodeURIComponent('Portfolio contact from ' + email);
  const body = encodeURIComponent(message + '\n\nFrom: ' + email);
  window.location.href = `mailto:ikathees128@gmail.com?subject=${subject}&body=${body}`;
});
