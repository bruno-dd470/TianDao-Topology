#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Z13_classification_400_couples_v3.py — Classification unifiée
==============================================================
Version corrigée et unifiée.

- Distances topologiques sur le GRAPHE HIÉRARCHIQUE STRICT (60 arêtes).
- Jointure avec les signatures spectrales (signatures_40_attracteurs.csv).
- Produit un CSV complet exploitable par Z14.

Produit : classification_400_couples_v3.csv
Colonnes : A, B, polarite_A, polarite_B, polarite_combinee,
           communaute_A, communaute_B, meme_communaute,
           distance_topo, epsilon_A, epsilon_B, delta_A, delta_B

Auteur : Bruno DE DOMINICIS
Date : Octobre 2026
"""

import os
import numpy as np
import pandas as pd
import networkx as nx

from Z00_reference import (
    ATTRACTEURS_ECO, ATTRACTEURS_GEO, COMMUNAUTES,
    construire_graphe_hierarchique, nom_canonique,
)


def charger_signatures(sig_file='signatures_40_attracteurs.csv'):
    """Charge les signatures spectrales (fallback si absent)."""
    if not os.path.exists(sig_file):
        print(f"⚠️  {sig_file} absent : signatures non jointes")
        return None
    return pd.read_csv(sig_file)


def classifier_couple(A, B_geo, dist_topo, sig_index=None):
    """Classifie un couple (A_eco, B_geo)."""
    pol_A = ATTRACTEURS_ECO[A][0]
    pol_B = ATTRACTEURS_GEO[B_geo][0]
    B_canon = nom_canonique(B_geo)

    row = {
        'A': A,
        'B': B_geo,
        'polarite_A': pol_A,
        'polarite_B': pol_B,
        'polarite_combinee': f"{pol_A} × {pol_B}",
        'communaute_A': COMMUNAUTES[A],
        'communaute_B': COMMUNAUTES[B_canon],
        'meme_communaute': (COMMUNAUTES[A] == COMMUNAUTES[B_canon]),
        'distance_topo': dist_topo[A][B_canon],
    }

    if sig_index is not None:
        row['epsilon_A'] = sig_index.get(A, {}).get('epsilon_str', '')
        row['epsilon_B'] = sig_index.get(B_geo, {}).get('epsilon_str', '')
        row['delta_A'] = sig_index.get(A, {}).get('delta', np.nan)
        row['delta_B'] = sig_index.get(B_geo, {}).get('delta', np.nan)

    return row


def main():
    print("=" * 70)
    print("Z13 v3 — CLASSIFICATION DES 400 COUPLES (CORRIGÉE)")
    print("Graphe : hiérarchique strict (60 arêtes)")
    print("=" * 70)

    G = construire_graphe_hierarchique()
    dist_topo = dict(nx.all_pairs_shortest_path_length(G))

    # Chargement des signatures
    df_sig = charger_signatures()
    sig_index = None
    if df_sig is not None:
        sig_index = df_sig.set_index('attracteur').to_dict('index')
        print(f"Signatures chargées : {len(sig_index)} attracteurs")

    # Classification
    rows = []
    for A in ATTRACTEURS_ECO:
        for B_geo in ATTRACTEURS_GEO:
            rows.append(classifier_couple(A, B_geo, dist_topo, sig_index))

    df = pd.DataFrame(rows)
    print(f"\n{len(df)} couples classifiés")

    # Vérifications critiques
    print(f"\nVérifications :")
    d_AB = df.loc[(df['A'] == 'A') & (df['B'] == 'B_geo'), 'distance_topo'].values[0]
    assert d_AB == 1, f"Erreur : d(A, B_geo) = {d_AB} au lieu de 1"
    print(f"   ✅ d(A, B_geo) = {d_AB} (attendu : 1)")

    d_AT = df.loc[(df['A'] == 'A') & (df['B'] == 'T_geo'), 'distance_topo'].values[0]
    assert d_AT == 6, f"Erreur : d(A, T_geo) = {d_AT} au lieu de 6"
    print(f"   ✅ d(A, T_geo) = {d_AT} (attendu : 6)")

    # Distribution des distances
    print(f"\nDistribution par distance topologique :")
    for d, group in df.groupby('distance_topo'):
        print(f"   Distance {d} : {len(group):>3} couples")

    # Sauvegarde
    df.to_csv('classification_400_couples_v3.csv', index=False)
    print(f"\n💾 Fichier sauvegardé : classification_400_couples_v3.csv")


if __name__ == '__main__':
    main()