MISSION : URGENCE AU BLOC

Centre Hospitalier Saint-Louis - Cellule de crise DSI
Difficulté : Intermédiaire | Durée estimée : 45 à 90 min
Catégories : Web, Forensics, Cryptographie


1. CONTEXTE OPÉRATIONNEL

Le 18 novembre 2024 à 03h48, le SOC (Security Operations Center) du Centre Hospitalier Saint-Louis a détecté une activité suspecte sur le serveur BlocManager. Cette application interne est critique : elle gère les plannings du bloc opératoire ainsi que les dossiers des patients en pré-opératoire.

Quelques minutes plus tard, l'alerte est confirmée : un ransomware a été exécuté sur le serveur. L'ensemble des sauvegardes locales ont été chiffrées par un groupe se revendiquant sous le nom de S0lar1s. Une note de rançon exige le paiement de 0.5 BTC sous 72 heures sous peine de destruction définitive de la clé de déchiffrement.

Le problème : Les premières interventions chirurgicales programmées débutent à 07h30. Sans accès aux plannings ni aux dossiers des patients, le bloc opératoire est paralysé. Reporter ces interventions mettrait directement en danger la vie des patients.

La cellule de crise refuse catégoriquement de payer la rançon. Vous êtes mobilisé en urgence pour intervenir sur le serveur et restaurer la situation.


2. OBJECTIFS DE LA MISSION

Votre objectif principal est de restaurer la sauvegarde chiffrée /tmp/backup.xor avant 07h00. Pour y parvenir, vous devrez reconstituer le chemin d'attaque emprunté par l'intrus et récupérer la clé de déchiffrement qu'il a laissée sur le serveur.

- Cible à analyser : Un serveur Linux simulant l'environnement compromis.
- Fichier chiffré : /tmp/backup.xor
- Flag attendu : Une clé de restauration système au format CTF{...} présente dans le fichier restauré.


3. SCÉNARIO D'ATTAQUE (INVESTIGATIONS)

Le SOC a identifié les phases suivantes de l'intrusion, que vous devez reproduire et analyser :

Étape 1 : Accès Initial (Web)
L'attaquant a ciblé l'interface de connexion du BlocManager :
http://<IP_BLOCMANAGER>/login

Aucun compte d'urgence n'est documenté par la DSI. Vous devez trouver un moyen de contourner cette authentification. Les premières analyses indiquent que l'application n'a pas été mise à jour depuis plusieurs mois et présente des faiblesses critiques dans sa gestion des entrées utilisateur.

Étape 2 : Élévation et Pivot (SSH)
Une fois l'accès à l'application obtenu, l'attaquant a cherché des identifiants système. Une note interne ou une configuration mal sécurisée sur le tableau de bord d'administration lui a permis de rebondir.
Identifiez ces informations pour vous connecter en SSH sur la machine :
ssh operateur@<IP_SERVEUR> -p 22

Étape 3 : Analyse Forense (Logs)
Une fois connecté sur le serveur, vous devez analyser l'activité de l'attaquant. Les répertoires d'intérêt sont :
- /var/log/apache2/access.log (Journal des requêtes HTTP)
- /var/log/apache2/error.log (Erreurs du serveur web)
- /var/www/html/uploads/ (Fichiers potentiellement déposés)

L'intrusion s'est déroulée sur une fenêtre d'environ 10 minutes au milieu d'un trafic légitime dense (postes infirmiers, requêtes de monitoring, scanners automatiques). Isolez l'adresse IP de l'attaquant et analysez ses requêtes pour comprendre ses actions. L'attaquant semble avoir fait une erreur critique en laissant fuiter une information sensible dans l'un des paramètres de ses requêtes.

Étape 4 : Déchiffrement de la Sauvegarde
Une fois la clé de chiffrement identifiée dans les logs, utilisez le script Python fourni sur le serveur pour déchiffrer la sauvegarde :
python3 /tmp/ransomware_fake.py /tmp/backup.xor <CLE>

Le fichier déchiffré contiendra la clé de restauration système (le flag).


4. OUTILS RECOMMANDÉS

- Analyse Web : Navigateur web, curl, ou outil d'interception (Burp Suite).
- Accès SSH : Client SSH standard (ssh).
- Analyse de Logs : Outils CLI classiques (grep, awk, cut, sort, uniq).
- Déchiffrement : Script /tmp/ransomware_fake.py fourni dans l'environnement.


5. RÈGLES DU JEU

- Le brute-force sur les formulaires d'authentification (Web et SSH) est inutile et interdit. Toutes les étapes reposent sur l'exploitation logique ou l'analyse d'indices.
- Ne modifiez pas les fichiers système en dehors du périmètre de résolution.
- Restez concentré sur le serveur du challenge.


6. INDICES (À n'utiliser qu'en cas de blocage)

Indice 1 : Blocage sur la page de connexion
Le formulaire de connexion construit sa requête SQL de manière dynamique sans protection. Une injection SQL de contournement d'authentification (Authentication Bypass) permet de se connecter sans connaître le mot de passe. Pensez à utiliser des caractères de commentaires SQL (-- ou #) pour neutraliser la vérification du mot de passe.

Indice 2 : Analyse des logs volumineux
Pour identifier l'adresse IP de l'attaquant, comptez le nombre de requêtes par adresse IP unique dans access.log. Une IP externe présentant un volume anormal de requêtes (notamment des tentatives automatisées sur /login) devrait se distinguer rapidement :
awk '{print $1}' access.log | sort | uniq -c | sort -rn

Indice 3 : Localisation de la clé dans les requêtes
Une fois l'IP de l'attaquant isolée, inspectez l'intégralité des lignes de log associées à cette IP. Ne vous limitez pas aux URL consultées : regardez attentivement tous les en-têtes HTTP enregistrés, notamment le User-Agent. L'attaquant y a laissé une configuration sensible.

Indice 4 : Erreur lors du déchiffrement
Si le script de déchiffrement indique que la clé est incorrecte, vérifiez qu'aucun espace ou caractère invisible n'a été copié par erreur depuis votre terminal, et respectez scrupuleusement la casse et les caractères spéciaux.