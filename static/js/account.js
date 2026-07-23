const accountPage = document.getElementById("account-page");
const accountLoading = document.getElementById("account-loading");
const accountMessage = document.getElementById("account-message");
const accountEmail = document.getElementById("account-email");
const accountStatus = document.getElementById("account-status");
const profileEmail = document.getElementById("profile-email");
const profileStatus = document.getElementById("profile-status");
const profileCreatedAt = document.getElementById("profile-created-at");
const accountYear = document.getElementById("account-year");

const qqqAccessBadge = document.getElementById("qqq-access-badge");
const qqqAccessLink = document.getElementById("qqq-access-link");
const spyAccessBadge = document.getElementById("spy-access-badge");
const spyAccessLink = document.getElementById("spy-access-link");

const subscriptionBadge =
  document.getElementById("subscription-badge");

const subscriptionPlan =
  document.getElementById("subscription-plan");

const subscriptionStatus =
  document.getElementById("subscription-status");

const manageSubscription =
  document.getElementById("manage-subscription");

const upgradeTrader =
  document.getElementById("upgrade-trader");

const upgradeProfessional =
  document.getElementById("upgrade-professional");


function showAccountMessage(message, type = "error") {
  if (!accountMessage) return;

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
  window.location.replace("/login");
}


function formatDate(value) {
  if (!value) return "Unavailable";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Unavailable";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  }).format(date);
}


function formatMembershipLabel(value) {
  if (!value) return "Free";

  return String(value)
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}


function setButtonLoading(button, isLoading, loadingText) {
  if (!button) return;

  if (isLoading) {
    button.dataset.originalText = button.textContent;
    button.textContent = loadingText;
    button.disabled = true;
    return;
  }

  button.textContent =
    button.dataset.originalText || button.textContent;

  button.disabled = false;
  delete button.dataset.originalText;
}


function renderScannerAccess({ hasAccess, badge, link }) {
  if (badge) {
    badge.textContent = hasAccess ? "Included" : "Locked";
    badge.dataset.access = hasAccess ? "included" : "locked";

    badge.classList.toggle(
      "account-card-badge-muted",
      !hasAccess
    );
  }

  if (!link) return;

  if (hasAccess) {
    link.classList.remove("account-card-action-disabled");
    link.removeAttribute("aria-disabled");
    link.removeAttribute("tabindex");
  } else {
    link.classList.add("account-card-action-disabled");
    link.setAttribute("aria-disabled", "true");
    link.setAttribute("tabindex", "-1");
  }
}


function handleLockedScannerClick(event) {
  const link = event.currentTarget;

  if (link.getAttribute("aria-disabled") !== "true") {
    return;
  }

  event.preventDefault();

  showAccountMessage(
    "This tool requires an active membership with access."
  );
}


function renderUpgradeButtons(membershipPlan) {
  const normalizedPlan = String(
    membershipPlan || "free"
  ).toLowerCase();

  if (upgradeTrader) {
    upgradeTrader.hidden = ![
      "free",
      "starter",
    ].includes(normalizedPlan);
  }

  if (upgradeProfessional) {
    upgradeProfessional.hidden =
      normalizedPlan === "professional";
  }
}


function renderUser(user) {
  const email = user.email || "Unavailable";
  const accountIsActive = Boolean(user.is_active);
  const membershipStatus =
    user.membership_status || "inactive";
  const membershipPlan =
    user.membership_plan || "free";
  const allowedTools = Array.isArray(user.allowed_tools)
    ? user.allowed_tools
    : [];

  if (accountEmail) {
    accountEmail.textContent = email;
  }

  if (accountStatus) {
    const hasActiveMembership =
      membershipStatus === "active";

    accountStatus.textContent = hasActiveMembership
      ? "Active membership"
      : "Inactive membership";

    accountStatus.dataset.status = hasActiveMembership
      ? "active"
      : "inactive";
  }

  if (profileEmail) {
    profileEmail.textContent = email;
  }

  if (profileStatus) {
    profileStatus.textContent = accountIsActive
      ? "Active"
      : "Inactive";
  }

  if (profileCreatedAt) {
    profileCreatedAt.textContent =
      formatDate(user.created_at);
  }

  renderScannerAccess({
    hasAccess:
      accountIsActive &&
      allowedTools.includes("qqq-live-chart"),
    badge: qqqAccessBadge,
    link: qqqAccessLink,
  });

  renderScannerAccess({
    hasAccess:
      accountIsActive &&
      allowedTools.includes("spy-live-chart"),
    badge: spyAccessBadge,
    link: spyAccessLink,
  });

  if (subscriptionBadge) {
    subscriptionBadge.textContent =
      `${formatMembershipLabel(membershipPlan)} · ` +
      `${formatMembershipLabel(membershipStatus)}`;

    subscriptionBadge.dataset.status =
      membershipStatus;
  }

  if (subscriptionPlan) {
    subscriptionPlan.textContent =
      formatMembershipLabel(membershipPlan);
  }

  if (subscriptionStatus) {
    subscriptionStatus.textContent =
      formatMembershipLabel(membershipStatus);
  }

  if (manageSubscription) {
    const hasStripeCustomer =
      membershipPlan !== "free";

    manageSubscription.disabled = !hasStripeCustomer;

    manageSubscription.classList.toggle(
      "account-card-action-disabled",
      !hasStripeCustomer
    );

    manageSubscription.title = hasStripeCustomer
      ? ""
      : "No Stripe billing account is connected.";
  }

  renderUpgradeButtons(membershipPlan);
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
    const response = await fetch("/api/auth/me", {
      method: "GET",
      credentials: "same-origin",
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });

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
    console.error("Account loading failed:", error);

    showAccountPage();

    showAccountMessage(
      "Unable to load your account. Please refresh the page."
    );
  }
}


async function openBillingPortal() {
  if (!manageSubscription) return;

  showAccountMessage("");

  setButtonLoading(
    manageSubscription,
    true,
    "Opening Portal..."
  );

  try {
    const response = await fetch(
      "/api/stripe/create-portal-session",
      {
        method: "POST",
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

    if (!response.ok || !data.portal_url) {
      throw new Error(
        data.detail ||
          "Unable to open subscription management."
      );
    }

    window.location.href = data.portal_url;
  } catch (error) {
    console.error(
      "Billing portal failed:",
      error
    );

    showAccountMessage(
      error.message ||
        "Unable to open subscription management."
    );

    setButtonLoading(
      manageSubscription,
      false,
      ""
    );
  }
}


async function changeSubscription(plan, button) {
  if (!button) return;

  showAccountMessage("");

  setButtonLoading(
    button,
    true,
    "Updating..."
  );

  try {
    const response = await fetch(
      "/api/stripe/change-subscription",
      {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          plan,
        }),
      }
    );

    const data = await getResponseData(response);

    if (response.status === 401) {
      redirectToLogin();
      return;
    }

    if (!response.ok) {
      throw new Error(
        data.detail ||
          "Unable to update your subscription."
      );
    }

    showAccountMessage(
      `Your membership was updated to ${formatMembershipLabel(plan)}.`,
      "success"
    );

    await loadAccount();
  } catch (error) {
    console.error(
      "Subscription update failed:",
      error
    );

    showAccountMessage(
      error.message ||
        "Unable to update your subscription."
    );
  } finally {
    setButtonLoading(
      button,
      false,
      ""
    );
  }
}


qqqAccessLink?.addEventListener(
  "click",
  handleLockedScannerClick
);

spyAccessLink?.addEventListener(
  "click",
  handleLockedScannerClick
);

manageSubscription?.addEventListener(
  "click",
  openBillingPortal
);

upgradeTrader?.addEventListener(
  "click",
  () => {
    changeSubscription(
      "trader",
      upgradeTrader
    );
  }
);

upgradeProfessional?.addEventListener(
  "click",
  () => {
    changeSubscription(
      "professional",
      upgradeProfessional
    );
  }
);

if (accountYear) {
  accountYear.textContent =
    String(new Date().getFullYear());
}

loadAccount();