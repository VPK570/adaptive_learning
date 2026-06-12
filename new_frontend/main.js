document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('login-form');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const emailError = document.getElementById('email-error');
  const passwordError = document.getElementById('password-error');
  const submitBtn = document.getElementById('submit-btn');

  // Simple validation logic
  const validateEmail = (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(String(email).toLowerCase());
  };

  const clearErrors = () => {
    emailInput.classList.remove('is-invalid');
    emailError.classList.remove('is-visible');
    passwordInput.classList.remove('is-invalid');
    passwordError.classList.remove('is-visible');
  };

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearErrors();

    let isValid = true;

    if (!emailInput.value.trim()) {
      emailInput.classList.add('is-invalid');
      emailError.textContent = 'Email address is required.';
      emailError.classList.add('is-visible');
      isValid = false;
    } else if (!validateEmail(emailInput.value)) {
      emailInput.classList.add('is-invalid');
      emailError.textContent = 'Please enter a valid email address.';
      emailError.classList.add('is-visible');
      isValid = false;
    }

    if (!passwordInput.value) {
      passwordInput.classList.add('is-invalid');
      passwordError.textContent = 'Password is required.';
      passwordError.classList.add('is-visible');
      isValid = false;
    }

    if (!isValid) return;

    // Simulate async login behaviour
    submitBtn.classList.add('is-loading');
    submitBtn.setAttribute('disabled', 'true');

    try {
      // Fake network request
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Simulate success
      console.log('Login intent registered successfully.');
    } catch (err) {
      console.error(err);
    } finally {
      // Revert loading state
      submitBtn.classList.remove('is-loading');
      submitBtn.removeAttribute('disabled');
    }
  });

  // Remove error state on input
  emailInput.addEventListener('input', () => {
    emailInput.classList.remove('is-invalid');
    emailError.classList.remove('is-visible');
  });

  passwordInput.addEventListener('input', () => {
    passwordInput.classList.remove('is-invalid');
    passwordError.classList.remove('is-visible');
  });

  // Role Tab Slider Logic
  const tabs = document.querySelectorAll('.role-tab');
  const slider = document.getElementById('role-tab-slider');

  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      // Remove active class from all tabs
      tabs.forEach(t => t.classList.remove('is-active'));
      
      // Add active class to clicked tab
      tab.classList.add('is-active');
      
      // Move slider to the corresponding index
      const index = parseInt(tab.getAttribute('data-index'), 10);
      slider.style.transform = `translateX(${index * 100}%)`;
    });
  });
});
