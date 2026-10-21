# EDITING KIT · istruzioni

Montaggio di video verticali parlati (talking head) dal girato al video pronto: tagli jump cut, velocità, color, audio,
b-roll trovati o generati, sottotitoli, grafiche, musica, outro, anteprima e collaudo con i numeri. Tre metodi: CapCut
scritto dal file, Remotion renderizzato da codice, o i due insieme.

Installazione e chiavi in [INSTALLA.md](INSTALLA.md). Se `.env` non c'è o gli strumenti non partono, prima si sistema
quello.

---

## Regole di scrittura

Valgono per i resoconti, i testi a schermo, i sottotitoli e i titoli.

- Sempre in italiano, con gli accenti giusti.
- Mai il trattino lungo: punto, virgola, due punti, o si riformula.
- Niente formule da AI: "non è X, ma Y", frasi a effetto in chiusura, coppie di aggettivi, parole da brochure
  ("ecosistema", "sinergia", "valore aggiunto"), riassunti finali che ripetono. Ogni frase deve poter essere detta a
  voce così com'è.
- Diretto e con i numeri. Si dice cosa è stato misurato e cosa no.

---

## Cosa entra e cosa no

| Entra | Non entra |
|-------|-----------|
| Montaggio del girato in CapCut o Remotion | Lo script del video: arriva dall'utente o dal cliente |
| Tagli, velocità, color, audio, sottotitoli, grafiche, musica, outro | Copy delle inserzioni e campagne |
| B-roll: libreria del cliente, girato vero, stock, generazione su fal | |
| Anteprime e controlli prima di passare il video all'utente | |

---

## Tre metodi di montaggio: si chiede ogni volta

Prima di ogni montaggio nuovo si chiede all'utente quale metodo usare.

| Metodo | Cosa esce | Dove |
|--------|-----------|------|
| **CapCut** | progetto CapCut scritto dal file, che l'utente apre, ritocca ed esporta | `_TOOLS/capcut.py`, skill `editing-capcut` |
| **Remotion** | MP4 renderizzato da codice, con zoom morbidi sui tagli, transizioni con effetto sonoro, sottotitoli animati | `_REMOTION/`, `_TOOLS/remotion.py`, skill `editing-remotion` |
| **Ibrido** | tagli, velocità, color e voce in CapCut; Remotion sopra l'export per b-roll, zoom, sottotitoli, grafiche e outro | `capcut.py` fino all'export, poi `remotion.py da-capcut` |

Tagli, piano b-roll e sottotitoli sono gli stessi file per tutti i metodi, e le regole qui sotto valgono per tutti.
Le regole 2, 3 e 4 riguardano solo CapCut. Il metodo con cui nasce un video si scrive nel suo MANIFEST e non si
richiede per i ritocchi.

---

## Dove sta il lavoro

| Cosa | Dove |
|------|------|
| Stato dei clienti e dei video | [00_INDICE.md](00_INDICE.md) |
| Regole di partenza, uscite da mesi di montaggi su clienti veri | [01_DECISIONI/REGOLE.md](01_DECISIONI/REGOLE.md) |
| Decisioni nuove dell'utente, con data | [01_DECISIONI/LOG_DECISIONI.md](01_DECISIONI/LOG_DECISIONI.md) |
| Profilo di montaggio di un cliente (chi parla, stile, librerie, progetto modello) | `CLIENTI/<Cliente>/PROFILO.md` |
| Cartella di un video nuovo | `CLIENTI/<Cliente>/<AAAA-MM>_<video>/`, struttura in `CLIENTI/_TEMPLATE/VIDEO/` |
| Strumenti | [_TOOLS/](_TOOLS/), guida in `_TOOLS/LEGGIMI.md` |
| Progetto Remotion (modello generico, componenti, effetti sonori) | [_REMOTION/](_REMOTION/), guida in `_REMOTION/LEGGIMI.md` |
| Lavoro Remotion di un video | `CLIENTI/<Cliente>/<video>/_remotion/`; export `EXPORT_remotion.mp4` |
| Progetti CapCut | `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/<cartella>/` |
| Media che CapCut deve leggere | `~/Downloads/<nome video>/`, mai sul Desktop: la sandbox di CapCut non li apre |

---

## Le regole che non si discutono

### 1. Nel montato parla solo il frontman

Nessuna voce di chi detta le battute, nemmeno la coda più bassa. Il silenzio si misura dal fondo della ripresa
(con un iPhone il fondo sta intorno a -86 dB, il silenzio vero sotto -79), non a occhio: dopo "Migliora voce" si
sente anche quello che nel file grezzo sta molto sotto il parlato. I confini dubbi si guardano sugli spettrogrammi,
uno per uno. Margine prima della voce di pochi centesimi, solo nel silenzio. Skill `editing-tagli`.

### 2. Prima color e audio sulle riprese intere, poi i tagli

Le riprese intere vanno in timeline, si applicano color e "Migliora voce", CapCut le elabora una volta per ripresa,
poi si taglia. I tagli si decidono sull'audio già elaborato, quello che sente l'utente. Tagliare prima costringe
CapCut a rielaborare la voce pezzo per pezzo a ogni versione.

### 3. CapCut si scrive dal file, chiuso, dopo un backup

Il progetto si modifica scrivendo `draft_info.json` e le sue cinque copie, con CapCut chiuso. Prima: backup della
cartella del progetto nella cartella del video, e controllo che l'utente non l'abbia toccato dall'ultima scrittura
(`capcut.py stato`). Se l'ha toccato, si chiede prima di sovrascrivere. Dall'interfaccia si fanno solo creazione del
progetto, import dei media ed export.

### 4. Mai toccare il Mac mentre lo usa l'utente

Prima di ogni clic o tasto su CapCut si verifica che CapCut sia in primo piano; se c'è un'altra app davanti, niente
interfaccia. Si cattura solo la finestra di CapCut (`screencapture -l <id>`), mai lo schermo intero o altre finestre.
Le coordinate si ricavano ogni volta dalla cattura, mai da una sessione precedente. Dall'interfaccia di CapCut non si
condivide mai niente: niente TikTok, YouTube, "Share", "Sign in". I permessi di macOS non si concedono al posto
dell'utente.

### 5. I b-roll devono sembrare veri e muoversi

Una clip che si muove poco sopra il parlato sembra una fotografia: si misura con `movimento_broll.py`, sotto 1 non
si usa. Si parte sempre dal girato o dai fotogrammi veri del cliente; quando il materiale vero è finito si genera da
zero su fal o si prende da stock. Una dimostrazione vera (il frontman che mostra il pezzo) non si copre mai. Skill
`editing-broll`.

### 6. Si consegna con i numeri, e si dice cosa non è stato ascoltato

Claude non ascolta l'audio: misura. Ogni consegna dice cosa è stato controllato e con quale numero, e dice
chiaramente che l'ascolto finale spetta all'utente. Prima di consegnare si ritrascrive il parlato montato e lo si
confronta con i sottotitoli: dove due trascrizioni dello stesso punto non coincidono, quel punto non si capisce, va
segnalato e se serve tolto. Skill `editing-verifica`.

### 7. Il nome di chi parla non si deduce

Gli script spesso hanno il nome sbagliato del frontman. Il nome si chiede o si legge nel profilo del cliente.

### 8. La normalizzazione loudness non si attiva mai

La casella "Normalize loudness" di CapCut ("Normalizza loudness" in italiano) resta spenta su ogni clip, per ogni
cliente, anche quando il progetto modello ce l'ha. Nel file è il materiale `loudnesses`: `capcut.py prepara` e
`taglia` non lo scrivono e lo tolgono dai segmenti che riscrivono, `capcut.py stato` segnala i segmenti dove è ancora
attivo, `capcut.py spegni-loudness` lo spegne su un progetto esistente.

### 9. Il girato non sta solo in Downloads

`~/Downloads/<video>/` è la copia di lavoro per la sandbox di CapCut, non l'archivio. Appena arriva un girato se ne
tiene una copia nella cartella del video (`CLIENTI/<Cliente>/<video>/GIRATO/`). Se Downloads si svuota, i progetti
perdono i riferimenti e senza copia il girato è perso.

### 10. Almeno il 65% dei b-roll di ogni video è nuovo

Clip mai usate in altri video, sia contando le clip sia contando i secondi. Il resto può venire dalla libreria, ma una
clip riciclata va in un solo video della stessa campagna. Le nuove possono essere girato vero del cliente, stock
(Pexels) o animazioni da fotogrammi veri, purché realistiche e senza i difetti tipici dell'AI. Con la libreria
riciclata i video escono tutti uguali. Skill `editing-broll`.

### 11. Niente grafiche sui volti

Sottotitoli, cartellini, sottopancia e schede non vanno mai sopra il viso di chi è in video. Prima di ogni consegna
`_TOOLS/volti.py` su parlato e b-roll, poi si spostano gli elementi (`y` per blocco o per grafica) o si tolgono se non
c'è spazio. La posizione fissa dei sottotitoli funziona solo con il viso in alto: con due persone o una persona
seduta va ricontrollata.

### 12. I sottotitoli restano anche sopra le grafiche

Chi guarda spesso ha l'audio spento: i sottotitoli non si tolgono sotto schede, tavole o motion graphic. La grafica
tiene il suo contenuto più in alto e il sottotitolo resta al suo posto.

---

## Valori di partenza (misurati su progetti veri, da confermare per ogni cliente)

| Cosa | Valore |
|------|--------|
| Velocità del girato | 1.03 sui talking head |
| Color | effetto "color-adjustment" (correzione colore intelligente a 0.8) più HSL neutro, su tutte le clip del parlato. Su girato SDR, `hdr_settings.mode` a 1 (vedi `editing-capcut`) |
| Audio | "Migliora voce" a 75, riduzione rumore spenta, normalizzazione loudness spenta (regola 8) |
| Tagli | l'ultima presa pulita di ogni frase, mai i "ripartiamo" e le domande di servizio |
| B-roll | traccia sopra il girato, volume a zero, nessun color copiato, legati alla frase che coprono |
| Sottotitoli | a blocchi, stile per cliente, attaccati su tutto il parlato, niente sull'outro. Quelli fatti a mano dall'utente non si toccano |
| Musica | sui reel organici sì, bassa sotto il parlato e più alta dove nessuno parla |
| Outro | in coda alla traccia principale |

---

## Skill

In `.claude/skills/`, si caricano da sole aprendo Claude Code in questa cartella.

| Comando | Cosa fa |
|---------|---------|
| `/editing` | Orchestratore: il flusso completo di un video e a quale skill passare |
| `/editing-tagli` | Scelta delle prese, separazione delle voci, confini sugli spettrogrammi, margini, verifica |
| `/editing-broll` | Libreria del cliente, girato vero, stock, generazione su fal, movimento, posizionamento |
| `/editing-capcut` | Scrittura del progetto: riprese intere, tagli, b-roll, outro, stato e backup |
| `/editing-sottotitoli` | Stile del cliente, blocchi, rilettura, scrittura, riallineamento dopo nuovi tagli |
| `/editing-verifica` | Collaudo prima di passare il video all'utente e forma del resoconto |
| `/editing-remotion` | Metodo Remotion: parlato, montaggio, grafiche, musica, anteprima, render, Studio |

---

## Strumenti

In `_TOOLS/`, uno per compito, ognuno con `--help`. Quelli con l'intestazione `# /// script` si lanciano con
`uv run`, gli altri con `python3`. Si lanciano dalla cartella `_TOOLS/`.

| Strumento | Cosa fa |
|-----------|---------|
| `trascrivi.py` | Scribe v2 su fal, parola per parola, con `--diarizza` per separare i parlanti |
| `voci.py` | livelli a 5 ms e altezza della voce a 10 ms per ripresa; statistiche per parlante |
| `spettrogrammi.py` | pagine di spettrogrammi con parole, altezza e livello per decidere i confini a vista |
| `tagli.py` | dai confini ai tagli (margini, fotogrammi interi) e verifica dei tagli |
| `capcut.py` | lista, stato, backup, chiusura, riprese intere, tagli, b-roll e outro nel progetto |
| `sottotitoli_capcut.py` | blocchi dei sottotitoli e scrittura nel progetto con lo stile del cliente |
| `evidenzia_sottotitoli.py` | parole chiave colorate dentro i sottotitoli CapCut |
| `transizioni.py`, `sfx.py` | dissolvenze sui jump cut ed effetti sonori nel progetto CapCut |
| `riallinea_broll.py` | riporta i b-roll sulle frasi dopo che l'utente ha ritoccato i tagli |
| `controlla_collegamenti.py`, `link_media.py`, `ripara_voce.py` | dopo un "Link media" di CapCut: scambi di riprese, ricollegamento, "Migliora voce" perso |
| `anteprima.py` | anteprima a 540p del progetto con b-roll, sottotitoli e audio esatto, anche con un piano b-roll non ancora scritto |
| `movimento_broll.py` | quanto si muove una clip |
| `genera_broll.py` | fotogrammi e ritagli dal girato vero, immagini, ingrandimenti e animazioni su fal (Veo o Kling) |
| `stock.py` | ricerca su Pexels con provino, preparazione in 9:16 e controllo di un candidato |
| `volti.py` | dove stanno i volti, per non metterci sopra grafiche e sottotitoli |
| `musica.py` | musica di sottofondo originale su fal |
| `voiceover.py` | voce fuori campo per i video senza girato |
| `ui_capcut.py` | interfaccia di CapCut: finestra, cattura, clic e tasti, solo con CapCut in primo piano |
| `remotion.py` | metodo Remotion: parlato tagliato (HDR convertito), sottotitoli, `montaggio.json`, render e Studio |

Le chiavi (fal, ed eventualmente Gemini) si leggono con `_TOOLS/chiavi.py` dal file `.env` di questa cartella e non
si chiedono mai in chat.
