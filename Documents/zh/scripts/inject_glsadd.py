#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
inject_glsadd.py — numéros de page pour l'index des mots-clés (关键词索引).

Pourquoi : bib2gls n'affiche un numéro de page que pour les entrées qui ont
été « enregistrées » dans le document (\gls, \glsadd... écrit des records
dans le .aux). Les index notations et concepts ont des pages car leurs
entrées sont référencées dans le texte ; les mots-clés ne le sont jamais
(selection={all} les affiche, mais sans localisation). Remède : injecter
\glsadd{cle} — commande SILENCIEUSE (n'affiche rien dans le PDF) — devant
chaque occurrence du terme dans le Markdown, avant l'appel à pandoc.

Fonctionnement :
  * lit le .bib de mots-clés (@entry/@index/@symbol/@abbreviation/@number),
    champ name (ou short/long/text), convertit la valeur LaTeX en texte brut ;
  * cherche la forme PLEINE du nom ET sa forme NUE : « 天命（Tianming） »
    matche aussi « 天命 », « GEP（生态系统生产总值） » matche aussi « GEP » ;
  * saute : YAML front matter, blocs de code clôturés, code en ligne,
    titres Markdown (# ...) — pour ne pas polluer la table des matières ni
    les signets PDF — et lignes LaTeX brutes commençant par « \ » ;
  * terme le plus long d'abord, sans chevauchement (« 土地财政 » enregistre
    土地 ET 财政 ; « 经济 » à l'intérieur de « 天道经济 » est évité si
    天道经济 est aussi un mot-clé) ;
  * ne touche à aucun \glsadd{...} existant : si un \glsadd{cle-de-mot-cle}
    précède déjà directement le terme, l'occurrence est laissée telle quelle
    (le script est donc idempotent, ré-exécutable sans doubler) ;
  * termes ASCII : frontières de mots (« GEP » ne matche pas dans « GEPs »).

Usage :
  # aperçu — ne modifie rien, affiche le rapport complet
  python3 inject_glsadd.py --bib bib/mots_cles_zh.bib --report rapport.md

  # injection sur COPIE (le .md source reste intact) — mode utilisé par le
  # script de build :
  python3 inject_glsadd.py --bib bib/mots_cles_zh.bib --output _injection.md rapport.md

  # injection en place (crée rapport.md.bak)
  python3 inject_glsadd.py --bib bib/mots_cles_zh.bib rapport.md

  # option : marquer seulement la première occurrence de chaque terme
  python3 inject_glsadd.py --bib bib/mots_cles_zh.bib --first-only rapport.md
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

ENTRY_TYPES = r'(?:entry|index|symbol|abbreviation|number)'
FENCE_RE = re.compile(r'^ {0,3}(```|~~~)')
HEADING_RE = re.compile(r'^ {0,3}#{1,6}(\s|$)')
SETTEXT_RE = re.compile(r'^ {0,3}(={3,}|-{3,})\s*$')
LATEXLINE_RE = re.compile(r'^\s*\\')
PARENS_TRAIL_RE = re.compile(r'[（(][^（）()]*[）)]\s*$')


def extract_braced(s, i):
    """s[i] doit être '{'. Renvoie (contenu, indice juste après '}')."""
    depth = 0
    for j in range(i, len(s)):
        c = s[j]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
    raise ValueError('accolade non fermée')


def latex_to_plain(t):
    """Approximation LaTeX -> texte brut (suffisante pour des noms simples)."""
    t = re.sub(r'(?<!\\)%[^\n]*', '', t)
    t = re.sub(r'\\[A-Za-z@]+\*?(\[[^\]\n]*\])?', ' ', t)
    t = t.replace('\\\\', ' ')
    t = t.replace('\\{', '\x01').replace('\\}', '\x02')
    t = t.replace('{', '').replace('}', '')
    t = t.replace('\x01', '{').replace('\x02', '}')
    t = t.replace('~', ' ').replace('$', '')
    return re.sub(r'\s+', ' ', t).strip()


def field_value(body, name):
    """Valeur du champ `name` dans le corps d'une entrée .bib."""
    m = re.search(r'(?<![A-Za-z@])' + name + r'\s*=\s*', body)
    if not m:
        return None
    i = m.end()
    n = len(body)
    while i < n and body[i] in ' \t\r\n':
        i += 1
    if i >= n:
        return None
    c = body[i]
    if c == '{':
        try:
            val, _ = extract_braced(body, i)
        except ValueError:
            return None
        return val
    if c == '"':
        j = body.find('"', i + 1)
        return body[i + 1:] if j == -1 else body[i + 1:j]
    j = i
    while j < n and body[j] not in ',\r\n':
        j += 1
    return body[i:j]


def parse_bib(path):
    """Renvoie ([(terme_ou_variante, clé)], avertissements)."""
    text = Path(path).read_text(encoding='utf-8-sig')
    pairs, seen, warns = [], set(), []
    for m in re.finditer(r'@\s*' + ENTRY_TYPES + r'\s*\{', text):
        try:
            body, _ = extract_braced(text, m.end() - 1)
        except ValueError as exc:
            warns.append('entrée illisible (%s)' % exc)
            continue
        key = body.split(',', 1)[0].strip()
        if not key:
            warns.append('entrée sans clé — ignorée')
            continue
        if key in seen:
            warns.append('clé en double dans le .bib : %s (ignorée)' % key)
            continue
        seen.add(key)
        term = ''
        for f in ('name', 'short', 'long', 'text'):
            v = field_value(body, f)
            if v:
                v = re.sub(r'^\[[^\]\n]*\]\s*', '', v)  # name={[tri]{affichage}}
                term = latex_to_plain(v)
                if term:
                    break
        if not term:
            warns.append('aucun nom exploitable pour : %s' % key)
            continue
        pairs.append((term, key))
        # variante NUE : « 天命（Tianming） » -> chercher aussi « 天命 »
        bare = PARENS_TRAIL_RE.sub('', term).strip()
        if bare and bare != term and len(bare) >= 2:
            pairs.append((bare, key))
    return pairs, warns


def compile_items(pairs):
    """Termes triés du plus long au plus court ; frontières pour l'ASCII."""
    term_map = {}
    for term, key in pairs:
        term_map.setdefault(term, []).append(key)
    items = []
    for term, keys in sorted(term_map.items(), key=lambda kv: -len(kv[0])):
        esc = re.escape(term)
        if re.match(r'^[A-Za-z0-9]', term) and re.search(r'[A-Za-z0-9]$', term):
            pat = re.compile('(?<![A-Za-z0-9])' + esc + '(?![A-Za-z0-9])')
        else:
            pat = re.compile(esc)
        items.append((pat, term, keys))
    return items, term_map


def inside_command_arg(seg, pos):
    """True si pos semble être à l'intérieur d'un argument \\commande{...}."""
    back = seg[max(0, pos - 80):pos]
    return re.search(r'\\[A-Za-z@]+\*?\s*\{[^{}]*\Z', back) is not None


def inject_segment(seg, items, marked_re, first_only, st):
    """Injecte \\glsadd{cle} devant les occurrences du segment (hors code)."""
    if not seg:
        return seg
    spans, hits = [], []
    for pat, term, keys in items:
        for m in pat.finditer(seg):
            a, b = m.span()
            if any(a < e and s < b for (s, e) in spans):
                st['overlap'] += 1
                continue
            if marked_re.search(seg[max(0, a - 60):a]):
                st['already'] += 1
                spans.append((a, b))
                continue
            if inside_command_arg(seg, a):
                st['guard'] += 1
                continue
            spans.append((a, b))
            hits.append((a, b, term, keys))
            if first_only:
                break
    if not hits:
        return seg
    hits.sort(key=lambda h: h[0])
    parts, last = [], 0
    for a, b, term, keys in hits:
        parts.append(seg[last:a])
        parts.append('\\glsadd{' + keys[0] + '}')
        parts.append(seg[a:b])
        last = b
        st['inj'] += 1
        st['per'][term] = st['per'].get(term, 0) + 1
    parts.append(seg[last:])
    return ''.join(parts)


def count_skipped(seg, items, st):
    """Compte (approximativement) les occurrences d'une zone ignorée."""
    for pat, term, keys in items:
        c = len(pat.findall(seg))
        if c:
            st['sk_per'][term] = st['sk_per'].get(term, 0) + c
            st['skipped'] += c


def process_file(path, items, marked_re, first_only):
    """Renvoie (texte_injecte, stats) sans écrire sur disque."""
    text = path.read_text(encoding='utf-8-sig')
    lines = text.split('\n')
    st = {'inj': 0, 'per': {}, 'skipped': 0, 'sk_per': {},
          'already': 0, 'overlap': 0, 'guard': 0,
          'n_heading': 0, 'n_latex': 0, 'yaml_unclosed': False}
    out = []
    in_fence = False
    in_yaml = bool(lines) and lines[0].strip() == '---'
    i = 0
    while i < len(lines):
        line = lines[i]
        if in_yaml:
            out.append(line)
            if i > 0 and line.strip() in ('---', '...'):
                in_yaml = False
            i += 1
            continue
        if FENCE_RE.match(line):
            in_fence = not in_fence
            out.append(line)
            i += 1
            continue
        if in_fence:
            count_skipped(line, items, st)
            out.append(line)
            i += 1
            continue
        if HEADING_RE.match(line):
            count_skipped(line, items, st)
            st['n_heading'] += 1
            out.append(line)
            i += 1
            continue
        if i + 1 < len(lines) and line.strip() and SETTEXT_RE.match(lines[i + 1]):
            count_skipped(line, items, st)
            st['n_heading'] += 1
            out.append(line)
            out.append(lines[i + 1])
            i += 2
            continue
        if LATEXLINE_RE.match(line):
            count_skipped(line, items, st)
            st['n_latex'] += 1
            out.append(line)
            i += 1
            continue
        parts = line.split('`')
        new_parts = []
        for k, seg in enumerate(parts):
            if k % 2 == 1:
                count_skipped(seg, items, st)
                new_parts.append(seg)
            else:
                new_parts.append(inject_segment(seg, items, marked_re,
                                                first_only, st))
        out.append('`'.join(new_parts))
        i += 1
    if in_yaml:
        st['yaml_unclosed'] = True
    return '\n'.join(out), st


def main():
    ap = argparse.ArgumentParser(
        description="Injecte \\glsadd{cle} dans un Markdown pour donner des "
                    "numéros de page à l'index des mots-clés bib2gls.")
    ap.add_argument('--bib', required=True,
                    help='.bib de mots-clés (ex. bib/mots_cles_zh.bib)')
    ap.add_argument('--report', action='store_true',
                    help='aperçu : ne modifie et n\'écrit aucun fichier')
    ap.add_argument('--first-only', action='store_true',
                    help='marquer seulement la première occurrence de chaque terme')
    ap.add_argument('--output', metavar='FICHIER',
                    help='écrire le résultat dans FICHIER au lieu de modifier '
                         'les fichiers en place (un seul fichier en entrée)')
    ap.add_argument('--prefix', default='',
                    help='préfixe des clés injectées, ex. kw- si la ressource '
                         'bib2gls utilise label-prefix={kw-}')
    ap.add_argument('files', nargs='+', help='fichiers Markdown à traiter')
    args = ap.parse_args()

    if args.output and len(args.files) != 1:
        sys.exit('>>> --output exige un seul fichier en entrée.')

    bib = Path(args.bib)
    if not bib.exists():
        sys.exit('>>> .bib introuvable : %s' % bib)
    pairs, warns = parse_bib(bib)
    if not pairs:
        sys.exit('>>> aucune entrée exploitable dans %s' % bib)
    items, term_map = compile_items(pairs)
    keys_all = sorted({args.prefix + k for _, k in pairs}, key=len, reverse=True)
    marked_re = re.compile(
        r'\\glsadd\s*\{\s*(?:' + '|'.join(re.escape(k) for k in keys_all)
        + r')\s*\}\s*$')

    for w in warns:
        print('[!] ' + w, file=sys.stderr)

    results = []
    g_per, g_sk_per = {}, {}
    tot = {'inj': 0, 'skipped': 0, 'already': 0, 'overlap': 0, 'guard': 0}
    for fp in args.files:
        p = Path(fp)
        if not p.exists():
            sys.exit('>>> fichier introuvable : %s' % p)
        new_text, st = process_file(p, items, marked_re, args.first_only)
        results.append((p, new_text, st))
        for t, n in st['per'].items():
            g_per[t] = g_per.get(t, 0) + n
        for t, n in st['sk_per'].items():
            g_sk_per[t] = g_sk_per.get(t, 0) + n
        for k in tot:
            tot[k] += st[k]
        if args.report:
            continue
        if args.output:
            Path(args.output).write_text(new_text, encoding='utf-8')
        else:
            bak = p.with_name(p.name + '.bak')
            shutil.copy2(p, bak)
            p.write_text(new_text, encoding='utf-8')

    # ---------------- rapport ----------------
    print('=== inject_glsadd — rapport ===')
    for p, _txt, st in results:
        if args.report:
            action = 'APERÇU — aucun fichier modifié'
        elif args.output:
            action = 'écrit -> %s' % args.output
        else:
            action = 'écrit -> %s (+ %s.bak)' % (p, p)
        print('--- %s : %d injection(s) [%s]' % (p, st['inj'], action))
        if st['already']:
            print('    déjà marquées \\glsadd      : %d' % st['already'])
        if st['overlap']:
            print('    chevauchements évités      : %d' % st['overlap'])
        if st['guard']:
            print('    garde \\commande{...}       : %d' % st['guard'])
        if st['skipped']:
            print('    ignorés (titres %d, lignes LaTeX brutes %d, code) : '
                  '%d occurrence(s)' % (st['n_heading'], st['n_latex'],
                                        st['skipped']))
        if st['yaml_unclosed']:
            print('    [!] front matter YAML jamais refermé — fichier entier ignoré')
    dupes = {t: ks for t, ks in term_map.items() if len(ks) > 1}
    if dupes:
        print('--- doublons de terme (1re clé retenue) :')
        for t, ks in sorted(dupes.items()):
            print('    %s -> %s' % (t, ', '.join(ks)))
    print('--- injections par terme :')
    if g_per:
        for t, n in sorted(g_per.items(), key=lambda kv: (-kv[1], kv[0])):
            print('    %s (%s) : %d' % (t, term_map[t][0], n))
    else:
        print('    (aucune occurrence trouvée dans les fichiers passés)')
    injected_keys = {term_map[t][0] for t in g_per}
    zero = [t for t in term_map
            if t not in g_per and not ({k for k in term_map[t]} & injected_keys)]
    if zero:
        print("--- termes jamais trouvés dans le texte (%d) — candidats à "
              "l'élagage, ou occurrences uniquement dans titres/code :" % len(zero))
        line = '    '
        for t in sorted(zero):
            tag = ' [titres/code : %d]' % g_sk_per[t] if g_sk_per.get(t) else ''
            item = '%s(%s)%s' % (t, term_map[t][0], tag)
            if len(line) + len(item) > 78:
                print(line.rstrip())
                line = '    '
            line += item + '  '
        print(line.rstrip())
    if tot['inj'] and not args.report:
        print('>>> %d injection(s) au total. Relancez ensuite le build complet.'
              % tot['inj'])


if __name__ == '__main__':
    main()
