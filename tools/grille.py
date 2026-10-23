"""Écrit prix-kwh-electricite.html : la grille des tarifs réglementés en vigueur, de 3 à 36 kVA.

Appelé par tools/prix.py avec les lignes en vigueur de l'open data de la CRE. La page est
statique et entièrement générée : sans changement de tarif, elle reste identique octet pour octet.
"""
import html
import json

URL = "https://komorebideuxiemedunom.github.io/creux-app/prix-kwh-electricite.html"
PAGE = "prix-kwh-electricite.html"
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]
CSP = """<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"><meta name="referrer" content="no-referrer"><meta name="viewport" content="width=device-width,initial-scale=1">"""


def eur(v, d=2):
    return f"{v:,.{d}f}".replace(",", " ").replace(".", ",") + " €"


def date_fr(iso):
    annee, mois, jour = iso.split("-")
    jour = "1er" if jour == "01" else str(int(jour))
    return f"{jour} {MOIS[int(mois) - 1]} {annee}"


def ecrire(date, grille_base, grille_hphc, nombre):
    quand = date_fr(date)
    annee = date[:4]
    lignes = []
    for kva in sorted(set(grille_base) | set(grille_hphc)):
        b, h = grille_base.get(kva), grille_hphc.get(kva)
        cellules = [f"{kva} kVA"]
        if b:
            abo = nombre(b["PART_FIXE_TTC"], 2)
            cellules += [eur(nombre(b["PART_VARIABLE_TTC"], 4), 4), f"{eur(abo)}<br><small>{eur(abo / 12)} / mois</small>"]
        else:
            cellules += ["—", "—"]
        if h:
            abo = nombre(h["PART_FIXE_TTC"], 2)
            cellules += [eur(nombre(h["PART_VARIABLE_HP_TTC"], 4), 4), eur(nombre(h["PART_VARIABLE_HC_TTC"], 4), 4),
                         f"{eur(abo)}<br><small>{eur(abo / 12)} / mois</small>"]
        else:
            cellules += ["—", "—", "—"]
        lignes.append("<tr>" + "".join(f"<td>{c}</td>" for c in cellules) + "</tr>")

    six_b, six_h = grille_base[6], grille_hphc[6]
    p_base = eur(nombre(six_b["PART_VARIABLE_TTC"], 4), 4)
    p_hp, p_hc = eur(nombre(six_h["PART_VARIABLE_HP_TTC"], 4), 4), eur(nombre(six_h["PART_VARIABLE_HC_TTC"], 4), 4)
    ecart = round((1 - nombre(six_h["PART_VARIABLE_HC_TTC"], 4) / nombre(six_h["PART_VARIABLE_HP_TTC"], 4)) * 100)
    faq = [
        (f"Quel est le prix du kWh d'électricité en {annee} ?",
         f"Au tarif réglementé en vigueur depuis le {quand}, le kWh coûte {p_base} TTC en option base (6 kVA). "
         f"En option heures pleines / heures creuses, il coûte {p_hp} en heures pleines et {p_hc} en heures creuses. "
         "S'y ajoute l'abonnement, qui dépend de la puissance souscrite."),
        ("Combien coûte le kWh en heures creuses ?",
         f"{p_hc} TTC au tarif réglementé, soit environ {ecart} % de moins qu'en heures pleines ({p_hp}). "
         "Le prix est le même quelle que soit la puissance souscrite."),
        ("Quelle puissance choisir, 6 ou 9 kVA ?",
         "6 kVA suffit à la plupart des logements chauffés au gaz ou au bois. Avec un chauffage électrique, des plaques à induction "
         "et un four, ou une voiture électrique, on passe souvent à 9 kVA. Si le disjoncteur saute quand plusieurs appareils tournent, "
         "la puissance est trop basse ; sinon, une puissance plus faible coûte moins cher d'abonnement."),
        ("Quand les prix de l'électricité changent-ils ?",
         "Les tarifs réglementés sont proposés par la Commission de régulation de l'énergie (CRE) et changent en général le 1er février "
         "et le 1er août. Cette page relit chaque semaine les données publiées par la CRE et se met à jour toute seule."),
        ("Les heures creuses sont-elles rentables ?",
         "Le kWh en heures pleines coûte plus cher que le kWh de l'option base : il faut consommer une part suffisante en heures creuses "
         'pour être gagnant. <a href="heures-creuses-rentable.html">Le calcul avec ta propre consommation</a>.'),
    ]
    texte = lambda s: html.unescape(s.replace('<a href="heures-creuses-rentable.html">', "").replace("</a>", ""))
    ld_faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": texte(a)}} for q, a in faq]}
    ld_table = {"@context": "https://schema.org", "@type": "Dataset",
                "name": f"Tarifs réglementés de l'électricité en vigueur depuis le {quand}",
                "description": "Prix du kWh et abonnement annuel TTC, options base et heures pleines / heures creuses, de 3 à 36 kVA.",
                "url": URL, "dateModified": date, "isBasedOn": "https://www.data.gouv.fr/fr/datasets/historique-des-tarifs-reglementes-de-vente-delectricite-pour-les-consommateurs-residentiels/",
                "license": "https://www.etalab.gouv.fr/licence-ouverte-open-licence/"}

    doc = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">{CSP}
<title>Prix du kWh d'électricité {annee} : base et heures creuses, de 3 à 36 kVA | Creux</title>
<meta name="description" content="Prix du kWh TTC en {annee} : {p_base} en option base, {p_hc} en heures creuses et {p_hp} en heures pleines (tarif réglementé depuis le {quand}). Abonnements de 3 à 36 kVA, mis à jour chaque semaine.">
<link rel="canonical" href="{URL}"><link rel="stylesheet" href="style.css">
<script type="application/ld+json">{json.dumps(ld_table, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(ld_faq, ensure_ascii=False)}</script></head>
<body><main><img class="icon" src="icon.png" alt="">
<h1>Prix du kWh d'électricité en {annee}</h1>
<p>Le tarif réglementé en vigueur depuis le <strong>{quand}</strong>, toutes taxes comprises, pour chaque puissance souscrite : prix du kWh et abonnement, en option base et en option heures pleines / heures creuses.</p>
<div class="card grille"><table>
<thead><tr><th>Puissance</th><th>kWh base</th><th>Abonnement base, par an</th><th>kWh heures pleines</th><th>kWh heures creuses</th><th>Abonnement heures creuses, par an</th></tr></thead>
<tbody>{"".join(lignes)}</tbody></table></div>
<p class="note">Source : open data de la Commission de régulation de l'énergie (historique des tarifs réglementés, licence ouverte) ; « — » : tarif non publié pour cette puissance. Page relue chaque semaine. Les offres de marché ont leurs propres prix : ta facture fait foi.</p>
<div class="cta"><p><strong>{eur(nombre(six_h["PART_VARIABLE_HP_TTC"], 4) - nombre(six_h["PART_VARIABLE_HC_TTC"], 4), 4)} d'écart par kWh entre heures pleines et heures creuses.</strong> Creux te dit si c'est le moment de lancer les machines, calcule le départ différé à régler sur ton lave-linge ou ton lave-vaisselle et te prévient quand les heures creuses commencent. Sur iPhone, sans compte, achat unique.</p><a class="btn" href="https://apps.apple.com/fr/app/id6818609550">Télécharger Creux</a></div>
{"".join(f"<h2>{q}</h2><p>{a}</p>" for q, a in faq)}
<p>Aussi gratuit : <a href="heures-creuses-rentable.html">les heures creuses sont-elles rentables pour toi ?</a> · <a href="verifier-heures-creuses.html">vérifier si tes heures creuses vont changer</a></p>
<footer><a href="index.html">Creux</a> · <a href="confidentialite.html">Confidentialité</a> · © 2026 Lucas Dansac</footer></main></body></html>
"""
    open(PAGE, "w", encoding="utf-8").write(doc)
