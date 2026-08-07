(() => {
  const guestItems = document.querySelectorAll('[data-nav-auth="guest"]');
  const memberItems = document.querySelectorAll('[data-nav-auth="member"]');
  const emailLabels = document.querySelectorAll('[data-nav-user-email]');

  function setAuthenticated(user) {
    guestItems.forEach((item) => { item.hidden = true; });
    memberItems.forEach((item) => { item.hidden = false; });

    emailLabels.forEach((label) => {
      label.textContent = user?.email || "Account";
    });
  }

  function setGuest() {
    guestItems.forEach((item) => { item.hidden = false; });
    memberItems.forEach((item) => { item.hidden = true; });
  }

  async function loadAuthState() {
    try {
      const response = await fetch('/api/auth/me', {
        method: 'GET',
        credentials: 'same-origin',
        cache: 'no-store',
        headers: { Accept: 'application/json' },
      });

      if (!response.ok) {
        setGuest();
        return;
      }

      const data = await response.json();
      if (data?.user) setAuthenticated(data.user);
      else setGuest();
    } catch (error) {
      console.error('Unable to load navigation account state:', error);
      setGuest();
    }
  }

  function closeDropdown(dropdown) {
    dropdown.classList.remove('is-open');
    dropdown.querySelector('[aria-expanded]')?.setAttribute('aria-expanded', 'false');
  }

  function closeAllDropdowns(except = null) {
    document.querySelectorAll('.account-nav-dropdown.is-open').forEach((dropdown) => {
      if (dropdown !== except) closeDropdown(dropdown);
    });
  }

  document.querySelectorAll('.account-nav-dropdown').forEach((dropdown) => {
    const trigger = dropdown.querySelector('.account-nav-trigger, .account-menu-trigger');
    if (!trigger) return;

    trigger.setAttribute('aria-haspopup', 'true');
    trigger.setAttribute('aria-expanded', 'false');

    trigger.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();

      const willOpen = !dropdown.classList.contains('is-open');
      closeAllDropdowns(dropdown);
      dropdown.classList.toggle('is-open', willOpen);
      trigger.setAttribute('aria-expanded', String(willOpen));
    });

    dropdown.addEventListener('focusout', (event) => {
      if (!dropdown.contains(event.relatedTarget)) closeDropdown(dropdown);
    });
  });

  document.addEventListener('click', () => closeAllDropdowns());
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeAllDropdowns();
  });

  const header = document.querySelector('.account-header');
  const mobileToggle = document.querySelector('.account-mobile-toggle');

  function closeMobileMenu() {
    if (!header || !mobileToggle) return;

    header.classList.remove('mobile-open');
    mobileToggle.classList.remove('is-open');
    mobileToggle.setAttribute('aria-expanded', 'false');

    closeAllDropdowns();
  }

  if (header && mobileToggle) {
    mobileToggle.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();

      const willOpen = !header.classList.contains('mobile-open');

      header.classList.toggle('mobile-open', willOpen);
      mobileToggle.classList.toggle('is-open', willOpen);
      mobileToggle.setAttribute('aria-expanded', String(willOpen));

      if (!willOpen) {
        closeAllDropdowns();
      }
    });

    document
      .querySelectorAll('.account-nav-links > a')
      .forEach((link) => {
        link.addEventListener('click', closeMobileMenu);
      });
  }
  loadAuthState();
})();
