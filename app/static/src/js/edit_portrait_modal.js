import inventoryUI from "./inventoryUI.js";
import { styledAlert } from "./utils.js";

const portraitModal = {
  page: "edit",
  portraitURL: "default-portrait.webp",
  customURLField: document.getElementById("edit-portrait-modal-custom-url"),
  portraitImage: document.getElementById("portrait-image"),
  customPortrait: false,
  userSelected: false,

  setImageURL(url) { },

  // set the portrait image to the modal selection
  setPortraitImage(custom = false) {
    if (custom) {
      this.portraitImage.src = this.portraitURL;
      this.customPortrait = true;
      return;
    } else {
      this.portraitImage.src = "/static/images/portraits/" + this.portraitURL;
    }
  },

  setCustomImage(custom) {
    this.customPortrait = custom;
  },

  getCustomImage() {
    return this.customPortrait;
  },

  getUserSelected() {
    return this.userSelected;
  },

  setUserSelected(selection) {
    if (selection == true || selection == false) {
      this.userSelected = selection;
    }
  },

  getImageURL() {
    return this.portraitURL;
  },

  isValidImageUrl(url) {
    // Regular expression to check if the URL is valid
    const validUrlPattern = /^(https?:\/\/)?[\w-]+(\.[\w-]+)+\.?(:\d+)?(\/\S*)?$/;
    if (!validUrlPattern.test(url)) {
      return false;
    }

    // Regular expression to check for valid image file extensions
    const validImageExtensions = /\.(jpg|jpeg|png|gif|bmp|svg)$/i;
    if (!validImageExtensions.test(url)) {
      return false;
    }

    return true;
  },

  removeHighlight() {
    document.querySelectorAll(".edit-portrait-modal-thumbnail").forEach((thumbnail) => {
      thumbnail.classList.remove("highlighted");
    });
    this.customURLField.classList.remove("highlighted");
  },

  initialize(page, custom_portrait = false, portrait_url = "default-portrait.webp") {
    console.log("initialize portrait modal", custom_portrait, portrait_url);

    this.customPortrait = custom_portrait;
    this.portraitURL = portrait_url;
    this.page = page;

    console.log(this.userSelected);

    const editPortraitModal = document.getElementById("edit-portrait-modal");

    document.querySelectorAll(".edit-portrait-modal-thumbnail").forEach((thumbnail) => {
      let imageUrl = thumbnail.getAttribute("data_url");
      thumbnail.addEventListener("click", () => {
        this.portraitURL = imageUrl;
        this.customPortrait = false;
        //this.setPortraitImage();
        this.removeHighlight();
        console.log(this.portraitURL);
        thumbnail.classList.add("highlighted");
      });
    });

    this.customURLField.addEventListener("input", () => {
      this.portraitURL = this.customURLField.value;
      this.customPortrait = true;
      //this.setPortraitImage(true);
    });

    this.customURLField.addEventListener("focus", () => {
      this.removeHighlight();
      this.customURLField.classList.add("highlighted");
      this.portraitURL = this.customURLField.value;
      this.customPortrait = true;
    });

    document.getElementById("edit-portrait-modal-close").addEventListener("click", () => {
      editPortraitModal.classList.remove("is-active");

      this.page == "edit" && inventoryUI.showSaveFooter();
    });

    document.getElementById("edit-portrait-modal-cancel").addEventListener("click", () => {
      editPortraitModal.classList.remove("is-active");
      this.page == "edit" && inventoryUI.showSaveFooter();
    });

    document.getElementById("edit-portrait-modal-save").addEventListener("click", () => {
      if (this.customPortrait) {
        if (this.isValidImageUrl(this.customURLField.value)) {
          this.portraitURL = this.customURLField.value;
          this.setPortraitImage(this.customPortrait);
          // document.getElementById("image_url").value = this.portraitURL;
          // document.getElementById("custom_image").value = this.customPortrait;
          this.page == "edit" && inventoryUI.showSaveFooter();
          editPortraitModal.classList.remove("is-active");
          this.userSelected = true;
        } else {
          //this.customURLField.classList.add("is-danger");
          styledAlert("Save portrait", "Image URL not valid\nor does not point to a valid image file.", "#edit-portrait-modal-image-select-container");
        }
      } else {
        this.setPortraitImage(this.customPortrait);
        // document.getElementById("image_url").value = this.portraitURL;
        // document.getElementById("custom_image").value = this.customPortrait;

        this.page == "edit" && inventoryUI.showSaveFooter();
        editPortraitModal.classList.remove("is-active");
      }
      document.getElementById("portrait-image").src = this.portraitImage.src;
    });

    document.getElementById("edit-portrait-modal-background").addEventListener("click", () => {
      editPortraitModal.classList.remove("is-active");
      this.page == "edit" && inventoryUI.showSaveFooter();
    });
  },

  getUserSelected() {
    return this.userSelected;
  },

  rollPortrait() {
    const portraitThumbnails = document.querySelectorAll(".edit-portrait-modal-thumbnail");
    const randomIndex = Math.floor(Math.random() * portraitThumbnails.length);
    const randomThumbnail = portraitThumbnails[randomIndex];
    randomThumbnail.classList.add("highlighted");

    this.portraitURL = randomThumbnail.getAttribute("data_url");
    this.customPortrait = false;
    this.userSelected = true; // user has selected a portrait via rolling
    this.setPortraitImage();
    //this.removeHighlight();
    randomThumbnail.classList.add("highlighted");
  },

  openModal() {
    const editPortraitModal = document.getElementById("edit-portrait-modal");
    editPortraitModal.classList.add("is-active");
    inventoryUI.hideSaveFooter();
    //this.removeHighlight();
    if (this.customPortrait) {
      console.log("custom portrait");
      this.customURLField.classList.add("highlighted");
      this.customURLField.value = this.portraitURL;
    } else {
      console.log("not custom portrait");
      this.customURLField.value = "";
    }
  },
};

export default portraitModal;
