const pricingMessage =
  document.getElementById("pricing-message");

const pricingAccountLink =
  document.getElementById("pricing-account-link");

const pricingYear =
  document.getElementById("pricing-year");

const planButtons =
  document.querySelectorAll("[data-plan-action]");

const planCards =
  document.querySelectorAll("[data-plan-card]");

let currentUser = null;


function showPricingMessage(message, type = "error") {
  if (!pricingMessage) return;

  pricingMessage.textContent = message;

  if (message) {
    pricingMessage.dataset.type = type;
  } else {
    delete pricingMessage.dataset.type;
  }
}


async function getResponseData(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}


function formatPlanName(plan) {
  if (!plan) return "Free";

  return String(plan)
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
    button.dataset.originalText =
      button.textContent;

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


function redirectToRegistration(plan) {
  const url = new URL(
    "/register",
    window.location.origin
  );

  if (plan && plan !== "free") {
    url.searchParams.set("plan", plan);
  }

  window.location.href = url.toString();
}


function renderLoggedOutState() {
  currentUser = null;

  if (pricingAccountLink) {
    pricingAccountLink.textContent = "Log In";
    pricingAccountLink.href = "/login";
  }

  planButtons.forEach((button) => {
    const plan =
      button.dataset.planAction || "free";

    if (plan === "free") {
      button.textContent = "Create Free Account";
      return;
    }

    button.textContent =
      `Choose ${formatPlanName(plan)}`;
  });
}


function renderLoggedInState(user) {
  currentUser = user;

  const currentPlan = String(
    user.membership_plan || "free"
  ).toLowerCase();

  if (pricingAccountLink) {
    pricingAccountLink.textContent = "My Account";
    pricingAccountLink.href = "/account";
  }

  planCards.forEach((card) => {
    const cardPlan = String(
      card.dataset.planCard || "free"
    ).toLowerCase();

    const isCurrentPlan =
      cardPlan === currentPlan;

    card.classList.toggle(
      "pricing-card-current",
      isCurrentPlan
    );

    if (isCurrentPlan) {
      card.dataset.current = "true";
    } else {
      delete card.dataset.current;
    }
  });

  planButtons.forEach((button) => {
    const plan = String(
      button.dataset.planAction || "free"
    ).toLowerCase();

    const isCurrentPlan =
      plan === currentPlan;

    button.disabled = isCurrentPlan;

    button.classList.toggle(
      "account-card-action-disabled",
      isCurrentPlan
    );

    if (isCurrentPlan) {
      button.textContent = "Current Plan";
      button.setAttribute(
        "aria-disabled",
        "true"
      );
    } else {
      button.textContent =
        plan === "free"
          ? "Free Plan"
          : `Choose ${formatPlanName(plan)}`;

      button.removeAttribute("aria-disabled");
    }
  });
}


async function loadCurrentUser() {
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

    if (response.status === 401) {
      renderLoggedOutState();
      return;
    }

    const data = await getResponseData(response);

    if (!response.ok || !data.user) {
      throw new Error(
        data.detail ||
        "Unable to load membership information."
      );
    }

    renderLoggedInState(data.user);
  } catch (error) {
    console.error(
      "Unable to load pricing account state:",
      error
    );

    renderLoggedOutState();
  }
}


async function selectPaidPlan(plan, button) {
  if (!currentUser) {
    redirectToRegistration(plan);
    return;
  }

  const currentPlan = String(
    currentUser.membership_plan || "free"
  ).toLowerCase();

  if (currentPlan === plan) {
    showPricingMessage(
      `You are already on the ${formatPlanName(plan)} plan.`,
      "success"
    );

    return;
  }

  showPricingMessage("");

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
      redirectToRegistration(plan);
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
      window.location.href = checkoutUrl;
      return;
    }

    showPricingMessage(
      `Your membership was updated to ${formatPlanName(plan)}.`,
      "success"
    );

    await loadCurrentUser();
  } catch (error) {
    console.error(
      "Pricing subscription update failed:",
      error
    );

    showPricingMessage(
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


function handlePlanSelection(event) {
  const button = event.currentTarget;

  const plan = String(
    button.dataset.planAction || "free"
  ).toLowerCase();

  if (button.disabled) return;

  if (plan === "free") {
    if (currentUser) {
      window.location.href = "/account";
    } else {
      redirectToRegistration("free");
    }

    return;
  }

  selectPaidPlan(plan, button);
}


planButtons.forEach((button) => {
  button.addEventListener(
    "click",
    handlePlanSelection
  );
});


if (pricingYear) {
  pricingYear.textContent =
    String(new Date().getFullYear());
}

document
  .querySelectorAll(".site-footer-year")
  .forEach((element) => {
    element.textContent =
      String(new Date().getFullYear());
  });


loadCurrentUser();