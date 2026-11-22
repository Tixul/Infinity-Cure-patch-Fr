# Infinity Cure — notes techniques (ROM, script, texte, affichage)

Tout ce qui suit a été mesuré sur la ROM japonaise (1 Mio, CRC32 `32DC2AA2`, titre interne
`InfinityCure`, KID). Adresses CPU : la cartouche commence en 0x200000 (fichier 0 = CPU 0x200000) ;
la 2e puce de la ROM traduite (fichier 0x200000) est vue en CPU 0x800000.

## Chaîne de construction
`tools/build.py` : ROM japonaise → sauvegarde déplacée → code ajouté (détournements) → police →
textes traduits encodés et mis en page en 2e puce → table de correspondance → menus → ROM de **4 Mio**
→ patch IPS **depuis la ROM japonaise**. Le script d'origine n'est **pas modifié** : à l'instant où le
jeu va afficher une réplique, il cherche sa traduction par l'adresse de la réplique japonaise.

## Script
- Machine virtuelle : compteur 32 bits en RAM 0x5B30, répartiteur 0x20295C, table 0x20E47A (8 octets
  par opcode : routine + pointeur vers son NOM : nop end if if_not goto call return ext_goto ext_call
  reg_calc rnd_get wait_time wait_key wait_page **mes_load** mes_clear mes_line **select**
  effect_start effect_end bg_load bg_erase bg_move char_load char_view char_erase char_move bgm_play
  bgm_stop se_play se_stop pcm_play pcm_stop pcm_wait wind_set wind_mode max_search save_title
  time_disp save_disp count_claer count_wait menu_lock staff_start staff_end). Opcode = 1 octet + 1
  octet de paramètre, non alignés.
- Sections : table u32 en 0x218300 (décalage / 4 depuis 0x26E000) ; `07 n` = ext_goto section n.
  Départ : sub_201CA0(mode) → section 0 (New Game), 2 (démo du titre), 3 (sketch d'avertissement).
- `0E 00 id16 texte 00` = réplique (mes_load) ; la machine saute le texte par strlen.
  `11 07 n16` + n chaînes = menu de choix ; puis `03 00 t16 | 07 60 k 00 00 00 | …` = « si choix = k ».
- 17 507 répliques (numéros continus par section) + 59 menus (160 choix) ; 15 481 textes distincts.

## Texte japonais (compression par dictionnaire)
- Octets Shift-JIS (0x81-0x9F, 0xE0-0xFC) = 2 octets ; 0x20-0x7F → mot n° b−0x20 ; 0xA0-0xDF → mot
  n° b−0x40 ; dictionnaire = 160 pointeurs u32 en 0x20EB6A.
- Codes : `%N` ligne, `%K%P` attente + page, `%K%N` attente + ligne (le texte suivant continue
  dessous), `%K`, `%P`. Les mots 0x21-0x26 sont « Nom「 » (誠「 優夏「 遙「 いづみ「 くるみ「 沙紀「).
- `tools/texte.py` décode, `tools/extrait.py` écrit `out/jp.tsv` (▼ = %K%P, ▽ = %K%N, ⏎ = %N).

## Affichage (et ce qui a été changé)
- sub_2045D0(ptr) développe la réplique dans le tampon RAM 0x4230 (ptr gardé en 0x5BC4).
  **Détournement** `jp DEVELOPPE` : recherche dichotomique de l'adresse dans la table triée
  (0x302000) ; trouvée → copie du texte traduit (déjà encodé) dans 0x4230 ; sinon → code d'origine.
- Rendu : sub_2047BE lit 0x4230 par **cases de 2 octets** ; sub_204655 range la case dans une grille
  puis sub_20560C la dessine au pixel près : glyphe 12×12 1 bpp (18 octets) dans un bitmap de 144 px.
  En début de page, sub_2046C0 cherche 「 : ce qui précède s'affiche en ligne 0 sous la forme 【Nom】,
  le texte commence ligne 1 ; 」 n'est jamais dessiné.
- **Chasse variable** (`tools/asm/fr.asm`, routine VWF à la place des appels à sub_20560C) : une case =
  2 lettres ; x = somme des avances des cases précédentes de la ligne (case Shift-JIS = 12 px).
  Toujours le mode de dessin 0 (pixel par pixel) : les modes rapides 1/2 supposent x multiple de 4.
  Le tampon de tuiles (0x5D22) est vidé (sub_207E83) après chaque lettre, sinon la 2e lettre efface
  la 1re.
- Grille déplacée de 0x5BD6 (12 lignes × 13 cases) en 0x6680 (12 × 21 cases, RAM libre sous la pile
  0x6C00) ; retour automatique à 20 cases.
- Police : octet simple b → glyphe 0xFE0+b de la police du jeu (0x218400) ; **détournement** `jp
  GLYPHE1` en sub_207F1E → police latine en 0x300800 (`tools/police_fr.txt`). 0x7F = bourrage
  invisible (largeur 0) pour compléter une case.
- Mise en page (`tools/mise.py`) : 142 px et 40 caractères par ligne, 4 lignes sous la ligne du nom ;
  au-delà `%K%P%N` (attente, page, ligne du nom sautée). Ponctuation haute jamais seule en début de
  ligne. Une réplique qui suit un `▽` démarre sous la précédente (chaînage par numéro de réplique).
- Menus de choix : titre 【Ｓｅｌｅｃｔ】 (0x20EB40) remplacé ; centrage par le jeu (approché).
- Menus hors script (Options, Sauvegarde, Quitter, Album…) : chaînes de 24 octets dessinées par
  sub_205674 (pleine chasse 12 px, octet simple 8 px), désignées par des tables de pointeurs
  0x20F13A… : chaînes françaises relogées en 0x380000, pointeurs réécrits (`tools/menus.py`).

## Sauvegarde
- 16 × 256 octets en 0x2FA000 (bloc 17 d'une puce 8 Mbit) ; effacement sub_20836D(bloc 0x11) en
  0x20639F et 0x2064EE ; écriture BIOS 0x2063CB (`add XWA,0x000FA000`) ; lectures 0x2FA000/0x2FA002.
- ROM agrandie : sauvegarde déplacée en 0x3FA000 (bloc 0x21 d'une puce 16 Mbit), zone livrée vierge.
- Une routine de développement (combinaison de touches, 0x201064) efface les blocs de la **puce 2** :
  sans effet sur la cartouche d'origine, elle détruirait le texte traduit ; son appel est neutralisé.

## Menu de débogage
Section 48 du script (0x2F3E30), jamais appelée par le jeu. Patch « debug » : 0x201CB9
`ld (0x5B2E),0x00` → `0x30`, « New Game » ouvre ce menu. Carte : 0 prologue, 1 ouverture, 2 démo,
3 sketch, 4-17 tronc commun (J1-J4 midi/soir/nuit, J4 cerisiers 16, crabes 17), 18-26 route de Yuka,
27-35 route d'Izumi (« Cure »), 36 générique (appelé en fin de route), 37-39 choix par jour (TEST00-02),
40 choix par chapitre (TEST03), 41 décors (53), 42 portraits (82), 43 illustrations (12), 44 musiques
(23), 45 bruitages (7), 46-47 textes de test jamais appelés, 48 ce menu.
