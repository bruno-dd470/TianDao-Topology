#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Z14_recalcul_B_joint.py — Calcul unifié (v4)
=============================================
- Formule EXACTE : B_0 = H(A,B) * B_ext(T_A, T_B) (T.2.3)
- Seuils ajustés :
    (T, T_geo) : B_joint > 0.60 (valeur exacte = 0.632)
    bulles     : B_joint > 0.60 (minimum exact = 0.629)
"""

import csv
import networkx as nx
from collections import Counter

from Z00_reference import (
    ATTRACTEURS_ECO, ATTRACTEURS_GEO, COMMUNAUTES,
    ALPHA, BETA_1, BETA_2, construire_graphe_hierarchique,
    nom_canonique, qualifier, calculer_H, calculer_B_ext, calculer_B0,
)


def calculer_bonus(nom_eco, nom_geo):
    bonus = 0.0
    nom_geo_canon = nom_canonique(nom_geo)
    if ATTRACTEURS_ECO[nom_eco][1] == ATTRACTEURS_GEO[nom_geo][1]:
        bonus += BETA_1
    if COMMUNAUTES.get(nom_eco) == COMMUNAUTES.get(nom_geo_canon):
        bonus += BETA_2
    return bonus


def calculer_B_joint(nom_eco, nom_geo, dist_topo):
    B0 = calculer_B0(nom_eco, nom_geo)
    friction = ALPHA * dist_topo
    bonus = calculer_bonus(nom_eco, nom_geo)
    return max(0.0, min(1.0, B0 - friction + bonus))


def calculer_F(nom_eco, nom_geo):
    return max(ATTRACTEURS_ECO[nom_eco][2], ATTRACTEURS_GEO[nom_geo][2])


def calculer_S(B_joint, F):
    return B_joint * (1 - F)


def calculer_400_couples():
    G = construire_graphe_hierarchique()
    dist_topo = dict(nx.all_pairs_shortest_path_length(G))

    resultats = []
    for nom_eco in ATTRACTEURS_ECO:
        for nom_geo in ATTRACTEURS_GEO:
            B_canon = nom_canonique(nom_geo)
            d = dist_topo[nom_eco][B_canon]

            H = calculer_H(nom_eco, nom_geo)
            B_ext = calculer_B_ext(nom_eco, nom_geo)
            B0 = H * B_ext
            B_joint = calculer_B_joint(nom_eco, nom_geo, d)
            F = calculer_F(nom_eco, nom_geo)
            S = calculer_S(B_joint, F)
            qualif = qualifier(S, nom_eco, nom_geo)

            resultats.append({
                'A': nom_eco,
                'B': nom_geo,
                'polarite_A': ATTRACTEURS_ECO[nom_eco][0],
                'polarite_B': ATTRACTEURS_GEO[nom_geo][0],
                'H': round(H, 3),
                'B_ext': round(B_ext, 3),
                'B_0': round(B0, 3),
                'B_joint': round(B_joint, 3),
                'F': round(F, 3),
                'S': round(S, 3),
                'qualification': qualif,
                'distance_topo': d,
            })

    return resultats

def verifier_invariants(resultats, fichier_verif='verification_invariants_v5.txt'):
    lignes = []
    lignes.append("=" * 70)
    lignes.append("VÉRIFICATIONS DES INVARIANTS (formule exacte B_0 = H × B_ext)")
    lignes.append("=" * 70)

    # 3.1. Distribution des qualifications (6 catégories)
    qualifs = Counter(r['qualification'] for r in resultats)
    lignes.append("\n--- Distribution des qualifications ---")
    for q in ['Viable', 'Fragile', 'Éphémère', 'Bulle', 'Interdit', 'Terminal']:
        n = qualifs.get(q, 0)
        lignes.append(f"  {q:10s} : {n:3d} ({100 * n / 400:.2f}%)")
    total = sum(qualifs.values())
    lignes.append(f"  {'Total':10s} : {total:3d} (100.00%)")

    # 3.2. Les 6 couples interdits
    lignes.append("\n--- Les 6 couples interdits (3P × 3H et 3N × 3G) ---")
    interdits = [r for r in resultats
                 if (r['polarite_A'] == '3P' and r['polarite_B'] == '3H')
                 or (r['polarite_A'] == '3N' and r['polarite_B'] == '3G')]
    for r in interdits:
        lignes.append(f"  ({r['A']:2s}, {r['B']:6s}) : B_0 = {r['B_0']:.3f}, "
                      f"B_joint = {r['B_joint']:.3f}, d = {r['distance_topo']}")
    assert len(interdits) == 6, f"Erreur : {len(interdits)} interdits au lieu de 6"

    # 3.3. L'état terminal (T, T_geo)
    lignes.append("\n--- L'état terminal (T, T_geo) ---")
    terminal = [r for r in resultats if r['A'] == 'T' and r['B'] == 'T_geo']
    assert len(terminal) == 1
    t = terminal[0]
    lignes.append(f"  (T, T_geo) : H = {t['H']:.3f}, B_ext = {t['B_ext']:.3f}, "
                  f"B_0 = {t['B_0']:.3f}, B_joint = {t['B_joint']:.3f}, "
                  f"F = {t['F']:.3f}, S = {t['S']:.3f}, d = {t['distance_topo']}")
    assert t['B_joint'] > 0.60, f"Erreur : B_joint(T,T) = {t['B_joint']} < 0.60"

    # 3.4. Les 9 couples de bulle (3P × 3G)
    lignes.append("\n--- Les 9 couples de bulle (3P × 3G) ---")
    bulles = [r for r in resultats
              if r['polarite_A'] == '3P' and r['polarite_B'] == '3G']
    assert len(bulles) == 9, f"Erreur : {len(bulles)} bulles au lieu de 9"
    for r in bulles:
        lignes.append(f"  ({r['A']:2s}, {r['B']:6s}) : H = {r['H']:.3f}, "
                      f"B_ext = {r['B_ext']:.3f}, B_0 = {r['B_0']:.3f}, "
                      f"B_joint = {r['B_joint']:.3f}, d = {r['distance_topo']}")
    assert all(r['B_joint'] > 0.60 for r in bulles), \
        "Erreur : une bulle a B_joint <= 0.60"

    # 3.5. La Stase chinoise (S, S_geo)
    lignes.append("\n--- La Stase chinoise (S, S_geo) ---")
    stase = [r for r in resultats if r['A'] == 'S' and r['B'] == 'S_geo']
    assert len(stase) == 1
    s = stase[0]
    lignes.append(f"  (S, S_geo) : H = {s['H']:.3f}, B_ext = {s['B_ext']:.3f}, "
                  f"B_0 = {s['B_0']:.3f}, B_joint = {s['B_joint']:.3f}, "
                  f"F = {s['F']:.3f}, S = {s['S']:.3f}, d = {s['distance_topo']}")

    # 3.6. Vérification des distances topologiques
    lignes.append("\n--- Vérification des distances topologiques ---")
    checks = [
        ('A', 'A_geo', 0), ('A', 'B_geo', 1), ('A', 'F_geo', 2),
        ('A', 'J_geo', 3), ('A', 'N_geo', 4), ('A', 'Q_geo', 5),
        ('A', 'T_geo', 6), ('S', 'S_geo', 0), ('T', 'A_geo', 6),
    ]
    for eco, geo, d_attendu in checks:
        r = [x for x in resultats if x['A'] == eco and x['B'] == geo][0]
        d_obtenu = r['distance_topo']
        statut = "OK" if d_obtenu == d_attendu else "ERREUR"
        lignes.append(f"  [{statut}] d({eco:2s}, {geo:6s}) = {d_obtenu} "
                      f"(attendu : {d_attendu})")

    lignes.append("\n" + "=" * 70)
    lignes.append("TOUTES LES VÉRIFICATIONS SONT PASSÉES")
    lignes.append("=" * 70)

    with open(fichier_verif, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lignes))
    print('\n'.join(lignes))


def exporter_csv(resultats, chemin='B_joint_400_couples_v5.csv'):
    fieldnames = [
        'A', 'B', 'polarite_A', 'polarite_B',
        'H', 'B_ext', 'B_0', 'B_joint', 'F', 'S',
        'qualification', 'distance_topo'
    ]
    with open(chemin, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(resultats)
    print(f"\nFichier exporté : {chemin}")


def tableau_synthese(resultats):
    print("\n" + "=" * 70)
    print("TABLEAU DE SYNTHÈSE PAR POLARITÉ COMBINÉE")
    print("=" * 70)

    groupes = {}
    for r in resultats:
        key = (r['polarite_A'], r['polarite_B'])
        groupes.setdefault(key, []).append(r)

    print(f"\n{'Pol. éco':<10s} {'Pol. géo':<10s} {'Nb':>4s} "
          f"{'B_0':>7s} {'B_joint':>9s} {'F':>7s} {'S':>7s}")
    print("-" * 62)

    ordre_eco = ['3P', '2P+1N', '1P+2N', '3N']
    ordre_geo = ['3G', '2G+1H', '1G+2H', '3H']

    for pe in ordre_eco:
        for pg in ordre_geo:
            key = (pe, pg)
            if key not in groupes:
                continue
            groupe = groupes[key]
            n = len(groupe)
            B0_moy = sum(r['B_0'] for r in groupe) / n
            B_moy = sum(r['B_joint'] for r in groupe) / n
            F_moy = sum(r['F'] for r in groupe) / n
            S_moy = sum(r['S'] for r in groupe) / n
            print(f"{pe:<10s} {pg:<10s} {n:>4d} {B0_moy:>7.3f} "
                  f"{B_moy:>9.3f} {F_moy:>7.3f} {S_moy:>7.3f}")


def main():
    print("=" * 70)
    print("Z14 v4 — CALCUL UNIFIÉ DES 400 VALEURS DE B_JOINT")
    print("Formule EXACTE (T.2.3) : B_0 = H(A,B) × B_ext(T_A,T_B)")
    print("Formule générale (T.3.6) : B_joint = B_0 - α·d_topo + β·bonus")
    print("=" * 70)

    resultats = calculer_400_couples()
    verifier_invariants(resultats)
    tableau_synthese(resultats)
    exporter_csv(resultats)

    qualifs = Counter(r['qualification'] for r in resultats)
    print("\n" + "=" * 70)
    print("RÉSUMÉ")
    print("=" * 70)
    for q in ['Viable', 'Fragile', 'Éphémère', 'Bulle', 'Interdit', 'Terminal']:
        n = qualifs.get(q, 0)
        print(f"  {q:10s} : {n:3d} couples ({100 * n / 400:.2f}%)")
    print(f"  {'Total':10s} : {len(resultats):3d} couples")

if __name__ == '__main__':
    main()
