"""Met à jour les prix par défaut du simulateur « heures creuses rentable ? ».

Source : open data de la CRE (tarifs réglementés résidentiels, options Base et HP/HC),
la ligne en vigueur (DATE_FIN vide) pour 6 kVA. Écrit prix.js et les valeurs des champs
de heures-creuses-rentable.html, et la grille de toutes les puissances dans
prix-kwh-electricite.html (page entièrement générée ici). Lancé chaque semaine par .github/workflows/prix.yml ;
sans changement de tarif, il ne modifie rien.

Usage, depuis la racine du dépôt : python3 tools/prix.py
"""
import csv
import io
import json
import re
import urllib.request

import grille

SOURCE = "https://www.cre.fr/fileadmin/Documents/Open_data/Marches_de_detail/Option_{}.csv"
KVA = "6"
PAGE = "heures-creuses-rentable.html"


def en_vigueur(option):
    """Les lignes en vigueur (DATE_FIN vide), par puissance souscrite."""
    # Le site de la CRE refuse l'agent par défaut de urllib (403).
    requete = urllib.request.Request(SOURCE.format(option), headers={"User-Agent": "Mozilla/5.0 (creux-app prix)"})
    with urllib.request.urlopen(requete, timeout=60) as reponse:
        texte = reponse.read().decode("utf-8-sig")
    return {int(l["P_SOUSCRITE"]): l for l in csv.DictReader(io.StringIO(texte), delimiter=";")
            if not l["DATE_FIN"].strip()}


def ligne_en_vigueur(lignes_option, option):
    lignes = [l for k, l in lignes_option.items() if k == int(KVA)]
    if len(lignes) != 1:
        raise SystemExit(f"{option} : {len(lignes)} lignes en vigueur pour {KVA} kVA, attendu 1")
    return lignes[0]


def nombre(texte, decimales):
    return round(float(texte.replace(",", ".")), decimales)


grille_base, grille_hphc = en_vigueur("Base"), en_vigueur("HPHC")
base, hphc = ligne_en_vigueur(grille_base, "Base"), ligne_en_vigueur(grille_hphc, "HPHC")
jour, mois, annee = base["DATE_DEBUT"].split("/")
prix = {
    "date": f"{annee}-{mois}-{jour}",
    "kva": int(KVA),
    "base": nombre(base["PART_VARIABLE_TTC"], 4),
    "aboBase": nombre(base["PART_FIXE_TTC"], 2),
    "hp": nombre(hphc["PART_VARIABLE_HP_TTC"], 4),
    "hc": nombre(hphc["PART_VARIABLE_HC_TTC"], 4),
    "aboHC": nombre(hphc["PART_FIXE_TTC"], 2),
}

with open("prix.js", "w", encoding="utf-8") as fichier:
    fichier.write("// Généré par tools/prix.py depuis l'open data de la CRE : ne pas modifier à la main.\n")
    fichier.write(f"window.PRIX_ELEC = {json.dumps(prix)};\n")

# Les valeurs dans le HTML aussi, pour qu'elles soient justes avant même le JavaScript.
champs = {"prixBase": "base", "aboBase": "aboBase", "prixHP": "hp", "prixHC": "hc", "aboHC": "aboHC"}
page = open(PAGE, encoding="utf-8").read()
for champ, cle in champs.items():
    valeur = f"{prix[cle]:.{2 if cle.startswith('abo') else 4}f}".replace(".", ",")
    page = re.sub(rf'(id="{champ}" inputmode="decimal" value=")[^"]*(")', rf"\g<1>{valeur}\g<2>", page)
open(PAGE, "w", encoding="utf-8").write(page)
grille.ecrire(prix["date"], grille_base, grille_hphc, nombre)
print(json.dumps(prix, ensure_ascii=False))
