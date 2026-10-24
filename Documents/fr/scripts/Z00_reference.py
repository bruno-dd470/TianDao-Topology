#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Z00_reference.py — Module de référence commun (v2)
===================================================
CORRECTION MAJEURE par rapport à v1 :
- Suppression de la table B0_TRIPLETS (approximation obsolète).
- Ajout de B_INT_ECO, B_INT_GEO, B_EXT_TABLE (formule exacte T.2.3).
- La fonction calculer_B0(A, B) implémente H(A,B) * B_ext(T_A, T_B).

STATUT ÉPISTÉMIQUE :
- B_0(A,B) = H(A,B) * B_ext(T_A,T_B) est la DÉFINITION EXACTE (T.2.3).
- Les B_int et B_ext sont des valeurs PRÉ-CALCULÉES (T.2.2, T.2.4).
- Les F_int sont des valeurs PRÉ-CALCULÉES (gap spectral, Z.4).

Auteur : Bruno DE DOMINICIS
Date : Octobre 2026
"""

import networkx as nx

# ============================================================
# 1. LES 20 ATTRACTEURS ÉCONOMIQUES
#    (polarité, niveau, F_intrinsèque, B_intrinsèque)
# ============================================================

ATTRACTEURS_ECO = {
    # nom : (polarité, niveau, F_int, B_int)
    'A': ('3P',      0, 0.90, 0.765),
    'B': ('3P',      1, 0.86, 0.750),
    'C': ('3P',      1, 0.88, 0.769),
    'D': ('2P+1N',   1, 0.50, 0.533),
    'E': ('2P+1N',   1, 0.56, 0.547),
    'F': ('2P+1N',   2, 0.52, 0.567),
    'G': ('2P+1N',   2, 0.58, 0.539),
    'H': ('2P+1N',   2, 0.54, 0.544),
    'I': ('1P+2N',   2, 0.80, 0.298),
    'J': ('1P+2N',   3, 0.82, 0.294),
    'K': ('1P+2N',   3, 0.84, 0.292),
    'L': ('1P+2N',   3, 0.78, 0.298),
    'M': ('1P+2N',   3, 0.80, 0.297),
    'N': ('1P+2N',   4, 0.82, 0.289),
    'O': ('1P+2N',   4, 0.80, 0.292),
    'P': ('1P+2N',   4, 0.76, 0.298),
    'Q': ('1P+2N',   5, 0.82, 0.301),
    'R': ('1P+2N',   5, 0.84, 0.292),
    'S': ('1P+2N',   5, 0.82, 0.294),
    'T': ('3N',      6, 0.94, 0.643),
}

# ============================================================
# 2. LES 20 ATTRACTEURS GÉOGRAPHIQUES
# ============================================================

ATTRACTEURS_GEO = {
    'A_geo': ('3G',      0, 0.90, 0.765),
    'B_geo': ('3G',      1, 0.86, 0.750),
    'C_geo': ('3G',      1, 0.88, 0.769),
    'D_geo': ('2G+1H',   1, 0.50, 0.533),
    'E_geo': ('2G+1H',   1, 0.56, 0.547),
    'F_geo': ('2G+1H',   2, 0.52, 0.567),
    'G_geo': ('2G+1H',   2, 0.58, 0.539),
    'H_geo': ('2G+1H',   2, 0.54, 0.544),
    'I_geo': ('1G+2H',   2, 0.80, 0.298),
    'J_geo': ('1G+2H',   3, 0.82, 0.294),
    'K_geo': ('1G+2H',   3, 0.84, 0.292),
    'L_geo': ('1G+2H',   3, 0.78, 0.298),
    'M_geo': ('1G+2H',   3, 0.80, 0.297),
    'N_geo': ('1G+2H',   4, 0.82, 0.289),
    'O_geo': ('1G+2H',   4, 0.80, 0.292),
    'P_geo': ('1G+2H',   4, 0.76, 0.298),
    'Q_geo': ('1G+2H',   5, 0.82, 0.301),
    'R_geo': ('1G+2H',   5, 0.84, 0.292),
    'S_geo': ('1G+2H',   5, 0.82, 0.294),
    'T_geo': ('3H',      6, 0.94, 0.643),
}

def nom_canonique(nom_geo):
    """Convertit 'A_geo' en 'A', etc."""
    return nom_geo.replace('_geo', '')

# ============================================================
# 3. LES 4 COMMUNAUTÉS (Z.2.5)
# ============================================================

COMMUNAUTES = {
    'A': 'C4', 'B': 'C2', 'C': 'C1', 'D': 'C1', 'E': 'C3',
    'F': 'C2', 'G': 'C4', 'H': 'C3', 'I': 'C4', 'J': 'C2',
    'K': 'C1', 'L': 'C2', 'M': 'C1', 'N': 'C3', 'O': 'C4',
    'P': 'C2', 'Q': 'C1', 'R': 'C3', 'S': 'C4', 'T': 'C3',
}

# ============================================================
# 4. TABLE B_EXT (T.2.4.3)
# ============================================================

B_EXT_TABLE = {
    ('3P',    '3G'):     0.870,
    ('3P',    '2G+1H'):  0.662,
    ('3P',    '1G+2H'):  0.402,
    ('3P',    '3H'):     0.152,
    ('2P+1N', '3G'):     0.702,
    ('2P+1N', '2G+1H'):  0.605,
    ('2P+1N', '1G+2H'):  0.438,
    ('2P+1N', '3H'):     0.282,
    ('1P+2N', '3G'):     0.552,
    ('1P+2N', '2G+1H'):  0.472,
    ('1P+2N', '1G+2H'):  0.395,
    ('1P+2N', '3H'):     0.268,
    ('3N',    '3G'):     0.215,
    ('3N',    '2G+1H'):  0.340,
    ('3N',    '1G+2H'):  0.518,
    ('3N',    '3H'):     0.780,
}

# ============================================================
# 5. PARAMÈTRES DE LA FORMULE GÉNÉRALE (T.3.6)
# ============================================================

ALPHA   = 0.03
BETA_1  = 0.08
BETA_2  = 0.05

# ============================================================
# 6. LES 7 NIVEAUX HIÉRARCHIQUES (Z.3.2)
# ============================================================

NIVEAUX = {
    0: ['A'],
    1: ['B', 'C', 'D', 'E'],
    2: ['F', 'G', 'H', 'I'],
    3: ['J', 'K', 'L', 'M'],
    4: ['N', 'O', 'P'],
    5: ['Q', 'R', 'S'],
    6: ['T'],
}

# ============================================================
# 7. GRAPHE HIÉRARCHIQUE STRICT (60 ARÊTES)
# ============================================================

def construire_graphe_hierarchique():
    """Construit le graphe hiérarchique strict (20 nœuds, 60 arêtes)."""
    G = nx.Graph()
    for niveau, attracteurs in NIVEAUX.items():
        for a in attracteurs:
            G.add_node(a, niveau=niveau)
    for n in range(6):
        for a in NIVEAUX[n]:
            for b in NIVEAUX[n + 1]:
                G.add_edge(a, b, type=f"Niveau {n} - Niveau {n+1}")
    assert G.number_of_edges() == 60, \
        f"Erreur : {G.number_of_edges()} arêtes au lieu de 60"
    assert nx.diameter(G) == 6, \
        f"Erreur : diamètre = {nx.diameter(G)} au lieu de 6"
    return G

# ============================================================
# 8. FONCTIONS DE CALCUL EXACT DE B_0 (T.2.3)
# ============================================================

def moyenne_harmonique(x, y):
    """Moyenne harmonique de x et y (0 si x + y = 0)."""
    if x + y == 0:
        return 0.0
    return 2 * x * y / (x + y)

def calculer_H(nom_eco, nom_geo):
    """H(A,B) = moyenne harmonique des B_int."""
    B_int_A = ATTRACTEURS_ECO[nom_eco][3]
    B_int_B = ATTRACTEURS_GEO[nom_geo][3]
    return moyenne_harmonique(B_int_A, B_int_B)

def calculer_B_ext(nom_eco, nom_geo):
    """B_ext(T_A, T_B) depuis la table T.2.4.3."""
    pol_eco = ATTRACTEURS_ECO[nom_eco][0]
    pol_geo = ATTRACTEURS_GEO[nom_geo][0]
    return B_EXT_TABLE.get((pol_eco, pol_geo), 0.0)

def calculer_B0(nom_eco, nom_geo):
    """
    B_0(A,B) = H(A,B) * B_ext(T_A,T_B).
    DÉFINITION EXACTE (T.2.3).
    """
    H = calculer_H(nom_eco, nom_geo)
    B_ext = calculer_B_ext(nom_eco, nom_geo)
    return H * B_ext

# ============================================================
# 9. FONCTIONS UTILITAIRES
# ============================================================

def qualifier(S, nom_eco=None, nom_geo=None):
    """
    Qualification selon S (T.3.4), avec cas particuliers (Annexe X).
    
    Cas particuliers (si nom_eco et nom_geo sont fournis) :
    - 6 états strictement interdits (3P × 3H ou 3N × 3G) → 'Interdit'
    - État terminal (T, T_géo) → 'Terminal'
    - 9 états de bulle (3P × 3G) → 'Bulle'
    
    Sinon, classification par S :
    - S > 0.15 → 'Viable'
    - 0.05 < S ≤ 0.15 → 'Fragile'
    - S ≤ 0.05 → 'Éphémère'
    """
    # Cas particuliers
    if nom_eco is not None and nom_geo is not None:
        pol_A = ATTRACTEURS_ECO[nom_eco][0]
        pol_B = ATTRACTEURS_GEO[nom_geo][0]
        
        # États strictement interdits (nilpotence violée)
        if (pol_A == '3P' and pol_B == '3H') or (pol_A == '3N' and pol_B == '3G'):
            return 'Interdit'
        
        # État terminal (puits absorbant)
        if nom_eco == 'T' and nom_geo == 'T_geo':
            return 'Terminal'
        
        # États de bulle
        if pol_A == '3P' and pol_B == '3G':
            return 'Bulle'
    
    # Classification par S (T.3.4)
    if S > 0.15:
        return 'Viable'
    elif S > 0.05:
        return 'Fragile'
    else:
        return 'Éphémère'

if __name__ == '__main__':
    print("=" * 70)
    print("Z00_reference.py — Vérification du module")
    print("=" * 70)

    # 1. Vérifier le graphe hiérarchique
    G = construire_graphe_hierarchique()
    print(f"\nGraphe hiérarchique : {G.number_of_nodes()} nœuds, "
          f"{G.number_of_edges()} arêtes, diamètre {nx.diameter(G)}")

    # 2. Vérifier B_0 = H × B_ext sur quelques couples
    print("\nVérification de B_0 = H × B_ext :")
    cas = [('A', 'A_geo'), ('A', 'T_geo'), ('D', 'D_geo'),
           ('S', 'S_geo'), ('T', 'T_geo')]
    for eco, geo in cas:
        H = calculer_H(eco, geo)
        B_ext = calculer_B_ext(eco, geo)
        B0 = calculer_B0(eco, geo)
        print(f"  ({eco}, {geo:6s}) : H={H:.3f}, B_ext={B_ext:.3f}, "
              f"B_0={B0:.3f}")

    # 3. Vérifier la fonction qualifier (cas particuliers)
    print("\nVérification de qualifier (cas particuliers) :")
    tests = [
        ('A', 'T_geo', 0.000, 'Interdit'),
        ('T', 'A_geo', 0.000, 'Interdit'),
        ('T', 'T_geo', 0.038, 'Terminal'),
        ('A', 'A_geo', 0.080, 'Bulle'),
        ('F', 'F_geo', 0.227, 'Viable'),
        ('D', 'E_geo', 0.153, 'Viable'),
        ('B', 'D_geo', 0.058, 'Fragile'),
        ('I', 'J_geo', 0.016, 'Éphémère'),
    ]
    for eco, geo, S, attendu in tests:
        obtenu = qualifier(S, eco, geo)
        statut = "OK" if obtenu == attendu else "ERREUR"
        print(f"  [{statut}] qualifier({eco}, {geo}, S={S:.3f}) = "
              f"'{obtenu}' (attendu : '{attendu}')")

    # 4. Vérifier la distribution attendue
    print("\nDistribution attendue des qualifications :")
    from collections import Counter
    toutes = []
    for eco in ATTRACTEURS_ECO:
        for geo in ATTRACTEURS_GEO:
            # S approximatif : on utilise une valeur moyenne
            # (le vrai S dépend de B_joint, calculé par Z14)
            toutes.append(qualifier(0.5, eco, geo))
    # Note : cette distribution n'est pas la bonne, car S=0.5 n'est pas
    # le vrai S. Elle sert juste à vérifier que les cas particuliers
    # sont bien détectés.
    count = Counter(toutes)
    for cat in ['Interdit', 'Terminal', 'Bulle', 'Viable', 'Fragile', 'Éphémère']:
        print(f"  {cat:10s} : {count.get(cat, 0):3d}")

    print("\n" + "=" * 70)
    print("VÉRIFICATION TERMINÉE")
    print("=" * 70)
