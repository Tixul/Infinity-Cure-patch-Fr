; Infinity Cure FR : réplique française, chasse variable, police latine.
;
; Points d'appel posés par tools/build.py :
;   0x2045D0 : jp DEVELOPPE      (entrée de sub_2045D0(ptr) : développe la réplique JP dans 0x4230)
;   0x20467F : call VWF          (sub_204655 : dessin d'une case de la grille, au lieu de sub_20560C)
;   0x204924 : call VWF          (sub_2048CD : réaffichage de la grille)
;   0x207F1E : jp GLYPHE1        (sub_207F1E : décalage du glyphe d'un octet simple dans la police)
;
; Texte français dans le tampon : cases de 2 octets = 2 lettres (codes de tools/police.py, jamais
; 0x00 / '%' / octet de tête SJIS) ; commandes %N %K %P d'origine ; 「 (81 75) sépare le nom du locuteur.
;
; Assemblage : asl -cpu 96C141 fr.asm ; p2bin fr.p   (tools/build.py)

        cpu     96C141
        maxmode on
        org     300000h

POLICE  equ     300800h         ; 256 x 18 octets (12x12, 1 bpp)
LARG    equ     301A00h         ; 256 octets : avance en pixels
NB      equ     301B00h         ; u32 : nombre de répliques françaises
TJP     equ     301B04h         ; u32 : -> table triée des adresses JP (u32)
TFR     equ     301B08h         ; u32 : -> table parallèle des adresses FR (u32)
GRILLE  equ     6680h           ; grille déplacée (12 lignes x PAS octets)
PAS     equ     42              ; 21 cases de 2 octets (20 + fin)
TAMPON  equ     4230h
BASEPOL equ     218400h         ; base de la police du jeu (RAM 0x5D0E)

; ---------------------------------------------------------------- sub_2045D0(ptr)
DEVELOPPE:
        ld      xhl,(xsp+4)
        ld      (5BC4h),xhl
        ld      xbc,0           ; bas
        ld      xde,(NB)        ; haut (exclu)
D_BOUCLE:
        cp      xbc,xde
        jr      nc,D_ABSENT
        ld      xwa,xbc
        add     xwa,xde
        srl     1,xwa           ; milieu
        ld      xix,xwa
        sll     2,xix
        add     xix,(TJP)
        ld      xiy,(xix)
        cp      xhl,xiy
        jr      z,D_TROUVE
        jr      c,D_BAS
        inc     1,xwa
        ld      xbc,xwa         ; bas = milieu + 1
        jr      D_BOUCLE
D_BAS:  ld      xde,xwa         ; haut = milieu
        jr      D_BOUCLE
D_TROUVE:
        sll     2,xwa
        add     xwa,(TFR)
        ld      xiy,(xwa)       ; texte français
        lda     xix,(TAMPON)
D_COPIE:
        ld      a,(xiy+)
        ld      (xix+),a
        cp      a,0
        jr      nz,D_COPIE
        ret
D_ABSENT:
        jp      2045D8h         ; suite d'origine (XHL = ptr)

; ---------------------------------------------------------------- VWF(ptr, x, y, mode)
; Pile : +4 ptr (u32), +8 x = col*12 (u16), +10 y = lig*12 (u16), +12 mode (u16).
VWF:    ld      wa,(xsp+8)
        extz    xwa
        div     xwa,12
        ld      de,wa           ; DE = colonne
        ld      wa,(xsp+10)
        extz    xwa
        div     xwa,12          ; WA = ligne
        mul     xwa,PAS
        extz    xwa
        add     xwa,GRILLE
        ld      xix,xwa         ; XIX = début de la ligne
        ld      bc,0            ; BC = x en pixels
V_SOMME:
        cp      de,0
        jr      z,V_DESSIN
        ld      a,(xix)
        call    TETE
        jr      nc,V_DEUX
        add     bc,12
        jr      V_SUIV
V_DEUX: call    AVANCE
        add     bc,wa
        ld      a,(xix+1)
        call    AVANCE
        add     bc,wa
V_SUIV: inc     2,xix
        dec     1,de
        jr      V_SOMME
V_DESSIN:
        ld      xhl,(xsp+4)
        ld      a,(xhl)
        call    TETE
        jr      nc,V_LETTRES
        ; case SJIS (12 px) : un seul glyphe, à la position calculée
        pushw   0
        ld      wa,(xsp+12)
        push    wa
        push    bc
        push    xhl
        call    20560Ch
        lda     xsp,(xsp+10)
        jp      207E83h
V_LETTRES:
        ; 1re lettre
        push    bc
        pushw   0               ; mode 0 = pixel par pixel (les modes 1/2 exigent x multiple de 4)
        ld      wa,(xsp+14)     ; y
        push    wa
        push    bc              ; x
        ld      xhl,(xsp+12)    ; ptr
        push    xhl
        call    20560Ch
        lda     xsp,(xsp+10)
        call    207E83h         ; vide le tampon de tuiles (sinon la 2e lettre efface la 1re)
        pop     bc
        ld      xhl,(xsp+4)
        ld      a,(xhl)
        call    AVANCE
        add     bc,wa
        ; 2e lettre
        pushw   0
        ld      wa,(xsp+12)
        push    wa
        push    bc
        ld      xhl,(xsp+10)
        inc     1,xhl
        push    xhl
        call    20560Ch
        lda     xsp,(xsp+10)
        jp      207E83h

; A = octet -> Carry = 1 si octet de tête SJIS (81-9F, E0-FC)
TETE:   cp      a,81h
        jr      c,T_NON
        cp      a,0A0h
        jr      c,T_OUI
        cp      a,0E0h
        jr      c,T_NON
        cp      a,0FDh
        jr      nc,T_NON
T_OUI:  scf
        ret
T_NON:  rcf
        ret

; A = code -> WA = avance (garde XBC XDE XHL XIX)
AVANCE: push    xix
        extz    wa
        extz    xwa
        add     xwa,LARG
        ld      xix,xwa
        ld      a,(xix)
        extz    wa
        pop     xix
        ret

; ---------------------------------------------------------------- sub_207F1E(code)
; Octet simple (code dans l'octet fort du mot) -> XHL = décalage du glyphe depuis la police du jeu.
GLYPHE1:
        ld      wa,(xsp+4)
        srl     8,wa
        extz    xwa
        ld      xhl,xwa
        sll     3,xhl
        add     xhl,xwa
        sll     1,xhl           ; x18
        add     xhl,POLICE-BASEPOL
        ret
