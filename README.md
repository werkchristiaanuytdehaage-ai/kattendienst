# 🐱 Kattendienst

Een speelse web-app om de **voederbakken** en **kattenbakken** van twee katten bij te houden.

- **2 voederbakken** met elk 4 voedingen. Lopen automatisch mee met twee voedertijden per dag (standaard 07:00 en 18:15). Melding bij nog 1 voeding over, NOOD-melding bij leeg, knop om weer op "vol" te zetten.
- **3 kattenbakken** met een snelheidsmeter (groen → oranje na 12u → rood na 24u). Melding "vuil" na 12u, NOOD-melding na 24u, knop om te resetten na verschonen.
- Werkt als **PWA**: te installeren op je telefoon-startscherm en werkt offline.
- Instellingen (⚙️ rechtsboven): namen en voedertijden zelf aanpassen.

De stand wordt lokaal op je apparaat bewaard (`localStorage`).

## Online zetten met GitHub Pages

1. Maak een nieuwe (lege) repository aan op https://github.com/new — bijvoorbeeld `kattendienst`. Niet aanvinken: README/licentie toevoegen.
2. Koppel deze map aan die repo en push (vervang `JOUW-NAAM`):

   ```bash
   git remote add origin https://github.com/JOUW-NAAM/kattendienst.git
   git branch -M main
   git push -u origin main
   ```

3. Ga in de repo naar **Settings → Pages**. Bij "Build and deployment" kies je:
   - **Source:** Deploy from a branch
   - **Branch:** `main` / `(root)` → Save

Na ~1 minuut staat de app op:

```
https://JOUW-NAAM.github.io/kattendienst/
```

Open die link op je telefoon → browsermenu → **"Zet op beginscherm" / "App installeren"**.

> Belangrijk: de PWA (offline + installeren) werkt alleen via deze https-link, niet door het bestand lokaal te openen.
