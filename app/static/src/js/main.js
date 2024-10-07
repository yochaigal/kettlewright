const toggleDarkMode = () => {
  document.body.classList.toggle("dark-mode");
  const isDarkMode = document.body.classList.contains("dark-mode");
  localStorage.setItem("darkMode", isDarkMode);
};

const applyDarkMode = () => {
  if (window.location.href.endsWith("/print/")) {
    document.body.classList.remove("dark-mode");
    return;
  }

  if (localStorage.getItem("darkMode") === "true") {
    document.body.classList.add("dark-mode");
  } else {
    document.body.classList.remove("dark-mode");
  }
};

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("nav-mobile-button").addEventListener("click", () => {
    document.getElementById("nav-menu").classList.toggle("is-active");
  });

  // Dark mode is enabled on page load directly in the HTML template, in order to prevent a flash of light mode

  document.getElementById("dark-mode-toggle").addEventListener("click", toggleDarkMode);
});
