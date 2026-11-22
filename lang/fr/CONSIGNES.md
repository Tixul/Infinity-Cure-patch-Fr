# Infinity Cure — consignes de traduction française

Jeu : roman visuel à suspense (KID, Neo Geo Pocket Color, 2000), sorti uniquement au Japon. Makoto,
étudiant, est en stage de séminaire sur une petite île ; le lundi 1er avril, il se réveille d'un
cauchemar où il perd une fille dans ses bras le samedi 6 avril… et les jours se répètent. Un grelot
mystérieux, un mal appelé « Cure ». Ton : quotidien léger et drôle entre amis, qui bascule par
moments dans l'angoisse et le drame. Selon les routes, le narrateur « je » est Makoto ou Yuka.

Traduit depuis le **japonais** (il n'existe pas d'autre version).

## 1. ADAPTER, pas traduire (règle n° 1)
- Chaque boîte doit avoir du sens SEULE, dite par CE personnage, comme un Français le dirait.
- Se demander ce que le personnage VEUT DIRE, puis l'écrire naturellement : pas de calque, pas
  d'ordre des mots « traduit ». Les gags et jeux de mots : un équivalent français qui garde la
  fonction de la réplique.
- Narration : passé composé / imparfait (présent si le japonais raconte au présent). Accorder au
  genre du narrateur (Makoto ou Yuka selon la route).

## 2. Choix fixés
- **Suffixes japonais gardés** exactement comme dans le japonais (-kun, -san, -chan, senpai,
  Onii-chan, Onee-chan) ; un nom sans suffixe en japonais reste sans suffixe.
- **Tutoiement partout**, entre tous les personnages (la politesse passe par les suffixes et le ton) ;
  seul le « vous » pluriel reste.
- **Lieux traduits** (plage de la Princesse, parc panoramique…), sauf les noms propres d'enseigne
  (Luna Beach, hôtel Tsukiya).
- Un personnage qui parle de lui à la 3e personne en japonais le fait aussi en français (Kurumi).
- Termes : voir `GLOSSAIRE.md`.

## 3. Format et contraintes (vérifiés par `tools/controle.py`)
- Fichiers `lot_NN_fr.tsv` : une ligne par texte, `adresse<TAB>texte`. Un même texte japonais répété
  ailleurs dans le script reprend automatiquement la traduction de sa première apparition.
- `▼` = attente du bouton puis nouvelle page ; `▽` = attente puis la suite continue en dessous.
  Garder exactement les mêmes `▼` `▽` (et `◇` `◆`) que le japonais, au même endroit logique.
- `⏎` (retour à la ligne japonais) : ne pas le recopier, le retour à la ligne est automatique.
  Exception : un `⏎` final sans ▼/▽, ou une mise en forme voulue (date, poème, liste).
- **Locuteur** : `Nom「réplique」` (le jeu affiche 【Nom】 au-dessus du texte). Garder les crochets
  「 」 uniquement pour ça, avec un nom de la liste de `tools/controle.py`.
- Page : 4 lignes d'environ 28 caractères (142 pixels, police à chasse variable). Plus long : une page
  de plus est ajoutée automatiquement (permis, mais rester concis).
- Choix de menu : une ligne, 142 pixels au plus (≈ 28 caractères).
- Caractères : lettres, chiffres, espace, `. , ; : ! ? ' " - ( ) [ ] / & ~ … « » — ♪ °` et
  `é è ê ë à â ä î ï ô ö û ù ü ç œ æ É È Ê Ë À Â Î Ï Ô Û Ù Ç Œ Æ`. Pas de `%` (écrire « pour cent »),
  pas d'apostrophe courbe ni de guillemets “ ”.
- Ponctuation française : espace avant `? ! : ;` et à l'intérieur des « » (elles ne passent jamais
  seules en début de ligne) ; `?!` collés. `…` est un seul caractère ; `—` pour ――.
- Pensées entre parenthèses ; 『』 → « ». Heures sur 24 h (« 17 h »), dates « lundi 1er avril ».
