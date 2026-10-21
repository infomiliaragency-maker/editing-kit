# _REMOTION · progetto Remotion del kit

Si usa attraverso `_TOOLS/remotion.py` e la skill `editing-remotion`: qui dentro si entra solo per cambiare i modelli.
Prima volta: `npm ci` in questa cartella (lo fa `installa.sh`).

## Cosa c'è

| Cosa | Dove |
|------|------|
| Modello generico usato da ogni video (composizione `Montaggio`, props = `montaggio.json`) | `src/montaggio/Montaggio.tsx`, forma del json in `src/montaggio/tipi.ts` |
| Sottotitoli a blocchi con lo stile del cliente | `src/templates/captions/BlocchiCaptions.tsx` |
| Sottotitoli "Ref2" (riga piccola parola per parola + frase grande, riquadro rosso opzionale) | `src/templates/captions/Ref2Captions.tsx` |
| Sottotitoli dinamici (provati e bocciati, restano disponibili) | `src/templates/captions/DinamiciCaptions.tsx` |
| Zoom morbido sui jump cut | `src/templates/smoothZoom.ts` |
| Transizioni swoosh e flash con effetto sonoro | `src/templates/transitions.tsx`, suoni in `public/sfx/` |
| Grafiche `nome`, `etichetta`, `scheda` con tema colori e font del cliente | `src/templates/grafiche/Grafiche.tsx`, dati in `<video>/grafiche.json` |
| Grafiche editoriali `titolo`, `capitolo`, `firma`, `passaggio` | `src/templates/grafiche/Editoriale.tsx` |
| Tavola dei numeri a tutto schermo | `src/templates/grafiche/Tavola.tsx` |

I campi di ogni grafica sono nel commento in testa al suo componente.

## Comandi

```bash
cd _REMOTION
npx tsc --noEmit          # dopo ogni modifica ai componenti
npm run dev               # Studio con tutte le composizioni (per un video: remotion.py studio)
```

## Scelte del modello

| Scelta | Perché |
|--------|--------|
| Un modello unico guidato da `montaggio.json`, generato da `tagli.json`, `piano_broll.json`, `sottotitoli_blocchi.json` | gli stessi file del metodo CapCut, con più riprese |
| Girato HDR dell'iPhone convertito in SDR, tarato sul colore di CapCut | senza conversione esce grigio e slavato |
| Parole da Scribe sulle riprese, mappate sui tagli | Whisper sulla timeline tagliata anticipa di 0,16 s in mediana |
| Audio unito in PCM esatto al campione, codificato una volta | l'audio a pezzi in AAC ritarda a ogni giunzione; così lo scarto da CapCut è 0-5 ms |
| Nessuna normalizzazione della voce se non si chiede (`--loudness -14` per attivarla) | regola 8 |
| Media collegati con link fisici nella cartella del video, `--public-dir` al render | niente copie in `public/` |
| Grafiche: entrata 18 fotogrammi, uscita 14 (`ENTRATA`, `USCITA` in `Grafiche.tsx`), transizioni 9 fotogrammi per lato (`HALF` in `transitions.tsx`) | più veloci erano "troppo veloci, non danno il tempo di essere letti" |

## Licenza

Remotion è gratuito per chi lavora da solo e per aziende fino a 3 persone; oltre serve la licenza aziendale
(https://www.remotion.dev/license).
