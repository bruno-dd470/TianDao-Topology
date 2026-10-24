#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calcul_400_couples_v7.py
========================
Annexe T.4 / Z.7 — Les 400 attracteurs conjoints (20 éco × 20 géo), modèle Cl(6,6).

Sortie : fichier .tex SANS PRÉAMBULE, à inclure via \\input{annexe_T4_contenu.tex}
dans un document construit avec template.tex (XeLaTeX + Libertinus).

FORMAT EXACT :
- \\scriptsize
- Pas de \\caption*, mais un \\multicolumn pour le titre
- En-têtes de colonnes en {\\tiny\\bfseries ...}
- Spécification exacte des colonnes longtable (12 colonnes)
- Largeurs : 7.95, 12.95, 46.95, 15.95, 19.95, 7.45, 7.45, 7.45, 7.95, 5.95, 7.45, 13.95 mm

CAS PARTICULIERS GÉRÉS :
- 6 états strictement interdits (B_joint = 0.000)
- 1 état terminal (T,T) (B_joint = 0.780)
- 9 états de bulle (B_joint = 0.880)
- 384 états normaux (B_joint = H × B_ext)
"""
from collections import OrderedDict

# ============================================================
# 0. PARAMÈTRES DE MISE EN PAGE (format validé)
# ============================================================
PT_PAR_MM  = 72.27 / 25.4
MM_PAR_PT  = 25.4 / 72.27

# Largeurs des 12 colonnes en mm
LARGEURS_MM = [7.95, 12.95, 46.95, 15.95, 19.95,
               7.45, 7.45, 7.45, 7.95, 5.95, 7.45, 13.95]
N_COL = len(LARGEURS_MM)  # = 12

TABCOLSEP_PT = 1.50
ARRAYRULE_PT = 0.4
MARGE_CM     = 2.0
TEXTWIDTH_MM = 210.0 - 2.0 * MARGE_CM  # = 170 mm

BASELINE = {'scriptsize': 10.0, 'tiny': 7.0}
LIGNES_BANNIERE = 2
BLOCS_PAR_PAGE  = 2
N_GEO           = 20
GRILLE_COMPLETE = False

# Largeur totale réelle de la table
LARGEUR_TABLE_MM = (sum(LARGEURS_MM)
                    + 2 * N_COL * TABCOLSEP_PT * MM_PAR_PT
                    + (N_COL + 1) * ARRAYRULE_PT * MM_PAR_PT)
DEPASSEMENT_MM = (LARGEUR_TABLE_MM - TEXTWIDTH_MM) / 2.0
LARGEUR_BANNIERE_MM = (LARGEUR_TABLE_MM
                       - 2 * TABCOLSEP_PT * MM_PAR_PT
                       - 2 * ARRAYRULE_PT * MM_PAR_PT)

# arraystretch fixé à 1.23 (format validé)
ARRAYSTRETCH = 1.23


def col_spec():
    """Génère la spécification des 12 colonnes au format validé."""
    cols = []
    for i, w in enumerate(LARGEURS_MM):
        inner = w - 2 * TABCOLSEP_PT * MM_PAR_PT
        align = 'raggedright' if i == 2 else 'centering'
        cols.append('>{\\%s\\arraybackslash}p{%.2fmm}' % (align, inner))
    return '|' + '|'.join(cols) + '|'


COLSPEC = col_spec()

# ============================================================
# 1. DONNÉES DU MODÈLE
# ============================================================
GAPS = {'A': 0.05, 'B': 0.07, 'C': 0.06,
        'D': 0.25, 'E': 0.22, 'F': 0.24, 'G': 0.21, 'H': 0.23,
        'I': 0.10, 'J': 0.09, 'K': 0.08, 'L': 0.11, 'M': 0.10,
        'N': 0.09, 'O': 0.10, 'P': 0.12, 'Q': 0.09, 'R': 0.08,
        'S': 0.09, 'T': 0.03}
GAP_MAX = 0.50

# Potentiel de polarité B0 (table des 16 classes)
B0_TABLE = {'3P': 0.75, '3G': 0.75,
            '2P+1N': 0.55, '2G+1H': 0.55,
            '1P+2N': 0.30, '1G+2H': 0.30,
            '3N': 0.65, '3H': 0.65}

# Facteur de qualité Q_int
QINT_TABLE = {'A': 1.020, 'B': 1.000, 'C': 1.025,
              'D': 0.970, 'E': 0.995, 'F': 1.030, 'G': 0.980, 'H': 0.990,
              'I': 0.995, 'J': 0.980, 'K': 0.975, 'L': 0.995, 'M': 0.990,
              'N': 0.965, 'O': 0.975, 'P': 0.995, 'Q': 1.005, 'R': 0.975,
              'S': 0.980, 'T': 0.990}

QINT_GEO_TABLE = {'Ag': 1.020, 'Bg': 1.000, 'Cg': 1.025,
                  'Dg': 0.970, 'Eg': 0.995, 'Fg': 1.030, 'Gg': 0.980,
                  'Hg': 0.990, 'Ig': 0.995, 'Jg': 0.980, 'Kg': 0.975,
                  'Lg': 0.995, 'Mg': 0.990, 'Ng': 0.965, 'Og': 0.975,
                  'Pg': 0.995, 'Qg': 1.005, 'Rg': 0.975, 'Sg': 0.980,
                  'Tg': 0.990}

# Table BEXT dérivée (valeurs corrigées, Annexe T §T.2.3.4)
BEXT = {
    ('3P', '3G'): 0.870, ('3P', '2G+1H'): 0.662,
    ('3P', '1G+2H'): 0.402, ('3P', '3H'): 0.152,
    ('2P+1N', '3G'): 0.702, ('2P+1N', '2G+1H'): 0.605,
    ('2P+1N', '1G+2H'): 0.438, ('2P+1N', '3H'): 0.282,
    ('1P+2N', '3G'): 0.552, ('1P+2N', '2G+1H'): 0.472,
    ('1P+2N', '1G+2H'): 0.395, ('1P+2N', '3H'): 0.268,
    ('3N', '3G'): 0.215, ('3N', '2G+1H'): 0.340,
    ('3N', '1G+2H'): 0.518, ('3N', '3H'): 0.780,
}

# ============================================================
# 2. CAS PARTICULIERS (interdits, terminal, bulles)
# ============================================================
# Couples strictement interdits (violation de nilpotence)
COUPLES_INTERDITS = {
    ('A', 'Tg'), ('B', 'Tg'), ('C', 'Tg'),   # 3P × 3H
    ('T', 'Ag'), ('T', 'Bg'), ('T', 'Cg'),   # 3N × 3G
}

# État terminal (puits absorbant)
COUPLE_TERMINAL = ('T', 'Tg')

# États de bulle (métastables, 3P × 3G)
COUPLES_BULLE = {
    ('A', 'Ag'), ('B', 'Bg'), ('C', 'Cg'),
    ('A', 'Bg'), ('A', 'Cg'),
    ('B', 'Ag'), ('B', 'Cg'),
    ('C', 'Ag'), ('C', 'Bg'),
}

# Valeurs de B_joint imposées par la règle topologique (Annexe Z, §Z.6)
BJOINT_IMPOSE = {}
for _c in COUPLES_INTERDITS:
    BJOINT_IMPOSE[_c] = 0.000
for _c in COUPLES_BULLE:
    BJOINT_IMPOSE[_c] = 0.880
BJOINT_IMPOSE[COUPLE_TERMINAL] = 0.780


def est_interdit(e, g):
    return (e, g) in COUPLES_INTERDITS


def est_terminal(e, g):
    return (e, g) == COUPLE_TERMINAL


def est_bulle(e, g):
    return (e, g) in COUPLES_BULLE


# ============================================================
# 3. ATTRACTEURS ET LIBELLÉS
# ============================================================
ATTRACTEURS_ECO = [
    ('A', 'P_1,P_2,P_4', '3P', 'A'), ('B', 'P_1,P_3,P_5', '3P', 'B'),
    ('C', 'P_2,P_3,P_6', '3P', 'C'), ('D', 'P_4,P_5,N_2', '2P+1N', 'D'),
    ('E', 'P_5,P_6,N_3', '2P+1N', 'E'), ('F', 'P_1,P_6,N_4', '2P+1N', 'F'),
    ('G', 'P_2,P_5,N_6', '2P+1N', 'G'), ('H', 'P_3,P_4,N_6', '2P+1N', 'H'),
    ('I', 'P_1,N_2,N_6', '1P+2N', 'I'), ('J', 'P_1,N_3,N_5', '1P+2N', 'J'),
    ('K', 'P_2,N_3,N_5', '1P+2N', 'K'), ('L', 'P_3,N_2,N_4', '1P+2N', 'L'),
    ('M', 'P_4,N_1,N_3', '1P+2N', 'M'), ('N', 'P_4,N_5,N_6', '1P+2N', 'N'),
    ('O', 'P_5,N_1,N_4', '1P+2N', 'O'), ('P', 'P_6,N_1,N_2', '1P+2N', 'P'),
    ('Q', 'P_2,N_1,N_4', '1P+2N', 'Q'), ('R', 'P_3,N_1,N_5', '1P+2N', 'R'),
    ('S', 'P_6,N_5,N_6', '1P+2N', 'S'), ('T', 'N_2,N_3,N_4', '3N', 'T'),
]

ATTRACTEURS_GEO = [
    ('Ag', 'G_1,G_2,G_4', '3G', 'A'), ('Bg', 'G_1,G_3,G_5', '3G', 'B'),
    ('Cg', 'G_2,G_3,G_6', '3G', 'C'), ('Dg', 'G_4,G_5,H_2', '2G+1H', 'D'),
    ('Eg', 'G_5,G_6,H_3', '2G+1H', 'E'), ('Fg', 'G_1,G_6,H_4', '2G+1H', 'F'),
    ('Gg', 'G_2,G_5,H_6', '2G+1H', 'G'), ('Hg', 'G_3,G_4,H_6', '2G+1H', 'H'),
    ('Ig', 'G_1,H_2,H_6', '1G+2H', 'I'), ('Jg', 'G_1,H_3,H_5', '1G+2H', 'J'),
    ('Kg', 'G_2,H_3,H_5', '1G+2H', 'K'), ('Lg', 'G_3,H_2,H_4', '1G+2H', 'L'),
    ('Mg', 'G_4,H_1,H_3', '1G+2H', 'M'), ('Ng', 'G_4,H_5,H_6', '1G+2H', 'N'),
    ('Og', 'G_5,H_1,H_4', '1G+2H', 'O'), ('Pg', 'G_6,H_1,H_2', '1G+2H', 'P'),
    ('Qg', 'G_2,H_1,H_4', '1G+2H', 'Q'), ('Rg', 'G_3,H_1,H_5', '1G+2H', 'R'),
    ('Sg', 'G_6,H_5,H_6', '1G+2H', 'S'), ('Tg', 'H_2,H_3,H_4', '3H', 'T'),
]

LIBELLES_ECO = OrderedDict([
    ('A', 'Croissance polarisée extrême'),
    ('B', 'Croissance polarisée exportatrice'),
    ('C', 'Croissance polarisée avec dispersion'),
    ('D', 'Croissance tempérée'),
    ('E', 'Expansion urbaine'),
    ('F', 'Stagflation naissante'),
    ('G', 'Croissance appauvrie'),
    ('H', 'Économie de rente'),
    ('I', 'Récession déflationniste'),
    ('J', 'Crise de liquidité'),
    ('K', 'Dépression agricole'),
    ('L', 'Économie de guerre'),
    ('M', 'Phase nodale en front pionnier'),
    ('N', 'Phase nodale avec dispersion'),
    ('O', 'Front pionnier en déflation'),
    ('P', 'Dispersion en régime œkoumène'),
    ('Q', "Récession avec pouvoir d'achat bas"),
    ('R', 'Stagflation'),
    ('S', 'Stase (Chine post-2018)'),
    ('T', 'Dépression terminale'),
])

LIBELLES_GEO = OrderedDict([
    ('Ag', 'Métropole hyper-concentrée'),
    ('Bg', 'Réseau métropolitain étendu'),
    ('Cg', 'Territoire industrialisé flexible'),
    ('Dg', 'Métropole contrainte'),
    ('Eg', 'Front pionnier dynamique'),
    ('Fg', 'Métropole en transition'),
    ('Gg', 'Territoire équilibré vertical'),
    ('Hg', 'Réseau macrocéphalique équilibré'),
    ('Ig', 'Métropole rigide équilibrée'),
    ('Jg', 'Métropole enclavée'),
    ('Kg', 'Verticalité enclavée'),
    ('Lg', 'Maillage sous contrainte'),
    ('Mg', 'Macrocéphalie en déclin'),
    ('Ng', 'Macrocéphalie enclavée'),
    ('Og', 'Front pionnier en déclin'),
    ('Pg', 'Institutionnel libéré sous contrainte'),
    ('Qg', 'Verticalité contrariée'),
    ('Rg', 'Maillage enclavé'),
    ('Sg', 'Stase territoriale (Chine post-2018)'),
    ('Tg', 'Périphérie en déclin'),
])

# ============================================================
# 4. CALCULS
# ============================================================
def b_int(pol, qi):
    return B0_TABLE[pol] * qi


def moyenne_harmonique(x, y):
    return 0.0 if x + y == 0 else 2 * x * y / (x + y)


def fragilite(gap):
    return 1.0 - gap / GAP_MAX


def qualification(S, nom_eco, nom_geo):
    """Qualification avec cas particuliers."""
    if est_interdit(nom_eco, nom_geo):
        return 'Interdit'
    if est_terminal(nom_eco, nom_geo):
        return 'Terminal'
    if est_bulle(nom_eco, nom_geo):
        return 'Bulle'
    if S > 0.15:
        return 'Viable'
    elif S > 0.05:
        return 'Fragile'
    return 'Éphémère'


def qualite_tex(S, nom_eco, nom_geo):
    """Rendu LaTeX de la qualification avec cas particuliers."""
    q = qualification(S, nom_eco, nom_geo)
    if q == 'Interdit':
        return r'\textcolor{failure}{\textbf{Interdit}}'
    if q == 'Terminal':
        return r'\textcolor{failure}{\textbf{Terminal}}'
    if q == 'Bulle':
        return r'\textcolor{warning}{\textbf{Bulle}}'
    if q == 'Viable':
        return r'\textcolor{success}{\textbf{Viable}}'
    if q == 'Fragile':
        return r'\textcolor{warning}{Fragile}'
    return r'\textcolor{failure}{Éphémère}'


def fmt(x, n=3):
    return ('%.*f' % (n, x)).replace('.', ',')


# Préparation des données des attracteurs
eco_data = OrderedDict()
for nom, triplet, pol, cle in ATTRACTEURS_ECO:
    eco_data[nom] = {'triplet': triplet, 'pol': pol,
                     'b_int': b_int(pol, QINT_TABLE[cle]),
                     'f': fragilite(GAPS[cle])}

geo_data = OrderedDict()
for nom, triplet, pol, cle in ATTRACTEURS_GEO:
    geo_data[nom] = {'triplet': triplet, 'pol': pol,
                     'b_int': b_int(pol, QINT_GEO_TABLE[nom]),
                     'f': fragilite(GAPS[cle])}

# ============================================================
# 5. LIGNES (format validé)
# ============================================================
def titre_table(nom_e1, nom_e2):
    """Génère la ligne de titre de la table (centrée, via \\multicolumn)."""
    return (r'\multicolumn{12}{|>{\centering\arraybackslash}p{174.49mm}|}'
            r'{\textbf{Table \thetable\,:\,} Blocs économiques %s et %s : '
            r'[Attracteurs %s et %s] $\times$ %d attracteurs géographiques} \\'
            % (nom_e1, nom_e2, nom_e1, nom_e2, N_GEO))


def ligne_banniere(nom_eco):
    """Génère la bannière d'un bloc économique (alignée à gauche)."""
    e = eco_data[nom_eco]
    triplet_fmt = r'$\{%s\}$' % e['triplet']
    texte = (r'\textbf{Bloc économique %s} : Attracteur %s (%s) ; '
             r'Triplet éco : %s ; Polarité : %s ; '
             r'$\mathcal{B}_{\text{int}} = %s$ ; $\mathcal{F} = %s$'
             % (nom_eco, nom_eco, LIBELLES_ECO[nom_eco],
                triplet_fmt, e['pol'],
                fmt(e['b_int']), fmt(e['f'], 2)))
    return r'\multicolumn{12}{|p{174.49mm}|}{%s} \\' % texte


def ligne_en_tete():
    """Génère l'en-tête des 12 colonnes (en \\tiny)."""
    c = [r'{\tiny\bfseries N°}',
         r'{\tiny\bfseries Couples}',
         r'{\tiny\bfseries Attracteur géographique}',
         r'{\tiny\bfseries Triplet géo}',
         r'{\tiny\bfseries Polarité}',
         r'{\tiny$\boldsymbol{\mathcal{B}_{\text{int}}}$}',
         r'{\tiny$\boldsymbol{\mathcal{H}}$}',
         r'{\tiny$\boldsymbol{\mathcal{B}_{\text{ext}}}$}',
         r'{\tiny$\boldsymbol{\mathcal{B}_{\text{joint}}}$}',
         r'{\tiny$\boldsymbol{\mathcal{F}}$}',
         r'{\tiny$\boldsymbol{\mathcal{S}}$}',
         r'{\tiny\bfseries Qualif.}']
    return ' & '.join(c) + r' \\'


def ligne_donnee(num, nom_eco, nom_geo):
    """Génère une ligne de données au format validé."""
    e, g = eco_data[nom_eco], geo_data[nom_geo]
    H    = moyenne_harmonique(e['b_int'], g['b_int'])
    bext = BEXT[(e['pol'], g['pol'])]

    cle = (nom_eco, nom_geo)
    if cle in BJOINT_IMPOSE:
        bjoint = BJOINT_IMPOSE[cle]
    else:
        bjoint = H * bext

    fj = max(e['f'], g['f'])
    S  = bjoint * (1.0 - fj)
    lettre_geo = nom_geo[:-1]  # enlever le 'g' final

    triplet_geo_fmt = r'$\{%s\}$' % g['triplet']
    couple_fmt = r'$(%s,%s_{\text{géo}})$' % (nom_eco, lettre_geo)

    cellules = [
        str(num),
        couple_fmt,
        LIBELLES_GEO[nom_geo],
        triplet_geo_fmt,
        g['pol'],
        fmt(g['b_int']), fmt(H), fmt(bext), fmt(bjoint),
        fmt(fj, 2), fmt(S),
        qualite_tex(S, nom_eco, nom_geo),
    ]
    return ' & '.join(cellules) + r' \\', S


# ============================================================
# 6. GÉNÉRATION DES TABLEAUX (1 tableau = 1 page = 2 blocs)
# ============================================================
def generer_tableau(num_table, nom_e1, nom_e2, num_debut):
    """Génère un tableau complet au format validé."""
    o = []
    # Préambule de page (format validé)
    o.append(r'\begingroup')
    o.append(r'\setstretch{1}')
    o.append(r'\scriptsize')
    o.append(r'\setlength{\tabcolsep}{1.50pt}')
    o.append(r'\setlength{\extrarowheight}{0pt}')
    o.append(r'\renewcommand{\arraystretch}{1.23}')
    o.append(r'\setlength{\LTleft}{-%.2fmm plus 1fill}' % DEPASSEMENT_MM)
    o.append(r'\setlength{\LTright}{-%.2fmm plus 1fill}' % DEPASSEMENT_MM)
    o.append(r'\refstepcounter{table}\label{tab:T4_blocs_%s_%s}'
             % (nom_e1, nom_e2))
    o.append('')
    o.append(r'\begin{longtable}{%s}' % COLSPEC)
    # Titre de la table (centré, via \multicolumn)
    o.append(titre_table(nom_e1, nom_e2))
    o.append(r'\hline')

    num = num_debut
    stats = []
    for k, nom_eco in enumerate((nom_e1, nom_e2)):
        # Bannière du bloc (alignée à gauche)
        o.append(ligne_banniere(nom_eco))
        o.append(r'\hline')
        # En-tête des colonnes
        o.append(ligne_en_tete())
        o.append(r'\hline')
        # Lignes de données
        for nom_geo in geo_data:
            ligne, S = ligne_donnee(num, nom_eco, nom_geo)
            o.append(ligne)
            if GRILLE_COMPLETE:
                o.append(r'\hline')
            stats.append(qualification(S, nom_eco, nom_geo))
            num += 1
        if not GRILLE_COMPLETE:
            o.append(r'\hline')

    # Fin du tableau
    o.append(r'\end{longtable}')
    o.append(r'\endgroup')
    o.append(r'\clearpage')
    o.append('')
    return '\n'.join(o), stats


# ============================================================
# 7. DOCUMENT FINAL
# ============================================================
def generer_contenu(nom_fichier='annexe_T4_contenu.tex'):
    """Génère le document complet des 10 tableaux."""
    b = [r'%% ========================================================',
         r'%% Annexe T.4 / Z.7 — Les 400 attracteurs conjoints (20 éco x 20 géo)',
         r'%% 10 tableaux d\'une page, 2 blocs de 22 lignes',
         r'%% Format LaTeX validé : longtable, scriptsize, arraystretch=1.23',
         r'%% Cas particuliers : 6 interdits, 1 terminal, 9 bulles',
         r'%% À inclure par : \input{%s}' % nom_fichier,
         r'%% ========================================================', '']

    b.append(r'\section*{Annexe T.4 — Calcul complet des 400 attracteurs conjoints}')
    b.append(r'\addcontentsline{toc}{section}{Annexe T.4 — Les 400 attracteurs conjoints}')
    b.append('')
    b.append(r'\subsection*{T.4.0. Méthode de calcul}')
    b.append('')
    b.append(r'Pour chaque couple $(A_{\text{éco}}, A_{\text{géo}})$ :')
    b.append(r'\begin{align*}')
    b.append(r'\mathcal{H} &= \frac{2\,\mathcal{B}_{\text{int}}(A_{\text{éco}})'
             r'\cdot\mathcal{B}_{\text{int}}(A_{\text{géo}})}'
             r'{\mathcal{B}_{\text{int}}(A_{\text{éco}})'
             r'+\mathcal{B}_{\text{int}}(A_{\text{géo}})} \\')
    b.append(r'\mathcal{B}_{\text{joint}} &= \mathcal{H}\cdot'
             r'\mathcal{B}_{\text{ext}}(T_E, T_G) \\')
    b.append(r'\mathcal{F} &= \max\!\big(\mathcal{F}(A_{\text{éco}}),'
             r'\mathcal{F}(A_{\text{géo}})\big) \\')
    b.append(r'\mathcal{S} &= \mathcal{B}_{\text{joint}}\cdot(1-\mathcal{F})')
    b.append(r'\end{align*}')
    b.append('')
    b.append(r'\noindent Qualification : \textcolor{success}{\textbf{Viable}} '
             r'($\mathcal{S} > 0{,}15$), '
             r'\textcolor{warning}{Fragile} ($0{,}05 < \mathcal{S} \leq 0{,}15$), '
             r'\textcolor{failure}{Éphémère} ($\mathcal{S} \leq 0{,}05$).')
    b.append('')
    b.append(r'\noindent Cas particuliers : '
             r'\textcolor{failure}{\textbf{Interdit}} (6 couples), '
             r'\textcolor{failure}{\textbf{Terminal}} (1 couple), '
             r'\textcolor{warning}{\textbf{Bulle}} (9 couples).')
    b.append(r'\newpage')

    # Compteur de statistiques
    compteur = OrderedDict([('Viable', 0), ('Fragile', 0), ('Éphémère', 0),
                            ('Bulle', 0), ('Terminal', 0), ('Interdit', 0)])

    noms = [n for n, _, _, _ in ATTRACTEURS_ECO]
    num = 1

    for t in range(len(noms) // BLOCS_PAR_PAGE):
        e1, e2 = noms[2 * t], noms[2 * t + 1]
        tex, stats = generer_tableau(t + 1, e1, e2, num)
        b.append(tex)
        for s in stats:
            compteur[s] += 1
        num += len(stats)

    # Écriture du fichier
    with open(nom_fichier, 'w', encoding='utf-8') as f:
        f.write('\n'.join(b))

    # Rapport de statistiques
    print('Fichier généré : %s' % nom_fichier)
    print('Tableaux (pages) : %d  |  Lignes/tableau : %d  |  Couples : %d'
          % (len(noms) // BLOCS_PAR_PAGE,
             BLOCS_PAR_PAGE * (N_GEO + 2), sum(compteur.values())))
    print('Largeur table : %.2f mm (texte %.0f mm, débordement %.2f mm/côté)'
          % (LARGEUR_TABLE_MM, TEXTWIDTH_MM, DEPASSEMENT_MM))
    print('arraystretch  : %.3f' % ARRAYSTRETCH)
    print('Statistiques :')
    for k, v in compteur.items():
        print('   %-9s : %3d couples (%.2f%%)' % (k, v, 100.0 * v / 400))


if __name__ == '__main__':
    generer_contenu()
