#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_bib.py — détecte les erreurs de syntaxe qui font échouer bib2gls,
notamment :  Error: Syntax error parsing @entry (X):
             fichier.bib:L: '}' immediately follows field name

Vérifie, pour chaque @entry / @index / @symbol / @abbreviation :
  1. un nom de champ immédiatement suivi de '}'  (pas de '=' ni de valeur)
  2. un nom de champ suivi de ',' sans '=' ni valeur
  3. un nom de champ suivi de '{' sans '=' (ex. description{...})
  4. des accolades déséquilibrées (entrée jamais fermée)

Usage :
  python3 check_bib.py bib/glossaire_v2_zh.bib bib/notations_zh.bib bib/mots_cles_zh.bib
"""
import re
import sys

IDENT = re.compile(r'[A-Za-z_][A-Za-z0-9_.+-]*')
HEAD = re.compile(r'@(\w+)\s*\{\s*([^,\s{}"]+)\s*,')


def check(path):
    try:
        text = open(path, encoding='utf-8-sig').read()
    except FileNotFoundError:
        return [(path, 0, "FICHIER INTROUVABLE")]
    except UnicodeDecodeError:
        return [(path, 0, "n'est pas de l'UTF-8 valide : vérifier l'encodage")], "encodage non UTF-8", 0

    # pré-calcul : offset -> numéro de ligne (1-based)
    line_of = [0]
    for ch in text:
        line_of.append(line_of[-1] + (1 if ch == '\n' else 0))
    lineno = lambda pos: line_of[pos] + 1

    problems = []
    n_ok = 0
    for m in HEAD.finditer(text):
        etype, key = m.group(1).lower(), m.group(2)
        if etype in ('string', 'comment', 'preamble'):
            continue
        entry_errs = []
        n = len(text)
        depth = 1
        i = m.end()
        while i < n and depth > 0:
            ch = text[i]
            if ch == '{':
                depth += 1
                i += 1
            elif ch == '}':
                depth -= 1
                i += 1
                if depth == 0:
                    break
            elif ch == '"' and depth >= 1:
                i += 1
                while i < n and text[i] != '"':
                    i += 1
                i += 1
            elif depth == 1 and ((ch.isalpha() and ch.isascii()) or ch == '_'):
                ident = IDENT.match(text[i:]).group(0)
                k = i + len(ident)
                while k < n and text[k] in ' \t\r\n':
                    k += 1
                nxt = text[k] if k < n else ''
                if nxt == '=':                       # champ normal : sauter la valeur
                    k += 1
                    while k < n and text[k] in ' \t\r\n':
                        k += 1
                    if k < n and text[k] == '{':
                        d = 0
                        while k < n:
                            if text[k] == '{':
                                d += 1
                            elif text[k] == '}':
                                d -= 1
                                if d == 0:
                                    break
                            k += 1
                        k += 1
                    elif k < n and text[k] == '"':
                        k += 1
                        while k < n and text[k] != '"':
                            k += 1
                        k += 1
                    else:                            # valeur « nue » : jusqu'à , ou }
                        while k < n and text[k] not in ',}':
                            k += 1
                    i = k
                elif nxt == '}':
                    entry_errs.append((lineno(i),
                        f"« {ident} » est suivi de '}}' sans '=' ni valeur "
                        f"→ écrire {ident} = {{...}} ou supprimer la ligne"))
                    i = k
                elif nxt == ',':
                    entry_errs.append((lineno(i),
                        f"« {ident} » n'a ni '=' ni valeur "
                        f"→ écrire {ident} = {{...}} ou supprimer la ligne"))
                    i = k + 1
                elif nxt == '{':
                    entry_errs.append((lineno(i),
                        f"« {ident}{{...}} » : il manque le '=' entre le nom "
                        f"du champ et sa valeur"))
                    i = k
                else:
                    entry_errs.append((lineno(i),
                        f"caractère inattendu ({nxt!r}) après le nom de champ « {ident} »"))
                    i = k
            else:
                i += 1
        if depth > 0:
            entry_errs.append((lineno(m.start()),
                "accolades déséquilibrées : cette entrée n'est jamais fermée "
                "(une '{' manque probablement dans une valeur au-dessus)"))
        if entry_errs:
            for ln, msg in entry_errs:
                problems.append((path, ln, f"@{etype} ({key}): {msg}"))
        else:
            n_ok += 1

    summary = (f"{n_ok} entrée(s) OK, {len(problems)} erreur(s)" if problems
               else f"{n_ok} entrée(s) analysée(s) sans erreur")
    return problems, summary, n_ok


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python3 check_bib.py fichier.bib [autres.bib ...]")
        sys.exit(2)
    total = 0
    for p in args:
        res = check(p)
        if len(res) == 3:
            problems, summary, _ = res
        else:
            problems, summary = res[:2], "fichier non analysé"
        print(f"=== {p} : {summary}")
        for path, ln, msg in problems:
            print(f"  {path}:{ln}: {msg}")
        total += len(problems)
    print(f"\n{'>>> ' + str(total) + ' erreur(s) à corriger.' if total
          else '>>> Aucun problème de syntaxe détecté.'}")


if __name__ == '__main__':
    main()
