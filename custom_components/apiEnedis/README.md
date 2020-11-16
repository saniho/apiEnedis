# apiEnedis

exemple de configuration sensors.yaml

```
# enedis
- platform: myEnedis
  token: <<votreToken>>
  code: <<votrecode>>
  scan_interval: 3600
```

![picture](img/sensor_v2.png)


VERSION

**1.0.0.0**

premiere version

**1.0.1.0**

ajout de la remontée yesterday au niveau du state pour permettre l'utilisation par certaines card( graphique par exemple )

**1.0.1.1**

gestion des contrats de moins de 2 ans

remonté d'un statut indiquant l'erreur remonté par la gateway s'il y a erreur

**1.0.1.2**

Delay est maintenant facultatif dans sensor.yaml

ajout de la consmmation last week, and current week

**1.0.2.0**

integration à HACS

**changement du nom du sensor dans le sensor.yaml, myEnedis remplace apiEnedis**

**1.0.2.1**

ajout des infost du lastMonthLastYear

Gestion erreur sur le currentWeek, currentMonth 

gestion du yesterday erreur ou pas de donnée tot le matin