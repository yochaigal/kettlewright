import utils from "./utils.js";

const categorySelect = document.getElementById("category-select");
const subcategorySelect = document.getElementById("subcategory-select");
const rollButton = document.getElementById("roll-button");

const categories = {
  Monsters: {
    "Random Monster": data["Random Monster"],
    "Custom Monster": data["Custom Monster"],
    "Reaction Roll": data["Reaction Roll"],
  },
  Events: {
    "Dungeon Events": data["Dungeon Events"],
    "Wilderness Events": data["Wilderness Events"],
  },
  Weather: data.Weather.Types,
  // Names: data.Names.NameFormulas,
  Worldbuilding: {
    Dungeon: data.Dungeon,
    Forest: data.Forest,
    Realm: data.Realm,
    Faction: data.Realm,
    NPC: data.NPCGenerator,
  },
  Items: {
    Relics: data.Relics,
    Spellbooks: data.Spellbooks,
  },
};

// Setup Selects and Buttons
const addOptionsToSelect = (data, element) => {
  element.innerHTML = '<option value="" selected disabled>Choose...</option>';
  for (let key in data) {
    let option = document.createElement("option");
    option.value = key;
    option.text = key;
    element.add(option);
  }
};

addOptionsToSelect(categories, categorySelect);

categorySelect.addEventListener("change", () => {
  const selectedCategory = categories[categorySelect.value];
  addOptionsToSelect(selectedCategory, subcategorySelect);
});

rollButton.addEventListener("click", () => {
  const category = categorySelect.value;
  const subcategory = subcategorySelect.value;

  switch (category) {
    case "Monsters":
      rollMonsters(categories.Monsters, subcategory);
      break;
    case "Events":
      rollEvents(categories.Events, subcategory);
      break;
    case "Weather":
      rollWeather(data.Weather, subcategory);
      break;
    case "Realm":
      rollRealm(categories.Realm, subcategory);
      break;
    case "Worldbuilding":
      rollWorldbuilding(categories["Worldbuilding"], subcategory);
      break;
    case "Items":
      rollRelics(categories.Items, subcategory);
      break;
  }
});

const clearResults = () => {
  const resultDisplay = document.getElementById("tools-result-display");
  resultDisplay.innerHTML = "";
};

const clearButton = document.getElementById("clear-button");
clearButton.addEventListener("click", clearResults);

const copyButton = document.getElementById("tools-copy-text-button");
copyButton.addEventListener("click", () => {
  const resultDisplay = document.getElementById("tools-result-display");
  const text = resultDisplay.innerText;
  navigator.clipboard.writeText(text);
  alert("Results copied to clipboard");
});

const roll = (sides) => {
  return Math.floor(Math.random() * sides);
};

// Output formatting functions
const formatObjectToString = (obj) => {
  return Object.entries(obj)
    .filter(([key, value]) => !(Array.isArray(value) && value.length === 0))
    .map(([key, value]) => {
      let formattedValue = Array.isArray(value) ? value.join(", ") : value;
      return `<b>${key}:</b> ${formattedValue}`;
    })
    .join("<br>");
};

const formatNumberedArrayToString = (arr) => {
  return arr.map((item, index) => `${index + 1}. ${item}`).join("<br>");
};

const convertName = (nameFormula, replacements) => {
  let name = nameFormula;

  replacements.forEach(({ type, word }) => {
    const regex = new RegExp(`\\[${type}\\]`, "g");
    name = name.replace(regex, word);
  });

  // Remove optional parts if their content wasn't replaced
  name = name.replace(/\([^()]*\[.*?\][^()]*\)/g, "");
  // Remove any remaining brackets
  name = name.replace(/[\[\]()]/g, "");
  // Trim any extra spaces
  return name.trim().replace(/\s+/g, " ");
};

const displayResult = (result) => {
  const resultDisplay = document.getElementById("tools-result-display");
  const line = "------------------------------------<br>";
  if (resultDisplay.innerHTML === "no events yet...") {
    resultDisplay.innerHTML = result + "<br><br>" + line;
  } else {
    resultDisplay.innerHTML = `<p>${result}</p>` + line + resultDisplay.innerHTML;
  }
  resultDisplay.scrollTop = 0;
};

// Roll functions
const rollMonsters = (data, subcategory) => {
  const Monsters = data[subcategory];
  if (subcategory === "Random Monster") {
    const result = Monsters[roll(Monsters.length)];
    const formattedTraits = result.Traits.map((trait) => trait.replace(/Critical Damage/g, "<b>Critical Damage</b>"));
    const textResult = `<b><u>${result.Name}</u></b><br><br>HP: ${result.HP}, ${
      result.Armor ? `Armor: ${result.Armor},` : ""
    } STR: ${result.STR}, DEX: ${result.DEX}, WIL: ${result.WIL}${
      result.Attack ? `, ${result.Attack}<br><br>` : ""
    }• ${formattedTraits.join("<br>• ")}`;
    displayResult(textResult);
  } else if (subcategory === "Custom Monster") {
    const physique = Monsters.MonsterAppearance.Physique[roll(Monsters.MonsterAppearance.Physique.length)];
    const feature = Monsters.MonsterAppearance.Feature[roll(Monsters.MonsterAppearance.Feature.length)];
    const quirks = Monsters.MonsterTraits.Quirks[roll(Monsters.MonsterTraits.Quirks.length)];
    const weakness = Monsters.MonsterTraits.Weakness[roll(Monsters.MonsterTraits.Weakness.length)];
    const attack = Monsters.MonsterAttacks.Type[roll(Monsters.MonsterAttacks.Type.length)];
    const criticalDamage = Monsters.MonsterAttacks.CriticalDamage[roll(Monsters.MonsterAttacks.CriticalDamage.length)];
    const ability = Monsters.MonsterAbilities.Ability[roll(Monsters.MonsterAbilities.Ability.length)];
    const target = Monsters.MonsterAbilities.Target[roll(Monsters.MonsterAbilities.Target.length)];
    const textResult = `<b><u>Custom Monster</u></b><br><br><b>Physique:</b> ${physique}<br><b>Feature:</b> ${feature}<br><b>Quirks:</b> ${quirks}<br><b>Weakness:</b> ${weakness}<br><b>Attack:</b> ${attack}<br><b>Critical Damage:</b> ${criticalDamage}<br><b>Ability:</b> ${ability}<br><b>Target:</b> ${target}`;
    displayResult(textResult);
  } else if (subcategory === "Reaction Roll") {
    let roll = utils.roll(2, 6);
    const result = Monsters[roll - 2]; //2-12 -> 0-10
    const textResult = `<b><u>Reaction Roll</u></b><br><br><b>${result}</b>`;
    displayResult(textResult);
  }
};

const rollEvents = (data, subcategory) => {
  const events = data[subcategory];
  if (subcategory === "Dungeon Events") {
    const result = events[roll(events.length)];
    const textResult = `<b><u>Dungeon Event</u></b><br><br>${result.description}`;
    displayResult(textResult);
  } else if (subcategory === "Wilderness Events") {
    const result = events[roll(events.length)];
    const textResult = `<b><u>Wilderness Event</u></b><br><br>${result.description}`;
    displayResult(textResult);
  }
};

const rollWeather = (data, subcategory) => {
  console.log(data);
  const weather = data.Types[subcategory];
  const type = weather[roll(weather.length)];
  console.log(type);
  const difficulty = data.Difficulty[type];
  const textResult = `<b><u>Weather</u></b><br><br><b>Season:</b> ${subcategory}<br><b>Type:</b> ${type}<br><b>Effect:</b> ${difficulty.Effect} <br><b>Examples:</b> ${difficulty.Examples}`;
  displayResult(textResult);
};

const rollRelics = (data, subcategory) => {
  const items = data[subcategory];
  const result = items[roll(items.length)];
  let name = result.name;
  let weight = "";
  if (result.tags.includes("petty")) {
    weight = " (petty)";
  } else if (result.tags.includes("bulky")) {
    weight = " (bulky)";
  }

  let tags = [];

  // Filter and add regular tags
  const regularTags = result.tags.filter(
    (tag) => !["bulky", "petty", "uses", "charges", "use", "charge"].includes(tag)
  );
  if (regularTags.length > 0) {
    tags.push(regularTags.join(", "));
  }

  // Add uses if present
  if (result.uses) {
    tags.push(`${result.uses} use${result.uses > 1 ? "s" : ""}`);
  }

  // Add charges if present
  if (result.max_charges) {
    tags.push(`${result.max_charges} charge${result.max_charges > 1 ? "s" : ""}`);
  }

  // Join all tags with proper comma placement
  const tagsString = tags.length > 0 ? `, ${tags.join(", ")}` : "";

  // Format description, splitting on "Recharge" and making only "Recharge" bold
  let descriptionText = "";
  if (result.description) {
    const parts = result.description.split(/(Recharge)/);
    descriptionText = parts
      .map((part, index) => {
        if (part === "Recharge") {
          return `<br>• <b>Recharge</b>`;
        } else if (index === 0) {
          return `• ${part}`;
        } else if (index % 2 === 0) {
          // Even indexes after 0 are text following "Recharge"
          return part;
        }
        return part; // This line should never be reached, but it's here for completeness
      })
      .join("");
  }

  // Add personality if it exists
  if (result.personality) {
    descriptionText += descriptionText ? "<br>" : ""; // Add a line break if there's already a description
    descriptionText += `• Personality: ${result.personality}`;
  }

  const textResult = `<b><u>${name}</u></b>${tagsString}<i>${weight}</i><br><br>${descriptionText}`;

  displayResult(textResult);
};

const rollWorldbuilding = (data, subcategory) => {
  const setting = data[subcategory];
  let result = {};

  const rollRealmFaction = () => {
    // Factions
    const advantageNumber =
      setting.Theme.Factions.FactionAdvantages.NumberOfAdvantages[
        roll(setting.Theme.Factions.FactionAdvantages.NumberOfAdvantages.length)
      ];
    let advantages = [];
    for (let i = 0; i < advantageNumber; i++) {
      advantages.push(
        setting.Theme.Factions.FactionAdvantages.Advantage[
          roll(setting.Theme.Factions.FactionAdvantages.Advantage.length)
        ]
      );
    }
    const nameFormula =
      setting.Theme.Factions.FactionNames.NameFormulas.Faction[
        roll(setting.Theme.Factions.FactionNames.NameFormulas.Faction.length)
      ];
    const adjective =
      setting.Theme.Factions.FactionNames.Adjectives[roll(setting.Theme.Factions.FactionNames.Adjectives.length)];
    const noun = setting.Theme.Factions.FactionNames.Nouns[roll(setting.Theme.Factions.FactionNames.Nouns.length)];
    const type =
      setting.Theme.Factions.FactionNames.FactionTypes[roll(setting.Theme.Factions.FactionNames.FactionTypes.length)];

    const name = convertName(nameFormula, [
      { type: "Noun", word: noun },
      { type: "Adjective", word: adjective },
      { type: "Group", word: type },
    ]);

    let factions = {};
    factions = {
      Name: name,
      Type: setting.Theme.Factions.FactionTypes.Type[roll(setting.Theme.Factions.FactionTypes.Type.length)],
      Agent: setting.Theme.Factions.FactionTypes.Agent[roll(setting.Theme.Factions.FactionTypes.Agent.length)],
      "Trait 1": setting.Theme.Factions.FactionTraits.Trait1[roll(setting.Theme.Factions.FactionTraits.Trait1.length)],
      "Trait 2": setting.Theme.Factions.FactionTraits.Trait2[roll(setting.Theme.Factions.FactionTraits.Trait2.length)],
      Advantages: advantages.join(", "),
      Agenda: setting.Theme.Factions.FactionAgendas.Agenda[roll(setting.Theme.Factions.FactionAgendas.Agenda.length)],
      Obstacle:
        setting.Theme.Factions.FactionAgendas.Obstacle[roll(setting.Theme.Factions.FactionAgendas.Obstacle.length)],
    };

    return factions;
  };

  if (subcategory === "Dungeon") {
    result.Purpose = {
      "Original Use": setting.Properties.Purpose.OriginalUse[roll(setting.Properties.Purpose.OriginalUse.length)],
      "Built By": setting.Properties.Purpose.BuiltBy[roll(setting.Properties.Purpose.BuiltBy.length)],
    };
    result.Construction = {
      Entrance: setting.Properties.Construction.Entrance[roll(setting.Properties.Construction.Entrance.length)],
      Composition:
        setting.Properties.Construction.Composition[roll(setting.Properties.Construction.Composition.length)],
    };
    result.Ruination = {
      Condition: setting.Properties.Ruination.Condition[roll(setting.Properties.Ruination.Condition.length)],
      Cause: setting.Properties.Ruination.Cause[roll(setting.Properties.Ruination.Cause.length)],
    };
    result.Factions = {
      ["Virtue"]: setting.Properties.Factions.Traits.Virtue[roll(setting.Properties.Factions.Traits.Virtue.length)],
      ["Vice"]: setting.Properties.Factions.Traits.Vice[roll(setting.Properties.Factions.Traits.Vice.length)],
      ["Goal"]: setting.Properties.Factions.Agendas.Goal[roll(setting.Properties.Factions.Agendas.Goal.length)],
      ["Obstacle"]:
        setting.Properties.Factions.Agendas.Obstacle[roll(setting.Properties.Factions.Agendas.Obstacle.length)],
    };

    // POIs
    const min = setting.POIs.Repeat.Min;
    const max = setting.POIs.Repeat.Max;
    const repeat = Math.floor(Math.random() * (max - min + 1)) + min;
    result.POIs = [];
    let groups = [];
    for (let group in setting.POIs.Monster.Group) {
      groups.push(group);
    }
    for (let i = 0; i < repeat; i++) {
      const poi = setting.POIs.DungeonDieDropTable[roll(setting.POIs.DungeonDieDropTable.length)];
      if (poi === "Monster") {
        const monsterGroup = groups[roll(groups.length)];
        const monsterType =
          setting.POIs.Monster.Group[monsterGroup][roll(setting.POIs.Monster.Group[monsterGroup].length)];
        const activity = setting.POIs.Monster.Activity[roll(setting.POIs.Monster.Activity.length)];
        result.POIs.push(`Monster: ${activity}, ${monsterType}`);
      }
      if (poi === "Lore") {
        const roomType = setting.POIs.Lore.RoomType[roll(setting.POIs.Lore.RoomType.length)];
        const clue = setting.POIs.Lore.Clue[roll(setting.POIs.Lore.Clue.length)];
        result.POIs.push(`Lore: ${roomType}, ${clue}`);
      }
      if (poi === "Special") {
        const special = setting.POIs.Special.Special[roll(setting.POIs.Special.Special.length)];
        const feature = setting.POIs.Special.Feature[roll(setting.POIs.Special.Feature.length)];
        result.POIs.push(`Special: ${special}, ${feature}`);
      }
      if (poi === "Trap") {
        const trap = setting.POIs.Trap.Trap[roll(setting.POIs.Trap.Trap.length)];
        const trigger = setting.POIs.Trap.Trigger[roll(setting.POIs.Trap.Trigger.length)];
        result.POIs.push(`Trap: ${trap}, ${trigger}`);
      }
    }

    const textResult = `<b><u>Dungeon</u></b><br><br>${formatObjectToString(result.Purpose)}<br>${formatObjectToString(
      result.Construction
    )}<br>${formatObjectToString(result.Ruination)}<br><br><b><u>Factions</u></b><br>${formatObjectToString(
      result.Factions
    )}<br><br><b><u>Rooms:</u></b><br>${formatNumberedArrayToString(result.POIs)}`;
    displayResult(textResult);
  } else if (subcategory === "Forest") {
    result.Traits = {
      Traits:
        setting.Properties.Traits.Description1[roll(setting.Properties.Traits.Description1.length)] +
        ", " +
        setting.Properties.Traits.Description2[roll(setting.Properties.Traits.Description2.length)].toLowerCase(),
    };
    result.Virtue = {
      Virtue: setting.Properties.SpiritTraits.Virtue[roll(setting.Properties.SpiritTraits.Virtue.length)],
    };
    result.Vice = { Vice: setting.Properties.SpiritTraits.Vice[roll(setting.Properties.SpiritTraits.Vice.length)] };
    result.Goal = { Goal: setting.Properties.ForestAgenda.Goal[roll(setting.Properties.ForestAgenda.Goal.length)] };
    result.Obstacle = {
      Obstacle: setting.Properties.ForestAgenda.Obstacle[roll(setting.Properties.ForestAgenda.Obstacle.length)],
    };

    const poeMin = setting.ForestPOIs.Repeat.Min;
    const poeMax = setting.ForestPOIs.Repeat.Max;
    const poiRepeat = Math.floor(Math.random() * (poeMax - poeMin + 1)) + poeMin;
    result.POIs = [];
    for (let i = 0; i < poiRepeat; i++) {
      const poi = setting.ForestPOIs.ForestDieDropTable[roll(setting.ForestPOIs.ForestDieDropTable.length)];
      if (poi === "Monster") {
        const monsterType = setting.ForestPOIs.Monster.Monster[roll(setting.ForestPOIs.Monster.Monster.length)];
        const activity = setting.ForestPOIs.Monster.Activity[roll(setting.ForestPOIs.Monster.Activity.length)];
        result.POIs.push(`Monster: ${activity}, ${monsterType}`);
      }
      if (poi === "Ruins") {
        const ruin = setting.ForestPOIs.Ruins.Ruin[roll(setting.ForestPOIs.Ruins.Ruin.length)];
        const feature = setting.ForestPOIs.Ruins.Feature[roll(setting.ForestPOIs.Ruins.Feature.length)];
        result.POIs.push(`Ruins: ${ruin}, ${feature}`);
      }
      if (poi === "Shelter") {
        const shelter = setting.ForestPOIs.Shelter.Shelter[roll(setting.ForestPOIs.Shelter.Shelter.length)];
        const feature = setting.ForestPOIs.Shelter.Feature[roll(setting.ForestPOIs.Shelter.Feature.length)];
        result.POIs.push(`Shelter: ${shelter}, ${feature}`);
      }
      if (poi === "Hazard") {
        const hazard = setting.ForestPOIs.Hazard.Hazard[roll(setting.ForestPOIs.Hazard.Hazard.length)];
        const feature = setting.ForestPOIs.Hazard.Feature[roll(setting.ForestPOIs.Hazard.Feature.length)];
        result.POIs.push(`Hazard: ${hazard}, ${feature}`);
      }
    }
    const name =
      setting.ForestNames.Adjectives[roll(setting.ForestNames.Adjectives.length)] +
      " " +
      setting.ForestNames.Nouns[roll(setting.ForestNames.Nouns.length)];

    const trailsRepeat = poiRepeat;
    result.trails = [];

    for (let i = 0; i < trailsRepeat; i++) {
      const path = setting.Trails.Path[roll(setting.Trails.Path.length)];
      const type = setting.Trails.Type[roll(setting.Trails.Type.length)];
      const marker = setting.Trails.Marker[roll(setting.Trails.Marker.length)];
      result.trails.push(`${path}, ${type}, ${marker}`);
    }

    const textResult = `<b><u>Forest</u></b><br><br>
    <b>${name}</b><br><br>
    ${formatObjectToString(result.Traits)}<br>${formatObjectToString(result.Virtue)}<br>${formatObjectToString(
      result.Vice
    )}
    <br>${formatObjectToString(result.Goal)}<br>${formatObjectToString(result.Obstacle)}
    <br><br><b><u>Points of Interest</u></b><br>${formatNumberedArrayToString(result.POIs)}
    <br><br><b><u>Trails</u></b><br>${formatNumberedArrayToString(result.trails)}
    `;
    displayResult(textResult);
  } else if (subcategory === "Realm") {
    result.Culture = {
      Character: setting.Theme.People.Culture.Character[roll(setting.Theme.People.Culture.Character.length)],
      Ambition: setting.Theme.People.Culture.Ambition[roll(setting.Theme.People.Culture.Ambition.length)],
    };
    result.Resources = {
      Abundance: setting.Theme.People.Resources.Abundance[roll(setting.Theme.People.Resources.Abundance.length)],
      Scarcity: setting.Theme.People.Resources.Scarcity[roll(setting.Theme.People.Resources.Scarcity.length)],
    };

    // Factions
    result.Factions = rollRealmFaction();

    // set terrain count to a random number 1-6
    const terrainCount = Math.floor(Math.random() * 6) + 1;
    result.Terrain = [];
    for (let i = 0; i < terrainCount; i++) {
      const difficulty = setting.Topography.Difficulty[roll(setting.Topography.Difficulty.length)];
      const terrain = `${
        setting.Topography.Terrain[difficulty].Terrain[roll(setting.Topography.Terrain[difficulty].Terrain.length)]
      }. Difficulty: ${difficulty}. Landmark: ${
        setting.Topography.Terrain[difficulty].Landmark[roll(setting.Topography.Terrain[difficulty].Landmark.length)]
      }.
     `;
      result.Terrain.push(terrain);
    }

    result.Weather = {
      Spring: setting.Weather.SeasonalWeather.Spring[roll(setting.Weather.SeasonalWeather.Spring.length)],
      Summer: setting.Weather.SeasonalWeather.Summer[roll(setting.Weather.SeasonalWeather.Summer.length)],
      Fall: setting.Weather.SeasonalWeather.Fall[roll(setting.Weather.SeasonalWeather.Fall.length)],
      Winter: setting.Weather.SeasonalWeather.Winter[roll(setting.Weather.SeasonalWeather.Winter.length)],
      ["Unusual Weather (optional)"]: setting.Weather.UnusualWeather[roll(setting.Weather.UnusualWeather.length)],
    };

    const poiCount = Math.floor(Math.random() * (8 - 3 + 1)) + 3;
    result.POIs = [];
    for (let i = 0; i < poiCount; i++) {
      let poi = "";

      const poiNameForumla = setting.Names.NameFormulas.POI[roll(setting.Names.NameFormulas.POI.length)];
      const adjective = setting.Names.Adjectives[roll(setting.Names.Adjectives.length)];
      const noun = setting.Names.Nouns[roll(setting.Names.Nouns.length)];
      const type = setting.PointsOfInterest.POI[roll(setting.PointsOfInterest.POI.length)];
      const poiName = convertName(poiNameForumla, [
        { type: "Noun", word: noun },
        { type: "Adjective", word: adjective },
        { type: "POI", word: type },
      ]);

      if (type === "Waypoint") {
        poi = `${poiName}: ${
          setting.PointsOfInterest.Waypoints.Waypoint[roll(setting.PointsOfInterest.Waypoints.Waypoint.length)]
        }, 
        ${setting.PointsOfInterest.Waypoints.Feature[roll(setting.PointsOfInterest.Waypoints.Feature.length)]}`;
      } else if (type === "Settlement") {
        poi = `${poiName}: ${
          setting.PointsOfInterest.Settlements.Settlement[roll(setting.PointsOfInterest.Settlements.Settlement.length)]
        }, ${setting.PointsOfInterest.Settlements.Feature[roll(setting.PointsOfInterest.Settlements.Feature.length)]}`;
      } else if (type === "Curiosity") {
        poi = `${poiName}: ${
          setting.PointsOfInterest.Curiosities.Curiosity[roll(setting.PointsOfInterest.Curiosities.Curiosity.length)]
        }, ${setting.PointsOfInterest.Curiosities.Feature[roll(setting.PointsOfInterest.Curiosities.Feature.length)]}`;
      } else if (type === "Lair") {
        poi = `${poiName}: ${setting.PointsOfInterest.Lairs.Lair[roll(setting.PointsOfInterest.Lairs.Lair.length)]}, ${
          setting.PointsOfInterest.Lairs.Feature[roll(setting.PointsOfInterest.Lairs.Feature.length)]
        }`;
      } else if (type === "Dungeon") {
        poi = `${poiName}: ${
          setting.PointsOfInterest.Dungeons.Type[roll(setting.PointsOfInterest.Dungeons.Type.length)]
        }, ${setting.PointsOfInterest.Dungeons.Feature[roll(setting.PointsOfInterest.Dungeons.Feature.length)]}`;
      }
      result.POIs.push(poi);
    }

    const realmNameFormula = setting.Names.NameFormulas.Realm[roll(setting.Names.NameFormulas.Realm.length)];
    const realmAdjective = setting.Names.Adjectives[roll(setting.Names.Adjectives.length)];
    const realmNoun = setting.Names.Nouns[roll(setting.Names.Nouns.length)];
    const realmRulerType = setting.Names.RulerTypes[roll(setting.Names.RulerTypes.length)];
    const realmName = convertName(realmNameFormula, [
      { type: "Noun", word: realmNoun },
      { type: "Adjective", word: realmAdjective },
      { type: "Rulers", word: realmRulerType },
    ]);

    const textResult = `<b><u>Realm</u></b><br><br>
    <b>${realmName}</b><br><br>
    <b><u>People</u></b><br>${formatObjectToString(result.Culture)}<br>${formatObjectToString(
      result.Resources
    )}<br><br><b><u>Factions</u></b><br>${formatObjectToString(
      result.Factions
    )}<br><br><b><u>Terrain</u></b><br>${formatNumberedArrayToString(
      result.Terrain
    )}<br><br><b><u>Weather</u></b><br>${formatObjectToString(
      result.Weather
    )}<br><br><b><u>Points of Interest</u></b><br>${formatNumberedArrayToString(result.POIs)}`;
    displayResult(textResult);
  } else if (subcategory === "Faction") {
    result = rollRealmFaction();
    const textResult = `<b><u>Faction</u></b><br><br>${formatObjectToString(result)}`;
    displayResult(textResult);
  } else if (subcategory === "NPC") {
    const name = setting.NPCNames.Names[roll(setting.NPCNames.Names.length)];
    const background = setting.NPCBackgrounds[roll(setting.NPCBackgrounds.length)];
    const virtue = setting.NPCTraits.Virtues[roll(setting.NPCTraits.Virtues.length)];
    const vice = setting.NPCTraits.Vices[roll(setting.NPCTraits.Vices.length)];
    const quirk = setting.NPCQuirks[roll(setting.NPCQuirks.length)];
    const goal = setting.NPCGoals.Goals[roll(setting.NPCGoals.Goals.length)];

    const textResult = `<b><u>NPC</u></b><br><br><b>Name:</b> ${name}<br><b>Background:</b> ${background}<br><b>Virtue:</b> ${virtue}<br><b>Vice:</b> ${vice}<br><b>Quirk:</b> ${quirk}<br><b>Goal:</b> ${goal}`;
    displayResult(textResult);
  }
};
