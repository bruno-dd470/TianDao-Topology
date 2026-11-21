#!/usr/bin/env python3
"""
Insère automatiquement les \\glsadd{} dans un fichier Markdown temporaire.
Compatible avec les entrées @entry de concepts.bib (option 3).

Version accélérée : boucle lignes→termes, pré-filtre substring.
Protections :
- Empêche l'imbrication \\glsadd{a\\glsadd{b}c} (cause de ! Missing \\endcsname)
- Empêche l'insertion de \\glsadd à l'intérieur des formules mathématiques $...$
- Empêche l'insertion de \\glsadd dans les commandes LaTeX (\\text, \\mathrm, etc.)
- Empêche l'insertion de \\glsadd dans les blocs de code Markdown (```)
- Nettoyage final des imbrications résiduelles (défense en profondeur)

mots_cles.bib est RÉACTIVÉ (dans FICHIERS_BIB_INDEX et FICHIER_MOTS_CLES_BIB).
Sa génération automatique reste désactivée : le fichier est manuel.
"""
import re
import os
import unicodedata
import hashlib

# --- Configuration des chemins absolus ---
DOSSIER_SCRIPT = os.path.dirname(os.path.abspath(__file__))
DOSSIER_RACINE = os.path.dirname(DOSSIER_SCRIPT)
FICHIER_SOURCE = os.path.join(DOSSIER_RACINE, 'src/doc_unique_fr_23-10.md')
FICHIER_INDEXE = os.path.join(DOSSIER_RACINE, 'src/doc_unique_fr_23-10_indexe.md')

FICHIERS_BIB_INDEX = [
    os.path.join(DOSSIER_RACINE, 'bib/notations.bib'),
    os.path.join(DOSSIER_RACINE, 'bib/glossaire_v2.bib'),
    os.path.join(DOSSIER_RACINE, 'bib/mots_cles.bib'),      # ← ACTIF
]

FICHIER_BIB_BIBLIO = os.path.join(DOSSIER_RACINE, 'bib/biblio-unique.bib')
FICHIER_MOTS_CLES_BIB = os.path.join(DOSSIER_RACINE, 'bib/mots_cles.bib')  # ← ACTIF
FICHIER_LOG_NON_TROUVES = os.path.join(DOSSIER_RACINE, 'termes_non_trouves.txt')

ENV_TABLEAU = r'(tabular|tabularx|xltabular|longtable|array|sidewaystable|table)'

# Termes à ne pas insérer automatiquement (apparaissent dans les formules)
TERMES_EXCLUS = {'gap', 'gap-spectral', 'gap_spectral'}


def creer_cle_valide(mot):
    cle = mot.strip().lower()
    cle = unicodedata.normalize('NFKD', cle).encode('ascii', 'ignore').decode('ascii')
    cle = re.sub(r'[^a-z0-9]+', '_', cle)
    cle = cle.strip('_')
    if not cle:
        cle = "mot_c_" + hashlib.md5(mot.encode('utf-8')).hexdigest()[:8]
    return cle


def extraire_termes_index(fichiers_bib):
    """Extrait les termes des fichiers .bib - compatible @entry et @misc"""
    termes = {}
    for fichier in fichiers_bib:
        if not os.path.exists(fichier):
            continue
        with open(fichier, 'r', encoding='utf-8') as f:
            contenu = f.read()

        entries = re.finditer(r'@\w+\{([^,\s]+)\s*,(.*?)(?=@|\Z)', contenu, re.DOTALL)
        for match in entries:
            cle = match.group(1).strip()
            bloc = match.group(2)

            name_match = re.search(r'name\s*=\s*\{([^}]+)\}', bloc)
            if name_match:
                nom = name_match.group(1).strip()
            else:
                nom = cle

            parts = re.split(r'\s*\(([^)]+)\)\s*', nom)
            for part in parts:
                part = part.strip()
                if not part:
                    continue

                nom_normalise = unicodedata.normalize('NFKD', part.lower()).encode('ascii', 'ignore').decode('ascii')
                nom_normalise = re.sub(r'\s+', ' ', nom_normalise).strip()

                if nom_normalise not in termes:
                    termes[nom_normalise] = (part, cle)

    return list(termes.values())


def extraire_mots_cles_biblio(fichier_bib):
    mots_cles = set()
    if not os.path.exists(fichier_bib):
        return []
    with open(fichier_bib, 'r', encoding='utf-8') as f:
        matches = re.findall(r'keywords\s*=\s*\{([^}]+)\}', f.read(), re.IGNORECASE)
        for kw_block in matches:
            for mot in kw_block.split(','):
                mot = mot.strip()
                if mot:
                    mots_cles.add(mot)
    return list(mots_cles)


def generer_bib_mots_cles(mots_cles, fichier_sortie):
    os.makedirs(os.path.dirname(fichier_sortie), exist_ok=True)
    with open(fichier_sortie, 'w', encoding='utf-8') as f:
        f.write("% Fichier généré automatiquement par inserer_index.py\n")
        for mot in mots_cles:
            cle = creer_cle_valide(mot)
            nom_echappe = mot.replace('_', '\\_')
            f.write(f"@entry{{{cle},\n  name = {{{nom_echappe}}},\n  description = {{}}\n}}\n")
    print(f"✅ Fichier d'index généré : {fichier_sortie} ({len(mots_cles)} mots-clés)")


# ---------------------------------------------------------------------------
# Protections
# ---------------------------------------------------------------------------

def proteger_glsadd_existants(texte):
    """Remplace temporairement chaque \\glsadd{...} par un placeholder \\x00N\\x00."""
    blocs = []

    def _sub(m):
        blocs.append(m.group(0))
        return f"\x00{len(blocs) - 1}\x00"

    texte_protege = re.sub(r"\\glsadd\{[^{}]*\}", _sub, texte)
    return texte_protege, blocs


def restaurer_glsadd(texte, blocs):
    def _sub(m):
        idx = int(m.group(1))
        return blocs[idx] if 0 <= idx < len(blocs) else m.group(0)

    return re.sub(r"\x00(\d+)\x00", _sub, texte)


def masquer_math(texte):
    return re.sub(r"\$[^$]*\$", lambda m: " " * len(m.group(0)), texte)


def masquer_latex(texte):
    """Masque les commandes LaTeX avec accolades (\\text{...}, \\mathrm{...}, etc.)
    pour éviter d'insérer des \\glsadd à l'intérieur."""
    return re.sub(
        r'\\(?:text|mathrm|mathbf|mathit|mathcal|mathbb|operatorname|gls|glspl|Gls|Glspl|emph|textbf|textit)\{[^{}]*\}',
        lambda m: " " * len(m.group(0)),
        texte
    )


def corriger_imbrications(lignes):
    pattern = re.compile(r"\\glsadd\{([^{}]*)\\glsadd\{([^{}]*)\}([^{}]*)\}")
    corrections = 0
    for i in range(len(lignes)):
        while True:
            m = pattern.search(lignes[i])
            if not m:
                break
            avant, cle_interne, apres = m.group(1), m.group(2), m.group(3)
            remplacement = f"\\glsadd{{{cle_interne}}}\\glsadd{{{avant}{apres}}}"
            lignes[i] = lignes[i][:m.start()] + remplacement + lignes[i][m.end():]
            corrections += 1
    return corrections


# ---------------------------------------------------------------------------
# Insertion (version accélérée : boucle lignes → termes + pré-filtre substring)
# ---------------------------------------------------------------------------

def inserer_dans_texte(fichier_entree, fichier_sortie, termes):
    if not os.path.exists(fichier_entree):
        print(f"⚠️  Fichier non trouvé : {fichier_entree}")
        return

    with open(fichier_entree, 'r', encoding='utf-8') as f:
        lignes = f.readlines()

    # Protection YAML
    yaml_header = ""
    if lignes and lignes[0].strip() == '---':
        idx = 0
        yaml_header += lignes[0]
        for i in range(1, len(lignes)):
            yaml_header += lignes[i]
            if lignes[i].strip() == '---':
                idx = i + 1
                break
        lignes = lignes[idx:]

    lignes_originales = list(lignes)

    # Masque tableau
    masque_tableau = [False] * len(lignes)
    dans_tableau = False
    for i, ligne in enumerate(lignes):
        if re.search(r'\\begin\{' + ENV_TABLEAU + r'\}', ligne):
            dans_tableau = True
        if re.search(r'\\end\{' + ENV_TABLEAU + r'\}', ligne):
            dans_tableau = False
        masque_tableau[i] = dans_tableau

    # Masque code (```...```)
    masque_code = [False] * len(lignes)
    dans_code = False
    for i, ligne in enumerate(lignes):
        if ligne.strip().startswith('```'):
            dans_code = not dans_code
        masque_code[i] = dans_code

    # Préparation des termes (patterns + pré-filtres)
    termes_prepares = []
    for mot_cherche, cle_inserer in termes:
        # Liste noire
        if cle_inserer in TERMES_EXCLUS or mot_cherche.lower() in TERMES_EXCLUS:
            continue

        is_cjk = bool(re.search(r'[\u4e00-\u9fff]', mot_cherche))
        if not is_cjk and len(mot_cherche) < 3:
            continue
        if is_cjk and len(mot_cherche) < 2:
            continue

        mot_a_chercher = mot_cherche.replace('!', ' ')
        cle_a_inserer = cle_inserer

        variantes = [mot_a_chercher]
        if mot_a_chercher.endswith('al'):
            variantes.append(mot_a_chercher[:-2] + 'aux')
        if mot_a_chercher.endswith('el'):
            variantes.append(mot_a_chercher[:-2] + 'elle')
        if mot_a_chercher.endswith('et'):
            variantes.append(mot_a_chercher + 'te')
        if mot_a_chercher.endswith('er'):
            variantes.append(mot_a_chercher[:-2] + 'ère')
        if mot_a_chercher.endswith('eux'):
            variantes.append(mot_a_chercher[:-3] + 'euse')
        if mot_a_chercher.endswith('f'):
            variantes.append(mot_a_chercher[:-1] + 've')

        alternatives_echappees = []
        for v in variantes:
            v_echappe = re.escape(v)
            v_echappe = v_echappe.replace(r'\ ', r'\s+')
            alternatives_echappees.append(v_echappe)
        alternatives = '|'.join(alternatives_echappees)

        # Pattern avec lookbehinds négatifs étendus
        pattern = re.compile(
            r'(?<![a-zA-Z0-9_])'
            r'(?<!\\glsadd\{)(?<!\\index\{)(?<!\\ref\{)(?<!\\label\{)'
            r'(?<!\\text\{)(?<!\\mathrm\{)(?<!\\mathbf\{)(?<!\\mathit\{)'
            r'(?<!\\mathcal\{)(?<!\\mathbb\{)(?<!\\operatorname\{)'
            r'(' + alternatives + r')'
            r'(?:e|elle|es|s)?'
            r'(?![a-zA-Z0-9_])'
            r'(?!\s*\\protect\\glsadd|\s*\\glsadd)',
            re.IGNORECASE
        )

        mot_lower = mot_a_chercher.lower()
        termes_prepares.append((pattern, cle_a_inserer, mot_lower, mot_cherche))

    trouve_par_terme = {t[3]: False for t in termes_prepares}

    # Boucle LIGNES en premier
    for i, ligne in enumerate(lignes):
        if masque_tableau[i] or masque_code[i]:
            continue

        est_titre = (
            bool(re.match(r'^\s*#+\s', ligne)) or
            bool(re.match(
                r'^\s*\\(part|chapter|section|subsection|subsubsection|paragraph|subparagraph)\*?\{',
                ligne
            ))
        )

        if est_titre:
            continue

        # Filtres existants
        if re.match(r'^\s*#+\s*[\d\.]+\s*$', ligne):
            continue
        if re.match(r'^\s*%', ligne):
            continue
        if re.match(r'^\s*\\(small|footnotesize|scriptsize|setlength|renewcommand|arraystretch)', ligne):
            continue
        if re.match(r'^\s*\\(section|subsection|subsubsection|chapter|part|begin|end|maketitle|tableofcontents|appendix|label|centering)', ligne):
            continue
        if any(ext in ligne for ext in ['.py', '.csv', '.png', '.jpg', '.pdf', '.tex', '.bib']):
            continue
        if re.match(r'^\s*[\$\|=&]', ligne.strip()):
            continue
        if ligne.strip().startswith('[') or ligne.strip().startswith(']'):
            continue

        ligne_protegee, blocs_glsadd = proteger_glsadd_existants(ligne)

        # Masquer les citations par des espaces (CONSERVER la longueur
        # pour que les offsets de ligne_recherche restent alignés sur nouvelle_ligne_p)
        ligne_sans_citations = re.sub(r'\[@[^\]]+\]', lambda m: ' ' * len(m.group(0)), ligne_protegee)
        ligne_sans_citations = re.sub(r'@\w+', lambda m: ' ' * len(m.group(0)), ligne_sans_citations)
        ligne_sans_citations = re.sub(r'\\cite\{[^}]+\}', lambda m: ' ' * len(m.group(0)), ligne_sans_citations)

        ligne_recherche = masquer_latex(masquer_math(ligne_sans_citations))
        ligne_recherche_lower = ligne_recherche.lower()
        ligne_protegee_lower = ligne_protegee.lower()          # NOUVEAU

        nouvelle_ligne_p = ligne_protegee
        modifiee = False

 
        # Phase 1a : collecter les insertions pour les termes NORMAUX
        insertions = []
        suffixe = '\\protect\\glsadd' if est_titre else '\\glsadd'

        for pattern, cle_a_inserer, mot_lower, mot_origine in termes_prepares:
            if '$' in mot_origine:
                continue  # termes LaTeX traités en phase 2
            if mot_lower not in ligne_recherche_lower:
                continue
            for m in pattern.finditer(ligne_recherche):
                insertions.append((m.end(), f'{suffixe}{{{cle_a_inserer}}}', mot_origine))

        # Phase 1b : appliquer les insertions normales (droite → gauche)
        if insertions:
            for pos, ins, mot_origine in sorted(insertions, key=lambda x: x[0], reverse=True):
                nouvelle_ligne_p = nouvelle_ligne_p[:pos] + ins + nouvelle_ligne_p[pos:]
                trouve_par_terme[mot_origine] = True
            modifiee = True

        # Phase 2 : termes LaTeX (sub direct sur nouvelle_ligne_p)
        for pattern, cle_a_inserer, mot_lower, mot_origine in termes_prepares:
            if '$' not in mot_origine:
                continue
            if mot_lower not in ligne_protegee_lower:
                continue
            if mot_origine.count('$') % 2 != 0:
                continue
            avant = nouvelle_ligne_p.count(f'\\glsadd{{{cle_a_inserer}}}')
            def repl_latex(m, _cle=cle_a_inserer, _suf=suffixe):
                return m.group(0) + f'{_suf}{{{_cle}}}'
            nouvelle_ligne_p = pattern.sub(repl_latex, nouvelle_ligne_p)
            count = nouvelle_ligne_p.count(f'\\glsadd{{{cle_a_inserer}}}') - avant
            if count > 0:
                modifiee = True
                trouve_par_terme[mot_origine] = True

        if modifiee:
            lignes[i] = restaurer_glsadd(nouvelle_ligne_p, blocs_glsadd)

    termes_non_trouves = [t for t, found in trouve_par_terme.items() if not found]

    # Diagnostic (inchangé)
    print(f"\n📊 Diagnostic des {len(termes_non_trouves)} termes non trouvés...")
    # Diagnostic (inchangé)
    print(f"\n📊 Diagnostic des {len(termes_non_trouves)} termes non trouvés...")
    if termes_non_trouves:
        motifs = [re.escape(t.replace('!', ' ')) for t in termes_non_trouves]
        motif_global = re.compile('(' + '|'.join(motifs) + ')', re.IGNORECASE)
        diagnostic = {t: [] for t in termes_non_trouves}

        for i, ligne in enumerate(lignes_originales):
            if masque_tableau[i]:
                categorie = "TABLEAU"
            elif masque_code[i]:
                categorie = "CODE"
            elif re.match(r'^\s*\\', ligne):
                categorie = "COMMANDE LATEX"
            elif re.match(r'^\s*%', ligne):
                categorie = "COMMENTAIRE"
            elif '\\cite{' in ligne or re.search(r'@\w+', ligne):
                categorie = "CITATION"
            elif '$' in ligne:
                categorie = "FORMULE"
            elif ligne.strip().startswith('[') or ligne.strip().startswith(']'):
                categorie = "RÉFÉRENCE"
            elif any(ext in ligne for ext in ['.py', '.csv', '.png', '.jpg', '.pdf', '.tex', '.bib']):
                categorie = "FICHIER"
            else:
                categorie = "TEXTE NARRATIF"

            for match in motif_global.finditer(ligne):
                terme_trouve = match.group(1)
                for t in termes_non_trouves:
                    if t.replace('!', ' ').lower() == terme_trouve.lower():
                        diagnostic[t].append(f"ligne {i+1} ({categorie})")
                        break

        with open(FICHIER_LOG_NON_TROUVES, 'w', encoding='utf-8') as f:
            f.write("# Diagnostic des termes non trouvés\n")
            f.write("# Format : terme : ligne N (catégorie), ligne M (catégorie), ...\n")
            for terme in termes_non_trouves:
                occurrences = diagnostic[terme]
                if occurrences:
                    f.write(f"{terme} : {', '.join(occurrences)}\n")
                else:
                    f.write(f"{terme} : ABSENT DU TEXTE\n")
    else:
        with open(FICHIER_LOG_NON_TROUVES, 'w', encoding='utf-8') as f:
            f.write("# Aucun terme non trouvé.\n")

    print(f"📝 Termes non trouvés : {len(termes_non_trouves)} (voir {FICHIER_LOG_NON_TROUVES})")

    texte_final = yaml_header + "".join(lignes)
    with open(fichier_sortie, 'w', encoding='utf-8') as f:
        f.write(texte_final)
    print(f"\n✅ Fichier indexé généré : {fichier_sortie}")


def main():
    print("=== 1. Génération de mots_cles.bib ===")
    print("⚠️  Génération automatique DÉSACTIVÉE.")
    print("   Le fichier bib/mots_cles.bib est maintenant manuel.")
    print("   Éditez-le directement pour ajouter/retirer des termes.\n")

    if not os.path.exists(FICHIER_MOTS_CLES_BIB):
        print(f"⚠️  Fichier non trouvé : {FICHIER_MOTS_CLES_BIB}")
        print("   Créez-le manuellement avec les termes utiles.")

    print("=== 2. Extraction des termes d'index (dédupliqués) ===")
    termes_index = extraire_termes_index(FICHIERS_BIB_INDEX)
    print(f"Trouvé {len(termes_index)} termes d'index (après déduplication).\n")

    print("=== 3. Insertion automatique des \\glsadd{} ===")
    termes_index = sorted(termes_index, key=lambda x: len(x[0]), reverse=True)
    inserer_dans_texte(FICHIER_SOURCE, FICHIER_INDEXE, termes_index)

if __name__ == '__main__':
    main()
