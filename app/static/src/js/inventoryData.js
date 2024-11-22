// This module manages the inventory data

import inventoryUI from "./inventoryUI.js";
import utils from "./utils.js";

const inventory = {
  items: [],
  containers: [{ name: "Main", slots: 10, id: 0 }],
  transfer: [],

  setItems(items) {
    this.items = items;
    const usedIds = new Set();

    this.items.forEach((item) => {
      if (!("id" in item) || item.id === undefined || item.id === null) {
        item.id = utils.getNextUniqueId(this.items);
      }

      if (usedIds.has(item.id)) {
        console.warn(`Duplicate item ID ${item.id} found. Assigning a new ID.`, item);
        item.id = utils.getNextUniqueId(this.items);
      }

      usedIds.add(item.id);
    });
  },

  getItems() {
    return this.items;
  },

  getItem(id) {
    return this.items.find((item) => item.id === id);
  },

  setContainers(containers) {
    this.containers = containers;

    // Leaving out checking for duplicate container IDs for now
    // Containers can rely on other id's if they are carried by another container, so the id's should never change

    // const usedIds = new Set();

    // this.containers.forEach((container) => {
    //   if (container.id === undefined) {
    //     container.id = utils.getNextUniqueId(this.containers);
    //   }

    //   if (usedIds.has(container.id)) {
    //     console.warn(`Duplicate container ID ${container.id} found. Assigning a new ID.`, container);
    //     container.id = utils.getNextUniqueId(this.containers);
    //   }

    //   usedIds.add(container.id);
    // });
  },

  getContainers() {
    return this.containers;
  },

  addContainer(container) {
    container.id = utils.getNextUniqueId(this.containers);
    this.containers.push(container);
    return container.id;
  },

  addOrUpdate(collection, item) {
    // function for adding either an item or a container to the collection and generating a uniquie id
    if (item.id) {
      // Find the item and update all its properties except for id
      let itemToUpdate = collection.find((i) => i.id === item.id);
      if (itemToUpdate) {
        for (let key in item) {
          if (key !== "id") {
            itemToUpdate[key] = item[key];
          }
        }
      } else {
        console.error("Item not found in collection", item, collection);
        item.id = utils.getNextUniqueId(collection);
        collection.push(item);
      }
    } else {
      // If the item doesn't have an id, generate a new unique id and add it to the collection
      item.id = utils.getNextUniqueId(collection);

      collection.push(item);
    }
  },

  addOrUpdateContainer(container) {
    this.addOrUpdate(this.containers, container);

    // Remove any carrying items for this container, incase this has changed
    this.items = this.items.filter((item) => item.carrying !== container.id);

    // If the container is carried by a container, add a carrying item
    if (container.carried_by && container.load && container.load > 0) {
      // add a carying item for each load
      for (let i = 0; i < container.load; i++) {
        let item = {
          name: "Carrying " + container.name,
          location: +container.carried_by,
          carrying: +container.id,
          tags: [],
        };
        this.addOrUpdateItem(item);
      }
    }
  },

  updateItem(id, key, value) {
    let item = this.items.find((item) => item.id === id);
    if (item) {
      item[key] = value;
    }
    if (key === "uses" && value === 0) {
      this.deleteItem(id);
    }
  },

  addOrUpdateItem(item) {
    // console.log("Adding or updating item", item, this.items);
    if (!item.location) {
      item.location = 0;
    }
    if (!item.tags) {
      item.tags = [];
    }

    this.addOrUpdate(this.items, item);
  },

  addItem(item) {
    item.id = utils.getNextUniqueId(this.items);
    this.items.push(item);
    if (!item.location) {
      item.location = 0;
    }
    if (!item.tags) {
      item.tags = [];
    }
    if (item.description === undefined) {
      item.description = "";
    }
    return item.id;
  },

  // addItems(items) {
  //   items.forEach((item) => {
  //     this.addItem(item);
  //   });
  // },

  addItems(items) {
    const newItems = items.map((item) => ({
      ...item,
      id: utils.getNextUniqueId(this.items),
    }));
    newItems.forEach((item) => this.addItem(item));
  },

  addFatigue() {
    this.addItem({ name: "Fatigue", location: 0, tags: [] });
  },

  resetInventory() {
    this.items = [];
    this.containers = [{ name: "Main", slots: 10, id: 0 }];
  },

  deleteItem(id) {
    // check if the item is carrying another item
    let item = this.items.find((item) => item.id === id);
    if (item && item.carrying) {
      // adjust the container load
      let container = this.containers.find((container) => container.id === item.carrying);
      if (container && container.load > 0) {
        container.load--;
      }
    }
    //delete the item
    this.items = this.items.filter((item) => item.id !== id);
  },

  getItemDescription(id) {
    let item = this.items.find((item) => item.id === id);
    return item.description;
  },

  getSlotsCount(containerID) {
    let slots = 0;
    // console.log("Getting slots for container: " + containerID, this.items);
    this.items.forEach((item) => {
      if (item.location === containerID && item.tags) {
        if (item.tags.includes("bulky")) {
          slots += 2;
        } else if (!item.tags.includes("petty")) {
          slots++;
        } else {
        }
      }
    });
    return slots;
  },

  getPartyMemberSlotsCount(items, containerID = 0) {
    if (!items) {
      return;
    }
    let slots = 0;
    items.forEach((item) => {
      if (item.location === containerID && item.tags) {
        if (item.tags.includes("bulky")) {
          slots += 2;
        } else if (!item.tags.includes("petty")) {
          slots++;
        } else {
        }
      }
    });
    return slots;
  },

  // NOTE: Moved to backend
  // getArmorValue() {
  // let armor = 0;
  // let bonusDefense = 0;

  // if (!this.items) {
  //   return { armor, bonusDefense };
  // }

  // this.items.forEach((item) => {
  //   if (item.tags && item.location === 0) {
  //     if (item.tags.includes("1 Armor")) {
  //       armor++;
  //     } else if (item.tags.includes("2 Armor")) {
  //       armor += 2;
  //     } else if (item.tags.includes("3 Armor")) {
  //       armor += 3;
  //     }
  //     if (item.tags.includes("bonus defense")) {
  //       bonusDefense++;
  //     }
  //   }
  // });
  // return { armor, bonusDefense };
  // },

  deleteContainer(id, moveItemsTo = null) {
    // console.log("Deleting container: " + id, "moveItemsTo: " + moveItemsTo);
    if (moveItemsTo) {
      this.items.forEach((item) => {
        if (item.location === id) {
          item.location = +moveItemsTo;
        }
      });
    } else {
      //delete items in the container
      this.items = this.items.filter((item) => item.location !== id);
    }
    //delete the container
    this.containers = this.containers.filter((container) => container.id !== id);
    //delete any items that are carrything this container
    this.items = this.items.filter((item) => item.carrying !== id);
  },

  getContainerID(name) {
    return this.containers.find((container) => container.name.toLowerCase() === name.toLowerCase())?.id ?? null;
  },

  convertCarriedByToID() {
    // this function is used durring character creation
    // it allows the  background json files to store the name of the container that is carrying the item
    // rather than the id of the container

    this.containers.forEach((container) => {
      if (typeof container.carried_by === "string") {
        let carriedBy = this.getContainerID(container.carried_by);
        if (typeof carriedBy === "number") {
          // if the container is found
          container.carried_by = carriedBy;
        }
        if (container.load > 0 && typeof container.carried_by === "number") {
          for (let i = 0; i < container.load; i++) {
            this.addOrUpdateItem({
              name: `Carrying ${container.name}`,
              location: carriedBy,
              carrying: container.id,
            });
          }
        }
      }
    });
  },

  transferItem(item) {
    item.location = 0;
    item.id = null;
    this.transfer.push(item);
  },
  transferPartyItem(item, characterID) {
    item.location = 0;
    item.id = null;
    let transferItem = { ...item, character: characterID };
    this.transfer.push(transferItem);
  },
  getTransfer() {
    return this.transfer;
  },
};

export default inventory;
