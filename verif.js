// Creux web : tes heures creuses vont-elles changer avec la réforme ? Tout est calculé dans le
// navigateur. Mêmes règles que l'app (Creux/Model/Planner.swift, enum Reform) : à garder alignées.
(function () {
  "use strict";
  const WINTER_PEAKS = [[7 * 60, 11 * 60], [17 * 60, 21 * 60]];
  const SUMMER_PEAKS = [[7 * 60, 10 * 60], [18 * 60, 23 * 60]];
  const NIGHT = [23 * 60, 7 * 60];
  const AFTERNOON = [11 * 60, 17 * 60];

  const contains = ([s, e], m) => (s === e ? false : s < e ? m >= s && m < e : m >= s || m < e);
  const duration = ([s, e]) => (e - s + 1440) % 1440;
  const inSlots = (slots, m) => slots.some((x) => contains(x, m));
  const minutesIn = (slots, win) => { let n = 0; for (let m = 0; m < 1440; m++) if (contains(win, m) && inSlots(slots, m)) n++; return n; };
  const total = (slots) => { let n = 0; for (let m = 0; m < 1440; m++) if (inSlots(slots, m)) n++; return n; };
  const longestNightRun = (slots) => { let best = 0, run = 0; for (let k = 0; k < duration(NIGHT); k++) { const m = (NIGHT[0] + k) % 1440; if (inSlots(slots, m)) { run++; best = Math.max(best, run); } else run = 0; } return best; };
  const clock = (min) => { const m = ((min % 1440) + 1440) % 1440; return m % 60 ? `${Math.floor(m / 60)} h ${String(m % 60).padStart(2, "0")}` : `${m / 60} h`; };

  function findings(winter, summer) {
    const out = [];
    const overlap = WINTER_PEAKS.map((p) => minutesIn(winter, p)).reduce((a, b) => a + b, 0);
    if (overlap > 0) out.push(["warning", `${clock(overlap)} de tes heures creuses tombent entre 7 h et 11 h ou entre 17 h et 21 h. Problème : avec la réforme, ces plages ne pourront plus être creuses. Tes horaires devraient donc bouger entre décembre 2026 et octobre 2027, et ton fournisseur doit te prévenir au moins un mois avant.`]);
    else out.push(["ok", "Bonne nouvelle : aucune heure creuse entre 7 h et 11 h ni entre 17 h et 21 h. Tes horaires d'hiver sont déjà dans les clous."]);
    const t = total(winter);
    if (t !== 480) out.push(["warning", `Tu as saisi ${clock(t)} d'heures creuses par jour, alors que les contrats en comptent 8. Petit coup d'œil à ta facture ?`]);
    if (longestNightRun(winter) < 300) out.push(["warning", "Moins de 5 heures creuses d'affilée la nuit (23 h – 7 h). Les nouvelles règles en imposent au moins 5 : ça va sûrement changer."]);
    if (summer) {
      if (SUMMER_PEAKS.some((p) => minutesIn(summer, p) > 0)) out.push(["warning", "En été, certaines heures creuses tombent entre 7 h et 10 h ou entre 18 h et 23 h. Ces horaires d'été méritent une vérif."]);
      if (minutesIn(summer, AFTERNOON) < 120) out.push(["warning", "En été, les nouvelles grilles prévoient au moins 2 heures creuses l'après-midi (11 h – 17 h)."]);
    }
    return out;
  }

  // Frise de 24 h : plages interdites l'hiver en rouge pâle, tes heures creuses en vert.
  function bar(slots, peaks) {
    const seg = (s, e, cls) => (s < e ? `<rect class="${cls}" x="${(s / 1440) * 100}%" width="${((e - s) / 1440) * 100}%" y="0" height="100%"/>` : `<rect class="${cls}" x="${(s / 1440) * 100}%" width="${((1440 - s) / 1440) * 100}%" y="0" height="100%"/><rect class="${cls}" x="0" width="${(e / 1440) * 100}%" y="0" height="100%"/>`);
    const ticks = [0, 6, 12, 18, 24].map((h) => `<span style="left:${(h / 24) * 100}%">${h} h</span>`).join("");
    return `<div class="frise"><svg viewBox="0 0 100 10" preserveAspectRatio="none" role="img" aria-label="Frise de la journée">${peaks.map(([s, e]) => seg(s, e, "pic")).join("")}${slots.map(([s, e]) => seg(s, e, "creux")).join("")}</svg><div class="heures">${ticks}</div></div>`;
  }

  const options = () => { let o = ""; for (let m = 0; m < 1440; m += 30) o += `<option value="${m}">${clock(m)}</option>`; return o; };
  const read = (box) => [...box.querySelectorAll(".plage")].filter((p) => p.querySelector("input[type=checkbox]").checked).map((p) => [Number(p.querySelector(".de").value), Number(p.querySelector(".a").value)]).filter(([s, e]) => s !== e);

  function compute() {
    const winter = read(document.getElementById("hiver"));
    const seasonal = document.getElementById("saison").checked;
    document.getElementById("ete").hidden = !seasonal;
    const summer = seasonal ? read(document.getElementById("ete")) : null;
    const res = document.getElementById("resultat");
    if (!winter.length) { res.innerHTML = `<p>Indique au moins une plage d'heures creuses.</p>`; return; }
    const f = findings(winter, summer);
    const verdict = f[0][0] === "ok" && f.length === 1;
    res.innerHTML = `<h2>${verdict ? "Tes horaires sont déjà conformes" : "Tes horaires vont probablement changer"}</h2>
      <p class="legende">Hiver : <span class="pastille creux"></span> tes heures creuses · <span class="pastille pic"></span> plages qui ne pourront plus être creuses</p>${bar(winter, WINTER_PEAKS)}
      ${summer && summer.length ? `<p class="legende">Été</p>${bar(summer, SUMMER_PEAKS)}` : ""}
      ${f.map(([lvl, text]) => `<p class="constat ${lvl}">${text}</p>`).join("")}`;
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("select.de, select.a").forEach((s) => { s.innerHTML = options(); s.value = s.dataset.v; });
    document.getElementById("verif").addEventListener("submit", (e) => e.preventDefault());
    document.querySelectorAll("#verif input, #verif select").forEach((el) => el.addEventListener("input", compute));
    compute();
  });
})();
