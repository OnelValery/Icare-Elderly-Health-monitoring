document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("registerForm")?.addEventListener("submit", function(event) {
        event.preventDefault();
        alert("Registration submitted!");
    });

    document.getElementById("loginForm")?.addEventListener("submit", function(event) {
        event.preventDefault();
        alert("Login submitted!");
    });
});
