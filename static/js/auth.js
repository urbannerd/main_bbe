const authMessage = document.getElementById("auth-message");
const registerForm = document.getElementById("register-form");
const loginForm = document.getElementById("login-form");


function showMessage(message, type = "error") {
  if (!authMessage) {
    return;
  }

  authMessage.textContent = message;

  if (message) {
    authMessage.dataset.type = type;
  } else {
    delete authMessage.dataset.type;
  }
}


async function getResponseData(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}


function setFormLoading(form, isLoading) {
  const submitButton = form.querySelector(
    'button[type="submit"], input[type="submit"]'
  );

  if (!submitButton) {
    return;
  }

  submitButton.disabled = isLoading;

  if (isLoading) {
    submitButton.dataset.originalText =
      submitButton.textContent || submitButton.value;

    if (submitButton.tagName === "INPUT") {
      submitButton.value = "Please wait...";
    } else {
      submitButton.textContent = "Please wait...";
    }
  } else {
    const originalText = submitButton.dataset.originalText;

    if (!originalText) {
      return;
    }

    if (submitButton.tagName === "INPUT") {
      submitButton.value = originalText;
    } else {
      submitButton.textContent = originalText;
    }

    delete submitButton.dataset.originalText;
  }
}


if (registerForm) {
  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage("");

    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const confirmPasswordInput =
      document.getElementById("confirm-password");
    const termsInput = document.getElementById("terms");

    const email = emailInput?.value.trim() || "";
    const password = passwordInput?.value || "";
    const confirmPassword = confirmPasswordInput?.value || "";

    if (!email || !password || !confirmPassword) {
      showMessage("Please complete every required field.");
      return;
    }

    if (password !== confirmPassword) {
      showMessage("Passwords do not match.");
      return;
    }

    if (password.length < 8) {
      showMessage("Password must be at least 8 characters.");
      return;
    }

    if (
      new TextEncoder().encode(password).length > 72
    ) {
      showMessage("Password must be 72 bytes or fewer.");
      return;
    }

    if (termsInput && !termsInput.checked) {
      showMessage(
        "You must accept the Terms, Privacy Policy, and Disclaimer."
      );
      return;
    }

    setFormLoading(registerForm, true);

    try {
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "same-origin",
        body: JSON.stringify({
          email,
          password,
        }),
      });

      const data = await getResponseData(response);

      if (!response.ok) {
        showMessage(
          data.detail || "Unable to create your account."
        );
        return;
      }

      showMessage(
        "Account created. Redirecting to login...",
        "success"
      );

      window.setTimeout(() => {
        window.location.href = "/login";
      }, 1000);
    } catch (error) {
      console.error("Registration failed:", error);

      showMessage(
        "Unable to connect to the server. Please try again."
      );
    } finally {
      setFormLoading(registerForm, false);
    }
  });
}


if (loginForm) {
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage("");

    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");

    const email = emailInput?.value.trim() || "";
    const password = passwordInput?.value || "";

    if (!email || !password) {
      showMessage("Enter your email address and password.");
      return;
    }

    setFormLoading(loginForm, true);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "same-origin",
        body: JSON.stringify({
          email,
          password,
        }),
      });

      const data = await getResponseData(response);

      if (!response.ok) {
        showMessage(
          data.detail || "Unable to log in."
        );
        return;
      }

      showMessage(
        "Login successful. Redirecting...",
        "success"
      );

      window.setTimeout(() => {
        window.location.href = "/account";
      }, 600);
    } catch (error) {
      console.error("Login failed:", error);

      showMessage(
        "Unable to connect to the server. Please try again."
      );
    } finally {
      setFormLoading(loginForm, false);
    }
  });
}