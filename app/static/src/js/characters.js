function redirectToCharacterPage(element) {
  const url = element.getAttribute("data-character");
  window.location.href = `${url}`;
}

document.addEventListener("DOMContentLoaded", function () {
  function copyLink(element) {
    const urlName = element.dataset.urlName;
    const ownerUsername = element.dataset.ownerUsername;

    const link = `https://kettlewright.cairnrpg.com/users/${ownerUsername}/characters/${urlName}/`;
    navigator.clipboard.writeText(link);
    alert("Link copied to clipboard");
  }

  // document.querySelectorAll(".character-card").forEach((card) => {
  //   card.addEventListener("click", function (event) {
  //     if (!event.target.closest(".character-card-footer")) {
  //       redirectToCharacterPage(this);
  //     }
  //   });
  // });

  document.querySelectorAll(".card-link-button").forEach((button) => {
    button.addEventListener("click", function (event) {
      event.stopPropagation();
      copyLink(this);
    });
  });

  document.querySelectorAll(".card-delete-character-button").forEach((button) => {
    button.addEventListener("click", function (event) {
      event.stopPropagation();
      const characterId = this.getAttribute("data-character-id");
      console.log("delete button clicked", characterId);

      if (confirm("Are you sure you want to delete this character?")) {
        window.location.href = `/delete-character/${characterId}/`;
      }
    });
  });
});
