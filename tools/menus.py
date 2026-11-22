"""Menus hors script (Options, Sauvegarde, Album…) : chaînes SJIS de 24 octets dessinées par
sub_205674 (pleine chasse = 12 px, octet simple = 8 px, 　 sauté), désignées par des tables de
pointeurs u32 (0x20F13A…, 0x20F6FA…). On écrit les chaînes françaises ailleurs et on repointe.
Largeur utile 144 px : ≤ 18 caractères simples ; centrage par 　 (12 px) et espaces (8 px)."""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from police import CODE

MENUS = {
    0x20F14E: 'Quitter', 0x20F168: 'Options', 0x20F182: 'Charger', 0x20F19C: 'Sauvegarder',
    0x20F1B6: '【Menu】',
    0x20F1DC: 'Boutons', 0x20F1F6: 'Avance rapide', 0x20F210: '【Options】',
    0x20F236: 'Tout passer', 0x20F250: 'Passer le déjà-lu', 0x20F26A: '【Avance rapide】',
    0x20F294: 'est sélectionné.', 0x20F2AE: 'Passer le déjà-lu', 0x20F2E2: '【Avance rapide】',
    0x20F30C: 'est sélectionné.', 0x20F326: 'Tout passer', 0x20F35A: '【Avance rapide】',
    0x20F380: 'B:OK  A:Annuler', 0x20F39A: 'A:OK  B:Annuler', 0x20F3B4: '【Boutons】',
    0x20F3DE: 'est sélectionné.', 0x20F3F8: 'A:OK  B:Annuler', 0x20F42C: '【Boutons】',
    0x20F456: 'est sélectionné.', 0x20F470: 'B:OK  A:Annuler', 0x20F4A4: '【Boutons】',
    0x20F4CE: 'Effacer données', 0x20F4E8: 'Boutons', 0x20F502: 'Avance rapide', 0x20F51C: '【Options】',
    0x20F542: 'Ne pas effacer', 0x20F55C: 'Effacer', 0x20F576: '【Effacer données】',
    0x20F59C: 'Retour au titre', 0x20F5B6: 'Retour au jeu', 0x20F5D0: '【Quitter】',
    0x20F6FE: '【Sauvegarder】', 0x20F71C: '【Charger】',
    0x20F742: 'Non', 0x20F75C: 'Oui', 0x20F776: '【Écraser ?】',
    0x20F79C: 'Non', 0x20F7B6: 'Oui', 0x20F7D0: '【Supprimer ?】',
    0x20F814: 'Sauvegarde…', 0x20F88C: 'Sauvegarde…', 0x20F8A6: 'Données système',
    0x20F902: 'Effacement…',
    0x20F97A: 'Sauvegarde finie.', 0x20F9F2: 'Échec sauvegarde.',
    0x20FA4C: 'Ne pas réessayer', 0x20FA66: 'Réessayer', 0x20FA80: '【Réessayer ?】',
    0x20FAC4: 'Effacement fini.', 0x20FB3C: 'Échec effacement.',
    0x20FB96: 'Ne pas réessayer', 0x20FBB0: 'Réessayer', 0x20FBCA: '【Réessayer ?】',
    0x20FC3A: 'G/D : choisir', 0x20FC54: '【Album】',
    0x20FC9C: 'Après la pluie', 0x20FCB6: "Crique de l'amour", 0x20FCD0: 'Mort tragique',
    0x20FCEA: "Le cap de l'amour…", 0x20FD04: 'Ici Luna Beach ♪', 0x20FD1E: "Un amour d'éons",
    0x20FD38: 'Adieu au passé', 0x20FD52: 'Au bout du cap…', 0x20FD6C: 'Étoiles de chagrin',
    0x20FD86: 'Le commencement', 0x20FDA0: '« Le grelot »', 0x20FDBA: 'Le grelot en main',
    0x20FDDC: 'HB:décor GD:perso', 0x20FDF6: '【Persos/Décors】',
}
# alignement à droite (comme le japonais) au lieu du centrage
DROITE = {0x20FC3A}


def chaine(t, droite=False):
    """Texte -> octets (SJIS pour 【】, police FR sinon), centré sur 144 px."""
    b, w = b'', 0
    for c in t:
        if c in '【】':
            b += c.encode('cp932'); w += 12
        else:
            b += bytes([CODE[c]]); w += 8
    if w > 144:
        raise ValueError('menu trop large (%d px) : %s' % (w, t))
    reste = 144 - w if droite else (144 - w) // 2
    n12, r = divmod(reste, 12)
    pre = '　'.encode('cp932') * n12 + b' ' * (r // 8)
    return pre + b + b'\0'


def applique(r, cpu2f, base):
    """Écrit les chaînes à partir de l'adresse CPU base et repointe les tables. -> adresse de fin."""
    pos = base
    jp = bytes(r[:0x100000])
    for a, t in MENUS.items():
        s = chaine(t, a in DROITE)
        r[cpu2f(pos):cpu2f(pos) + len(s)] = s
        cible = struct.pack('<I', a)
        n = 0
        for i in range(0xF100, 0xFE20, 2):      # tables de menus (fichier)
            if jp[i:i + 4] == cible:
                struct.pack_into('<I', r, i, pos)
                n += 1
        assert n == 1, '%X : %d pointeurs' % (a, n)
        pos += len(s) + (len(s) & 1)
    return pos
