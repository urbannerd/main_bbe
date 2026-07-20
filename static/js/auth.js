const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const authMessage = document.getElementById("auth-message");

if (loginForm && authMessage) {
  loginForm.addEventListener("submit", (event) => {
    event.preventDefault();

    authMessage.textContent =
      "Login functionality will be connected next.";
  });
}

if (registerForm && authMessage) {
  registerForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const password = document.getElementById("password").value;
    const confirmPassword =
      document.getElementById("confirm-password").value;

    if (password !== confirmPassword) {
      authMessage.textContent = "Passwords do not match.";
      return;
    }

    authMessage.textContent =
      "Registration functionality will be connected next.";
  });
}