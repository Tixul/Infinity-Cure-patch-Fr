"""Construit la ROM traduite d'Infinity Cure (base : ROM japonaise d'origine, non modifiée).

    python tools/build.py --rom "Infinity Cure (Japan).ngc" [--lang fr] [--debug] [--ips]
        ->  out/<code>.ngc (ou out/<code>_debug.ngc) (+ .ips, revérifié)

ROM portée à 4 Mio :
  puce 1 (fichier 0-0x1FFFFF, CPU 0x200000-0x3FFFFF) = jeu d'origine + ajouts en CPU 0x300000 :
    0x300000 code (tools/asm/fr.asm)   0x300800 police 12×12   0x301A00 avances   0x301B00 NB/TJP/TFR
    0x302000 tables triées : adresse JP de la réplique -> adresse du texte traduit   0x380000 menus
  puce 2 (fichier 0x200000+, CPU 0x800000+) = textes traduits (encodés, mis en page).
  Sauvegarde déplacée du bloc 17 (0x2FA000) au bloc 33 (0x3FA000), comme le prévoit une cartouche
  16 Mbit ; effacement caché des blocs de la puce 2 (combinaison de touches de développement) neutralisé.
--debug : « New Game » ouvre le menu de débogage du script (section 48), au lieu du prologue.

Le code assembleur est livré assemblé (tools/asm/fr.bin + fr.sym.json). Pour le réassembler après
modification, installer AS (Macro Assembler AS, asl + p2bin) et donner son dossier dans ASL_DIR.
"""
import glob, hashlib, json, os, re, struct, subprocess, sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import police, mise, menus, extrait   # noqa: E402

PROJET = os.path.dirname(ICI)
TAILLE = 0x400000
P2 = 0x200000                          # fichier de la puce 2 (CPU 0x800000)
SHA1_JP = 'b0f3f57c5ad084a009631e7e0fa497451415e73b'   # ROM japonaise, zone de sauvegarde vidée
TITRE_CHOIX = 'Choix'                  # remplace 【Ｓｅｌｅｃｔ】 au-dessus des menus de choix


def cpu2f(a):
    return a - 0x200000 if a < 0x800000 else a - 0x800000 + P2


def assemble():
    d = os.path.join(ICI, 'asm')
    asl = os.environ.get('ASL_DIR')
    if asl:
        ext = '.exe' if os.name == 'nt' else ''
        subprocess.run([os.path.join(asl, 'asl' + ext), '-cpu', '96C141', '-q', '-L', 'fr.asm'], cwd=d,
                       check=True, stdout=subprocess.DEVNULL)
        subprocess.run([os.path.join(asl, 'p2bin' + ext), 'fr.p', 'fr.bin'], cwd=d, check=True,
                       stdout=subprocess.DEVNULL)
        t = open(os.path.join(d, 'fr.lst'), encoding='latin1').read()
        S = {m.group(1): int(m.group(2), 16) for m in re.finditer(r'\b([A-Z_0-9]+) :\s+([0-9A-F]+) C\b', t)}
        S = {k: S[k] for k in ('DEVELOPPE', 'VWF', 'GLYPHE1')}
        json.dump({k: '%06X' % v for k, v in S.items()}, open(os.path.join(d, 'fr.sym.json'), 'w'), indent=1)
    S = {k: int(v, 16) for k, v in json.load(open(os.path.join(d, 'fr.sym.json'))).items()}
    return open(os.path.join(d, 'fr.bin'), 'rb').read(), S


def patch(r, a, avant, apres):
    f = cpu2f(a)
    avant = bytes.fromhex(avant)
    apres = bytes.fromhex(apres) if isinstance(apres, str) else apres
    if r[f:f + len(avant)] != avant:
        raise SystemExit('octets inattendus en %X : %s' % (a, r[f:f + len(avant)].hex(' ')))
    r[f:f + len(apres)] = apres


def a24(x):
    return struct.pack('<I', x)[:3]


def lire_lang(code):
    """lang/<code>/*.tsv : `adresse<TAB>texte` (dernière colonne = texte) ; # = commentaire."""
    T = {}
    fichiers = sorted(glob.glob(os.path.join(PROJET, 'lang', code, '*.tsv')))
    if not fichiers:
        raise SystemExit('aucun fichier lang/%s/*.tsv' % code)
    for fn in fichiers:
        for l in open(fn, encoding='utf-8'):
            l = l.rstrip('\r\n')
            if not l or l.startswith('#'):
                continue
            c = l.split('\t')
            if len(c) >= 2 and c[-1].strip():
                T[int(c[0], 16)] = c[-1]
    return T


def rom_jp(chemin):
    jp = open(chemin, 'rb').read()
    if len(jp) != 0x100000:
        raise SystemExit('ROM inattendue (%d octets) : il faut la ROM japonaise de 1 048 576 octets' % len(jp))
    z = bytearray(jp)
    z[0xFA000:0xFC000] = b'\xff' * 0x2000       # une sauvegarde éventuelle n'empêche pas la construction
    if hashlib.sha1(z).hexdigest() != SHA1_JP:
        raise SystemExit('ce n\'est pas la ROM japonaise attendue (voir README, 1.1)')
    return bytes(z)


def construit(jp, code='fr', debug=False):
    r = bytearray(b'\xFF' * TAILLE)
    r[:len(jp)] = jp

    # --- sauvegarde : bloc 17 (puce 8 Mbit) -> bloc 33 (puce 16 Mbit) en 0x3FA000
    for a in (0x20639F, 0x2064EE):
        patch(r, a, '0B 11 00', '0B 21 00')
    patch(r, 0x2063CB, 'E8 C8 00 A0 0F 00', 'E8 C8 00 A0 1F 00')
    for a in (0x206039, 0x2061A3, 0x2061D9, 0x2062FF, 0x2063F3, 0x206406, 0x206412, 0x206421, 0x206458,
              0x20647C, 0x206495):
        f = cpu2f(a)
        k = r.find(b'\xA0\x2F', f, f + 6)
        assert k > 0, hex(a)
        r[k + 1] = 0x3F
    # --- version debug : « New Game » ouvre le menu de développement (section 48 du script)
    if debug:
        patch(r, 0x201CB9, 'F2 2E 5B 00 00 00', 'F2 2E 5B 00 00 30')
    # --- effacement caché des blocs de la puce 2 (tuerait les textes) : neutralisé
    patch(r, 0x20106A, '1D 6D 83 20', '00 00 00 00')

    # --- code, police
    code_bin, S = assemble()
    assert len(code_bin) < 0x800
    r[cpu2f(0x300000):cpu2f(0x300000) + len(code_bin)] = code_bin
    pol, lar = police.binaire()
    r[cpu2f(0x300800):cpu2f(0x300800) + len(pol)] = pol
    r[cpu2f(0x301A00):cpu2f(0x301A00) + 256] = lar
    patch(r, 0x2045D0, 'AF 04 23 F2', b'\x1B' + a24(S['DEVELOPPE']))
    patch(r, 0x20467F, '1D 0C 56 20', b'\x1D' + a24(S['VWF']))
    patch(r, 0x204924, '1D 0C 56 20', b'\x1D' + a24(S['VWF']))
    patch(r, 0x207F1E, '9F 04 20 D8', b'\x1B' + a24(S['GLYPHE1']))
    # --- grille de texte déplacée en 0x6680 : 12 lignes x 42 octets (20 cases)
    for a in (0x2045BD, 0x204976):
        patch(r, a, '0B 38 01', '0B F8 01')
    for a in (0x2045C6, 0x20497F):
        patch(r, a, '0B D6 5B', '0B 80 66')
    patch(r, 0x20468D, 'DB 09 1A 00', 'DB 09 2A 00')
    patch(r, 0x2048FC, 'D8 09 1A 00', 'D8 09 2A 00')
    for a in (0x204695, 0x204902):
        patch(r, a, 'F2 D6 5B 00 31', 'F2 80 66 00 31')
    patch(r, 0x204870, '91 3F 0C 00', '91 3F 14 00')

    # --- textes
    FR = lire_lang(code)
    jpt = extrait.lignes(jp)
    connues = {int(a, 16) for a, t, n, s in jpt}
    inconnues = sorted(set(FR) - connues)
    if inconnues:
        raise SystemExit('adresses inconnues dans lang/%s : %s' % (code, ' '.join('%06X' % a for a in inconnues[:10])))
    par_texte = {}                     # doublons : même texte japonais (et même type) -> même traduction
    for a, typ, n, s in jpt:
        if int(a, 16) in FR:
            par_texte.setdefault((typ, s), FR[int(a, 16)])
    for a, typ, n, s in jpt:
        if int(a, 16) not in FR and (typ, s) in par_texte:
            FR[int(a, 16)] = par_texte[(typ, s)]
    ligne, prec = 0, None
    blobs, erreurs, ajouts = {}, [], 0
    for a, typ, n, s in jpt:
        a = int(a, 16)
        if typ == 'S':
            if a in FR:
                try:
                    blobs.setdefault(mise.encode_choix(FR[a]) + b'\0', []).append(a)
                except mise.Erreur as e:
                    erreurs.append('%06X %s' % (a, e))
            continue
        if prec is None or int(n) != prec + 1:      # la ligne de départ dépend de la réplique précédente
            ligne = 0 if (prec is None or int(n) == 0) else ligne
        if a in FR:
            try:
                b, ligne, k = mise.encode(FR[a], ligne)
                ajouts += k
                blobs.setdefault(b + b'\0', []).append(a)
            except mise.Erreur as e:
                erreurs.append('%06X %s' % (a, e))
                ligne = 0
        else:
            ligne = 0 if s.endswith('▼') else ligne + 1 if s.endswith('▽') else 0
        prec = int(n)
    if erreurs:
        for e in erreurs[:40]:
            print('ERREUR', e)
        raise SystemExit('%d erreur(s) : ROM non fabriquée (tools/controle.py pour le détail)' % len(erreurs))
    pos, table = P2, []
    for b, adrs in blobs.items():
        if pos + len(b) > TAILLE:
            raise SystemExit('puce 2 pleine')
        r[pos:pos + len(b)] = b
        for a in adrs:
            table.append((a, 0x800000 + pos - P2))
        pos += len(b)
    table.sort()
    tjp, tfr = 0x302000, 0x302000 + 4 * len(table)
    assert tfr + 4 * len(table) < 0x380000
    for k, (a, f) in enumerate(table):
        struct.pack_into('<I', r, cpu2f(tjp) + 4 * k, a)
        struct.pack_into('<I', r, cpu2f(tfr) + 4 * k, f)
    struct.pack_into('<III', r, cpu2f(0x301B00), len(table), tjp, tfr)

    # --- titre des menus de choix (sub_204B8A, cases de 2 octets)
    t = mise.enc(TITRE_CHOIX)
    sel = '　　　【'.encode('cp932') + t + '】'.encode('cp932') + bytes(1)
    f = cpu2f(0x20EB40)
    assert r[f:f + 21] == bytes.fromhex('81408140817982728285828c828582838294817a00')
    assert len(sel) <= 22
    r[f:f + len(sel)] = sel
    # --- menus hors script (relogés en 0x380000, tables repointées)
    assert menus.applique(r, cpu2f, 0x380000) < 0x3F0000
    print('%d répliques traduites, %d textes distincts, puce 2 : %d octets, pages ajoutées : %d'
          % (len(table), len(blobs), pos - P2, ajouts))
    return bytes(r)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    a = sys.argv
    if '--rom' not in a:
        raise SystemExit(__doc__)
    rom = a[a.index('--rom') + 1]
    code = a[a.index('--lang') + 1] if '--lang' in a else 'fr'
    debug = '--debug' in a
    jp = rom_jp(rom)
    r = construit(jp, code, debug)
    out = os.path.join(PROJET, 'out')
    os.makedirs(out, exist_ok=True)
    nom = os.path.join(out, code + ('_debug' if debug else ''))
    open(nom + '.ngc.tmp', 'wb').write(r)
    os.replace(nom + '.ngc.tmp', nom + '.ngc')
    print(nom + '.ngc', 'SHA-1', hashlib.sha1(r).hexdigest())
    if '--ips' in a:
        import ips
        p = ips.fabrique(jp, r)
        assert ips.applique(jp, p) == r, 'patch IPS incorrect'
        open(nom + '.ips', 'wb').write(p)
        print(nom + '.ips', len(p), 'octets (revérifié)')


if __name__ == '__main__':
    main()
