#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Z20_generer_tableaux_latex.py — Génération des 10 tableaux LaTeX (v5)
======================================================================
CORRECTIONS par rapport à v4 :
- titre : \\textbf englobe tout le contenu (accolade fermée à la fin).
- sous_titre : idem.
- Aucun backslash dans les f-strings.
- \\setstretch{1} conservé (nécessite \\usepackage{setspace} dans le
  préambule LaTeX).

Entrée :
    B_joint_400_couples_v5.csv (produit par Z14 v4)

Sorties :
    table_T4_bloc_AB.tex ... table_T4_bloc_ST.tex (10 fichiers)
    table_T4_complet.tex (fichier maître)

Auteur : Bruno DE DOMINICIS
Date : Octobre 2026
"""

import csv
import os
from collections import OrderedDict


# ============================================================
# 1. MÉTADONNÉES DES 20 ATTRACTEURS ÉCONOMIQUES
# ============================================================

METADONNEES_ECO = OrderedDict([
    ('A', ('Croissance polarisée extrême',       r'\{P_1,P_2,P_4\}', '3P',    '0,765', '0,90')),
    ('B', ('Croissance polarisée exportatrice',  r'\{P_1,P_3,P_5\}', '3P',    '0,750', '0,86')),
    ('C', ('Croissance polarisée avec dispersion', r'\{P_2,P_3,P_6\}', '3P', '0,769', '0,88')),
    ('D', ('Croissance tempérée',                r'\{P_4,P_5,N_2\}', '2P+1N', '0,533', '0,50')),
    ('E', ('Expansion urbaine',                  r'\{P_5,P_6,N_3\}', '2P+1N', '0,547', '0,56')),
    ('F', ('Stagflation naissante',              r'\{P_1,P_6,N_4\}', '2P+1N', '0,567', '0,52')),
    ('G', ('Croissance appauvrie',               r'\{P_2,P_5,N_6\}', '2P+1N', '0,539', '0,58')),
    ('H', ('Économie de rente',                  r'\{P_3,P_4,N_6\}', '2P+1N', '0,544', '0,54')),
    ('I', ('Récession déflationniste',           r'\{P_1,N_2,N_6\}', '1P+2N', '0,298', '0,80')),
    ('J', ('Crise de liquidité',                 r'\{P_1,N_3,N_5\}', '1P+2N', '0,294', '0,82')),
    ('K', ('Dépression agricole',                r'\{P_2,N_3,N_5\}', '1P+2N', '0,292', '0,84')),
    ('L', ('Économie de guerre',                 r'\{P_3,N_2,N_4\}', '1P+2N', '0,298', '0,78')),
    ('M', ('Phase nodale en front pionnier',     r'\{P_4,N_1,N_3\}', '1P+2N', '0,297', '0,80')),
    ('N', ('Phase nodale avec dispersion',       r'\{P_4,N_5,N_6\}', '1P+2N', '0,289', '0,82')),
    ('O', ('Front pionnier en déflation',        r'\{P_5,N_1,N_4\}', '1P+2N', '0,292', '0,80')),
    ('P', ('Dispersion en régime œkoumène',      r'\{P_6,N_1,N_2\}', '1P+2N', '0,298', '0,76')),
    ('Q', ('Récession avec pouvoir d\'achat bas', r'\{P_2,N_1,N_4\}', '1P+2N', '0,301', '0,82')),
    ('R', ('Stagflation',                        r'\{P_3,N_1,N_5\}', '1P+2N', '0,292', '0,84')),
    ('S', ('Stase (Chine post-2018)',            r'\{P_6,N_5,N_6\}', '1P+2N', '0,294', '0,82')),
    ('T', ('Dépression terminale',               r'\{N_2,N_3,N_4\}', '3N',    '0,643', '0,94')),
])


# ============================================================
# 2. MÉTADONNÉES DES 20 ATTRACTEURS GÉOGRAPHIQUES
# ============================================================

METADONNEES_GEO = OrderedDict([
    ('A_geo', ('Métropole hyper-concentrée',           r'\{G_1,G_2,G_4\}', '3G')),
    ('B_geo', ('Réseau métropolitain étendu',          r'\{G_1,G_3,G_5\}', '3G')),
    ('C_geo', ('Territoire industrialisé flexible',    r'\{G_2,G_3,G_6\}', '3G')),
    ('D_geo', ('Métropole contrainte',                 r'\{G_4,G_5,H_2\}', '2G+1H')),
    ('E_geo', ('Front pionnier dynamique',             r'\{G_5,G_6,H_3\}', '2G+1H')),
    ('F_geo', ('Métropole en transition',              r'\{G_1,G_6,H_4\}', '2G+1H')),
    ('G_geo', ('Territoire équilibré vertical',        r'\{G_2,G_5,H_6\}', '2G+1H')),
    ('H_geo', ('Réseau macrocéphalique équilibré',     r'\{G_3,G_4,H_6\}', '2G+1H')),
    ('I_geo', ('Métropole rigide équilibrée',          r'\{G_1,H_2,H_6\}', '1G+2H')),
    ('J_geo', ('Métropole enclavée',                   r'\{G_1,H_3,H_5\}', '1G+2H')),
    ('K_geo', ('Verticalité enclavée',                 r'\{G_2,H_3,H_5\}', '1G+2H')),
    ('L_geo', ('Maillage sous contrainte',             r'\{G_3,H_2,H_4\}', '1G+2H')),
    ('M_geo', ('Macrocéphalie en déclin',              r'\{G_4,H_1,H_3\}', '1G+2H')),
    ('N_geo', ('Macrocéphalie enclavée',               r'\{G_4,H_5,H_6\}', '1G+2H')),
    ('O_geo', ('Front pionnier en déclin',             r'\{G_5,H_1,H_4\}', '1G+2H')),
    ('P_geo', ('Institutionnel libéré sous contrainte', r'\{G_6,H_1,H_2\}', '1G+2H')),
    ('Q_geo', ('Verticalité contrariée',               r'\{G_2,H_1,H_4\}', '1G+2H')),
    ('R_geo', ('Maillage enclavé',                     r'\{G_3,H_1,H_5\}', '1G+2H')),
    ('S_geo', ('Stase territoriale (Chine post-2018)', r'\{G_6,H_5,H_6\}', '1G+2H')),
    ('T_geo', ('Périphérie en déclin',                 r'\{H_2,H_3,H_4\}', '3H')),
])


# ============================================================
# 3. GROUPES DE BLOCS (A/B, C/D, ..., S/T)
# ============================================================

BLOCS = [
    ('AB', ['A', 'B'], 'Blocs économiques A et B'),
    ('CD', ['C', 'D'], 'Blocs économiques C et D'),
    ('EF', ['E', 'F'], 'Blocs économiques E et F'),
    ('GH', ['G', 'H'], 'Blocs économiques G et H'),
    ('IJ', ['I', 'J'], 'Blocs économiques I et J'),
    ('KL', ['K', 'L'], 'Blocs économiques K et L'),
    ('MN', ['M', 'N'], 'Blocs économiques M et N'),
    ('OP', ['O', 'P'], 'Blocs économiques O et P'),
    ('QR', ['Q', 'R'], 'Blocs économiques Q et R'),
    ('ST', ['S', 'T'], 'Blocs économiques S et T'),
]

LABELS_BLOCS = {
    'AB': 'tab:T4_blocs_A_B', 'CD': 'tab:T4_blocs_C_D',
    'EF': 'tab:T4_blocs_E_F', 'GH': 'tab:T4_blocs_G_H',
    'IJ': 'tab:T4_blocs_I_J', 'KL': 'tab:T4_blocs_K_L',
    'MN': 'tab:T4_blocs_M_N', 'OP': 'tab:T4_blocs_O_P',
    'QR': 'tab:T4_blocs_Q_R', 'ST': 'tab:T4_blocs_S_T',
}


# ============================================================
# 4. CHARGEMENT DES 400 COUPLES
# ============================================================

def charger_resultats(csv_file='B_joint_400_couples_v5.csv'):
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"Fichier {csv_file} introuvable.")
    resultats = {}
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            resultats[(row['A'], row['B'])] = row
    assert len(resultats) == 400, f"Erreur : {len(resultats)} couples"
    return resultats


# ============================================================
# 5. FORMATAGE
# ============================================================

def fmt_num(val, decimals=3):
    try:
        x = float(val)
    except (ValueError, TypeError):
        return str(val)
    return f"{x:.{decimals}f}".replace('.', ',')

def qualification_et_couleur(row):
    pol_A = row['polarite_A']
    pol_B = row['polarite_B']
    S = float(row['S'])
    
    # États strictement interdits
    if (pol_A == '3P' and pol_B == '3H') or (pol_A == '3N' and pol_B == '3G'):
        return 'Interdit', 'failure'
    
    # État terminal
    if row['A'] == 'T' and row['B'] == 'T_geo':
        return 'Terminal', 'terminal'
    
    # États de bulle
    if pol_A == '3P' and pol_B == '3G':
        return 'Bulle', 'warning'
    
    # Classification par S
    if S > 0.15:
        return 'Viable', None
    elif S > 0.05:
        return 'Fragile', 'warning'
    else:
        return 'Éphémère', 'failure'

# ============================================================
# 6. GÉNÉRATION D'UNE LIGNE (sans backslash dans f-string)
# ============================================================

def generer_ligne(numero, nom_eco, nom_geo, row):
    desc_geo, triplet_geo, pol_geo = METADONNEES_GEO[nom_geo]
    _, _, _, B_int_eco, _ = METADONNEES_ECO[nom_eco]

    H = fmt_num(row['H'])
    B_ext = fmt_num(row['B_ext'])
    B_joint = fmt_num(row['B_joint'])
    F = fmt_num(row['F'])
    S = fmt_num(row['S'])

    qualif, couleur = qualification_et_couleur(row)
    if couleur:
        qualif_str = "\\textcolor{" + couleur + "}{\\textbf{" + qualif + "}}"
    else:
        qualif_str = qualif

    # Pré-calcul du label (backslash hors f-string)
    geo_label = nom_geo.replace('_geo', r'_{\text{géo}}')
    couple_str = "$(" + nom_eco + "," + geo_label + ")$"

    return (
        str(numero) + " & " + couple_str + " & " + desc_geo + " & $"
        + triplet_geo + "$ & " + pol_geo + " & "
        + B_int_eco + " & " + H + " & " + B_ext + " & " + B_joint
        + " & " + F + " & " + S + " & " + qualif_str + " \\\\"
    )


# ============================================================
# 7. GÉNÉRATION D'UN BLOC (corrigé)
# ============================================================

def generer_bloc(nom_bloc, liste_eco, description_bloc, resultats, numero_debut):
    label = LABELS_BLOCS[nom_bloc]
    lignes = []
    lignes.extend([
        r"\newpage", r"\begingroup", r"\setstretch{1}", r"\scriptsize",
        r"\setlength{\tabcolsep}{1.50pt}",
        r"\setlength{\extrarowheight}{1pt}",
        r"\renewcommand{\arraystretch}{1.5}",
        r"\setlength{\LTleft}{-15.09mm plus 1fill}",
        r"\setlength{\LTright}{-15.09mm plus 1fill}",
        r"\begin{longtable}{|>{\centering\arraybackslash}p{7.95mm}|"
        r">{\centering\arraybackslash}p{12.95mm}|"
        r">{\raggedright\arraybackslash}p{46.95mm}|"
        r">{\centering\arraybackslash}p{15.95mm}|"
        r">{\centering\arraybackslash}p{19.95mm}|"
        r">{\centering\arraybackslash}p{7.45mm}|"
        r">{\centering\arraybackslash}p{7.45mm}|"
        r">{\centering\arraybackslash}p{7.45mm}|"
        r">{\centering\arraybackslash}p{7.95mm}|"
        r">{\centering\arraybackslash}p{5.95mm}|"
        r">{\centering\arraybackslash}p{7.45mm}|"
        r">{\centering\arraybackslash}p{13.95mm}|}",
        r"\hline",
    ])

    # ---- TITRE DU BLOC (CORRIGÉ) ----
    # \textbf englobe tout le contenu : accolade fermée à la fin (pas après \,)
    liste_eco_str = ' et '.join(liste_eco)
    titre = (
        r"\multicolumn{12}{|>{\centering\arraybackslash}p{174.49mm}|}"
        r"{\textbf{Table \thetable\,:\, "
        + description_bloc + r" : "
        + "[Attracteurs " + liste_eco_str + r"] $\times$ 20 attracteurs géographiques}} \\"
    )
    lignes.extend([titre, r"\hline"])

    numero = numero_debut
    for i, nom_eco in enumerate(liste_eco):
        desc_eco, triplet_eco, pol_eco, B_int_eco, F_eco = METADONNEES_ECO[nom_eco]

        # ---- SOUS-TITRE DU BLOC (CORRIGÉ) ----
        # \textbf englobe tout le contenu : accolade fermée à la fin
        sous_titre = (
            r"\multicolumn{12}{|p{174.49mm}|}{\textbf{Bloc économique "
            + nom_eco + " : Attracteur " + nom_eco + " (" + desc_eco
            + ") ; Triplet éco : $" + triplet_eco + "$ ; Polarité : "
            + pol_eco + r" ; $\mathcal{B}_{\text{int}} = " + B_int_eco
            + r"$ ; $\mathcal{F} = " + F_eco + r"$}} \\"
        )
        lignes.extend([sous_titre, r"\hline"])

        # ---- EN-TÊTE DES COLONNES ----
        lignes.append(
            r"{\scriptsize\bfseries N°} & {\scriptsize\bfseries Couples} & "
            r"{\scriptsize\bfseries Attracteur géographique} & "
            r"{\scriptsize\bfseries Triplet géo} & {\scriptsize\bfseries Polarité} & "
            r"{\scriptsize$\boldsymbol{\mathcal{B}_{\text{int}}}$} & "
            r"{\scriptsize$\boldsymbol{\mathcal{H}}$} & "
            r"{\scriptsize$\boldsymbol{\mathcal{B}_{\text{ext}}}$} & "
            r"{\scriptsize$\boldsymbol{\mathcal{B}_{\text{joint}}}$} & "
            r"{\scriptsize$\boldsymbol{\mathcal{F}}$} & "
            r"{\scriptsize$\boldsymbol{\mathcal{S}}$} & "
            r"{\scriptsize\bfseries Qualif.} \\"
        )
        lignes.append(r"\hline")

        # ---- LIGNES DE DONNÉES ----
        for nom_geo in METADONNEES_GEO:
            key = (nom_eco, nom_geo)
            if key not in resultats:
                print(f"ATTENTION : couple ({nom_eco}, {nom_geo}) absent")
                continue
            lignes.append(generer_ligne(numero, nom_eco, nom_geo, resultats[key]))
            numero += 1

        # Séparateur entre sous-blocs (sauf après le dernier)
        if i < len(liste_eco) - 1:
            lignes.append(r"\hline")

    lignes.extend([r"\hline", r"\end{longtable}", r"\endgroup", r"\clearpage"])
    return "\n".join(lignes), numero


# ============================================================
# 8. GÉNÉRATION DES 10 BLOCS
# ============================================================

def generer_tous_les_blocs(resultats):
    numero = 1
    tous = []
    for nom_bloc, liste_eco, description in BLOCS:
        print(f"Génération du bloc {nom_bloc}...")
        texte, numero = generer_bloc(nom_bloc, liste_eco, description,
                                     resultats, numero)
        fichier = f"table_T4_bloc_{nom_bloc}.tex"
        with open(fichier, 'w', encoding='utf-8') as f:
            f.write(texte)
        print(f"  -> {fichier}")
        tous.append(texte)

    with open('table_T4_complet.tex', 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(tous))
    print(f"\nFichier maître : table_T4_complet.tex")


# ============================================================
# 9. POINT D'ENTRÉE
# ============================================================

def main():
    print("=" * 70)
    print("Z20 v5 — GÉNÉRATION DES 10 TABLEAUX LATEX")
    print("=" * 70)
    resultats = charger_resultats('B_joint_400_couples_v5.csv')
    print(f"400 couples chargés : {len(resultats)}")
    generer_tous_les_blocs(resultats)
    print("\n" + "=" * 70)
    print("GÉNÉRATION TERMINÉE")
    print("=" * 70)


if __name__ == '__main__':
    main()
