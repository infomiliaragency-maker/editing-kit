---
name: editing-tagli
description: Tagli jump cut dei talking head dei clienti con separazione delle voci. Usa quando l'utente dice "/editing-tagli", "fai i tagli", "taglia il girato", "si sente la voce di chi detta", "c'è una voce esterna", "tagli troppo bruschi", "lascia un attimo prima che parli", "togli le ripetizioni", o quando dal girato bisogna scegliere le prese buone e decidere dove tagliare. Copre trascrizione con parlanti, scelta dell'ultima presa pulita, livelli e altezza della voce, confini decisi sugli spettrogrammi, margini di pochi centesimi nel silenzio, fotogrammi interi, verifica. Strumenti in _TOOLS.
---

# Tagli e voci

Obiettivo: nel montato parla solo il frontman, ogni frase è l'ultima presa pulita, l'attacco non è troncato e non
c'è niente di chi detta, nemmeno la coda più bassa.

## Prima

1. Profilo del cliente: nome del frontman (se manca, chiedilo), soglie misurate sulle riprese precedenti.
2. Script del video, dall'utente: serve per scegliere le prese.
3. L'audio su cui si decide è quello **elaborato** da CapCut (riprese intere con "Migliora voce", esportate): è quello
   che sente l'utente. Se non c'è ancora l'export, lavora sul grezzo ma usa soglie dal fondo e controlla il risultato
   sull'export appena arriva.
4. Girato a frame rate variabile (tipico dei file passati da WhatsApp): va normalizzato a 30 fps costanti prima di
   entrare in CapCut, e si importa la copia normalizzata.

## Procedura

Cartella di lavoro: `<cartella video>/_build/`. Strumenti: `_TOOLS/` del kit.

1. **Trascrizione con parlanti**, tutte le riprese insieme:
   `python3 trascrivi.py ~/Downloads/<video>/IMG_*.MOV --out _build/diarizzazione --diarizza --parole-chiave "termini,del,cliente"`
2. **Analisi**: `uv run voci.py analizza <ripresa> --out _build/analisi` per ogni ripresa (stampa il fondo), poi
   `uv run voci.py parlanti _build/analisi <ripresa> _build/diarizzazione/<ripresa>.json`. Il frontman è il più
   forte; chi detta di solito 7-12 dB sotto e con altezza diversa.
3. **Scelta delle prese.** Per ogni frase dello script tieni l'ultima presa completa e pulita del frontman. Fuori:
   lettura del titolo, "ripartiamo", "si vede il mio viso?", prese interrotte, parole di chi detta. Se due frasi
   consecutive sono la stessa presa con solo silenzio in mezzo, sono un taglio unico. Una frase che il girato tronca
   si toglie, non si rattoppa.
4. **Confini proposti**: per ogni frase inizio e fine dalle parole diarizzate del frontman.
5. **Confini decisi a vista**, tutti, non solo i dubbi:
   `uv run spettrogrammi.py --ripresa <ripresa> --analisi _build/analisi --diar _build/diarizzazione/<ripresa>.json --frontman speaker_1 --punti "t1:inizio frase,t2:fine frase,..." --out _build/spettri/<ripresa>`
   e leggi ogni pagina come immagine. Per i casi stretti `--stretto` (0.8 s, griglia a 20 ms).
   - inizio (`voce_da`): primo istante di energia del frontman, consonante compresa (la "s" e la "f" stanno sopra
     i 2 kHz e nello spettrogramma si vedono poco: guarda il livello verde che sale);
   - fine (`voce_a`): dove finisce la sua coda, prima di qualunque suono dopo;
   - se le due voci sono attaccate, il punto più basso fra le due.
   Scrivi `_build/confini.json` (formato in `_TOOLS/LEGGIMI.md`); `"fine_fissa": true` dove la rifinitura
   automatica spingeva la fine a ridosso dell'altra voce.
6. **Tagli**: `python3 tagli.py calcola _build/confini.json --analisi _build/analisi --out _build/tagli.json`
7. **Verifica**: `python3 tagli.py verifica _build/tagli.json --analisi _build/analisi`. Deve dire 0 ms di altezza da
   chi detta fuori dalla voce. Il suono residuo accettabile è solo fondo che oscilla fra -79 e -76 dB.
8. **Pannelli finali**: rifai gli spettrogrammi sui tagli veri (`--punti` con `da` e `a` di ogni taglio, `--stretto`)
   almeno per le fini spostate dalla rifinitura e per i confini attaccati. Correggi e ricalcola.
9. Se una frase ha inizio e fine a margine zero e la coda accorciata, cerca un'altra presa della stessa frase con
   un po' di silenzio attorno: allargare il margine riporterebbe dentro chi detta.
10. Un lapsus dentro una frase si può togliere se il taglio regge: prepara più tagli candidati, ritrascrivili e tieni
    quello che si legge pulito. Chiedi prima all'utente.

## Numeri e trappole (misurati su una serie di video girati con iPhone)

- **Il silenzio si misura dal fondo.** Riprese iPhone con gate: fondo -86 dB, silenzio vero sotto -79. Una versione
  che considerava silenzio tutto sotto -55 lasciava 5.9 s di suono non del frontman in 58 tagli su 71, e si sentiva.
- **Il volume non separa le voci.** Chi detta a volte arriva forte quanto il frontman.
- **L'altezza aiuta ma non basta.** Chi detta 250 Hz di mediana contro 140, però chiude le frasi scendendo sotto i
  180 Hz, e il frontman enfatizzando sale oltre 220.
- **Il classificatore di timbro** (MFCC, 97% sui frame interni alle parole) sbaglia proprio sui confini e sui tratti
  bassi. Sui confini decide lo spettrogramma: 102 confini su 142 corretti a mano.
- **Margini**: al massimo 0.08 s prima e 0.05 dopo, solo nel silenzio e 25 ms prima di qualunque suono. Con 0.22 s
  entravano le code; con il taglio sull'attacco calcolato da -40 dB la consonante sembrava troncata. Con voci
  attaccate molti inizi e fini restano a margine zero: va detto nel resoconto.
- **Fotogrammi interi**: a 30 fps e velocità 1.03 un fotogramma sono 34 ms di sorgente. Il pezzo che manca si prende
  dal silenzio; se non c'è si toglie dalla coda, al massimo 32 ms.
- **Soffi senza voce in coda** (respiro, rilascio della parola) con chi detta ancora zitto: dentro, altrimenti
  l'aggancio ai fotogrammi taglia la vocale.
- **La diarizzazione sul montato non trova le code**: dava un parlante solo anche su una versione bocciata.
- **La cache audio di CapCut** (`Resources/audioAlg/`) è codificata: non usarla per analizzare, serve l'export.

## Sull'audio elaborato da CapCut

Export WAV della timeline delle riprese intere (skill `editing-capcut`). Si divide per ripresa con i tempi del
progetto, si riporta al tempo sorgente (velocità), poi si rifanno `voci.py analizza` e `tagli.py verifica` sui pezzi.
Lo script si scrive in `_build/` del video.
- L'export anticipa di 5 ms sul grezzo (misurato su 4 riprese, correlazione dei livelli sopra 0,9): va compensato.
- "Migliora voce" alza il fondo da -85 a circa -63 dB e fa sentire code e attacchi bassi: su un video quattro
  confini erano stretti sull'attacco o sulla coda del frontman.
- Un'altezza fra 185 e 225 Hz attaccata all'attacco o alla coda, con l'armonica che continua dentro la parola, è del
  frontman (vocali finali "-e", "-i", attacchi): guardarla sullo spettrogramma stretto prima di stringere il taglio.

## Dopo i tagli

- `capcut.py taglia` (skill `editing-capcut`), oppure `remotion.py parlato` (skill `editing-remotion`).
- Audio del montato ricostruito e ritrascritto (`trascrivi.py`) per sottotitoli e piano b-roll.
- Controllo dei salti di livello della voce fra un pezzo e l'altro.
- Se è una nuova versione: sottotitoli e b-roll vanno riportati sui tempi nuovi passando per il tempo nella ripresa
  sorgente (`sottotitoli_capcut.py riallinea`, `riallinea_broll.py`).
- Nel MANIFEST: versione, regole, numeri della verifica, tagli a margine zero.
