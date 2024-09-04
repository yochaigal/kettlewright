export const createElement = (type, options = {}) => {
  const element = document.createElement(type);
  if (options.classes) {
    element.classList.add(...options.classes);
  }
  if (options.attributes) {
    Object.keys(options.attributes).forEach((key) => {
      element.setAttribute(key, options.attributes[key]);
    });
  }
  if (options.ariaLabel) {
    element.setAttribute("aria-label", options.ariaLabel);
  }
  if (options.content) {
    element.textContent = options.content;
  }
  if (options.html) {
    element.innerHTML = options.html;
  }
  if (options.id) {
    element.id = options.id;
  }
  if (options.events) {
    Object.entries(options.events).forEach(([event, handler]) => {
      element.addEventListener(event, handler);
    });
  }
  return element;
};

export const createOption = (text, value = "") => {
  const option = document.createElement("option");
  option.value = value;
  option.text = text;
  return option;
};

export const addOptionToSelect = (selectElement, value, text, selected = false, disabled = false) => {
  const option = document.createElement("option");
  option.value = value;
  option.textContent = text;
  if (disabled) {
    option.disabled = true;
  }
  if (selected) {
    option.selected = true;
  }
  selectElement.appendChild(option);
};

export const selectOptionByIndex = (selectElement, index) => {
  if (index >= 0 && index < selectElement.options.length) {
    selectElement.selectedIndex = index;
  }
};

export const roll = (numRolls, sides) => {
  let results = 0;
  for (let i = 0; i < numRolls; i++) {
    const rollResult = Math.floor(Math.random() * sides) + 1;
    results += rollResult;
  }
  return results;
};

export const kebabToCamel = (str) => {
  return str.split("-").reduce((result, word, index) => {
    return result + (index === 0 ? word : word.charAt(0).toUpperCase() + word.slice(1));
  }, "");
};

export const createVariablesForIds = () => {
  const elementsById = {};
  const allElements = document.querySelectorAll("[id]");
  allElements.forEach((element) => {
    const camelCaseId = kebabToCamel(element.id); // Note the direct call to kebabToCamel
    elementsById[camelCaseId] = element;
  });
  return elementsById;
};

export const getNextUniqueId = (arr) => {
  if (!Array.isArray(arr)) {
    console.error("Invalid input: arr is not an array", arr);
    return undefined; // or throw an error, depending on your error handling strategy
  }

  const highestId = arr
    .filter((item) => item.id !== undefined && Number.isInteger(item.id))
    .reduce((max, item) => (item.id > max ? item.id : max), 0);
  return highestId + 1;
};

export const sanitizeStringForJSON = (str) => {
  if (str !== undefined) {
    let sanitized = str.replace(/["`()]/g, "'");
    sanitized = sanitized.replace(/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]/g, "");
    return sanitized;
  } else {
    return str;
  }
};

export const rollDice = (sides) => {
  const result = Math.floor(Math.random() * sides) + 1;
  // console.log(`Rolled a d${sides} and got a ${result}`);

  // return `d${sides} (${result})`;
  return result;
};

export const rollDoubleDice = (sides) => {
  const roll1 = Math.floor(Math.random() * sides) + 1;
  const roll2 = Math.floor(Math.random() * sides) + 1;
  return [roll1, roll2];
  // return `d${sides}+d${sides} (${roll1}, ${roll2})`;
};

import * as utils from "./utils.js"; // Assuming the above exports are in utils.js

export default utils;
