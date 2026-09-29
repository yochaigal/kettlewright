// Shared structured generators. Table data is supplied by Tools or the map editor.
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

export function generateWorldbuilding(data, subcategory, random = Math.random) {
  const roll = sides => Math.floor(random() * sides);
  const setting = data[subcategory];
  let result = {};

  const rollRealmFaction = (realmSetting) => {
    // Factions
    const advantageNumber =
      realmSetting.Theme.Factions.FactionAdvantages.NumberOfAdvantages[
        roll(realmSetting.Theme.Factions.FactionAdvantages.NumberOfAdvantages.length)
      ];
    let advantages = [];
    for (let i = 0; i < advantageNumber; i++) {
      advantages.push(
        realmSetting.Theme.Factions.FactionAdvantages.Advantage[
          roll(realmSetting.Theme.Factions.FactionAdvantages.Advantage.length)
        ]
      );
    }
    const nameFormula =
      realmSetting.Theme.Factions.FactionNames.NameFormulas.Faction[
        roll(realmSetting.Theme.Factions.FactionNames.NameFormulas.Faction.length)
      ];
    const adjective =
      realmSetting.Theme.Factions.FactionNames.Adjectives[
        roll(realmSetting.Theme.Factions.FactionNames.Adjectives.length)
      ];
    const noun =
      realmSetting.Theme.Factions.FactionNames.Nouns[
        roll(realmSetting.Theme.Factions.FactionNames.Nouns.length)
      ];
    const type =
      realmSetting.Theme.Factions.FactionNames.FactionTypes[
        roll(realmSetting.Theme.Factions.FactionNames.FactionTypes.length)
      ];

    const name = convertName(nameFormula, [
      { type: "Noun", word: noun },
      { type: "Adjective", word: adjective },
      { type: "Group", word: type },
    ]);

    let factions = {};
    factions = {
      Name: name,
      Type: realmSetting.Theme.Factions.FactionTypes.Type[
        roll(realmSetting.Theme.Factions.FactionTypes.Type.length)
      ],
      Agent:
        realmSetting.Theme.Factions.FactionTypes.Agent[
          roll(realmSetting.Theme.Factions.FactionTypes.Agent.length)
        ],
      "Trait 1":
        realmSetting.Theme.Factions.FactionTraits.Trait1[
          roll(realmSetting.Theme.Factions.FactionTraits.Trait1.length)
        ],
      "Trait 2":
        realmSetting.Theme.Factions.FactionTraits.Trait2[
          roll(realmSetting.Theme.Factions.FactionTraits.Trait2.length)
        ],
      Advantages: advantages.join(", "),
      Agenda:
        realmSetting.Theme.Factions.FactionAgendas.Agenda[
          roll(realmSetting.Theme.Factions.FactionAgendas.Agenda.length)
        ],
      Obstacle:
        realmSetting.Theme.Factions.FactionAgendas.Obstacle[
          roll(realmSetting.Theme.Factions.FactionAgendas.Obstacle.length)
        ],
    };

    return factions;
  };

  const rollStandaloneFaction = (factionSetting) => {
    const advantageNumber = Math.floor(random() * 3) + 1;

    let advantages = [];
    for (let i = 0; i < advantageNumber; i++) {
      advantages.push(
        factionSetting.FactionAdvantages[
          roll(factionSetting.FactionAdvantages.length)
        ]
      );
    }

    const nameFormula =
      factionSetting.FactionNames.NameFormulas[
        roll(factionSetting.FactionNames.NameFormulas.length)
      ];
    const adjective =
      factionSetting.FactionNames.Adjectives[
        roll(factionSetting.FactionNames.Adjectives.length)
      ];
    const noun =
      factionSetting.FactionNames.Nouns[
        roll(factionSetting.FactionNames.Nouns.length)
      ];
    const group =
      factionSetting.FactionNames.Group[
        roll(factionSetting.FactionNames.Group.length)
      ];

    const name = convertName(nameFormula, [
      { type: "Noun", word: noun },
      { type: "Adjective", word: adjective },
      { type: "Group", word: group },
    ]);

    const agents = [
      "Leader",
      "Champion",
      "Envoy",
      "Spy",
      "Fixer",
      "Priest",
      "Scholar",
      "Assassin",
      "Magician",
      "Quartermaster",
      "Captain",
      "Herald",
    ];

    let factions = {};
    factions = {
      Name: name,
      Type: factionSetting.FactionTypes[roll(factionSetting.FactionTypes.length)],
      Agent: agents[roll(agents.length)],
      "Trait 1":
        factionSetting.FactionTraits.Virtues[
          roll(factionSetting.FactionTraits.Virtues.length)
        ],
      "Trait 2":
        factionSetting.FactionTraits.Vices[
          roll(factionSetting.FactionTraits.Vices.length)
        ],
      Advantages: advantages.join(", "),
      Agenda:
        factionSetting.FactionAgendas.Goals[
          roll(factionSetting.FactionAgendas.Goals.length)
        ],
      Obstacle:
        factionSetting.FactionAgendas.Obstacles[
          roll(factionSetting.FactionAgendas.Obstacles.length)
        ],
    };

    return factions;
  };

  if (subcategory === "Dungeon") {
    result.Purpose = {
      "Original Use":
        setting.Properties.Purpose.OriginalUse[
          roll(setting.Properties.Purpose.OriginalUse.length)
        ],
      "Built By":
        setting.Properties.Purpose.BuiltBy[
          roll(setting.Properties.Purpose.BuiltBy.length)
        ],
    };
    result.Construction = {
      Entrance:
        setting.Properties.Construction.Entrance[
          roll(setting.Properties.Construction.Entrance.length)
        ],
      Composition:
        setting.Properties.Construction.Composition[
          roll(setting.Properties.Construction.Composition.length)
        ],
    };
    result.Ruination = {
      Condition:
        setting.Properties.Ruination.Condition[
          roll(setting.Properties.Ruination.Condition.length)
        ],
      Cause:
        setting.Properties.Ruination.Cause[
          roll(setting.Properties.Ruination.Cause.length)
        ],
    };
    result.Factions = {
      ["Virtue"]:
        setting.Properties.Factions.Traits.Virtue[
          roll(setting.Properties.Factions.Traits.Virtue.length)
        ],
      ["Vice"]:
        setting.Properties.Factions.Traits.Vice[
          roll(setting.Properties.Factions.Traits.Vice.length)
        ],
      ["Goal"]:
        setting.Properties.Factions.Agendas.Goal[
          roll(setting.Properties.Factions.Agendas.Goal.length)
        ],
      ["Obstacle"]:
        setting.Properties.Factions.Agendas.Obstacle[
          roll(setting.Properties.Factions.Agendas.Obstacle.length)
        ],
    };

    // POIs
    const min = setting.POIs.Repeat.Min;
    const max = setting.POIs.Repeat.Max;
    const repeat = Math.floor(random() * (max - min + 1)) + min;
    result.POIs = [];
    let groups = [];
    for (let group in setting.POIs.Monster.Group) {
      groups.push(group);
    }
    for (let i = 0; i < repeat; i++) {
      const poi =
        setting.POIs.DungeonDieDropTable[
          roll(setting.POIs.DungeonDieDropTable.length)
        ];
      if (poi === "Monster") {
        const monsterGroup = groups[roll(groups.length)];
        const monsterType =
          setting.POIs.Monster.Group[monsterGroup][
            roll(setting.POIs.Monster.Group[monsterGroup].length)
          ];
        const activity =
          setting.POIs.Monster.Activity[
            roll(setting.POIs.Monster.Activity.length)
          ];
        result.POIs.push(`Monster: ${activity}, ${monsterType}`);
      }
      if (poi === "Lore") {
        const roomType =
          setting.POIs.Lore.RoomType[roll(setting.POIs.Lore.RoomType.length)];
        const clue =
          setting.POIs.Lore.Clue[roll(setting.POIs.Lore.Clue.length)];
        result.POIs.push(`Lore: ${roomType}, ${clue}`);
      }
      if (poi === "Special") {
        const special =
          setting.POIs.Special.Special[
            roll(setting.POIs.Special.Special.length)
          ];
        const feature =
          setting.POIs.Special.Feature[
            roll(setting.POIs.Special.Feature.length)
          ];
        result.POIs.push(`Special: ${special}, ${feature}`);
      }
      if (poi === "Trap") {
        const trap =
          setting.POIs.Trap.Trap[roll(setting.POIs.Trap.Trap.length)];
        const trigger =
          setting.POIs.Trap.Trigger[roll(setting.POIs.Trap.Trigger.length)];
        result.POIs.push(`Trap: ${trap}, ${trigger}`);
      }
    }

    return {title: 'Dungeon', category: 'location', fields: result, mapKind: 'dungeon'};
  } else if (subcategory === "Forest") {
    result.Traits = {
      Traits:
        setting.Properties.Traits.Description1[
          roll(setting.Properties.Traits.Description1.length)
        ] +
        ", " +
        setting.Properties.Traits.Description2[
          roll(setting.Properties.Traits.Description2.length)
        ].toLowerCase(),
    };
    result.Virtue = {
      Virtue:
        setting.Properties.SpiritTraits.Virtue[
          roll(setting.Properties.SpiritTraits.Virtue.length)
        ],
    };
    result.Vice = {
      Vice: setting.Properties.SpiritTraits.Vice[
        roll(setting.Properties.SpiritTraits.Vice.length)
      ],
    };
    result.Goal = {
      Goal: setting.Properties.ForestAgenda.Goal[
        roll(setting.Properties.ForestAgenda.Goal.length)
      ],
    };
    result.Obstacle = {
      Obstacle:
        setting.Properties.ForestAgenda.Obstacle[
          roll(setting.Properties.ForestAgenda.Obstacle.length)
        ],
    };

    const poeMin = setting.ForestPOIs.Repeat.Min;
    const poeMax = setting.ForestPOIs.Repeat.Max;
    const poiRepeat =
      Math.floor(random() * (poeMax - poeMin + 1)) + poeMin;
    result.POIs = [];
    for (let i = 0; i < poiRepeat; i++) {
      const poi =
        setting.ForestPOIs.ForestDieDropTable[
          roll(setting.ForestPOIs.ForestDieDropTable.length)
        ];
      if (poi === "Monster") {
        const monsterType =
          setting.ForestPOIs.Monster.Monster[
            roll(setting.ForestPOIs.Monster.Monster.length)
          ];
        const activity =
          setting.ForestPOIs.Monster.Activity[
            roll(setting.ForestPOIs.Monster.Activity.length)
          ];
        result.POIs.push(`Monster: ${activity}, ${monsterType}`);
      }
      if (poi === "Ruins") {
        const ruin =
          setting.ForestPOIs.Ruins.Ruin[
            roll(setting.ForestPOIs.Ruins.Ruin.length)
          ];
        const feature =
          setting.ForestPOIs.Ruins.Feature[
            roll(setting.ForestPOIs.Ruins.Feature.length)
          ];
        result.POIs.push(`Ruins: ${ruin}, ${feature}`);
      }
      if (poi === "Shelter") {
        const shelter =
          setting.ForestPOIs.Shelter.Shelter[
            roll(setting.ForestPOIs.Shelter.Shelter.length)
          ];
        const feature =
          setting.ForestPOIs.Shelter.Feature[
            roll(setting.ForestPOIs.Shelter.Feature.length)
          ];
        result.POIs.push(`Shelter: ${shelter}, ${feature}`);
      }
      if (poi === "Hazard") {
        const hazard =
          setting.ForestPOIs.Hazard.Hazard[
            roll(setting.ForestPOIs.Hazard.Hazard.length)
          ];
        const feature =
          setting.ForestPOIs.Hazard.Feature[
            roll(setting.ForestPOIs.Hazard.Feature.length)
          ];
        result.POIs.push(`Hazard: ${hazard}, ${feature}`);
      }
    }
    const name =
      setting.ForestNames.Adjectives[
        roll(setting.ForestNames.Adjectives.length)
      ] +
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

    return {title: name, category: 'location', fields: result, mapKind: 'forest'};
  } else if (subcategory === "Realm") {
    result.Culture = {
      Character:
        setting.Theme.People.Culture.Character[
          roll(setting.Theme.People.Culture.Character.length)
        ],
      Ambition:
        setting.Theme.People.Culture.Ambition[
          roll(setting.Theme.People.Culture.Ambition.length)
        ],
    };
    result.Resources = {
      Abundance:
        setting.Theme.People.Resources.Abundance[
          roll(setting.Theme.People.Resources.Abundance.length)
        ],
      Scarcity:
        setting.Theme.People.Resources.Scarcity[
          roll(setting.Theme.People.Resources.Scarcity.length)
        ],
    };

    // Factions
    result.Factions = rollRealmFaction(setting);

    // set terrain count to a random number 1-6
    const terrainCount = Math.floor(random() * 6) + 1;
    result.Terrain = [];
    for (let i = 0; i < terrainCount; i++) {
      const difficulty =
        setting.Topography.Difficulty[
          roll(setting.Topography.Difficulty.length)
        ];
      const terrain = `${
        setting.Topography.Terrain[difficulty].Terrain[
          roll(setting.Topography.Terrain[difficulty].Terrain.length)
        ]
      }. Difficulty: ${difficulty}. Landmark: ${
        setting.Topography.Terrain[difficulty].Landmark[
          roll(setting.Topography.Terrain[difficulty].Landmark.length)
        ]
      }.
     `;
      result.Terrain.push(terrain);
    }

    result.Weather = {
      Spring:
        setting.Weather.SeasonalWeather.Spring[
          roll(setting.Weather.SeasonalWeather.Spring.length)
        ],
      Summer:
        setting.Weather.SeasonalWeather.Summer[
          roll(setting.Weather.SeasonalWeather.Summer.length)
        ],
      Fall: setting.Weather.SeasonalWeather.Fall[
        roll(setting.Weather.SeasonalWeather.Fall.length)
      ],
      Winter:
        setting.Weather.SeasonalWeather.Winter[
          roll(setting.Weather.SeasonalWeather.Winter.length)
        ],
      ["Unusual Weather (optional)"]:
        setting.Weather.UnusualWeather[
          roll(setting.Weather.UnusualWeather.length)
        ],
    };

    const poiCount = Math.floor(random() * (8 - 3 + 1)) + 3;
    result.POIs = [];
    const poiKinds = [];
    for (let i = 0; i < poiCount; i++) {
      let poi = "";

      const poiNameForumla =
        setting.Names.NameFormulas.POI[
          roll(setting.Names.NameFormulas.POI.length)
        ];
      const adjective =
        setting.Names.Adjectives[roll(setting.Names.Adjectives.length)];
      const noun = setting.Names.Nouns[roll(setting.Names.Nouns.length)];
      const type =
        setting.PointsOfInterest.POI[roll(setting.PointsOfInterest.POI.length)];
      const poiName = convertName(poiNameForumla, [
        { type: "Noun", word: noun },
        { type: "Adjective", word: adjective },
        { type: "POI", word: type },
      ]);

      if (type === "Waypoint") {
        poi = `${poiName}: ${
          setting.PointsOfInterest.Waypoints.Waypoint[
            roll(setting.PointsOfInterest.Waypoints.Waypoint.length)
          ]
        }, 
        ${
          setting.PointsOfInterest.Waypoints.Feature[
            roll(setting.PointsOfInterest.Waypoints.Feature.length)
          ]
        }`;
      } else if (type === "Settlement") {
        poi = `${poiName}: ${
          setting.PointsOfInterest.Settlements.Settlement[
            roll(setting.PointsOfInterest.Settlements.Settlement.length)
          ]
        }, ${
          setting.PointsOfInterest.Settlements.Feature[
            roll(setting.PointsOfInterest.Settlements.Feature.length)
          ]
        }`;
      } else if (type === "Curiosity") {
        poi = `${poiName}: ${
          setting.PointsOfInterest.Curiosities.Curiosity[
            roll(setting.PointsOfInterest.Curiosities.Curiosity.length)
          ]
        }, ${
          setting.PointsOfInterest.Curiosities.Feature[
            roll(setting.PointsOfInterest.Curiosities.Feature.length)
          ]
        }`;
      } else if (type === "Lair") {
        poi = `${poiName}: ${
          setting.PointsOfInterest.Lairs.Lair[
            roll(setting.PointsOfInterest.Lairs.Lair.length)
          ]
        }, ${
          setting.PointsOfInterest.Lairs.Feature[
            roll(setting.PointsOfInterest.Lairs.Feature.length)
          ]
        }`;
      } else if (type === "Dungeon") {
        poi = `${poiName}: ${
          setting.PointsOfInterest.Dungeons.Type[
            roll(setting.PointsOfInterest.Dungeons.Type.length)
          ]
        }, ${
          setting.PointsOfInterest.Dungeons.Feature[
            roll(setting.PointsOfInterest.Dungeons.Feature.length)
          ]
        }`;
      } else if (type === "Forest") {
        poi = poiName;
      }
      result.POIs.push(poi);
      poiKinds.push(type.toLowerCase());
    }

    const realmNameFormula =
      setting.Names.NameFormulas.Realm[
        roll(setting.Names.NameFormulas.Realm.length)
      ];
    const realmAdjective =
      setting.Names.Adjectives[roll(setting.Names.Adjectives.length)];
    const realmNoun = setting.Names.Nouns[roll(setting.Names.Nouns.length)];
    const realmRulerType =
      setting.Names.RulerTypes[roll(setting.Names.RulerTypes.length)];
    const realmName = convertName(realmNameFormula, [
      { type: "Noun", word: realmNoun },
      { type: "Adjective", word: realmAdjective },
      { type: "Rulers", word: realmRulerType },
    ]);

    return {title: realmName, category: 'location', fields: result, mapKind: 'realm', poiKinds};
  } else if (subcategory === "Faction") {
    result = rollStandaloneFaction(setting);
    return {title: result.Name, category: 'faction', fields: result};
  } else if (subcategory === "Faction Actions") {
    const actions = setting;
    const action = actions[roll(actions.length)];
    return {title: 'Faction Action', category: 'note', fields: action};
  } else if (subcategory === "NPC") {
    const name = setting.NPCNames.Names[roll(setting.NPCNames.Names.length)];
    const background =
      setting.NPCBackgrounds[roll(setting.NPCBackgrounds.length)];
    const virtue =
      setting.NPCTraits.Virtues[roll(setting.NPCTraits.Virtues.length)];
    const vice = setting.NPCTraits.Vices[roll(setting.NPCTraits.Vices.length)];
    const quirk = setting.NPCQuirks[roll(setting.NPCQuirks.length)];
    const goal = setting.NPCGoals.Goals[roll(setting.NPCGoals.Goals.length)];

    return {title: name, category: 'npc', fields: {Name:name, Background:background, Virtue:virtue, Vice:vice, Quirk:quirk, Goal:goal}};
  }
};
