const API_URL = "http://127.0.0.1:8000";


// ---------------- SIGNUP ----------------

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

            message.textContent = "Account created successfully!";
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


// ---------------- LOGIN ----------------

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