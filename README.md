# myEnedis

**Cette integration est compatible avec la carte : https://github.com/saniho/content-card-linky**

**Un question ? Un problème ? Une demande ? Venez en parler sur le [fil de discussion dédié](https://forum.hacf.fr/t/sensor-pour-enedis-apienedis/935) sur le [forum HACF](https://forum.hacf.fr/).**

## Bienvenue !

Cette intégration fonctionne à l'aide de la passerelle fournie par https://enedisgateway.tech/.

Avant de pouvoir utiliser cette intégration, assurez vous d' : 
* Avoir validé la partage de données avec la [passerelle](https://enedisgateway.tech/),
* Avoir activé sur votre [espace privé Enedis](https://mon-compte-client.enedis.fr/) la remontée des informations de votre linky.

## Installer l'intégration

### Via HACS (mise à jour en un clic) : 

*si vous n'avez pas HACS, pour l'installer cela se passe ici : [HACS : Ajoutez des modules et des cartes personnalisées](https://forum.hacf.fr/t/hacs-ajoutez-des-modules-et-des-cartes-personnalisees/359)*

<img src="https://raw.githubusercontent.com/saniho/apiEnedis/main/img/HACS_add_repo_01.png" height="300"/>
<img src="https://raw.githubusercontent.com/saniho/apiEnedis/main/img/HACS_add_repo_02.png" width="600"/>

* Ajoutez le dépot personnalisé : `https://github.com/saniho/apiEnedis`

<img src="https://raw.githubusercontent.com/saniho/apiEnedis/main/img/HACS_install_integration_01.png" width="400"/>

* Cliquez sur le bouton `Installer` de la carte correspondant à l'intégration

<img src="https://raw.githubusercontent.com/saniho/apiEnedis/main/img/HACS_install_integration_02.png" width="600"/>

* Cliquez sur le bouton `Installer` de la popup

<img src="https://raw.githubusercontent.com/saniho/apiEnedis/main/img/HACS_install_integration_03.png" width="400"/>

* La carte de l'intégration est maintenant rouge, signifiant qu'un redémarrage du serveur Home Assistant est nécessaire

* Accédez à la vue `Contrôle du serveur` (`Configuration` -> `Contrôle du serveur`)

<img src="https://raw.githubusercontent.com/saniho/apiEnedis/main/img/HACS_install_integration_04.png" width="400"/>

* Cliquez sur le bouton `Redémarrer` dans la zone `Gestion du serveur`

### Manuellement (à faire à chaque mise à jour)

* Copiez tout le contenu du dossier [custom_components](https://github.com/saniho/apiEnedis/tree/main/custom_components/apiEnedis) dans votre propre dossier `custom_components`, dans un dossier nommé `apiEnedis`

* Redémarrez votre serveur Home Assistant

## Ajouter l'intégration

### Via l'interface graphique

* Accédez à la vue `Intégrations` (`Configuration` -> `Intégration`)

* Appuyez sur le bouton bleu `Ajouter l'intégration` en bas à droite de la vue

<img src="https://raw.githubusercontent.com/saniho/apiEnedis/main/img/HACS_add_integration_01.png" height="500"/>

* Tapez dans le champ de recherche qui vient d'apparaître : `myenedis` et cliquez sur l'intégration

<img src="https://raw.githubusercontent.com/saniho/apiEnedis/main/img/HACS_add_integration_02.png" height="300"/>

* Renseigner : 
  * Votre `token`
  * Votre `code` (PDL)
  * Si vous disposez d'un contrat heures pleines/heures creuses : 
    * Le prix des heures creuses
    * Le prix des heures pleines
  * cocher la case heures creuses si votre contrat comporte des heures creuses  
  * vos heures creuses si différentes de celles proposées par enedis
    exemple de format : ``[['00:00','05:00'], ['22:00', '24:00']]``
    
* Validez la saisie avec le bouton `Soumettre`

<img src="https://raw.githubusercontent.com/saniho/apiEnedis/main/img/HACS_add_integration_03.png" width="300"/>

* Fermez la popup de confirmation en cliquant sur le bouton `Terminer`

*Si vous ne voyez pas l'intégration dans la liste, effacer le cache de votre navigateur en faisant la combinaison de touche `CTRL+F5` ou `CTRL+SHIFT+R`*

### Via YAML << DEPRECIATED >>

### Redémarrer votre serveur Home Assistant

## Entité disponible

L'intégration crée l'entité `sensor.myenedis_<<votrecode>>`

<img src="https://raw.githubusercontent.com/saniho/apiEnedis/main/img/sensor_v2.png"/>


**************

N'hésitez pas à aller faire un tour sur ce forum ou vous trouverez pleins d'informations

https://forum.hacf.fr/t/hacs-ajoutez-des-modules-et-des-cartes-personnalisees/359 

*************

_**VERSION**_


**1.2.0.0**
refactoring du code

**suppression de la configuration possible par le fichier yaml, uniquement possible via l'integration**

heures creuses disponible dans l'interface de l'integration

**1.1.2.2**
possibilité de forcer ses propres horaires dans le yaml( differentes de celles de enedis)

tag heures_creuses

Possibilité de forcer l'absence de HC/HP, meme si Enedis en fournit

tag heuresCreusesON

dans l'integration yaml et via flow, possibilité de forcer l'absence de HC/HP

``heuresCreusesON: False``

**1.1.0.0**

nouvelle version, permettant l'integration via flow

**1.0.4.0**

gestion de contrat recent, correction calcul de monté si relevé compteur par tranche de 10 minutes, 30 minutes

attention le nom du sensor contiendra maintenant le numéro de PDL( cela permet de piloter plusieurs compteurs )

**1.0.2.5**

state general du sensor converti en Kwh

correction de bugs

**1.0.2.4**

add Unit of measurement

**1.0.2.3**

correction bug

**1.0.2.2**

ajout de la gestion des heures HC/HP, pour cela indiquer dans votre sensor yalm les tranches horaires

ajout gestion du calcul du prix sur la veille

**changement du nom du sensor dans le sensor.yaml, myEnedis remplace apiEnedis**

**1.0.2.0**

integration à HACS

**changement du nom du sensor dans le sensor.yaml, myEnedis remplace apiEnedis**
**1.0.1.2**

Delay est maintenant facultatif dans sensor.yaml

ajout de la consmmation last week, and current week

**1.0.1.1**

gestion des contrats de moins de 2 ans

remonté d'un statut indiquant l'erreur remonté par la gateway s'il y a erreur

**1.0.1.0**

ajout de la remontée yesterday au niveau du state pour permettre l'utilisation par certaines card( graphique par exemple )

**1.0.0.0**

premiere version

