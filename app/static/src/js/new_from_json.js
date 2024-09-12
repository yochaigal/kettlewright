let data;

document.getElementById("jsonFile").addEventListener("change", function (event) {
  var file = event.target.files[0];
  var reader = new FileReader();
  reader.onload = function (e) {
    data = JSON.parse(e.target.result);
  };
  reader.readAsText(file);
});

document.getElementById("character-form").addEventListener("submit", function (event) {
  document.getElementById("strength").value = data.strength;
  document.getElementById("strength_max").value = data.strength_max;
  document.getElementById("dexterity").value = data.dexterity;
  document.getElementById("dexterity_max").value = data.dexterity_max;
  document.getElementById("willpower").value = data.willpower;
  document.getElementById("willpower_max").value = data.willpower_max;
  document.getElementById("hp").value = data.hp;
  document.getElementById("hp_max").value = data.hp_max;
  document.getElementById("gold").value = data.gold;
  document.getElementById("description").value = data.description;
  document.getElementById("bonds").value = data.bonds;
  document.getElementById("omens").value = data.omens;
  document.getElementById("scars").value = data.scars;
  document.getElementById("notes").value = data.notes;
  document.getElementById("custom_image").value = data.custom_image;
  document.getElementById("image_url").value = data.image_url;
  document.getElementById("name").value = data.name;
  document.getElementById("background").value = data.background;
  document.getElementById("items").value = JSON.stringify(data.items);
  document.getElementById("containers").value = JSON.stringify(data.containers);
});
