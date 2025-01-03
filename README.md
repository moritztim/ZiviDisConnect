![ZiviDisConnect](Logo/Light.png)
Eine bessere User Experience für ZiviConnect (in einer Excel Tabelle statt einer unfertigen mobile Web UI für 20 Mio. CHF).

## Was ist das?
Die Nutzeroberfläche des offiziellen Portals des Schweizer Zivildienst "ZiviConnect" ist fehlerbehaftet und unübersichtlich. Dieses Projekt enthält Werkzeuge, die bei der Verwendung von ZiviConnect helfen und die Benutzererfahrung verbessern sollen.

## Funktionen
- **Einsatzsuche**: Eine Tabelle mit allen relevanten Informationen zu einzelnen Pflichtenheftern auf einen Blick.
- **Kontaktliste**: Automatische Extraktion der Kontaktdaten aus Pflichtenheftern.
- **JSON Schema für Pflichtenhefter**: Ein Schema, das die Struktur von Pflichtenheftern definiert, wie sie von der API kommen.

## Verwendung
### Einsatzsuche
1. Die [ZiviConnect Einsatzsuche](https://ziviconnect.admin.ch/zdp/einsatz) öffnen
2. <details> <summary> Beliebige Filter setzen (siehe den Button rechts unter den Hauptfiltern `weitere Filter`) </summary> <img alt='Screenshots des "weitere Filter\" Button' src="img/Verwendung/Einsatzsuche/Schritte/2.png"/> </details>
3. Mit `f12` oder `Strg` + `Shift` + `I` die Entwicklerwerkzeuge öffnen
4. Den Tab `Netzwerk` auswählen
5. Auf der Webseite auf `Suchen` klicken
6. <details> <summary> In den Entwicklerwerkzeugen den Ersten Eintrag via Rechtsklick-Menü herunterladen </summary> <img alt="Screenshot des Rechtsklick-Menü" src="img/Verwendung/Einsatzsuche/Schritte/6.png"/> </details>
7. Die Datei zu `CSV` konvertieren, zum Beispiel mit [ConvertCSV](https://www.convertcsv.com/json-to-csv.htm)
8. Das Resultat in der [Excel Tabelle](Einsatzsuche.xlsx) im Arbeitsblatt `Suchresultate` einfügen
9. <details> <summary> Möglicherweise muss der Import der Daten konfiguriert werden. Hierbei als Trennzeichen das Komma `,` und als Texttrennzeichen das Anführungszeichen `"` verwenden. </summary>
    <img alt="Screenshot des Einfügemenüs in OnlyOffice" src="img/Verwendung/Einsatzsuche/Schritte/9a.png"/> <br>
    <img alt="Screenshot der Text Import Konfiguration in OnlyOffice" src="img/Verwendung/Einsatzsuche/Schritte/9b.png"/>
</details>

#### Optional: Zusatzinformationen aus Pflichtenheftern

10. Einzelnes Pflichtenheft öffnen
11. Schritte `3` bis `4` wiederholen
12. Mit `f5` oder `Strg` + `R` die Seite neu laden
13. In den Entwicklerwerkzeugen den Eintrag mit vom Typ `json` mit der Pflichtenheftnummer als Dateiname via Rechtsklick-Menü herunterladen
14. Die Datei in einem Ordner speichern
15. Schritte `10` bis `15` für alle Pflichtenhefte wiederholen
16. Die Dateien mit dem Python Skript [pflichtenheft_parser.py](pflichtenheft_parser.py) einlesen
17. Das Resultat in der [Excel Tabelle](Einsatzsuche.xlsx) im Arbeitsblatt `Pflichtenhefte` einfügen, in der Reihenfolge der Suchresultate.
