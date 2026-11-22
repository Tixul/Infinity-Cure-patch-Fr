"""Mise en page et encodage d'une réplique française pour le tampon 0x4230.

Texte français (comme trad/jp.tsv) : `Nom「réplique」` pour un locuteur (」 facultatif, jamais dessiné),
⏎ retour forcé, ▼ attente + page, ▽ attente + ligne (la réplique suivante continue dessous), ◇ attente,
◆ page. Retour à la ligne automatique à LARG px / MAXCAR caractères ; page de MAXLIG lignes sous la
ligne 0 (réservée au nom) : au-delà, « %K%P%N » (attente, page, ligne 0 sautée).
Chaque morceau entre deux commandes a une longueur paire (cases de 2 lettres), complétée par une espace.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from police import CODE, glyphes

LARG = 142        # px utiles (bitmap de 144)
MAXCAR = 40       # 20 cases de grille
MAXLIG = 4        # lignes 1..4
_, W = glyphes()
NOMS = ('Makoto', 'Yuka', 'Haruka', 'Izumi', 'Kurumi', 'Saki', 'Okuhiko')


class Erreur(Exception):
    pass


NORM = {'～': '~', '　': ' ', '‘': "'", '’': "'", '–': '—', ' ': ' '}


def px(t):
    return sum(W[CODE[NORM.get(c, c)]] for c in t)


def enc(t):
    t = ''.join(NORM.get(c, c) for c in t)
    try:
        b = bytes(CODE[c] for c in t)
    except KeyError as e:
        raise Erreur('caractère hors police %r' % e.args[0])
    return b + bytes([0x7F]) if len(b) % 2 else b     # 0x7F = bourrage invisible (largeur 0)


def coupe(seg):
    """Segment sans commande -> lignes (coupure aux espaces, mots trop longs coupés de force)."""
    lignes, cur = [], ''
    mots = []
    for m in seg.split(' '):           # ponctuation haute et guillemets : jamais seuls en début de ligne
        if mots and (m[:1] in '?!:;»' or mots[-1] in ('«', '—')) and m:
            mots[-1] += ' ' + m
        else:
            mots.append(m)
    for mot in mots:
        essai = (cur + ' ' + mot) if cur else mot
        if px(essai) <= LARG and len(essai) <= MAXCAR:
            cur = essai
            continue
        if cur:
            lignes.append(cur)
        cur = mot
        while px(cur) > LARG or len(cur) > MAXCAR:
            k = len(cur)
            while px(cur[:k]) > LARG or k > MAXCAR:
                k -= 1
            lignes.append(cur[:k])
            cur = cur[k:]
    lignes.append(cur)
    return lignes


def encode(texte, ligne0):
    """texte FR, ligne de départ (0 = page neuve) -> (octets sans le 00 final, ligne de départ de la
    réplique suivante (0 = page neuve), nombre de pages ajoutées)."""
    out = b''
    ajout = 0
    t = texte.replace('」', '')
    if ligne0 == 0:
        if '「' in t[:16]:
            nom, t = t.split('「', 1)
            out += enc(nom) + b'\x81\x75'
        lig = 1
    else:
        lig = ligne0
        if '「' in t[:16]:
            nom, reste = t.split('「', 1)
            t = nom + ' : ' + reste if nom in NOMS or len(nom) < 12 else t
        if lig > MAXLIG:
            out += b'%P%N'
            lig = 1
            ajout += 1

    def saut(attente):
        nonlocal out, lig, ajout
        if lig + 1 > MAXLIG:
            out += b'%K%P%N'
            lig = 1
            ajout += 1
        else:
            out += (b'%K' if attente else b'') + b'%N'
            lig += 1

    seg = ''
    fin = None
    i = 0
    while i < len(t):
        c = t[i]
        if c in '⏎▽▼◇◆':
            lignes = coupe(seg.strip()) if seg.strip() else []
            for k, l in enumerate(lignes):
                if k:
                    saut(False)
                out += enc(l)
            seg = ''
            if c == '⏎':
                saut(False)
            elif c == '▽':
                if i == len(t) - 1:
                    # la suivante continue dessous
                    out += b'%K%N'
                    fin = lig + 1
                else:
                    saut(True)
            elif c == '▼':
                out += b'%K%P'
                if i < len(t) - 1:
                    out += b'%N'
                    lig = 1
                else:
                    fin = 0
            elif c == '◇':
                out += b'%K'
            elif c == '◆':
                out += b'%P%N'
                lig = 1
        else:
            seg += c
        i += 1
    if seg.strip():
        for k, l in enumerate(coupe(seg.strip())):
            if k:
                saut(False)
            out += enc(l)
    if fin is None:
        fin = lig   # ⏎ final (saut déjà compté) ou rien : la suivante continue sur la même ligne
    return out, fin, ajout


def encode_choix(texte):
    t = texte.replace('▼', '').replace('▽', '')
    if px(t) > LARG or len(t) > MAXCAR:
        raise Erreur('choix trop long (%d px) : %s' % (px(t), t))
    return enc(t)
