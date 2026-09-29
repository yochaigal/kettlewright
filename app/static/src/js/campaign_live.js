let refreshing = false;
let pending = false;

export async function refreshPartyContent(partyId = null) {
  const host=document.querySelector('[data-party-content]');
  if (!host || partyId !== null && String(partyId)!==host.dataset.partyContent) return;
  pending=true;
  if (refreshing) return;
  refreshing=true;
  try {
    while (pending) {
      pending=false;
      const response=await fetch(host.dataset.mapUrl || location.href,{cache:'no-store'});
      if (!response.ok || response.redirected) {
        if ([403,404].includes(response.status) || response.redirected) {
          document.getElementById('party-content-results')?.replaceChildren();
          window.dispatchEvent(new CustomEvent('campaign-access-lost'));
        }
        return;
      }
      if (host.dataset.mapUrl) {
        window.dispatchEvent(new CustomEvent('campaign-refresh',{detail:{graph:await response.json()}}));
      } else {
        const page=new DOMParser().parseFromString(await response.text(),'text/html');
        const container=document.getElementById('party-content-results'), updated=page.getElementById('party-content-results');
        if (container && updated) container.replaceChildren(...updated.childNodes);
      }
    }
  } catch { /* Retain the last view during transient connection failures. */ }
  finally {refreshing=false;}
}
window.addEventListener('focus',()=>refreshPartyContent());
// Reauthorize open tabs even when a former member no longer receives events.
setInterval(()=>{if (!document.hidden) refreshPartyContent();},30000);
