---
name: editing-capcut
description: Scrittura dei progetti CapCut dal file per i video dei clienti. Usa quando l'utente dice "/editing-capcut", "crea il progetto su CapCut", "metti le clip in timeline", "applica color e audio", "migliora voce", "velocizza a 1.03", "aggiungi l'outro", "scrivi i tagli nel progetto", "CapCut sta elaborando troppe features", o quando bisogna leggere lo stato di un progetto, fare un backup o chiudere CapCut. Copre il flusso riprese intere, poi tagli, poi b-roll e outro, le sei copie del progetto, la sandbox dei media, le regole sull'interfaccia. Strumento capcut.py in _TOOLS.
---

# CapCut dal file

CapCut si pilota scrivendo `draft_info.json`, non a clic: l'interfaccia è web dentro CEF, i clic simulati sulle
caselle non arrivano e l'automazione a coordinate si rompe al primo pannello fuori posto.

Gli strumenti sono stati collaudati su CapCut per Mac 9.5.0. Con una versione diversa il formato del file può
cambiare: se `capcut.py stato` dà errori strani, controlla prima la versione (`defaults read
/Applications/CapCut.app/Contents/Info.plist CFBundleShortVersionString`) e dillo all'utente.

## Regole

1. **CapCut chiuso** mentre si scrive, altrimenti al salvataggio sovrascrive. `python3 capcut.py chiudi` rifiuta se
   CapCut è in primo piano (l'utente lo sta usando): in quel caso si chiede.
2. **Backup** prima di ogni scrittura: `python3 capcut.py backup "<progetto>" --dest <cartella video> --etichetta <cosa sto per fare>`.
3. **L'utente tocca i progetti.** Prima di riscrivere, `capcut.py stato` e confronto con l'ultima scrittura: durate
   dei tagli contro `tagli.json`, tempi dei sottotitoli contro `sottotitoli_blocchi.json`, b-roll contro
   `piano_broll.json`. Dove lo scarto supera mezzo fotogramma (0,017 s) ci ha messo le mani l'utente: si chiede prima
   di sovrascrivere. `stato` dice che un progetto è coerente con sé stesso, non che è ancora quello che avevi scritto.
4. **Sei copie**: `draft_info.json`, `.bak`, `template-2.tmp` e le stesse in `Timelines/<id>/`, con id diversi fra
   loro. `capcut.py` scrive in tutte cercando per ripresa e tempo. Uno script che cerca per id scrive in una sola.
5. **Dall'interfaccia solo**: creazione del progetto, import dei media (i permessi della sandbox li dà l'import),
   export. Prima di ogni clic o tasto: CapCut in primo piano, altrimenti niente. Catture solo della finestra
   (`screencapture -l <windowID>`). Il dialogo dei permessi macOS lo accetta l'utente. **Mai condividere**: niente
   TikTok, YouTube, "Share", "Sign in".
6. **Media fuori dal Desktop**: CapCut non li apre. Girato in `~/Downloads/<video>/`, b-roll in
   `~/Downloads/<video>/BROLL/`, con una copia del girato nella cartella del video. Se compare "Link media", si
   ricollega scegliendo un file della cartella con la spunta "Link media when selecting a folder", poi
   `python3 controlla_collegamenti.py` (vede le riprese scambiate, che `stato` non vede) e se serve `ripara_voce.py`.
7. **Normalizzazione loudness mai.** La casella "Normalize loudness" resta spenta su ogni clip, anche se il modello
   ce l'ha. `prepara` e `taglia` non la scrivono e la tolgono dai segmenti che riscrivono. Se `capcut.py stato` dice
   "NORMALIZZAZIONE LOUDNESS ATTIVA", si dice all'utente e solo dopo il suo sì, con CapCut chiuso e dopo il backup,
   `python3 capcut.py spegni-loudness "<progetto>"`.

## Il progetto modello

`capcut.py prepara` copia color, velocità e "Migliora voce" da un progetto modello del cliente. Per un cliente nuovo
l'utente ne crea uno in CapCut: una clip del girato con correzione colore intelligente a 0.8, HSL neutro, velocità
1.03, "Migliora voce" a 75, riduzione rumore e normalizzazione spente. Il nome va nel `PROFILO.md` del cliente.

## Il flusso

```bash
cd _TOOLS
python3 capcut.py lista                          # trova il progetto
python3 capcut.py stato "<progetto>"             # tracce, copie, audio, orfani, media mancanti
```

1. **Riprese intere con color e audio**, CapCut chiuso:
   `python3 capcut.py prepara "<progetto>" --modello "<progetto modello del cliente>" --riprese IMG_1,IMG_2,... --velocita 1.03`
   Copia dal modello color (effetto "color-adjustment" e HSL), velocità e "Migliora voce" a 75 sull'intera ripresa.
   La normalizzazione loudness del modello non la copia (regola 7).
2. **Elaborazione**: l'utente apre il progetto (o Claude, con CapCut libero) e si aspetta "Enhance voice applied".
   Una elaborazione per ripresa, non per taglio. Poi `capcut.py chiudi`.
3. **Export della timeline non tagliata** dall'interfaccia: è l'audio su cui si decidono i tagli (skill `editing-tagli`).
4. **Tagli**: `python3 capcut.py taglia "<progetto>" --tagli _build/tagli.json --velocita 1.03`
   Ogni taglio clona il segmento della sua ripresa intera: stesso color, stessa voce già elaborata (file della
   ripresa intera), nessuna normalizzazione loudness. Dice quanti tagli trovano la voce già elaborata e da quanti
   ha tolto la normalizzazione.
5. **Transizioni sui jump cut**, se l'utente li trova bruschi: `python3 transizioni.py "<progetto>" --durata 0.2 --fade 0.04`
   (dissolvenza "Mix" senza spostare i tempi e 40 ms di audio per lato; CapCut chiuso, dopo il backup).
6. **B-roll e outro**: `python3 capcut.py broll ...` (skill `editing-broll`).
7. **Effetti sonori**: `python3 sfx.py scrivi "<progetto>" --piano piano_sfx.json --da-progetto "<un progetto che li usa già>"`.
8. **Sottotitoli**: skill `editing-sottotitoli`.
9. **Anteprima**: `python3 anteprima.py "<progetto>" --out <cartella video>/ANTEPRIMA_540p.mp4 --stile-ass <dal profilo> --font-dir <dal profilo>`

Controllo da ripetere a ogni video: prima di `taglia`, `capcut.py stato` deve dire "file già elaborati" pari alle
riprese (CapCut ha finito); dopo, pari ai tagli. All'apertura non deve ripartire nessuna elaborazione.

## Interfaccia (quando l'utente dà il via e lascia il Mac)

- Clic con eventi Quartz (`uv run ui_capcut.py`), tasti con System Events; prima di ognuno, CapCut in primo piano.
  Catture con `screencapture -l <id>` della finestra di CapCut: i menu e i pannelli stanno in finestre di CapCut a
  livello più alto. **Le coordinate si leggono ogni volta dalla cattura**: la finestra può riaprirsi di un'altra
  dimensione, e una catena di clic a coordinate fisse finisce su pulsanti sbagliati (anche quelli di condivisione).
- Prima di digitare si controlla con una cattura che il dialogo sia davvero aperto: CapCut legge le lettere come
  scorciatoie (`B` divide la clip). Per entrare in una cartella conviene il doppio clic, che non digita niente.
- La home ordina i progetti per ultima modifica, quindi l'ordine cambia dopo ogni import: si ricattura prima di ogni
  clic su una riga, e dopo aver aperto un progetto si controlla il titolo nella barra.
- Home: "Create project" crea la cartella `MMDD`. Il nome si cambia a mano dalla home (clic destro, Rename).
- Import: il pulsante apre un menu "From device / From library". Nella finestra "Open": Cmd+Maiusc+G e il percorso;
  Cmd+A non seleziona, si clicca il primo file e si estende con Maiusc+freccia giù (o Maiusc+clic sull'ultimo).
- Export dei video finiti: Cmd+E (in `ui_capcut.py` il modificatore si scrive `command`, non `cmd`) apre la finestra
  "Export-<progetto>". Impostazioni di partenza: 1080P, bit rate Higher, H.264, mp4, 30 fps, audio a parte spento
  (circa 14,7 Mbps). Il percorso "Export to" è troncato e non si legge: si sceglie una cartella nuova dal pulsante
  accanto (Cmd+Maiusc+G, percorso, Invio, "Open"), così non si sovrascrivono export vecchi. CapCut salva in
  `<cartella>/<nome>/<nome>.mp4` più la copertina, e tronca il nome a 45 caratteri. La finestra finale si chiude solo
  con "Close", verificato sulla cattura. Per passare al progetto dopo: chiudere CapCut e riaprirlo, chiudere la
  finestra "Version update" se compare (senza aggiornare). Dopo ogni export si confronta la durata del file con quella
  del progetto. Se in primo piano compare un'altra app ci si ferma e si aspetta.
- Export dell'audio per `editing-tagli`: togliere la spunta a Video, scorrere il pannello, spuntare Audio, formato WAV
  (l'MP3 aggiunge ritardo in testa). CapCut salva nell'ultima cartella di export usata: il file va cercato e spostato
  nella cartella del video. La finestra "Audio exported" va chiusa con OK, altrimenti CapCut non si chiude.
- Caricamento su Drive con rclone: un file alla volta, `--drive-chunk-size 16M --timeout 30m`. La cartella di
  destinazione si indica **per id** (`"gdrive,root_folder_id=<id>:<file>"`): i nomi con gli accenti caricati da Mac
  sono in NFD e, passati per nome, fanno creare a rclone una cartella doppia. Il girato del cliente su Drive non si
  tocca mai.

## Com'è fatto il file (per quando serve metterci le mani)

- Tempi in microsecondi. `target_timerange` è la timeline, `source_timerange` il punto nel file. Nei progetti di
  CapCut la durata in timeline è sempre un numero intero di fotogrammi e la sorgente è timeline x velocità.
- Velocità: materiale `speeds` più `speed` sul segmento.
- HDR: ogni segmento ha `hdr_settings` (`mode`, `intensity`, `nits`). Nei progetti recenti CapCut mette `mode` 4, che
  sul girato SDR dell'iPhone scurisce e satura la pelle (saturazione del viso da 0,39 a 0,50). Con `mode` 1 l'export
  è identico al girato: si porta a 1 su tutte le sei copie, come per il color.
- Color: materiale `effects` con nome "color-adjustment" (smart color adjust 0.8) e `hsl`. Copiati su un b-roll gli
  applicano il color del girato: sui b-roll si tolgono e i campi `enable_*` vanno a false.
- Audio: `loudnesses` è la casella "Normalize loudness". Quando l'utente toglie la spunta, CapCut lascia il materiale
  e il riferimento e mette `enable` a false. Spenta vuol dire assente oppure `enable` false: `spegni-loudness` fa come
  CapCut, `taglia` la toglie del tutto (regola 7). `vocal_beautifys` (enable, `ambient_sound_level` 75,
  `production_path` con il segnaposto della cartella e `Resources/audioAlg/<prefisso>_<inizio>_<durata>.wav`,
  `time_range`), `realtime_denoises` con `is_denoise` false. Scritti nel file, CapCut li applica all'apertura
  ("Applying N features"). Il prefisso del file voce lo calcola CapCut: si legge dal progetto dopo la prima
  elaborazione.
- Traccia b-roll: video con `flag` 2, `render_index` 1, `volume` 0. Outro in coda alla traccia principale.
- Il nome scritto in `draft_meta_info.json` viene riportato al nome della cartella quando CapCut apre il progetto:
  il rinomino lo fa l'utente dalla home.
- Percorsi con accenti ("può") in NFD nel file: confronto sempre dopo `unicodedata.normalize("NFC")`.
- `unique_id` dei video lo assegna CapCut quando il media entra in timeline.
- La cache `Resources/audioAlg/` è codificata con una chiave per file: non si legge per analizzare l'audio.
- Transizioni: la prima va messa dall'interfaccia (pannello Transitions), poi si copia nel file. "Mix" è la dissolvenza.
- Effetti sonori: il materiale esiste solo dentro i progetti che lo usano, il file sta nella cache di CapCut.
