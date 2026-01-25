# Additional Resources

## Glossar
- IPC: Inter-Process Communication (openLCA Server-Schnittstelle)
- LCIA: Life Cycle Impact Assessment
- GWP: Global Warming Potential

## FAQ
### Warum ein FastAPI-Service?
Weil Odoo SaaS/Browser stark eingeschränkt ist (keine freien Python-Imports/Requests). Der Service macht die Berechnung über HTTP verfügbar.

### Warum müssen Flow-UUIDs gepflegt sein?
Damit eine Komponente eindeutig auf einen LCA-Datenbank-Flow gemappt werden kann.

## Troubleshooting 
|Fehlerbild                                                | Lösung                                                          |
| -------------------------------------------------------- | --------------------------------------------------------------- |
| openLCA Ergebnis = 0                                     | Provider/Produktsystem prüfen, korrekte Datenbank/Methode wählen|
| Varianten übersprungen                                   | UUID/Gewicht auf Variante pflegen                               |
| Odoo Feld nicht gefunden                                 | technischen Feldnamen prüfen (Studio)                           |