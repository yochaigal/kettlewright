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

// Styled alert dialog
// @param {string} title alert title
// @param {string} message alert message 
export const styledAlert = (title, message) => {
  Swal.fire({
    title: title,
    text: message,
    confirmButtonText: 'Close',
    background: 'var(--bg)',
    color: 'var(--fg)',
    buttonsStyling: false,
    animation: true,
    customClass: {
      popup: 'modal-alert',
      title: 'modal-alert-card-title',
      htmlContainer: 'modal-alert-content',
      actions: 'modal-alert-actions'
    }
  });
}

// Styled confirm dialog
// @param {string} title confirm title
// @param {string} message confirm message 
//
// @returns promise to proceed with confirmation
export const styledConfirm = (title, message, confirmButton, cancelButton) => {
  return Swal.fire({
    title: title,
    text: message,
    confirmButtonText: confirmButton ? confirmButton : "OK",
    cancelButtonText: cancelButton ? cancelButton : "Cancel",
    showCancelButton: true,
    background: 'var(--bg)',
    color: 'var(--fg)',
    buttonsStyling: false,
    animation: true,
    customClass: {
      popup: 'modal-alert',
      title: 'modal-alert-card-title',
      htmlContainer: 'modal-alert-content',
      actions: 'modal-alert-actions'
    }
  });
}

// Utility function for attaching business logic to 'click' event on the element.
// @param {string} elementSelector element selector
// @param {function} eventCallback function taking two parameters: 'event' (click event) and 'element' (click target) 
export const handleClick = (elementSelector, eventCallback) => {
  document.querySelectorAll(elementSelector).forEach((element) => {
    element.addEventListener("click", function (event) {
      eventCallback(event, element);
    });
  });
}

// Register confirm handler for all HTMX actions
document.addEventListener("htmx:confirm", function (e) {
  // The event is triggered on every trigger for a request, so we need to check if the element
  // that triggered the request has a hx-confirm attribute, if not we can return early and let
  // the default behavior happen
  if (!e.target.hasAttribute('hx-confirm')) return

  e.preventDefault()

  // Get styled confirm promise and run it.
  styledConfirm(
    e.target.dataset.confirmTitle ? e.target.dataset.confirmTitle : "", // data-confirm-title attribute
    e.detail.question, //  hx-confirm attribute value
    e.target.dataset.confirmButton, // data-confirm-button attribute
    e.target.dataset.cancelButton, // data-cancel-button attribute
  ).then(function (result) {
    if (result.isConfirmed) {
      // If the user confirms, we manually issue the request
      e.detail.issueRequest(true); // true to skip the built-in window.confirm()
    }
  })
})

import * as utils from "./utils.js"; // Assuming the above exports are in utils.js

export default utils;
