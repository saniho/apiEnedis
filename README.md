# apiEnedis

exemple de configuration sensors.yaml

```
# enedis
- platform: apiEnedis
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