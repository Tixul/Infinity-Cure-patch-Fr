"""Police latine à chasse variable d'Infinity Cure : glyphes 12×12 1 bpp (18 octets, ligne par ligne,
bit fort à gauche — le format de la police du jeu), lus dans tools/police_fr.txt.

Codes : ASCII 0x20-0x7E tel quel ; lettres accentuées et ponctuation en 0xA0-0xDF (jamais un octet de
tête Shift-JIS 0x81-0x9F / 0xE0-0xFC, jamais 0x00 ni '%' en tête de case). 0x7F = bourrage invisible.

Pour une autre langue : ajouter / remplacer des blocs dans police_fr.txt (code libre en 0xA0-0xDF),
avance = largeur en pixels, espace compris.

    python tools/police.py   ->  out/police.png (planche agrandie, pour vérifier)
"""
import os

ICI = os.path.dirname(os.path.abspath(__file__))
FICHIER = os.path.join(ICI, 'police_fr.txt')


def _lire():
    G, W, CODE = {}, {}, {}
    lignes = open(FICHIER, encoding='utf-8').read().split('\n')
    i = 0
    while i < len(lignes):
        l = lignes[i]
        if l.startswith('== '):
            ch, code, av = l[3:].rsplit(' ', 2)
            ch = ' ' if ch == 'espace' else ch
            c = int(code.split('=')[1], 16)
            CODE[ch] = c
            W[c] = int(av.split('=')[1])
            G[c] = lignes[i + 1:i + 13]
            i += 13
        else:
            i += 1
    return G, W, CODE


_G, _W, CODE = _lire()


def glyphes():
    """-> (dict code -> 12 lignes '.#', dict code -> avance en px)."""
    return _G, _W


def octets(rows):
    bits = ''.join('1' if v == '#' else '0' for r in rows for v in r)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, 144, 8))


def binaire():
    """-> (police 256×18 octets, table des avances 256 octets)."""
    pol = bytearray(256 * 18)
    lar = bytearray(256)
    for c in range(256):
        lar[c] = _W.get(c, 12 if c >= 0x80 else 6)
        if c in _G:
            pol[c * 18:c * 18 + 18] = octets(_G[c])
    lar[0x7F] = 0
    return bytes(pol), bytes(lar)


if __name__ == '__main__':
    import zlib, struct
    # planche PNG sans dépendance (16 glyphes par rangée, ×3)
    codes = sorted(_G)
    cols, z = 16, 3
    w, h = cols * 14 * z, ((len(codes) + cols - 1) // cols) * 14 * z
    img = [[255] * w for _ in range(h)]
    for k, c in enumerate(codes):
        ox, oy = (k % cols) * 14 * z, (k // cols) * 14 * z
        for y, r in enumerate(_G[c]):
            for x, v in enumerate(r):
                if v == '#':
                    for dy in range(z):
                        for dx in range(z):
                            img[oy + y * z + dy][ox + x * z + dx] = 0
    raw = b''.join(b'\0' + bytes(r) for r in img)
    def bloc(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d))
    png = b'\x89PNG\r\n\x1a\n' + bloc(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 0, 0, 0, 0)) \
        + bloc(b'IDAT', zlib.compress(raw)) + bloc(b'IEND', b'')
    os.makedirs(os.path.join(os.path.dirname(ICI), 'out'), exist_ok=True)
    open(os.path.join(os.path.dirname(ICI), 'out', 'police.png'), 'wb').write(png)
    print('out/police.png :', len(codes), 'glyphes')
