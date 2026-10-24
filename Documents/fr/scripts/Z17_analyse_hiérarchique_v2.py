#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Z17_analyse_hiérarchique_v2.py — Analyse topologique du graphe hiérarchique
=============================================================================
Version corrigée et complète de Z17.

- Utilise le graphe hiérarchique strict (60 arêtes), PAS le dodécaèdre.
- Calcule distances, centralité, communautés.
- Calcule la corrélation topologie <-> spectre à partir de
  signatures_40_attracteurs.csv (fallback si absent).

Produit :
    - analyse_topologique_hiérarchique_v2.csv (centralité, distances)
    - correlation_topo_spec.txt (résultat de la corrélation)

Auteur : Bruno DE DOMINICIS
Date : Octobre 2026
"""

import os
import numpy as np
import pandas as pd
import networkx as nx
from scipy.stats import spearmanr

from Z00_reference import construire_graphe_hierarchique


# ============================================================
# 1. CHARGEMENT DU GRAPHE
# ============================================================

def charger_graphe():
    """Charge le graphe hiérarchique strict (60 arêtes)."""
    G = construire_graphe_hierarchique()
    assert G.number_of_edges() == 60
    assert nx.diameter(G) == 6
    return G


# ============================================================
# 2. DISTANCES TOPOLOGIQUES
# ============================================================

def statistiques_distances(G):
    """Calcule les statistiques des distances topologiques."""
    attracteurs = sorted(G.nodes())
    distances = [
        nx.shortest_path_length(G, a, b)
        for a in attracteurs for b in attracteurs if a < b
    ]
    return {
        'min': int(min(distances)),
        'max': int(max(distances)),
        'moyenne': float(np.mean(distances)),
        'mediane': float(np.median(distances)),
        'n_paires': len(distances),
    }


# ============================================================
# 3. CENTRALITÉ
# ============================================================

def calculer_centralite(G):
    """Calcule degré, betweenness, closeness pour chaque nœud."""
    betweenness = nx.betweenness_centrality(G)
    closeness = nx.closeness_centrality(G)
    resultats = []
    for a in sorted(G.nodes()):
        resultats.append({
            'attracteur': a,
            'niveau': G.nodes[a]['niveau'],
            'degre': G.degree(a),
            'betweenness': round(betweenness[a], 4),
            'closeness': round(closeness[a], 4),
        })
    return pd.DataFrame(resultats)


# ============================================================
# 4. COMMUNAUTÉS
# ============================================================

def calculer_communautes(G):
    """Détecte les communautés par greedy modularity."""
    communities = nx.community.greedy_modularity_communities(G)
    return [sorted(c) for c in communities]


# ============================================================
# 5. CORRÉLATION TOPOLOGIE <-> SPECTRE
# ============================================================

def parser_epsilon(eps_str):
    """
    Parse une signature ternaire.

    Accepte deux formats :
    - Compact : '0--+++++0++++0+' (15 caractères)
    - Espacé  : '0 -1 -1 1 1 1 1 1 0 1 1 1 1 0 1' (15 tokens)
    """
    if pd.isna(eps_str):
        return None
    s = str(eps_str).strip()
    if ' ' in s:
        return np.array([int(t) for t in s.split()], dtype=np.float64)
    # Format compact
    mapping = {'+': 1.0, '-': -1.0, '0': 0.0}
    return np.array([mapping[c] for c in s], dtype=np.float64)


def calculer_correlation_topo_spec(G, sig_file='signatures_40_attracteurs.csv'):
    """
    Calcule la corrélation de Spearman entre distances topologiques
    et distances spectrales, sur les 20 attracteurs économiques.

    Retourne : (rho, p_value, n_paires) ou None si fichier absent.
    """
    if not os.path.exists(sig_file):
        return None

    df_sig = pd.read_csv(sig_file)

    # Filtrer les attracteurs économiques
    eco = df_sig[df_sig['domaine'] == 'éco'].copy()
    if len(eco) != 20:
        print(f"⚠️  Attention : {len(eco)} attracteurs éco au lieu de 20")

    # Parser les signatures
    eco['eps'] = eco['epsilon_str'].apply(parser_epsilon)

    # Vérification : 15 composantes
    for i, row in eco.iterrows():
        if row['eps'] is None or len(row['eps']) != 15:
            raise ValueError(f"Signature invalide pour {row['attracteur']}")

    n = len(eco)
    dist_spec = np.zeros((n, n))
    dist_topo = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            # Distance spectrale : L1
            dist_spec[i, j] = np.sum(np.abs(eco['eps'].iloc[i] - eco['eps'].iloc[j]))
            # Distance topologique
            a = eco['attracteur'].iloc[i]
            b = eco['attracteur'].iloc[j]
            dist_topo[i, j] = nx.shortest_path_length(G, a, b)

    # Masque : paires distinctes uniquement
    mask = dist_topo > 0
    if mask.sum() == 0:
        return None

    rho, p = spearmanr(dist_topo[mask], dist_spec[mask])
    return {
        'rho': float(rho),
        'p_value': float(p),
        'n_paires': int(mask.sum()),
        'dist_spec_moyenne': float(dist_spec[mask].mean()),
        'dist_topo_moyenne': float(dist_topo[mask].mean()),
    }


# ============================================================
# 6. POINT D'ENTRÉE
# ============================================================

def main():
    print("=" * 70)
    print("Z17 v2 — ANALYSE TOPOLOGIQUE DU GRAPHE HIÉRARCHIQUE STRICT")
    print("=" * 70)

    # Chargement
    G = charger_graphe()
    print(f"\nGraphe : {G.number_of_nodes()} sommets, "
          f"{G.number_of_edges()} arêtes, diamètre {nx.diameter(G)}")

    # 1. Distances
    stats = statistiques_distances(G)
    print(f"\nStatistiques des distances :")
    print(f"   Min     : {stats['min']}")
    print(f"   Max     : {stats['max']}")
    print(f"   Moyenne : {stats['moyenne']:.2f}")
    print(f"   Médiane : {stats['mediane']:.2f}")
    print(f"   Paires  : {stats['n_paires']}")

    # 2. Centralité
    print(f"\nCentralité :")
    df_centralite = calculer_centralite(G)
    print(df_centralite.to_string(index=False))

    # 3. Communautés
    print(f"\nCommunautés (greedy modularity) :")
    communities = calculer_communautes(G)
    for i, c in enumerate(communities):
        print(f"   Communauté {i+1} ({len(c)} sommets) : {c}")

    # 4. Corrélation topologie <-> spectre
    print(f"\nCorrélation topologie <-> spectre :")
    corr = calculer_correlation_topo_spec(G)
    if corr is None:
        print("   ⚠️  signatures_40_attracteurs.csv absent : corrélation non calculée")
    else:
        print(f"   ρ (Spearman)      : {corr['rho']:.4f}")
        print(f"   p-value           : {corr['p_value']:.4e}")
        print(f"   Paires            : {corr['n_paires']}")
        print(f"   d_spec moyenne    : {corr['dist_spec_moyenne']:.2f}")
        print(f"   d_topo moyenne    : {corr['dist_topo_moyenne']:.2f}")

        # Interprétation
        if abs(corr['rho']) < 0.10:
            interpretation = "ORTHOGONALITÉ (ρ proche de 0)"
        elif abs(corr['rho']) < 0.30:
            interpretation = "Corrélation faible"
        else:
            interpretation = "Corrélation significative"
        print(f"   Interprétation    : {interpretation}")

        # Écriture
        with open('correlation_topo_spec.txt', 'w', encoding='utf-8') as f:
            f.write("Corrélation topologie <-> spectre\n")
            f.write("=" * 50 + "\n")
            f.write(f"ρ (Spearman) : {corr['rho']:.4f}\n")
            f.write(f"p-value      : {corr['p_value']:.4e}\n")
            f.write(f"Paires       : {corr['n_paires']}\n")
            f.write(f"Interprétation : {interpretation}\n")
        print(f"   💾 Fichier sauvegardé : correlation_topo_spec.txt")

    # 5. Export
    df_centralite.to_csv('analyse_topologique_hiérarchique_v2.csv', index=False)
    print(f"\n💾 Fichier sauvegardé : analyse_topologique_hiérarchique_v2.csv")


if __name__ == '__main__':
    main()