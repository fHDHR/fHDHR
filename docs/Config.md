<p align="center">fHDHR    <img src="images/logo.ico" alt="Logo"/></p>

---
[Main](README.md)  |  [Setup and Usage](Usage.md)  |  [Locast](Origin.md)  |  [Credits/Related Projects](Related-Projects.md)
---
**f**un
**H**ome
**D**istribution
**H**iatus
**R**ecreation

---

[Basic Configuration](Config.md)  | [Advanced Configuration](ADV_Config.md) |  [WebUI](WebUI.md)

---

The example config file contains all of the things that the typical user may need to fill out.

Please see the Advanced Configuration page for more information.

## fHDHR

Under `fhdhr`, you'll find 2 addresses listed. `0.0.0.0` works great for a listen address, however, it seems that SSDP works best if the discovery address is set to the IP to say that there is a service at.

````
[fhdhr]
# address = 0.0.0.0
# port = 5004
# discovery_address = 0.0.0.0
````

## Locast

Locast requires signin credentials, so add those.

````
[locast]
# username =
# password =
````
