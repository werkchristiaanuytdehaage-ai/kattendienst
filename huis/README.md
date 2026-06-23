# 🏠 Spontaan sociaal

Een speelse app waarmee je in één oogopslag ziet of je vrienden zin hebben om af te spreken
— of juist even met rust gelaten willen worden.

Iedereen verschijnt als een Sims-achtig **personage met een menselijk gezicht** in een gedeeld
studentenhuis. De avatars **lopen** door het huis (bank, fauteuil, keuken, bij het raam…),
worden groter als ze vooraan staan, en hebben subtiele idle-bewegingen. Boven elk hoofd
zweeft een gekleurd "bolletje" (plumbob) met je stand — en je **gezichtsuitdrukking verandert
mee** met je stand (blij bij groen, gesloten/serieus bij rood):

| Kleur | Stand |
|------|-------|
| 🔴 donkerrood | Druk · liever met rust |
| 🟠 oranje | Open voor iets rustigs |
| 🟡 geel | Wel zin om wat te doen |
| 🟢 groen | Ik wil graag iets doen! |

De avatars rouleren vanzelf door het huis (bank, fauteuil, keuken, bij het raam…), net als
in de Sims.

## Avatars
De menselijke gezichten worden gemaakt met de **avataaars**-stijl van [DiceBear](https://dicebear.com)
(huidskleur, kapsel, haarkleur, kleding, bril — allemaal instelbaar, of druk op 🎲 voor een willekeurig
personage). De avatar-SVG's worden opgehaald van `api.dicebear.com` en daarna **lokaal gecachet**
(`localStorage`), zodat ze na de eerste keer ook offline werken. Er is geen account of API-sleutel
nodig voor DiceBear.

## Gebruik
- Open de app, maak je personage (naam + uiterlijk) en kies je stand. Geen wachtwoord nodig.
- Tik op je eigen avatar (of het chipje rechtsboven) om je stand te wijzigen.
- Tik op een vriend om te zien hoe die zich voelt en hoe lang geleden dat was.
- Installeerbaar als app: in Safari/Chrome → "Zet op beginscherm".

## Delen met vrienden (Firebase instellen)
Zonder Firebase werkt de app **lokaal**: je ziet alleen jezelf plus een paar demo-huisgenoten.
Om de stand écht live met vrienden te delen over apparaten:

1. Maak een gratis project op <https://console.firebase.google.com>.
2. Voeg een **Realtime Database** toe (kies regio `europe-west1`), start in testmodus.
3. Voeg een **Web-app** toe en kopieer de config-gegevens.
4. Plak die in `index.html` bovenaan het script bij `const FIREBASE_CONFIG = { … }`.
5. Klaar — de footer toont dan "🔄 live · zichtbaar voor je vrienden".

Datastructuur is simpel: alles staat onder `users/<id>` met `{ name, color, face, mood, updatedAt }`.

## Bestanden
- `index.html` — de volledige app (HTML + CSS + JS in één bestand)
- `manifest.json`, `sw.js`, `icon.svg` — PWA (installeerbaar, offline shell)

Losstaand van de Kattendienst-app in de hoofdmap; deze app leeft volledig in `huis/`.
