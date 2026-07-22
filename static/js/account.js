const accountPage = document.getElementById("account-page");
const accountLoading = document.getElementById("account-loading");
const accountMessage = document.getElementById("account-message");

const accountEmail = document.getElementById("account-email");
const accountStatus = document.getElementById("account-status");

const profileEmail = document.getElementById("profile-email");
const profileStatus = document.getElementById("profile-status");
const profileCreatedAt =
  document.getElementById("profile-created-at");

const logoutButton = document.getElementById("logout-button");
const accountYear = document.getElementById("account-year");

const qqqAccessBadge =
  document.getElementById("qqq-access-badge");

const qqqAccessLink =
  document.getElementById("qqq-access-link");

const spyAccessBadge =
  document.getElementById("spy-access-badge");

const spyAccessLink =
  document.getElementById("spy-access-link");

const subscriptionBadge =
  document.getElementById("subscription-badge");


function showAccountMessage(message, type = "error") {
  if (!accountMessage) {
    return;
  }

  accountMessage.textContent = message;

  if (message) {
    accountMessage.dataset.type = type;
  } else {
    delete accountMessage.dataset.type;
  }
}


async function getResponseData(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}


function redirectToLogin() {
  const nextPath = encodeURIComponent(
    window.location.pathname
  );

  window.location.replace(
    `/login?next=${nextPath}`
  );
}


function formatDate(value) {
  if (!value) {
    return "Unavailable";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Unavailable";
  }

  return new Intl.DateTimeFormat(
    "en-US",
    {
      month: "long",
      day: "numeric",
      year: "numeric",
    }
  ).format(date);
}


function formatMembershipLabel(value) {
  if (!value) {
    return "Free";
  }

  return value
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase()
    );
}


function renderScannerAccess({
  hasAccess,
  badge,
  link,
}) {
  if (badge) {
    badge.textContent = hasAccess
      ? "Included"
      : "Locked";

    badge.dataset.access = hasAccess
      ? "included"
      : "locked";

    badge.classList.toggle(
      "account-card-badge-muted",
      !hasAccess
    );
  }

  if (!link) {
    return;
  }

  if (hasAccess) {
    link.classList.remove(
      "account-card-action-disabled"
    );

    link.removeAttribute("aria-disabled");
    link.removeAttribute("tabindex");

    return;
  }

  link.classList.add(
    "account-card-action-disabled"
  );

  link.setAttribute("aria-disabled", "true");
  link.setAttribute("tabindex", "-1");
}


function handleLockedScannerClick(event) {
  const link = event.currentTarget;

  if (
    link.getAttribute("aria-disabled") !== "true"
  ) {
    return;
  }

  event.preventDefault();

  showAccountMessage(
    "This scanner requires an active membership.",
    "error"
  );
}


function renderUser(user) {
  const email = user.email || "Unavailable";
  const accountIsActive = Boolean(user.is_active);

  const status = accountIsActive
    ? "Active"
    : "Inactive";

  const membershipStatus =
    user.membership_status || "inactive";

  const membershipPlan =
    user.membership_plan || "free";

  const hasQqqAccess =
    accountIsActive &&
    Boolean(user.qqq_access);

  const hasSpyAccess =
    accountIsActive &&
    Boolean(user.spy_access);

  if (accountEmail) {
    accountEmail.textContent = email;
  }

  if (accountStatus) {
    accountStatus.textContent =
      membershipStatus === "active"
        ? "Active member"
        : "Inactive membership";

    accountStatus.dataset.status =
      membershipStatus === "active"
        ? "active"
        : "inactive";
  }

  if (profileEmail) {
    profileEmail.textContent = email;
  }

  if (profileStatus) {
    profileStatus.textContent = status;
  }

  if (profileCreatedAt) {
    profileCreatedAt.textContent =
      formatDate(user.created_at);
  }

  renderScannerAccess({
    hasAccess: hasQqqAccess,
    badge: qqqAccessBadge,
    link: qqqAccessLink,
  });

  renderScannerAccess({
    hasAccess: hasSpyAccess,
    badge: spyAccessBadge,
    link: spyAccessLink,
  });

  if (subscriptionBadge) {
    const planLabel =
      formatMembershipLabel(membershipPlan);

    const statusLabel =
      formatMembershipLabel(membershipStatus);

    subscriptionBadge.textContent =
      `${planLabel} · ${statusLabel}`;

    subscriptionBadge.dataset.status =
      membershipStatus;
  }
}


function showAccountPage() {
  if (accountLoading) {
    accountLoading.hidden = true;
  }

  if (accountPage) {
    accountPage.hidden = false;
  }
}


async function loadAccount() {
  try {
    const response = await fetch(
      "/api/auth/me",
      {
        method: "GET",
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
        },
      }
    );

    const data = await getResponseData(response);

    if (response.status === 401) {
      redirectToLogin();
      return;
    }

    if (!response.ok || !data.user) {
      throw new Error(
        data.detail || "Unable to load account."
      );
    }

    renderUser(data.user);
    showAccountPage();
  } catch (error) {
    console.error(
      "Account loading failed:",
      error
    );

    showAccountPage();

    showAccountMessage(
      "Unable to load your account. Please refresh the page."
    );
  }
}


async function logout() {
  if (!logoutButton) {
    return;
  }

  logoutButton.disabled = true;
  logoutButton.textContent = "Logging out...";

  showAccountMessage("");

  try {
    const response = await fetch(
      "/api/auth/logout",
      {
        method: "POST",
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
        },
      }
    );

    if (!response.ok) {
      const data =
        await getResponseData(response);

      throw new Error(
        data.detail || "Unable to log out."
      );
    }

    window.location.replace("/login");
  } catch (error) {
    console.error("Logout failed:", error);

    showAccountMessage(
      "Unable to log out. Please try again."
    );

    logoutButton.disabled = false;
    logoutButton.textContent = "Log Out";
  }
}


if (qqqAccessLink) {
  qqqAccessLink.addEventListener(
    "click",
    handleLockedScannerClick
  );
}


if (spyAccessLink) {
  spyAccessLink.addEventListener(
    "click",
    handleLockedScannerClick
  );
}


if (logoutButton) {
  logoutButton.addEventListener(
    "click",
    logout
  );
}


if (accountYear) {
  accountYear.textContent =
    String(new Date().getFullYear());
}


loadAccount();