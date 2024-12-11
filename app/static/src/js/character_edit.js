htmx.on("charedit_loaded", function(evt){ 
  document.querySelectorAll(".textarea").forEach((element) => {
    element.style.height = "auto";
    element.style.height = element.scrollHeight + 4 + "px";
    });
});

  