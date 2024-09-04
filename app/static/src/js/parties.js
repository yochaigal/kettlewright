function redirectToPartyPage(element) {
  // const party = JSON.parse(element.getAttribute("data-party"));
  // window.location = `${baseURL}/users/${party.owner_username}/parties/${party.party_url}/`;

  const ownername = element.getAttribute("data-ownername");
  const partyurl = element.getAttribute("data-partyurl");
  window.location.href = `/users/${ownername}/parties/${partyurl}/`;
}

document.addEventListener("DOMContentLoaded", function () {
  const newPartyModal = document.getElementById("new-party-modal");

  document.getElementById("new-party-button").addEventListener("click", function () {
    newPartyModal.classList.toggle("is-active");
  });

  document.getElementById("new-party-cancel-button").addEventListener("click", function () {
    newPartyModal.classList.toggle("is-active");
  });

  // document.getElementById("new-party-modal-close").addEventListener("click", function () {
  //   newPartyModal.classList.toggle("is-active");
  // });
});
