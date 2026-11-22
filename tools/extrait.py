"""Extraction du texte japonais depuis VOTRE ROM d'Infinity Cure (il n'est pas distribué).

    python tools/extrait.py "Infinity Cure (Japan).ngc" [out/jp.tsv]

Une ligne par texte : adresse CPU (hex) · type (M = réplique, S = choix de menu) · numéro · texte
lisible (⏎ ligne, ▼ attente + page, ▽ attente + ligne, ◇ attente, ◆ page).

M : `0E 00 id16 texte 00` suivi d'un opcode < 0x2D, à partir de 0x6E000, sans chevauchement
(numéros continus : 17 507 répliques). S : `11 07 n16` + n textes (59 menus, 160 choix).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from texte import dico, developpe, lisible

DEBUT, FIN = 0x6E000, 0xFA000


def mes(d, D):
    r, fin = [], 0
    for i in range(DEBUT, FIN):
        if d[i] == 0x0E and d[i + 1] == 0 and i >= fin:
            try:
                s, e = developpe(d, i + 4, D)
            except ValueError:
                continue
            if e > i + 4 and d[e + 1] < 0x2D:
                r.append((0x200000 + i + 4, 'M', str(d[i + 2] | d[i + 3] << 8), s))
                fin = e
    return r


def selects(d, D):
    r, ns = [], 0
    for i in range(DEBUT, FIN):
        if d[i] != 0x11 or d[i + 1] != 7:
            continue
        n = d[i + 2] | d[i + 3] << 8
        if not 1 <= n <= 8:
            continue
        j, L = i + 4, []
        try:
            for k in range(n):
                s, e = developpe(d, j, D)
                if e == j:
                    raise ValueError
                L.append((0x200000 + j, 'S', '%d.%d' % (ns, k), s))
                j = e + 1
        except ValueError:
            continue
        r += L
        ns += 1
    return r


def textes(d):
    """ROM japonaise (octets) -> [(adresse CPU, type, numéro, texte SJIS développé)] triée."""
    D = dico(d)
    return sorted(mes(d, D) + selects(d, D))


def lignes(d):
    """-> [(adresse hex, type, numéro, texte lisible)] (comme out/jp.tsv)."""
    return [('%06X' % a, t, n, lisible(s)) for a, t, n, s in textes(d)]


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    d = open(sys.argv[1], 'rb').read()
    sortie = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), 'out', 'jp.tsv')
    os.makedirs(os.path.dirname(sortie), exist_ok=True)
    L = lignes(d)
    with open(sortie, 'w', encoding='utf-8', newline='\n') as f:
        for x in L:
            f.write('\t'.join(x) + '\n')
    print(sortie, ':', len(L), 'textes,', sum(1 for x in L if x[1] == 'S'), 'choix')
