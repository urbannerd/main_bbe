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

const qqqBoardScaleAccessBadge =
  document.getElementById(
    "qqq-board-scale-access-badge"
  );

const qqqBoardScaleAccessLink =
  document.getElementById(
    "qqq-board-scale-access-link"
  );

const spyBoardScaleAccessBadge =
  document.getElementById(
    "spy-board-scale-access-badge"
  );

const spyBoardScaleAccessLink =
  document.getElementById(
    "spy-board-scale-access-link"
  );

const impulseAccessBadge =
  document.getElementById(
    "impulse-access-badge"
  );

const impulseAccessLink =
  document.getElementById(
    "impulse-access-link"
  );

const leapAccessBadge =
  document.getElementById(
    "leap-access-badge"
  );

const leapAccessLink =
  document.getElementById(
    "leap-access-link"
  );

const subscriptionBadge =
  document.getElementById("subscription-badge");

const subscriptionPlan =
  document.getElementById("subscription-plan");

const subscriptionStatus =
  document.getElementById("subscription-status");

const subscriptionRenewalItem =
  document.getElementById("subscription-renewal-item");

const subscriptionRenewalLabel =
  document.getElementById("subscription-renewal-label");

const subscriptionRenewalDate =
  document.getElementById("subscription-renewal-date");

const subscriptionCancellationNotice =
  document.getElementById("subscription-cancellation-notice");

const subscriptionCancellationCopy =
  document.getElementById("subscription-cancellation-copy");

const manageSubscription =
  document.getElementById("manage-subscription");

const upgradeTrader =
  document.getElementById("upgrade-trader");

const upgradeProfessional =
  document.getElementById("upgrade-professional");

const upgradeStarter =
  document.getElementById("upgrade-starter");

const reactivateSubscription =
  document.getElementById("reactivate-subscription");

const paymentWarning =
  document.getElementById("payment-warning");

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


function formatBillingDate(value) {
  if (!value) return "Unavailable";

  let normalizedValue = value;

  if (
    typeof value === "string" &&
    /^\d+$/.test(value)
  ) {
    normalizedValue = Number(value);
  }

  if (
    typeof normalizedValue === "number" &&
    normalizedValue < 1000000000000
  ) {
    normalizedValue *= 1000;
  }

  const date = new Date(normalizedValue);

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
    .replace(/\b\w/g, (character) =>
      character.toUpperCase()
    );
}


function setButtonLoading(
  button,
  isLoading,
  loadingText = "Please wait..."
) {
  if (!button) return;

  if (isLoading) {
    if (!button.dataset.originalText) {
      button.dataset.originalText =
        button.textContent;
    }

    button.textContent = loadingText;
    button.disabled = true;
    return;
  }

  button.textContent =
    button.dataset.originalText ||
    button.textContent;

  button.disabled = false;

  delete button.dataset.originalText;
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

  if (!link) return;

  if (hasAccess) {
    link.classList.remove(
      "account-card-action-disabled"
    );

    link.removeAttribute("aria-disabled");
    link.removeAttribute("tabindex");
  } else {
    link.classList.add(
      "account-card-action-disabled"
    );

    link.setAttribute(
      "aria-disabled",
      "true"
    );

    link.setAttribute(
      "tabindex",
      "-1"
    );
  }
}


function handleLockedScannerClick(event) {
  const link = event.currentTarget;

  if (
    link.getAttribute("aria-disabled") !==
    "true"
  ) {
    return;
  }

  event.preventDefault();

  showAccountMessage(
    "This tool requires an active membership with access."
  );
}


function normalizeMembershipPlan(plan) {
  const value = String(
    plan || "free"
  ).trim().toLowerCase();

  const aliases = {
    basic: "free",
    starter_plan: "starter",
    trader_plan: "trader",
    professional_plan: "professional",
    pro: "professional",
  };

  return aliases[value] || value;
}


function normalizeMembershipStatus(status) {
  return String(
    status || "inactive"
  ).trim().toLowerCase();
}


function isActiveMembership(status) {
  return [
    "active",
    "trialing",
  ].includes(status);
}


function renderSubscriptionActions(user) {
  const plan = normalizeMembershipPlan(
    user.membership_plan
  );

  const status = normalizeMembershipStatus(
    user.membership_status ||
    user.stripe_subscription_status
  );

  const buttons = [
    upgradeStarter,
    upgradeTrader,
    upgradeProfessional,
    manageSubscription,
    reactivateSubscription,
  ];

  /*
   * Reset every subscription action before deciding
   * which controls should be visible.
   */
  buttons.forEach((button) => {
    if (button) {
      button.hidden = true;
    }
  });

  if (paymentWarning) {
    paymentWarning.hidden = true;
  }

  /*
   * Cancelled or inactive users may still have an old
   * paid membership_plan stored in the database.
   */
  const inactiveStatuses = [
    "cancelled",
    "canceled",
    "inactive",
    "unpaid",
    "incomplete",
    "incomplete_expired",
  ];

  if (inactiveStatuses.includes(status)) {
    const hasStripeCustomer =
      Boolean(user.stripe_customer_id);
  
    /*
     * A free user without a Stripe customer is a new/free
     * member, not a cancelled subscriber.
     */
    if (plan === "free" && !hasStripeCustomer) {
      if (upgradeStarter) {
        upgradeStarter.hidden = false;
      }
  
      if (upgradeTrader) {
        upgradeTrader.hidden = false;
      }
  
      if (upgradeProfessional) {
        upgradeProfessional.hidden = false;
      }
  
      return;
    }
  
    /*
     * A user with an existing Stripe billing account can
     * reopen the portal to reactivate or resubscribe.
     */
    if (
      reactivateSubscription &&
      hasStripeCustomer
    ) {
      reactivateSubscription.hidden = false;
      return;
    }
  
    /*
     * Fallback when no Stripe customer exists.
     */
    if (upgradeStarter) {
      upgradeStarter.hidden = false;
    }
  
    if (upgradeTrader) {
      upgradeTrader.hidden = false;
    }
  
    if (upgradeProfessional) {
      upgradeProfessional.hidden = false;
    }
  
    return;
  }

  if (status === "past_due") {
    if (manageSubscription) {
      manageSubscription.hidden = false;
    }

    if (paymentWarning) {
      paymentWarning.hidden = false;
    }

    return;
  }

  if (!isActiveMembership(status)) {
    if (reactivateSubscription) {
      reactivateSubscription.hidden = false;
    }

    return;
  }

  switch (plan) {
    case "free":
      if (upgradeStarter) {
        upgradeStarter.hidden = false;
      }

      if (upgradeTrader) {
        upgradeTrader.hidden = false;
      }

      if (upgradeProfessional) {
        upgradeProfessional.hidden = false;
      }

      break;

    case "starter":
      if (manageSubscription) {
        manageSubscription.hidden = false;
      }

      if (upgradeTrader) {
        upgradeTrader.hidden = false;
      }

      if (upgradeProfessional) {
        upgradeProfessional.hidden = false;
      }

      break;

    case "trader":
      if (manageSubscription) {
        manageSubscription.hidden = false;
      }

      if (upgradeProfessional) {
        upgradeProfessional.hidden = false;
      }

      break;

    case "professional":
      if (manageSubscription) {
        manageSubscription.hidden = false;
      }

      break;

    default:
      console.warn(
        "Unknown membership plan:",
        plan
      );

      if (reactivateSubscription) {
        reactivateSubscription.hidden = false;
      }
  }
}

function renderSubscriptionDetails({
  membershipPlan,
  membershipStatus,
  cancelAtPeriodEnd,
  currentPeriodEnd,
}) {
  const formattedPlan =
    formatMembershipLabel(membershipPlan);

  const formattedStatus =
    formatMembershipLabel(membershipStatus);

  const formattedPeriodEnd =
    formatBillingDate(currentPeriodEnd);

  if (subscriptionBadge) {
    subscriptionBadge.textContent =
      `${formattedPlan} · ${formattedStatus}`;

    subscriptionBadge.dataset.status =
      membershipStatus;
  }

  if (subscriptionPlan) {
    subscriptionPlan.textContent =
      formattedPlan;
  }

  if (subscriptionStatus) {
    if (
      cancelAtPeriodEnd &&
      membershipStatus === "active"
    ) {
      subscriptionStatus.textContent =
        "Active — Cancels at period end";
    } else {
      subscriptionStatus.textContent =
        formattedStatus;
    }
  }

  const isPaidPlan =
    String(membershipPlan).toLowerCase() !==
    "free";

  const hasValidPeriodEnd =
    currentPeriodEnd &&
    formattedPeriodEnd !== "Unavailable";

  if (subscriptionRenewalItem) {
    subscriptionRenewalItem.hidden =
      !isPaidPlan || !hasValidPeriodEnd;
  }

  if (
    subscriptionRenewalLabel &&
    isPaidPlan &&
    hasValidPeriodEnd
  ) {
    subscriptionRenewalLabel.textContent =
      cancelAtPeriodEnd
        ? "Access Until"
        : "Renews On";
  }

  if (
    subscriptionRenewalDate &&
    isPaidPlan &&
    hasValidPeriodEnd
  ) {
    subscriptionRenewalDate.textContent =
      formattedPeriodEnd;
  }

  const shouldShowCancellationNotice =
    cancelAtPeriodEnd &&
    membershipStatus === "active" &&
    isPaidPlan &&
    hasValidPeriodEnd;

  if (subscriptionCancellationNotice) {
    subscriptionCancellationNotice.hidden =
      !shouldShowCancellationNotice;
  }

  if (subscriptionCancellationCopy) {
    subscriptionCancellationCopy.textContent =
      shouldShowCancellationNotice
        ? ` Your ${formattedPlan} access remains active through ${formattedPeriodEnd}. You can resume your subscription from the billing portal before that date.`
        : "";
  }
}


function renderUser(user) {
  const email =
    user.email || "Unavailable";

  const accountIsActive =
    Boolean(user.is_active);

  const membershipStatus = String(
    user.membership_status || "inactive"
  ).toLowerCase();

  const membershipPlan = String(
    user.membership_plan || "free"
  ).toLowerCase();

  const allowedTools =
    Array.isArray(user.allowed_tools)
      ? user.allowed_tools
      : [];

  const cancelAtPeriodEnd =
    user.cancel_at_period_end === true ||
    user.cancel_at_period_end === 1 ||
    user.cancel_at_period_end === "true";

  const currentPeriodEnd =
    user.current_period_end ||
    user.subscription_period_end ||
    user.cancel_at ||
    null;

  if (accountEmail) {
    accountEmail.textContent = email;
  }

  if (accountStatus) {
    const hasActiveMembership =
      membershipStatus === "active" ||
      membershipStatus === "trialing";

    if (
      hasActiveMembership &&
      cancelAtPeriodEnd
    ) {
      accountStatus.textContent =
        "Cancels at period end";
    } else if (hasActiveMembership) {
      accountStatus.textContent =
        "Active membership";
    } else {
      accountStatus.textContent =
        "Inactive membership";
    }

    accountStatus.dataset.status =
      hasActiveMembership
        ? "active"
        : "inactive";
  }

  if (profileEmail) {
    profileEmail.textContent = email;
  }

  if (profileStatus) {
    const hasActiveMembership =
      membershipStatus === "active" ||
      membershipStatus === "trialing";
  
    profileStatus.textContent =
      hasActiveMembership
        ? "Active Membership"
        : "Inactive Membership";
  
    profileStatus.dataset.status =
      hasActiveMembership
        ? "active"
        : "inactive";
  }

  if (profileCreatedAt) {
    profileCreatedAt.textContent =
      formatDate(user.created_at);
  }

  renderScannerAccess({
    hasAccess:
      accountIsActive &&
      allowedTools.includes(
        "qqq-live-chart"
      ),
    badge: qqqAccessBadge,
    link: qqqAccessLink,
  });

  renderScannerAccess({
    hasAccess:
      accountIsActive &&
      allowedTools.includes(
        "spy-live-chart"
      ),
    badge: spyAccessBadge,
    link: spyAccessLink,
  });

  renderScannerAccess({
    hasAccess:
      accountIsActive &&
      allowedTools.includes(
        "qqq-board-scale"
      ),
    badge: qqqBoardScaleAccessBadge,
    link: qqqBoardScaleAccessLink,
  });
  
  renderScannerAccess({
    hasAccess:
      accountIsActive &&
      allowedTools.includes(
        "spy-board-scale"
      ),
    badge: spyBoardScaleAccessBadge,
    link: spyBoardScaleAccessLink,
  });
  
  renderScannerAccess({
    hasAccess:
      accountIsActive &&
      allowedTools.includes(
        "impulse"
      ),
    badge: impulseAccessBadge,
    link: impulseAccessLink,
  });
  
  renderScannerAccess({
    hasAccess:
      accountIsActive &&
      allowedTools.includes(
        "leap"
      ),
    badge: leapAccessBadge,
    link: leapAccessLink,
  });

  renderSubscriptionDetails({
    membershipPlan,
    membershipStatus,
    cancelAtPeriodEnd,
    currentPeriodEnd,
  });

  if (manageSubscription) {
    const hasStripeCustomer =
      Boolean(user.stripe_customer_id);

    manageSubscription.disabled =
      !hasStripeCustomer;

    manageSubscription.classList.toggle(
      "account-card-action-disabled",
      !hasStripeCustomer
    );

    manageSubscription.title =
      hasStripeCustomer
        ? ""
        : "No Stripe billing account is connected.";
  }

  renderSubscriptionActions(user);
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
        cache: "no-store",
        headers: {
          Accept: "application/json",
        },
      }
    );

    const data =
      await getResponseData(response);

    if (response.status === 401) {
      redirectToLogin();
      return;
    }

    if (
      !response.ok ||
      !data.user
    ) {
      throw new Error(
        data.detail ||
        "Unable to load account."
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


async function openBillingPortal(
  button = manageSubscription
) {
  if (!button) return;

  showAccountMessage("");

  setButtonLoading(
    button,
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

    const data =
      await getResponseData(response);

    if (response.status === 401) {
      redirectToLogin();
      return;
    }

    if (
      !response.ok ||
      !data.portal_url
    ) {
      throw new Error(
        data.detail ||
        "Unable to open subscription management."
      );
    }

    window.location.href =
      data.portal_url;
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
      button,
      false
    );
  }
}


async function changeSubscription(
  plan,
  button
) {
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
          "Content-Type":
            "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          plan,
        }),
      }
    );

    const data =
      await getResponseData(response);

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

    const checkoutUrl =
      data.checkout_url ||
      data.url ||
      data.session_url;

    if (checkoutUrl) {
      window.location.href =
        checkoutUrl;
      return;
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
      false
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

qqqBoardScaleAccessLink?.addEventListener(
  "click",
  handleLockedScannerClick
);

spyBoardScaleAccessLink?.addEventListener(
  "click",
  handleLockedScannerClick
);

impulseAccessLink?.addEventListener(
  "click",
  handleLockedScannerClick
);

leapAccessLink?.addEventListener(
  "click",
  handleLockedScannerClick
);

manageSubscription?.addEventListener(
  "click",
  () => openBillingPortal(
    manageSubscription
  )
);

reactivateSubscription?.addEventListener(
  "click",
  () => openBillingPortal(
    reactivateSubscription
  )
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

upgradeStarter?.addEventListener(
  "click",
  () => {
    changeSubscription(
      "starter",
      upgradeStarter
    );
  }
);

if (accountYear) {
  accountYear.textContent =
    String(new Date().getFullYear());
}

loadAccount();