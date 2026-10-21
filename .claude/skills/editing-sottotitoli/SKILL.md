---
name: editing-sottotitoli
description: Sottotitoli a tempo nei video dei clienti, con lo stile del cliente, in CapCut o in Remotion. Usa quando l'utente dice "/editing-sottotitoli", "fai i sottotitoli", "metti i sottotitoli a tempo", "crea un template dei sottotitoli", "il sottotitolo è sbagliato", "i sottotitoli non sono a tempo", o dopo nuovi tagli che spostano le parole. Copre stile per cliente ricavato da un video già sottotitolato o dal sito del cliente, proposta dei blocchi, rilettura a mano, scrittura nel progetto, riallineamento dopo nuovi tagli, verifica dei tempi sull'audio del progetto. Strumento sottotitoli_capcut.py in _TOOLS.
---

# Sottotitoli

## Stile

Lo stile è del cliente e sta nel profilo (`CLIENTI/<Cliente>/PROFILO.md`): un json per CapCut (per esempio
`CLIENTI/<Cliente>/ASSET/SOTTOTITOLI/stile_sottotitoli_<cliente>.json`) e un'intestazione .ass per l'anteprima.

Per un cliente nuovo, in quest'ordine:
1. **Da un video che l'utente ha già sottotitolato in CapCut**: dal suo progetto si prendono il materiale testo
   (font, corpo, colore, bordo, posizione), il segmento e la traccia, e si mettono in un json con le chiavi
   `regole`, `stile_testo`, `materiale_testo`, `segmento`, `animazione`, `traccia`. Le regole dei blocchi si
   misurano sui suoi sottotitoli: caratteri per blocco, a capo, durata minima, stacco.
2. **Dal sito del cliente**: font e colori letti dalle pagine, non inventati. Se il font non è installato si scarica
   e si mette nella cartella font di CapCut.
3. Se lo stile del sito è troppo piatto per il pubblico del video, si propone un bold leggibile (Poppins, Montserrat,
   Inter) bianco su bordo nero, due o tre parole per blocco, parole chiave in un colore acceso
   (`evidenzia_sottotitoli.py`).

Il default è a blocchi. Lo stile "dinamico" (parole che entrano a tempo, parole enormi dietro la persona) è stato
provato e bocciato: si propone solo se l'utente lo chiede, con un video di riferimento e un'anteprima di pochi secondi.

**I sottotitoli fatti a mano dall'utente non si toccano** se non lo chiede. Un template per serie, uguale su tutti i video.

## Procedura

```bash
cd _TOOLS
python3 sottotitoli_capcut.py proposta "<progetto>" --cartella <cartella video> --stile <stile.json>
```

1. **Proposta**: prende le parole dalle trascrizioni Scribe delle riprese intere (`<cartella>/_build/trascrizioni/`,
   quelle fatte per i tagli), le porta in timeline segmento per segmento con la velocità, divide in blocchi sulle frasi
   e scrive `<cartella>/sottotitoli_blocchi.json`. Solo se le trascrizioni delle riprese mancano trascrive la timeline
   con Whisper, che però anticipa le parole di 0,16 s in mediana (0,29 nel 10% dei casi): su un video 55 blocchi su
   86 partivano prima della parola, fino a 0,83 s.
   **Un blocco non scavalca mai un taglio e non parte prima della sua clip**: mostrerebbe la frase della clip dopo
   mentre scorre ancora quella prima.
   La divisione pesa anche i blocchi sotto mezzo secondo e quelli che finiscono su una parola che regge la successiva
   ("ED", "QUELLI"). Un blocco corto resta solo quando la clip è corta.
2. **Rilettura di tutti i blocchi**, a mano, contro il parlato vero (non contro lo script):
   - parole sbagliate dal riconoscimento ("sotto squadro" invece di "sottosquadro", una "a" sentita in più);
   - blocchi che spezzano un legame ("sullo stesso / pezzo", "tre voci diverse perché / rappresentano");
   - quando il frontman dice diverso dallo script, vale quello che dice, salvo errori evidenti da togliere;
   - i tempi si lasciano.
3. **Scrittura**, CapCut chiuso (lo script si ferma se è aperto e fa da solo il backup):
   `python3 sottotitoli_capcut.py scrivi "<progetto>" --cartella <cartella video> --stile <stile.json> --traccia "<nome dal profilo>"`
   Scrive anche `sottotitoli.srt`. Blocchi attaccati su tutto il parlato, anche sopra i b-roll e le grafiche, niente
   sull'outro. Con Remotion i blocchi vanno a `remotion.py montaggio` (skill `editing-remotion`).
4. **Verifica sulle parole delle riprese**: per ogni blocco la prima parola deve cadere dopo l'inizio del blocco di
   pochi centesimi (media attesa intorno a 0,035 s, massimo 0,07), nessun blocco prima della sua clip o con parole
   di due clip. A fine blocco si accetta lo stacco di un fotogramma dello stile.
5. **Volti**: `uv run volti.py` sull'anteprima o sull'export. Dove il blocco cadrebbe sul viso si sposta (`y` per
   blocco) o, se non c'è spazio, si accorcia.
6. Anteprima con i sottotitoli e un controllo a occhio dei blocchi più lunghi.

## Quando cambiano i tagli, o i sottotitoli sono fuori tempo

Non si ritrascrive da capo perdendo le correzioni a mano:

```bash
python3 sottotitoli_capcut.py riallinea "<progetto>" --cartella <cartella video> --stile <stile.json> --traccia "<nome>"
python3 sottotitoli_capcut.py scrivi    "<progetto>" --cartella <cartella video> --stile <stile.json> --traccia "<nome>"
```

`riallinea` tiene i testi dei sottotitoli che stanno nel progetto (anche quelli ritoccati dall'utente), aggancia ogni
parola alla stessa parola delle riprese nei tagli di adesso (difflib) e rifà inizio e fine. Le clip dove un blocco
scavalcava un taglio vengono ridivise per intero con le regole del cliente; le altre restano come erano state riviste.
Il json precedente resta in `_build/sottotitoli/`. Se CapCut ha tolto il nome alla traccia, `scrivi` la riconosce lo
stesso quando è l'unica traccia di testo, invece di aggiungerne una seconda.

## Trappole

- Concatenare pezzi AAC per l'anteprima sposta i sottotitoli di decimi verso la fine: l'audio va ricostruito in PCM
  (`anteprima.py` lo fa).
- Senza la velocità di ogni segmento la trascrizione della timeline sfasa di secondi (a 1.03, 4 s su 2 minuti).
- Whisper spezza gli apostrofi ("C" + "'è"): lo strumento li riunisce.
- Due trascrizioni diverse dello stesso punto vogliono dire che lì non si capisce: non si sceglie una delle due in
  silenzio, si segnala all'utente.
