# MISSION : URGENCE AU BLOC

Centre Hospitalier Saint-Louis - Cellule de crise DSI
Niveau : Intermediaire
Duree estimee : 45 a 90 min
Categories : Web, Forensics, Crypto


## Contexte operationnel

03:48, nuit du 17 au 18 novembre 2024. Le SOC du Centre Hospitalier
Saint-Louis detecte une activite anormale sur le serveur BlocManager,
l'application interne qui gere les plannings du bloc operatoire et les
dossiers patients en pre-operatoire.

Quelques minutes plus tard, le constat tombe : ransomware. Toutes les
sauvegardes nocturnes ont ete chiffrees par un groupe se faisant appeler
S0lar1s. Une note est laissee sur le serveur, exigeant 0.5 BTC sous 72h.

Le probleme : les premieres chirurgies programmees commencent a 07:30.
Sans plannings, sans dossiers patients, le bloc operatoire ne peut pas
tourner. Reporter, c'est mettre des vies en danger.

La cellule de crise refuse de payer. Vous etes appele en renfort.


## Votre mission

Restaurer la sauvegarde chiffree `/tmp/backup.xor` avant 07:00 en
exploitant la meme chaine d'attaque que l'intrus, et en recuperant la
cle de restauration systeme qu'il a (sans le savoir) laissee trainer
sur le serveur.

Flag attendu : `CTF{xxxxx_xxxxx_xxxxx}`


## Etapes du parcours

### 1. Reconnaissance Web

Vous arrivez sur l'ecran de connexion du BlocManager :

    http://<IP_BLOCMANAGER>/login

Aucun compte d'urgence ne vous a ete fourni (la DSI cherche encore).
Le formulaire est minimaliste, classique : username + password.
Cote SOC, on vous souffle que l'application n'a pas ete patchee depuis
8 mois.

Indice : l'attaquant est passe par la. S'il a reussi, vous aussi.


### 2. Exploitation - SQL Injection

Le formulaire est vulnerable a une injection SQL classique (type
authentication bypass).

Pas besoin d'outil automatise : un payload manuel suffit.
Une fois connecte, vous arrivez sur le dashboard operateur.

Indice : l'attaquant, lui, a utilise sqlmap. Ca laisse des traces.


### 3. Pivotement - Acces SSH

Le dashboard contient une note interne de la DSI mentionnant un compte
de maintenance d'urgence :

    operateur / Hopital2024

Connectez-vous au serveur compromis :

    ssh operateur@<IP_SERVEUR> -p 22


### 4. Forensics - Analyse des logs

Une fois sur le serveur, le terrain de jeu est :

    /var/log/apache2/access.log    (journal principal)
    /var/log/apache2/error.log     (indices PHP/SQL bavards)
    /var/www/html/uploads/         (ce que l'attaquant a depose)

L'attaque s'est etalee sur ~10 minutes au milieu de plus de 1000 lignes
de trafic legitime (postes infirmiers, monitoring Prometheus, bots
Internet). Il faut trier.

Pistes pour orienter votre grep :
 - L'attaquant utilise une IP unique pendant toute l'attaque.
 - Il commence en navigateur, puis bascule sur un outil bruyant.
 - A un moment, il fait une erreur OPSEC majeure : il met une
   information sensible dans un endroit ou elle n'aurait jamais
   du etre.


### 5. Crypto - Dechiffrement XOR

Une fois la cle recuperee, dechiffrez la sauvegarde :

    python3 /tmp/ransomware_fake.py /tmp/backup.xor <CLE>

L'outil affichera le contenu en clair. Le flag est dedans, sous
l'etiquette "CLE DE RESTAURATION SYSTEME".


### 6. Validation

Soumettez le flag au format CTF{xxxxx_xxxxx_xxxxx}.


## Outils suggeres

| Etape | Outils |
|-------|--------|
| Web   | curl, navigateur, Burp Suite (optionnel) |
| SQLi  | Payload manuel (' OR 1=1-- , admin'-- , etc.) |
| SSH   | client SSH standard |
| Logs  | grep, awk, cut, sort, uniq -c |
| Crypto| Script Python fourni (/tmp/ransomware_fake.py) |


## Indices progressifs

Indice 1 - Bloque sur le login ?

  L'injection cherche a faire evaluer la clause WHERE a TRUE en
  permanence. Plusieurs payloads classiques fonctionnent, pensez aux
  commentaires SQL (-- , #) pour neutraliser la fin de la requete.


Indice 2 - Trop de lignes dans les logs ?

  Commencez par compter les requetes par IP :
      awk '{print $1}' access.log | sort | uniq -c | sort -rn
  Une IP externe avec beaucoup de requetes sur /login se detache vite.


Indice 3 - J'ai l'IP, et apres ?

  Filtrez sur cette IP et regardez toutes les colonnes, pas juste
  l'URL. Le User-Agent est tres bavard, parfois trop.


Indice 4 - Je vois la cle mais ca ne marche pas

  Recopiez-la exactement : casse, caracteres speciaux, ponctuation.
  Si vous copiez depuis le terminal, attention aux espaces parasites.


## Fichiers fournis

 - generate_challenge.py : genere les artefacts du challenge
 - ransomware_fake.py    : outil de dechiffrement
 - banner.txt            : banniere SSH du serveur compromis
 - mission.md            : ce document


## Regles du jeu

 - Pas de bruteforce du formulaire de login (l'injection passe en 1 requete)
 - Pas de bruteforce SSH (les identifiants sont sur le dashboard)
 - Pas d'exploitation hors-scope (autres VMs, autres services)
 - Tous les indices necessaires sont sur le serveur compromis
 - Les logs ne mentent pas, mais ils sont bavards


Bonne chance, operateur. Le bloc compte sur vous.