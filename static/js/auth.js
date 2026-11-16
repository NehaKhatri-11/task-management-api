
// ==================================================
// API CONFIGURATION
// ==================================================

const API_URL = window.location.origin;

// ==================================================
// SIGNUP
// ==================================================

const signupForm = document.getElementById("signupForm");

if (signupForm) {

    signupForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        const name = document.getElementById("name").value.trim();
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        const message = document.getElementById("message");

        try {

            const response = await fetch(`${API_URL}/auth/signup`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    name: name,
                    email: email,
                    password: password
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Signup failed");
            }

            message.textContent = data.message;
            message.style.color = "green";

            signupForm.reset();

            setTimeout(() => {
                window.location.href = "login.html";
            }, 1000);

        } catch (error) {

            message.textContent = error.message;
            message.style.color = "red";
        }
    });
}


// ==================================================
// LOGIN
// ==================================================

const loginForm = document.getElementById("loginForm");

if (loginForm) {

    loginForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        const name = document.getElementById("loginName").value.trim();
        const password = document.getElementById("loginPassword").value;

        const message = document.getElementById("message");

        try {

            const formData = new URLSearchParams();

            formData.append("username", name);
            formData.append("password", password);

            const response = await fetch(`${API_URL}/auth/login`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Login failed");
            }

            localStorage.setItem("access_token", data.access_token);

            message.textContent = "Login successful!";
            message.style.color = "green";

            window.location.href = "tasks.html";

        } catch (error) {

            message.textContent = error.message;
            message.style.color = "red";
        }
    });
}


// ==================================================
// FORGOT PASSWORD
// ==================================================

const forgotPasswordForm = document.getElementById("forgotPasswordForm");

if (forgotPasswordForm) {

    forgotPasswordForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        const email = document.getElementById("forgotEmail").value.trim();
        const message = document.getElementById("message");

        try {

            const response = await fetch(`${API_URL}/auth/forgot-password`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    email: email
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Something went wrong");
            }

            message.textContent = data.message;
            message.style.color = "green";

            forgotPasswordForm.reset();

        } catch (error) {

            message.textContent = error.message;
            message.style.color = "red";
        }
    });
}


// ==================================================
// RESET PASSWORD
// ==================================================

const resetPasswordForm = document.getElementById("resetPasswordForm");

if (resetPasswordForm) {

    resetPasswordForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        const newPassword = document.getElementById("newPassword").value;
        const confirmPassword = document.getElementById("confirmPassword").value;

        const message = document.getElementById("message");

        if (newPassword !== confirmPassword) {

            message.textContent = "Passwords do not match.";
            message.style.color = "red";

            return;
        }

        const params = new URLSearchParams(window.location.search);
        const token = params.get("token");

        if (!token) {

            message.textContent = "Invalid password reset link.";
            message.style.color = "red";

            return;
        }

        try {

            const response = await fetch(`${API_URL}/auth/reset-password`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    token: token,
                    new_password: newPassword
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Password reset failed");
            }

            message.textContent = data.message;
            message.style.color = "green";

            resetPasswordForm.reset();

        } catch (error) {

            message.textContent = error.message;
            message.style.color = "red";
        }
    });
}
