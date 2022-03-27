# Contribuer

## `testEnedis.py`

`testEnedis.py` a pour but de lancer un test réel avec les identifiants du
développeur.

Ces identifiants doivent être enregistres dans un fichier accessible de façon
relative depuis la racine du projet comme ceci:

`../myCredential/security.txt`

Le contenu de ce fichier ressemble aux fichiers de type `setup.cfg`.\
Il faut une section `ENEDIS` et puis quelques valeurs pour definir
le login.

```ini
[ENEDIS]
# Description libre
QUI=Description
# Point de Livraison - Un vrai numéro de livraison
CODE=21000000000000
# Le TOKEN qui correspond à ce point de livraison
TOKEN=LeVraiTokenDuService_enedisgateway.tech/api___________
```
