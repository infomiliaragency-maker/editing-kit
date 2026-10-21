# <Cliente> · profilo di montaggio

Cosa fa il cliente in una riga. Sito, profili social, dove stanno logo e materiali.

## Chi parla

| Video | Frontman | Fuori campo |
|-------|----------|-------------|
| | nome chiesto all'utente, mai dedotto | chi detta le battute, se c'è: altezza e livello misurati con `voci.py parlanti` |

Fondo delle riprese e soglia del silenzio (`voci.py analizza`):

## Stile

| Cosa | Valore | Dove |
|------|--------|------|
| Velocità | | |
| Color e audio | | progetto CapCut modello per `capcut.py prepara --modello` |
| Sottotitoli | | json di stile per `sottotitoli_capcut.py --stile`, intestazione .ass per `anteprima.py` |
| Nome della traccia sottotitoli | | |
| Outro | | (alcuni clienti non lo vogliono) |
| Zoom e transizioni Remotion | | risposta dell'utente alla prima anteprima |
| Musica | | sì sui reel organici, salvo indicazione |
| Nome della traccia b-roll | | |
| Palette e font | | |

Uno stile nuovo si ricava da un video già montato dall'utente: si leggono i materiali del suo progetto CapCut
(testo, effetti, velocità, audio) e si copiano in un json `stile_sottotitoli_<cliente>.json`. In mancanza, font e
colori dal sito del cliente.

## Librerie di b-roll

| Libreria | Cosa c'è | Note (provenienza, movimento, clip scartate) |
|----------|----------|---------------------------------------------|

## Video montati

| Video | Cartella | Progetto CapCut |
|-------|----------|-----------------|
