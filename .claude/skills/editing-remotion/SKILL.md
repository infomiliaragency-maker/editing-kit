---
name: editing-remotion
description: Montaggio dei video dei clienti con il metodo Remotion o ibrido, renderizzato a file. Usa quando l'utente sceglie "Remotion" o "ibrido" alla domanda sul metodo di /editing, o dice "/editing-remotion", "montalo con Remotion", "renderizza il video", "zoom sui tagli", "transizioni con swoosh", "grafiche animate", "musica di sottofondo", "apri lo Studio". Usa gli stessi tagli, piano b-roll e sottotitoli del metodo CapCut e li trasforma in un export MP4 con zoom morbidi, transizioni con effetto sonoro, sottotitoli, grafiche e musica. Strumento remotion.py in _TOOLS, progetto in _REMOTION.
---

# Metodo Remotion

Il montaggio è codice React (Remotion) che si renderizza a MP4. Niente progetto CapCut, niente interfaccia da
cliccare: il risultato è un file, che l'utente guarda e approva.

## Quando conviene, e quando no

| Conviene | Resta meglio CapCut |
|----------|---------------------|
| Zoom sui tagli, transizioni con effetto sonoro, grafiche animate, musica | L'utente vuole rimettere le mani sulla timeline dopo |
| Tanti video uguali di struttura (serie), render in batch | Serve "Migliora voce" e non c'è ancora l'audio elaborato |
| CapCut è occupato o l'utente sta usando il Mac (Remotion non tocca l'interfaccia) | Il cliente ha già un progetto modello in CapCut da copiare |

L'**ibrido** prende il meglio dei due: tagli, color e voce in CapCut (ritoccabili a mano), tutto il resto in
Remotion. Il metodo lo sceglie l'utente ogni volta (lo chiede `/editing`); questa tabella serve per consigliare.

## Cosa resta identico al metodo CapCut

Le regole dell'area valgono tutte: solo la voce del frontman (regola 1), b-roll veri e in movimento (regole 5 e 10),
si consegna con i numeri (regola 6), nome di chi parla mai dedotto (regola 7), loudness non normalizzata se l'utente
non lo chiede (regola 8), girato copiato nella cartella del video (regola 9), niente grafiche sui volti (regola 11),
sottotitoli anche sopra le grafiche (regola 12).

Tagli, piano b-roll e sottotitoli si fanno con le skill di sempre (`editing-tagli`, `editing-broll`,
`editing-sottotitoli`), negli stessi file: `_build/tagli.json`, `piano_broll.json`, `sottotitoli_blocchi.json`.
Le durate dei tagli sono calcolate come `capcut.py taglia`, quindi lo stesso piano funziona con tutti i metodi e un
video si può passare da un metodo all'altro.

## Il flusso

```bash
cd _TOOLS
V="../CLIENTI/<Cliente>/<cartella video>"
python3 remotion.py parlato     "$V"                       # tagli -> _remotion/public/parlato.mp4
python3 remotion.py sottotitoli "$V" --stile <stile.json>  # solo se sottotitoli_blocchi.json non c'è
#   rilettura a mano dei blocchi, come sempre
python3 remotion.py montaggio   "$V" --outro <outro.mp4> --stile <stile.json> [--piano piano_broll.json --cartella-clip DIR] [--sottotitoli blocchi|ref2|nessuno] [--transizioni auto|nessuna] [--senza-zoom]
python3 remotion.py render      "$V" --anteprima           # ANTEPRIMA_remotion_540p.mp4, circa 2 s di render per 1 s di video
python3 remotion.py render      "$V"                       # EXPORT_remotion.mp4, 1080x1920
python3 remotion.py studio      "$V"                       # Remotion Studio nel browser, per guardare e ritoccare
```

| Passo | Cosa fa, cosa controllare |
|-------|---------------------------|
| `parlato` | taglia e unisce le riprese a 1.03, verticale 1080x1920 a 30 fps. Audio da `_build/elaborato/<ripresa>.wav` se c'è (voce già passata da "Migliora voce"), altrimenti il grezzo: **dirlo nel resoconto**, perché senza CapCut non c'è "Migliora voce". Girato HDR convertito in SDR con il colore tarato su CapCut. Controlla che la durata stampata sia quella attesa |
| `sottotitoli` | stessi blocchi di `sottotitoli_capcut.py` (parole da Scribe sulle riprese, nessun blocco a cavallo di un taglio). Non sovrascrive un `sottotitoli_blocchi.json` già riletto senza `--rifai` |
| `montaggio` | scrive `_remotion/montaggio.json` e collega b-roll, outro, effetti sonori in `_remotion/public/` (link fisici, zero spazio in più). Le clip HDR le converte. Legge da sé `grafiche.json` e `musica.json` del video se ci sono |
| `render` | un export precedente va in `_build/export_precedenti/`, mai cancellato |

## Metodo ibrido

Tagli, velocità, color e "Migliora voce" in CapCut (l'utente può ritoccarli a mano), export pulito senza
sottotitoli, b-roll e outro. Al posto di `parlato`:

```bash
python3 remotion.py da-capcut "$V" --progetto "<progetto CapCut>" --export "$V/EXPORT_capcut_montato.mp4"
```

L'export diventa il parlato così com'è, i tagli si leggono dalla traccia principale del progetto. Poi `sottotitoli`
(con `--rifai` se i tagli sono cambiati), `montaggio`, `render`.

## Cosa aggiunge rispetto a CapCut, e come si spegne

| Elemento | Default | Si cambia con |
|----------|---------|---------------|
| Zoom morbido sui jump cut: 1.0 e 1.12 alternati, curva ease in-out di 0,6 s, deriva lentissima (0,006 al secondo), origine al 32% dell'altezza | acceso | `--senza-zoom`; `--zoom 1.08 --deriva 0.003` per girato a bassa risoluzione o volto basso; livelli e rampa in `montaggio.json` → `zoom` |
| Transizioni all'entrata e all'uscita di ogni b-roll, alternate: swoosh (whip pan + motion blur + whoosh) e flash (lampo caldo + otturatore) | acceso | `--transizioni nessuna`; una per una in `montaggio.json` → `transizioni` |
| Push-in lento sui b-roll (1.0 → 1.08) | acceso | `push_in: false` per clip nel piano |
| Sottotitoli `blocchi`: lo stile del cliente (font, colori e posizione dal suo stile json), parole chiave nel colore del brand (`parole_in_blu` dello stile o `_build/parole_blu.json` del video) | `blocchi` | `--sottotitoli ref2`: riga piccola parola per parola + frase grande; `dinamici` esiste ma è stato bocciato, si propone solo con un riferimento e un'anteprima di pochi secondi |

**Prima volta per un cliente:** mostrare l'anteprima e chiedere all'utente se zoom e transizioni vanno bene per
quel cliente, poi scrivere la risposta nel suo `PROFILO.md`. Molti clienti vogliono solo lo zoom morbido e
dissolvenze semplici, niente swoosh né flash né transizioni che ruotano: in quel caso `--transizioni nessuna`.

## Grafiche animate

`<video>/grafiche.json` con `tema` (fondo, testo, accento, accento_scuro, font titoli e corpo) ed `elenco` di grafiche.
Ogni grafica entra sulla parola che la nomina, con i tempi presi da `sottotitoli_blocchi.json` → `parole`.

| Tipo | Componente | Cosa è |
|------|------------|--------|
| `nome` | `Grafiche.tsx` | sottopancia con nome e ruolo (nome e cognome completi) |
| `etichetta` | `Grafiche.tsx` | cartellino numerato, di solito sopra un b-roll |
| `scheda` | `Grafiche.tsx` | tutto schermo, titolo e voci con `at` sulla parola detta. Contenuto fra 260 e 1150 px, il sottotitolo sotto al solito posto; l'ultima voce resta almeno 2 s |
| `titolo`, `capitolo`, `firma`, `passaggio` | `Editoriale.tsx` | tipografia grande e animata, serif del cliente: è lo stile da preferire ai cartellini |
| `tavola` | `Tavola.tsx` | tavola dei numeri a tutto schermo: etichetta, barra, titolo con `*parola*` nel colore d'accento, righe voce/valore, elenco, `apertura` per la copertina |

I campi di ogni tipo sono nel commento in testa al componente. Ogni elemento ha `y` in px: si sceglie con
`volti.py` dove non ci sono volti né sottotitoli. Se il volto è basso nell'inquadratura, anche i sottotitoli si
spostano per blocco (`y` in `sottotitoli_blocchi.json`) dopo aver misurato il mento, tenendo conto dello zoom.
`--via-sotto-schede` toglie i sottotitoli sotto le schede, ma la regola è tenerli.

Le grafiche con numeri si scrivono sempre in codice, mai con un modello di immagini: sbaglia cifre e tipografia.

## Musica di sottofondo

Sui reel organici va messa senza chiederlo.

```bash
python3 musica.py --prompt "<genere, strumenti, umore, bpm, strumentale>" --durata 80 --out "$V/_build/musica_a.wav"
```

Due o tre candidate, misurate secondo per secondo (possono finire prima della durata chiesta). Poi
`<video>/musica.json`: `{"file": "...", "offset": 0, "punti": [[0, 0.5], [2.5, 0.12], ...]}`, volume 0-1 per punti
interpolati. Bassa sotto il parlato, più alta dove nessuno parla; quasi 3 s di dissolvenza fra musica piena e
parlato, 1,2 s negli altri passaggi. La musica non si ascolta: va detto nel resoconto.

## Ritocchi a mano

- Un singolo video: si modifica `<video>/_remotion/montaggio.json` e si rilancia solo `render`. Dopo un nuovo
  `montaggio` le modifiche a mano si perdono: annotarle nel MANIFEST.
- Un elemento nuovo per tutti i video (una grafica, uno stile di sottotitoli): componente in
  `_REMOTION/src/templates/`, letto da `src/montaggio/Montaggio.tsx`. Controllo con `npx tsc --noEmit` in `_REMOTION/`.
- Un video senza girato (presentazione animata): composizione a sé in `_REMOTION/src/presentazioni/<nome>/`,
  registrata in `src/Root.tsx`.

## Video senza girato e voiceover

```bash
uv run voiceover.py genera <testo.json> --out <cartella>
uv run voiceover.py verifica <cartella>
```

Motori e campi di `testo.json` nell'`--help`. Per i reel conviene `eleven-v3-fal` o `gemini-38`; Chatterbox con un
riferimento sintetico esce piatta, Kokoro è troppo robotica (e il modello non è nel kit). Prima di scegliere una
voce, prove alla cieca sulle prime battute livellate a -16 LUFS. Le parole inglesi e i nomi dei brand vanno scritti
come si pronunciano in `pronuncia`, poi `verifica` le ritrascrive con Scribe (sotto l'85% una battuta va ascoltata).
Il video si adatta alla voce, non il contrario: durate delle scene e partenze delle animazioni si ricavano dalle
parole trascritte. Non usare XTTS né i modelli F5 italiani: licenza non commerciale.

## Verifica

Le stesse di `editing-verifica`, più:
- durata dell'export uguale a `montaggio.json` → `durata`, fotogrammi del parlato uguali a `parlato.json`;
- provino di fotogrammi su parlato, b-roll, transizione, grafiche e outro, letto come immagine;
- `volti.py` sull'export: nessuna grafica e nessun sottotitolo sopra un viso;
- se il video esiste anche in CapCut: scarto audio per finestre di 10 s (atteso 0-5 ms).

Riferimento di collaudo: un video da 65 tagli rifatto con Remotion dagli stessi file del montaggio CapCut è uscito
con durata identica, sottotitoli e b-roll negli stessi istanti e audio allineato a CapCut entro 5 ms. Colore del
girato HDR: `hable` più saturazione 0,65 e gamma 1,1, scarto medio da CapCut 6 su 255 per canale.
