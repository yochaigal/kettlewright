htmx.on("charedit-loaded", function(evt){ 
  document.querySelectorAll(".textarea").forEach((element) => {
    element.style.height = "auto";
    element.style.height = element.scrollHeight + 4 + "px";
    });
});

htmx.on("refresh-stats", function(evt){ 
  if (evt.detail.gold)
    document.getElementById('gold-input').value = evt.detail.gold;
});

htmx.on("omen-roll", function(evt){ 
  const element = document.getElementById('omens-field');
  element.style.height = "auto";
  element.style.height = element.scrollHeight + 4 + "px";
});

htmx.on("scar-roll", function(evt){ 
  const element = document.getElementById('scars-field');
  element.style.height = "auto";
  element.style.height = element.scrollHeight + 4 + "px";
});
