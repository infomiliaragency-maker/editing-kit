---
name: editing-broll
description: B-roll per i video dei clienti, trovati o generati, e il loro posizionamento nel montato. Usa quando l'utente dice "/editing-broll", "metti i b-roll", "aggiungi qualche b-roll", "cerca dei b-roll", "genera un b-roll", "sembra una foto", "sembra finto", "b-roll più realistici", "i video sembrano tutti uguali", "rifai i b-roll", "b-roll nuovi", o quando un video va coperto con immagini di reparto, prodotto o processo. Copre la quota di b-roll nuovi per video, libreria del cliente, girato vero (canale YouTube, Drive), stock Pexels, generazione su fal da fotogrammi veri (Veo, Kling, Topaz), misura del movimento, controllo dei difetti, piano sulle frasi, anteprima del piano, agganci ai tagli, copie per CapCut. Strumenti in _TOOLS.
---

# B-roll

Un b-roll regge se sembra girato dal cliente, si muove e dice la stessa cosa della frase che copre.

## Quota di clip nuove

**Almeno il 65% dei b-roll di ogni video sono clip nuove**, mai usate in altri video, sia contando le clip sia contando
i secondi: con la libreria riciclata i video escono tutti uguali. Il resto può venire dalla libreria, ma una clip
riciclata va in un solo video della stessa campagna.

Prima di scegliere, fai l'elenco delle clip già usate negli altri video del cliente (tracce b-roll dei progetti o
`BROLL_USATI/`). Ricicla solo quelle che sono comparse al massimo in un video. Alla fine controlla la varietà su un
provino con un fotogramma per clip, raggruppato per video: due scene quasi uguali in video diversi contano come riciclo.

Eccezione: se lo stock non rappresenta il mondo del cliente (un processo molto specifico, attrezzature riconoscibili),
le clip fatte per quella serie valgono più dello stock generico. In quel caso la quota si concorda con l'utente.

## Dove cercare, in quest'ordine

1. **Girato vero del cliente che si muove già**: video del canale, foto e video su Drive
   (`rclone backend copyid gdrive: <id> <dest>`). Si ritaglia in verticale e si ingrandisce con Topaz:
   `python3 genera_broll.py ingrandisci-video clip.mp4 --out clip_hd.mp4 --fattore 2` (x3 per le sorgenti a 720p).
   È la fonte più credibile e l'unica giusta per le **mani**. Prima di usarla guarda i fotogrammi fitti (4-8 al
   secondo): i video dei canali hanno dissolvenze, scritte e sfocature a pochi decimi dal tratto buono. Le riprese al
   rallentatore o quasi ferme sembrano foto: meglio usarle come fotogramma di partenza.
2. **Libreria del cliente** (tabella in `CLIENTI/<Cliente>/PROFILO.md`), dentro la quota del 35%. Misura il tratto:
   `python3 movimento_broll.py <clip> --da <offset> --durata <secondi>`.
3. **Stock Pexels** per tutto quello che il cliente non ha girato (uffici, magazzino, linee, controlli):
   `uv run stock.py cerca <etichetta> "V:query verticale" "query" --cartella <lavoro>`, guarda il provino, poi
   `uv run stock.py prepara <nome> --id <id> --da 0 --a 8 [--x 0.5] --cartella <lavoro>` e guarda la striscia.
   Criteri e divieti sono nell'`--help`. I b-roll sopra un messaggio tecnico mostrano il mestiere di chi ascolta,
   non un mestiere vicino.
4. **Animazione da un fotogramma vero**, quando il girato vero è fermo, corto o sfocato:
   `python3 genera_broll.py fotogramma <video> --t 30.55 --out base.jpg --verticale`
   `python3 genera_broll.py ingrandisci-immagine base.jpg --out base_hd.jpg`
   `python3 genera_broll.py anima base_hd.jpg --prompt "<azione>. Camera movement is slow and steady, no cut, no zoom blur. Nothing new enters the frame, objects keep their exact shape, no text appears. Quiet documentary footage, natural light, real time." --out AI_n.mp4 [--modello kling]`
   Veo per acqua, nebbia, film che scorre. **Kling per oggetti rigidi con la camera che si muove** (rastrelliere, pile
   di pezzi): su una rastrelliera Veo ha fatto staccare e oscillare i pezzi tre volte su tre.
5. **Generazione da zero** (nano-banana poi Kling o Veo), quando il materiale vero è finito o non c'è niente da cui
   partire. Va detto all'utente.
6. **Scena costruita**: quando lo stock non ha la scena (un software, un'interfaccia, un modello 3D), si costruisce in
   una pagina web e si registra.

Ogni clip nuova entra nella libreria del cliente con provenienza, tratto pulito e movimento, in un
`DA_DOVE_VENGONO.md` accanto alle clip. Prefissi dei nomi `VERO_`, `AI_`, `STOCK_`.

Con molte clip da trovare si possono dividere le ricerche stock fra più agenti in parallelo, uno per video, con un
brief comune (criteri, divieti, varietà) e un file di selezione ciascuno, che gli altri leggono per non ripetere id o
scene. Le loro scelte si ricontrollano sempre sulle strisce prima di accettarle: su 26 clip ne sono state scartate 3.

## Controllo di ogni clip, prima del piano

1. Movimento sul tratto che finisce nel montaggio: almeno 2; fra 1.2 e 2 solo sotto 1.5 s; sotto 1.2 mai.
2. Clip generate: griglia di 12 fotogrammi sull'intera clip, poi 4-8 al secondo sui passaggi dubbi. Si tiene solo il
   tratto pulito e la clip finale si taglia lì, così nessuno usa per sbaglio i secondi con i difetti.
3. Stock: fotogrammi a piena risoluzione per scritte e loghi (spesso entrano a metà clip), volti in camera, pose.
4. Ingrandimento: al massimo 1.35 dalla sorgente, oltre la clip diventa morbida.
5. Clienti di medicina estetica: niente iniezioni, aghi, siringhe o sangue, nemmeno nello stock (Meta può bloccare).

## Cosa è stato bocciato

- Scene AI generate da zero quando c'era materiale vero: "sembra finto", un film sull'acqua "poco credibile".
- Clip quasi ferme sopra il parlato: "non dovevi mettere immagini ma sempre video". Movimento misurato con
  `movimento_broll.py`: sotto 1 sembra una foto (0.06 e 0.37 bocciate), 1-3 lento (1.12 usata solo breve), oltre 4
  si muove (7.8, 14.4).
- Animazioni 3D decorative nel montato: tolte tutte, solo b-roll realistici.
- Veo che a metà clip inventa difetti (un pezzo che vola, una maniglia che si allunga, fori in più): si guarda la
  clip fotogramma per fotogramma e si tiene solo il tratto pulito.
- La stessa libreria riciclata su tutti i video: "stanno uscendo tutti uguali".
- Stock da spot (sorrisi, cappellino e badge, fondale grigio da studio), clip con la mascherina, Veo su superfici
  lucide viste dall'alto (il riflesso diventa un disco, la trama si schiarisce a chiazze), Veo su fotogrammi con
  scritte in dissolvenza (tornano come lettere fantasma).

## Piano sulle frasi

1. Parti dalla trascrizione del montato con i tempi in timeline. Se il progetto è stato toccato dopo l'ultimo
   manifest, ricostruisci l'audio dalla traccia principale e ritrascrivilo: le posizioni dei b-roll le leggi dal
   progetto, non dal manifest (l'utente sposta e toglie clip a mano).
2. Ogni clip copre una frase o un pezzo di frase che dice la stessa cosa, ed entra sulla parola che la nomina o sul
   gesto che mostra. Negli elenchi ("pezzo, processo, volumi, controlli") uno stacco per parola.
3. Densità: la decide l'utente per video. Se non è detto, 3-4 clip nei tratti densi, si coprono i tratti astratti e
   si lascia il volto sulle frasi forti e sulla chiusura. Quando si rifanno i b-roll di un video montato, si tengono
   le posizioni che ci sono.
4. **Mai coprire una dimostrazione vera**: il frontman che prende in mano il pezzo resta scoperto.
5. **Agganci**: inizi e fini nella pausa fra due parole, mai a metà parola. Un confine che cade entro 0.2 s da un
   taglio del girato va sul taglio, altrimenti si vede il salto del volto per qualche fotogramma. Fra due b-roll
   consecutivi niente volto per meno di mezzo secondo.
6. **Durata**: tratto usato + offset non oltre la durata della clip. `capcut.py broll` si ferma se succede.
7. Scrivi `_build/piano_broll.json` (formato in `_TOOLS/LEGGIMI.md`).
8. **Anteprima del piano prima di toccare CapCut**:
   `python3 anteprima.py "<progetto>" --out ANTEPRIMA_broll.mp4 --stile-ass <.ass> --piano _build/piano_broll.json --cartella-clip <dir>`
   poi un provino con tre fotogrammi per b-roll (subito dopo l'inizio, a metà, subito prima della fine).

## Nel progetto

1. Copie delle clip scelte in `<cartella video>/BROLL_USATI/` e nella cartella da cui il progetto importa i b-roll
   (`~/Downloads/<video>/BROLL/`: leggila dai percorsi dei media nel progetto). CapCut non legge il Desktop. Gli
   originali della libreria restano dove sono.
2. Import delle clip nuove dall'interfaccia di CapCut (skill `editing-capcut`), solo con il via dell'utente.
3. Con CapCut chiuso e dopo il backup:
   `python3 capcut.py broll "<progetto>" --piano _build/piano_broll.json --cartella-clip ~/Downloads/<video>/BROLL --outro <outro del cliente> --traccia "<nome dal profilo>"`
   La traccia b-roll ha volume zero, velocità 1, nessun color e nessun effetto audio.
4. Controllo: `anteprima.py`, poi un fotogramma a metà di ogni b-roll in un provino (`VERIFICA_montaggio.jpg`), e
   uno a cavallo di ogni confine vicino a un taglio.

Con il metodo Remotion o ibrido lo stesso `piano_broll.json` va a `remotion.py montaggio` (skill `editing-remotion`).

## Quando l'utente ritocca i tagli

In CapCut la traccia dei b-roll non segue i tagli ritoccati: un taglio allungato di 4 fotogrammi lascia tutti i
b-roll successivi in anticipo, e dove un b-roll finiva su un taglio si vede il volto prima del salto. Prima di
consegnare di nuovo un progetto che l'utente ha toccato:

```bash
python3 riallinea_broll.py "<progetto>" --piano <video>/_build/piano_broll.json --riferimento <video>/_BACKUP_CAPCUT_prima-broll_<data>
python3 riallinea_broll.py ... --scrivi --dest <cartella video>     # CapCut chiuso
```

Ogni b-roll torna sulla frase del piano seguendo i tagli di adesso. Quelli che l'utente ha spostato a mano restano
fermi e vengono segnalati. I sottotitoli si riallineano con `sottotitoli_capcut.py riallinea` (skill `editing-sottotitoli`).
