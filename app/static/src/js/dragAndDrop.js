// DragAndDropModule.js
export const DragAndDropModule = (() => {
  let items = [];
  let dragSrcEl = null; // The item being dragged
  let parentContainer; // The parent container of the items
  let placeholder = document.createElement("li");
  placeholder.className = "invt-drag-drop-line";

  function handleDragStart(e) {
    dragSrcEl = e.target;
    e.dataTransfer.effectAllowed = "move";
    // Temporarily hide the original item
    dragSrcEl.style.opacity = "0.5"; // Make the item semi-transparent
    e.dataTransfer.setData("text/html", e.target.outerHTML);
    dragSrcEl.classList.add("dragging");
  }

  function handleDragOver(e) {
    e.preventDefault(); // Necessary to allow dropping
    e.dataTransfer.dropEffect = "move";

    const overElement = e.target.closest(".draggable-item");
    // Check if the overElement is a child of the parentContainer
    if (overElement && parentContainer.contains(overElement)) {
      const bounding = overElement.getBoundingClientRect();
      const offset = bounding.y + bounding.height / 2;

      // Determine whether to place the placeholder above or below the target element
      if (e.clientY < offset) {
        overElement.before(placeholder);
      } else {
        overElement.after(placeholder);
      }
    }
  }

  function handleDragEnter(e) {
    e.target.classList.add("over");
  }

  function handleDragLeave(e) {
    e.target.classList.remove("over");
  }

  function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation(); // Prevents the browser from redirecting.

    // Check if the drop is occurring inside the parentContainer
    if (placeholder.parentNode === parentContainer) {
      const newIndex = Array.from(parentContainer.children).indexOf(placeholder);

      // Perform the item reordering logic
      if (newIndex > -1) {
        parentContainer.insertBefore(dragSrcEl, placeholder);
        items.splice(newIndex, 0, dragSrcEl); // Adjusts the items array
      }

      // Clean up
      updateIndexes();
      placeholder.remove();
      dragSrcEl.classList.remove("dragging", "hidden");
      dragSrcEl.style.opacity = ""; // or remove this if using "hidden" class
    }
  }

  function handleDragEnd(e) {
    items.forEach((item) => {
      item.classList.remove("over", "dragging");
      item.style.opacity = ""; // Restore the item's visibility
    });
    placeholder.remove(); // Ensure the placeholder is removed
  }

  function attachEventListeners() {
    items.forEach((item) => {
      item.setAttribute("draggable", true);
      item.addEventListener("dragstart", handleDragStart, false);
      item.addEventListener("dragenter", handleDragEnter, false);
      item.addEventListener("dragover", handleDragOver, false);
      item.addEventListener("dragleave", handleDragLeave, false);
      item.addEventListener("drop", handleDrop, false);
      item.addEventListener("dragend", handleDragEnd, false);
    });
  }

  function updateIndexes() {
    // Optionally, update each item's data-index attribute to reflect the new order
    items.forEach((item, index) => item.setAttribute("data-index", index));
  }

  function init(draggableItems, container) {
    items = Array.from(draggableItems);
    parentContainer = container;
    attachEventListeners();
  }

  return {
    init,
  };
})();
