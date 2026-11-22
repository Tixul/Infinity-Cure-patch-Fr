"""Décodage du texte d'Infinity Cure (script compressé par dictionnaire).
Octet SJIS (81-9F, E0-FC) = 2 octets ; 20-7F -> DICO[b-0x20] ; A0-DF -> DICO[b-0x40].
DICO : table de 160 pointeurs 32 bits en 0x20EB6A (fichier 0xEB6A)."""
import struct
TABLE = 0xEB6A


def dico(d):
    r = []
    for k in range(160):
        p = struct.unpack_from('<I', d, TABLE + 4 * k)[0] - 0x200000
        r.append(d[p:d.index(b'\0', p)])
    return r


def lead(b):
    return 0x81 <= b <= 0x9F or 0xE0 <= b <= 0xFC


def developpe(d, i, D=None):
    """Texte à l'adresse fichier i -> (octets SJIS développés, fin = index du 00)."""
    D = D or dico(d)
    out = b''
    while d[i]:
        b = d[i]
        if lead(b):
            out += d[i:i + 2]; i += 2
        elif 0x20 <= b <= 0x7F:
            out += D[b - 0x20]; i += 1
        elif 0xA0 <= b <= 0xDF:
            out += D[b - 0x40]; i += 1
        else:
            raise ValueError('octet %02X en %X' % (b, i))
    return out, i


def lisible(s):
    """SJIS développé -> texte unicode avec codes : %N = ⏎ , %K%P = ▼ (page), %K%N = ▽ (ligne)."""
    t = s.decode('cp932', 'replace')
    return t.replace('%K%P', '▼').replace('%K%N', '▽').replace('%N', '⏎').replace('%K', '◇').replace('%P', '◆')
