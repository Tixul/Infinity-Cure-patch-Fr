"""Contrôle d'une traduction contre le japonais de VOTRE ROM.

    python tools/controle.py --rom "Infinity Cure (Japan).ngc" [--lang fr]

Pour chaque ligne de lang/<code>/*.tsv : adresse connue, mêmes ▼ ▽ ◇ ◆ que le japonais (nombre et
ordre), structure `Nom「…」` présente si et seulement si le japonais en a une, nom de locuteur connu et
cohérent avec le japonais (un décalage de lignes se voit tout de suite), caractères de la police,
mise en page possible, choix de menu ≤ 142 px. Liste aussi les textes japonais sans traduction.
"""
import os, re, sys, glob
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import mise, extrait   # noqa: E402
PROJET = os.path.dirname(ICI)

# Noms de locuteurs admis (ligne du nom, au-dessus de la réplique) — à adapter pour une autre langue.
NOMS = {'Makoto', 'Yuka', 'Izumi', 'Kurumi', 'Saki', 'Haruka', 'Okuhiko', '???', 'Garçon', 'Fillette',
        'Gamin', 'Tous', 'Voix', 'Senpai', 'Aînée', 'Aîné', 'Vendeur', 'Vendeuse', 'Femme', 'Chauffeur',
        'Père', 'Sœurs Morino'}
CORR = {'誠': 'Makoto', '優夏': 'Yuka', 'いづみ': 'Izumi', 'くるみ': 'Kurumi', '沙紀': 'Saki', '遙': 'Haruka',
        '億彦': 'Okuhiko', '？？': '???'}


def codes(s):
    return re.sub(r'[^▼▽◇◆]', '', s)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    a = sys.argv
    if '--rom' not in a:
        raise SystemExit(__doc__)
    code = a[a.index('--lang') + 1] if '--lang' in a else 'fr'
    jp = {x[0]: (x[1], x[3]) for x in extrait.lignes(open(a[a.index('--rom') + 1], 'rb').read())}
    err, fr = [], {}
    for fn in sorted(glob.glob(os.path.join(PROJET, 'lang', code, '*.tsv'))):
        for k, l in enumerate(open(fn, encoding='utf-8'), 1):
            l = l.rstrip('\r\n')
            if not l or l.startswith('#'):
                continue
            c = l.split('\t')
            ad = c[0].upper()
            ou = '%s:%d %s' % (os.path.basename(fn), k, ad)
            if ad not in jp:
                err.append('%s adresse inconnue' % ou)
                continue
            f = c[-1]
            fr[ad] = f
            t, j = jp[ad]
            if codes(f) != codes(j):
                err.append('%s codes %s ≠ %s (japonais) : %s' % (ou, codes(f), codes(j), f))
            nj = re.match(r'^([^「」]{1,8})「', j)
            nf = re.match(r'^([^「」]{1,16})「', f)
            if bool(nj) != bool(nf):
                err.append('%s structure Nom「 : %s' % (ou, f))
            elif nf and nf.group(1) not in NOMS:
                err.append('%s nom inconnu %r' % (ou, nf.group(1)))
            elif nf and nj.group(1) in CORR and CORR[nj.group(1)] != nf.group(1):
                err.append('%s locuteur %s ≠ %s (décalage ?)' % (ou, nj.group(1), nf.group(1)))
            if f.count('「') > (1 if nf else 0):
                err.append('%s 「 en trop : %s' % (ou, f))
            try:
                mise.encode_choix(f) if t == 'S' else mise.encode(f, 0)
            except mise.Erreur as e:
                err.append('%s %s' % (ou, e))
    # textes sans traduction (un doublon d'un texte traduit est couvert automatiquement)
    trad = {(jp[ad][0], jp[ad][1]) for ad in fr}
    manque = [ad for ad, (t, j) in jp.items() if ad not in fr and (t, j) not in trad]
    for e in err[:200]:
        print(e)
    print('%d ligne(s), %d erreur(s), %d texte(s) japonais sans traduction' % (len(fr), len(err), len(manque)))
    if manque:
        print('  ex. :', ' '.join(manque[:10]))
    sys.exit(1 if err else 0)


if __name__ == '__main__':
    main()
