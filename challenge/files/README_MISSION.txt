BREFING DE MISSION : URGENCE AU BLOC OPÉRATOIRE

Rédigé en urgence par la cellule de crise DSI
Difficulté : Intermédiaire | Durée estimée : 45 à 90 min
Catégories : Web, Forensics, Cryptographie


--- 1. CE QU'IL SE PASSE ---

Ce matin à 03h48, notre équipe sécurité a repéré une intrusion majeure sur l'application BlocManager. C'est la catastrophe : l'ensemble des bases de données de l'hôpital vient d'être chiffré par le ransomware Solaris. Le groupe exige une rançon faramineuse pour nous donner la clé de déchiffrement.

Le vrai problème ? Les chirurgies programmées démarrent à 07h30. Sans les dossiers des patients et les plannings d'affectation, les médecins sont totalement aveugles. Impossible de reporter ces opérations sans risquer la vie de nos patients.

Nous refusons de céder au chantage. On a besoin de toi en urgence pour infiltrer le serveur, remonter la trace de l'attaquant et sauver la sauvegarde système avant le début des interventions.


--- 2. TA MISSION ---

Ta priorité absolue est de décoder le backup bloqué dans `/tmp/backup.xor` avant 07h00. Pour cela, tu vas devoir analyser l'historique de l'attaque et mettre la main sur la clé de déchiffrement que le pirate a laissée traîner sur la machine.

- Cible à analyser : Un serveur Linux simulant l'environnement compromis.
- Fichier chiffré : /tmp/backup.xor
- Flag attendu : Une clé de restauration système au format CTF{...} présente dans le fichier restauré.


--- 3. LE FIL DE L'ENQUÊTE ---

Le SOC a identifié les phases suivantes de l'intrusion, que vous devez reproduire et analyser :

1. Trouver la brèche (Portail Web)
L'attaquant a ciblé l'interface de connexion du BlocManager :
http://<IP_BLOCMANAGER>/login

Aucun compte d'urgence n'est documenté par la DSI. Vous devez trouver un moyen de contourner cette authentification. Les premières analyses indiquent que l'application n'a pas été mise à jour depuis plusieurs mois et présente des faiblesses critiques dans sa gestion des entrées utilisateur.

2. Prendre le contrôle (SSH)
Une fois l'accès à l'application obtenu, l'attaquant a cherché des identifiants système. Une note interne ou une configuration mal sécurisée sur le tableau de bord d'administration lui a permis de rebondir.
Identifiez ces informations pour vous connecter en SSH sur la machine :
ssh operateur@<IP_SERVEUR> -p 22

3. Traquer ses pas (Logs)
Une fois connecté sur le serveur, vous devez analyser l'activité de l'attaquant. Les répertoires d'intérêt sont :
- /var/log/apache2/access.log (Journal des requêtes HTTP)
- /var/log/apache2/error.log (Erreurs du serveur web)
- /var/www/html/uploads/ (Fichiers potentiellement déposés)

L'intrusion s'est déroulée sur une fenêtre d'environ 10 minutes au milieu d'un trafic légitime dense (postes infirmiers, requêtes de monitoring, scanners automatiques). Isolez l'adresse IP de l'attaquant et analysez ses requêtes pour comprendre ses actions. L'attaquant semble avoir fait une erreur critique en laissant fuiter une information sensible dans l'un des paramètres de ses requêtes.

4. Libérer le backup (Déchiffrement)
Une fois la clé de chiffrement identifiée dans les logs, utilisez le script Python fourni sur le serveur pour déchiffrer la sauvegarde :
python3 /tmp/ransomware_fake.py /tmp/backup.xor <CLE>

Le fichier déchiffré contiendra la clé de restauration système (le flag).


--- 4. LA BOÎTE À OUTILS ---

- Analyse Web : Navigateur web, curl, ou outil d'interception (Burp Suite).
- Accès SSH : Client SSH standard (ssh).
- Analyse de Logs : Outils CLI classiques (grep, awk, cut, sort, uniq).
- Déchiffrement : Script /tmp/ransomware_fake.py fourni dans l'environnement.


--- 5. RÈGLES À RESPECTER ---

- Le brute-force sur les formulaires d'authentification (Web et SSH) est inutile et interdit. Toutes les étapes reposent sur l'exploitation logique ou l'analyse d'indices.
- Ne modifiez pas les fichiers système en dehors du périmètre de résolution.
- Restez concentré sur le serveur du challenge.


--- 6. UN COUP DE POUCE ? (INDICES) ---

Indice 1 : Blocage sur la page de connexion
Le formulaire de connexion construit sa requête SQL de manière dynamique sans protection. Une injection SQL de contournement d'authentification (Authentication Bypass) permet de se connecter sans connaître le mot de passe. Pensez à utiliser des caractères de commentaires SQL (-- ou #) pour neutraliser la vérification du mot de passe.

Indice 2 : Analyse des logs volumineux
Pour identifier l'adresse IP de l'attaquant, comptez le nombre de requêtes par adresse IP unique dans access.log. Une IP externe présentant un volume anormal de requêtes (notamment des tentatives automatisées sur /login) devrait se distinguer rapidement :
awk '{print $1}' access.log | sort | uniq -c | sort -rn

Indice 3 : Localisation de la clé dans les requêtes
Une fois l'IP de l'attaquant isolée, inspectez l'intégralité des lignes de log associées à cette IP. Ne vous limitez pas aux URL consultées : regardez attentivement tous les en-têtes HTTP enregistrés, notamment le User-Agent. L'attaquant y a laissé une configuration sensible.

Indice 4 : Erreur lors du déchiffrement
Si le script de déchiffrement indique que la clé est incorrecte, vérifiez qu'aucun espace ou caractère invisible n'a été copié par erreur depuis votre terminal, et respectez scrupuleusement la casse et les caractères spéciaux.