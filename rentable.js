// Creux web : l'option heures creuses est-elle rentable ? Calculé dans le navigateur.
// Prix par défaut : prix.js, régénéré chaque semaine depuis l'open data de la CRE
// (tools/prix.py, .github/workflows/prix.yml).
(function () {
  "use strict";
  const eur = (v) => new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR" }).format(v);
  const pct = (v) => new Intl.NumberFormat("fr-FR", { style: "percent", maximumFractionDigits: 0 }).format(v);
  const val = (id) => parseFloat(String(document.getElementById(id).value).replace(",", ".")) || 0;

  const PRIX = window.PRIX_ELEC;

  function compute() {
    const kwh = val("conso"), share = Math.min(Math.max(val("part"), 0), 100) / 100;
    const base = val("prixBase"), hp = val("prixHP"), hc = val("prixHC");
    const subBase = val("aboBase"), subHC = val("aboHC");
    const costBase = subBase + kwh * base;
    const costHC = subHC + kwh * (share * hc + (1 - share) * hp);
    const diff = costBase - costHC;
    // Part d'heures creuses à partir de laquelle les deux options coûtent pareil.
    const breakEven = hp > hc ? ((hp - base) * kwh + subHC - subBase) / ((hp - hc) * kwh) : NaN;

    const rows = [
      ["Option base", eur(costBase) + " par an"],
      ["Option heures pleines / heures creuses", eur(costHC) + " par an"],
      [diff >= 0 ? "Économie avec les heures creuses" : "Surcoût avec les heures creuses", `<strong>${eur(Math.abs(diff))} par an</strong>`],
      ["Seuil de rentabilité", isFinite(breakEven) ? `${pct(Math.max(breakEven, 0))} de ta consommation en heures creuses` : "—"],
    ];
    const verdict = !isFinite(breakEven) ? "Avec ces prix, le kWh en heures creuses n'est pas moins cher : l'option ne peut pas être rentable."
      : diff >= 0 ? `Avec ${pct(share)} de ta consommation en heures creuses, l'option est rentable. Chaque machine décalée la rend un peu plus intéressante.`
      : `Il faudrait passer au moins ${pct(breakEven)} de ta consommation en heures creuses, contre ${pct(share)} aujourd'hui. Un ballon d'eau chaude, une voiture électrique ou des machines lancées en différé font vite monter cette part.`;

    document.getElementById("resultat").innerHTML =
      `<table>${rows.map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`).join("")}</table>` +
      `<p class="constat ${diff >= 0 ? "ok" : "warning"}">${verdict}</p>` +
      `<p class="note">Abonnement + consommation × prix du kWh, toutes taxes comprises. Prix par défaut : tarif réglementé ${PRIX ? `en vigueur depuis le ${new Date(PRIX.date + "T12:00:00").toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" }).replace(/^1 /, "1er ")}, ${PRIX.kva} kVA` : "en vigueur"} ; remplace-les par ceux de ta facture si ton offre est différente.</p>`;
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("calcul").addEventListener("submit", (e) => e.preventDefault());
    document.querySelectorAll("#calcul input").forEach((el) => el.addEventListener("input", compute));
    compute();
  });
})();
