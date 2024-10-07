const toggleDarkMode = () => {
  document.body.classList.toggle("dark-mode");
  const isDarkMode = document.body.classList.contains("dark-mode");
  localStorage.setItem("darkMode", isDarkMode);
};

// Function to apply dark mode based on local storage
const applyDarkMode = () => {
  // if current url ends in /print/ remove dark mode
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
  // Get all "navbar-burger" elements
  // const $navbarBurgers = Array.prototype.slice.call(document.querySelectorAll(".navbar-burger"), 0);

  // // Add a click event on each of them
  // $navbarBurgers.forEach((el) => {
  //   el.addEventListener("click", () => {
  //     // Get the target from the "data-target" attribute
  //     const target = el.dataset.target;
  //     const $target = document.getElementById(target);

  //     // Toggle the "is-active" class on both the "navbar-burger" and the "navbar-menu"
  //     el.classList.toggle("is-active");
  //     $target.classList.toggle("is-active");
  //   });
  // });

  console.log("page loaded");

  // Apply dark mode on page load
  applyDarkMode();

  // Toggle dark mode when button is clicked
  document.getElementById("dark-mode-toggle").addEventListener("click", toggleDarkMode);
});
