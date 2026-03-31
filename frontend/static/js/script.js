// const API_BASE = "http://localhost:5000";
const API_BASE = "https://hisab-kitab-hezo.onrender.com";

function getUser() {
    return {
        name: localStorage.getItem("name"),
        username: localStorage.getItem("username")
    };
}

function requireLogin() {
    const username = localStorage.getItem("username");
    if (!username) {
        window.location.href = "login.html";
    }
}

function logout() {
    localStorage.removeItem("name");
    localStorage.removeItem("username");
    window.location.href = "login.html";
}

function setHeader() {
    const user = getUser();
    const headerUser = document.getElementById("headerUser");
    const authButtons = document.getElementById("authButtons");

    if (headerUser && authButtons) {
        if (user.username) {
            headerUser.textContent = `👤 ${user.name}`;
            authButtons.innerHTML = `
                <a href="dashboard.html" class="btn secondary-btn" style="padding:8px 16px;font-size:14px;">Dashboard</a>
                <button onclick="logout()" class="btn danger-btn" style="padding:8px 16px;font-size:14px;">Logout</button>
            `;
        } else {
            headerUser.textContent = "";
            authButtons.innerHTML = `
                <a href="login.html" class="btn outline-btn" style="padding:8px 18px;font-size:14px;">Login</a>
                <a href="signup.html" class="btn" style="padding:8px 18px;font-size:14px;">Signup</a>
            `;
        }
    }
}

function generateMemberFields() {
    const memberCountInput = document.getElementById("member_count");
    const memberFieldsDiv = document.getElementById("memberFields");

    memberFieldsDiv.innerHTML = "";

    const count = parseInt(memberCountInput.value);
    if (isNaN(count) || count < 1) {
        memberFieldsDiv.innerHTML = "<p class='error-message'>Please enter a valid number of people.</p>";
        return;
    }

    const currentUsername = localStorage.getItem("username") || "";

    const firstInput = document.createElement("input");
    firstInput.type = "text";
    firstInput.name = "member_1";
    firstInput.value = currentUsername;
    firstInput.readOnly = true;
    firstInput.className = "member-input";
    memberFieldsDiv.appendChild(firstInput);

    for (let i = 2; i <= count; i++) {
        const input = document.createElement("input");
        input.type = "text";
        input.name = `member_${i}`;
        input.placeholder = `Username of member ${i}`;
        input.required = true;
        input.className = "member-input";
        memberFieldsDiv.appendChild(input);
    }
}

function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

document.addEventListener("DOMContentLoaded", setHeader);