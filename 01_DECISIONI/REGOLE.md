# Regole di partenza

Uscite da mesi di montaggi su clienti veri (aziende manifatturiere, cliniche, saloni, software, personal brand): ogni
riga è una cosa provata e bocciata, o provata e tenuta. Valgono finché l'utente non decide diversamente; le sue
decisioni nuove vanno in [LOG_DECISIONI.md](LOG_DECISIONI.md) e, se contraddicono una regola di qui, vince la sua.

## Metodo

| Regola | Perché |
|--------|--------|
| Prima di ogni montaggio nuovo si chiede il metodo: CapCut, Remotion o ibrido | ogni video ha esigenze diverse, e la scelta cambia tutto il flusso |
| Ibrido quando l'utente vuole poter ritoccare i tagli a mano: tagli, velocità, color e "Migliora voce" in CapCut, export pulito, Remotion parte dall'export e non ricostruisce i tagli dal grezzo | i ritocchi fatti in CapCut arrivano identici all'export finale |
| Remotion senza CapCut si può fare, ma senza "Migliora voce": va detto nel resoconto | è l'unico elaborato audio che manca al metodo Remotion |
| Creazione del progetto e import dei media li può fare Claude dall'interfaccia, solo quando l'utente dà il via e lascia il Mac | sono le uniche operazioni che dal file non si possono fare |

## Tagli e voce

| Regola | Perché |
|--------|--------|
| Nel montato solo la voce del frontman, nessuna coda di chi detta, né all'inizio né alla fine delle clip | con "Migliora voce" si sentono anche le code che nel grezzo stanno molto sotto il parlato. Margini di 0,22 s le facevano entrare |
| Tagli non bruschi: un attimo prima che la voce parta, pochi centesimi nel silenzio | tagliando sull'attacco la consonante sembra troncata |
| Color, normalizzazione e "Migliora voce" sulle riprese intere, poi si taglia; i tagli si decidono sull'audio elaborato | con i tagli già fatti CapCut rielabora la voce pezzo per pezzo (71 elaborazioni invece di 6) e a ogni nuova versione |
| "Normalize loudness" di CapCut mai attiva, su nessuna clip | scelta di fondo dell'area |
| Un lapsus dentro una frase si toglie, se il taglio regge: si verificano i tagli candidati ritrascrivendoli | la frase si legge pulita e nessuno nota il taglio |
| Una frase che il girato tronca a metà parola si toglie, non si rattoppa con fermo immagine e riverbero | i rattoppi si sentono sempre |
| Il girato a frame rate variabile (per esempio arrivato da WhatsApp) si normalizza a 30 fps costanti prima di entrare in CapCut | con il frame rate misto ogni cambio di velocità accumula scarto: oltre un secondo su 94 s |
| Se i jump cut risultano bruschi: dissolvenza incrociata di 0,2 s e 40 ms di dissolvenza audio per lato (`transizioni.py`). Niente transizioni complicate o che ruotano | le transizioni vistose sui tagli del parlato sono state bocciate |
| Dopo i tagli si controllano anche i salti di livello della voce fra un pezzo e l'altro | una ripresa più forte dell'altra si nota quanto un taglio sbagliato |
| Il nome di chi parla si chiede sempre. Alcuni clienti non lo vogliono a schermo: si scrive nel profilo e non si richiede | per tre versioni un frontman è stato chiamato con il nome scritto nello script, ed era sbagliato |

## Colore

| Regola | Perché |
|--------|--------|
| Pelle abbronzata o rossiccia nell'export: prima di tutto `hdr_settings.mode` da 4 a 1 su ogni clip, poi eventualmente si toglie la correzione colore intelligente | CapCut mette il modo 4 nei progetti recenti anche su girato SDR. Saturazione del viso misurata: girato 0,39, export con modo 4 0,50-0,52, con modo 1 0,39 |
| Il colore si controlla misurando (saturazione sul viso, livello del muro), non a occhio | due correzioni a occhio non si confrontano |
| Più luce su un girato buio si può dare con ffmpeg sull'export, senza toccare b-roll e grafiche | si interviene solo sul parlato |

## B-roll

| Regola | Perché |
|--------|--------|
| Sempre video che si muovono, mai clip che sembrano immagini: movimento misurato, sotto 1 non si usa | due riprese quasi ferme (0,06 e 0,37) sono state bocciate: "non dovevi mettere immagini ma sempre video" |
| Almeno il 65% delle clip di ogni video è nuovo, contando clip e secondi; una clip riciclata va in un solo video della stessa campagna | con la stessa libreria su tutti i video "stanno uscendo tutti uguali" |
| Prima il materiale vero: ritagli del girato del cliente ingranditi con Topaz, animazioni Veo o Kling partite da un fotogramma vero | le scene AI generate da zero, quando il vero c'era, sono state bocciate come finte |
| Quando il materiale vero è finito, si genera da zero su fal (immagine con nano-banana, movimento con Kling) o si prende da stock | con le foto del cliente esaurite la copertura era scesa al 6% |
| Se lo stock non rappresenta il mondo del cliente (attrezzature, colori, ambienti riconoscibili), meglio le clip fatte per quella serie che lo stock generico: in quel caso la quota del 65% si concorda con l'utente | lo stock industriale generico è stato bocciato su un processo molto specifico |
| I b-roll sopra un messaggio tecnico mostrano il mestiere di chi ascolta, non un mestiere vicino | stock di disegno meccanico sopra un video per sviluppatori di videogiochi: bocciato |
| Quando lo stock non ha la scena (un software, un'interfaccia, un modello 3D) la si costruisce in una pagina web e la si registra | è la cosa più vera che si può mostrare |
| Niente animazioni 3D decorative nel montato: solo b-roll realistici legati alle frasi | tolte tutte dalla timeline |
| B-roll e grafiche entrano sulla parola che li nomina, misurata sulla trascrizione, e mostrano il gesto di cui si parla | spostati di 0,6-2,8 s per andare a tempo con la voce |
| Densità: la decide l'utente per video. Senza indicazioni, 3-4 clip nei tratti densi, volto sulle frasi forti e sulla chiusura | |
| Una dimostrazione vera del frontman non si copre mai | |
| Per i clienti di medicina estetica: niente iniezioni, aghi, siringhe o sangue, nemmeno nello stock | Meta può bloccare l'inserzione |

## Sottotitoli

| Regola | Perché |
|--------|--------|
| Sottotitoli a blocchi. Lo stile "dinamico" (parole a tempo, parole enormi dietro la persona) è stato provato e bocciato: se l'utente lo chiede, prima un video di riferimento e un'anteprima di pochi secondi | visto il risultato, è stato chiesto di rimetterli "normali com'erano prima" |
| Seguono il parlato vero, non lo script: il girato si rilegge parola per parola prima di scrivere i blocchi | il frontman spesso dice diverso dallo script |
| Un sottotitolo non compare prima della clip in cui la frase viene detta, e non parte prima della sua prima parola | 55 blocchi su 86 in anticipo fino a 0,83 s, e 18 a cavallo di un taglio |
| Restano anche sopra le grafiche animate e le schede | chi guarda spesso ha l'audio spento |
| Prima di consegnare si ritrascrive il montato e si confronta con i sottotitoli. Due trascrizioni diverse dello stesso punto vogliono dire che non si capisce: si segnala e si toglie | un sottotitolo scritto sopra un borbottio: "sembra una lingua strana" |
| Lo stile di un cliente nuovo si ricava da un video che l'utente ha già sottotitolato, o dal sito del cliente (font e colori letti dalle pagine, non inventati). Un font mancante si scarica e si mette nella cartella font di CapCut | |
| Se lo stile copiato dal sito è troppo piatto per il pubblico del video, si propone un bold leggibile con le parole chiave in un colore acceso | un Raleway preso dal sito è stato bocciato per un pubblico di sviluppatori |
| Un template di sottotitoli per serie, uguale su tutti i video | |

## Grafiche

| Regola | Perché |
|--------|--------|
| Nessun elemento grafico sopra un volto: si misura con `volti.py` e si sposta o si toglie | sottotitoli e cartellino sugli occhi e sul mento di una cliente: "fai attenzione a questi dettagli" |
| Niente cartellini a pillola: tipografia grande e animata sopra il girato (`Editoriale.tsx`), con font e accento del cliente | i cartellini semplici sono stati bocciati come "banali" |
| Entrata 0,6 s con curva morbida, uscita 0,47 s, transizioni di 9 fotogrammi per lato, durata minima di una grafica 2,5 s dove c'è spazio; cartellini in basso, sopra i sottotitoli | a 0,3 s "troppo veloci, non danno il tempo di essere letti" |
| In una scheda l'ultima voce resta a schermo almeno 2 s prima dell'uscita; se non c'è spazio si anticipano le voci | una riga rimasta 0,95 s "non si vede" |
| Una scheda entra in dissolvenza sopra la fine del b-roll e mostra subito il titolo; il sottotitolo prima si accorcia fino al suo ingresso invece di sparire | la scheda entrava vuota per 2 s e il volto restava senza sottotitoli |
| Le grafiche con numeri (tabelle, KPI, confronti) si scrivono in codice (Remotion o HTML), mai con un modello di immagini | un modello di immagini sbaglia cifre e tipografia, e lì le cifre sono il contenuto |
| Ogni scena mostra un'immagine che dice quello che dice il testo. La stessa foto non si ripete, né nel video né nella serie; dove il cliente non ha la foto giusta, stock | ritratti ripetuti e foto che "non combaciano con quello che stai dicendo" |
| Nei sottopancia nome e cognome completi (con il titolo, per esempio Dott.ssa), mai il solo cognome; i nomi si prendono dai materiali del cliente | |
| Niente scritte di servizio (nome della serie, titolo della rubrica, firme) se il cliente non le chiede; in chiusura di un reel di brand basta il logo, circa 2 s, senza voce | firme di serie e rubriche sono state tolte |
| Alla prima anteprima Remotion di un cliente si chiede se zoom e transizioni vanno bene, e la risposta va nel profilo. Molti vogliono solo zoom morbido e dissolvenze semplici, niente swoosh né flash | |

## Musica e voce fuori campo

| Regola | Perché |
|--------|--------|
| Sui reel organici va la musica di sottofondo senza chiederlo: bassa sotto il parlato, più alta dove nessuno parla | "fai tutto tu compresa la musica di sottofondo e la alzi quando serve" |
| I cambi di volume della musica sempre in dissolvenza lunga: quasi 3 s fra musica piena e parlato, 1,2 s negli altri passaggi | un passaggio in 0,35 s è stato bocciato come "cambio drastico" |
| Si generano due o tre tracce candidate e si misurano secondo per secondo: possono finire prima della durata chiesta | la prima traccia non è piaciuta; una finiva a 71 s su 80 |
| Prima di scegliere una voce fuori campo si fanno prove alla cieca sulle prime battute, livellate a -16 LUFS | la voce giusta non si sceglie dal catalogo: quella catalogata "morbida" è uscita "troppo lenta" |
| Tutte le battute in una sola registrazione, poi tagliate sui tempi: l'intonazione scorre da una frase all'altra | registrate una per una suonano staccate |
| Una voce un po' lenta si prova ad accelerare di poco (`atempo=1.08`) prima di scartarla | |
| Il nome del brand si scrive per la voce come va pronunciato, staccato e con l'accento | scritto attaccato, sotto la musica, si capiva un'altra parola |
| Chatterbox con un riferimento sintetico esce piatta, Kokoro è troppo robotica: per i reel meglio ElevenLabs v3 o Gemini | |

## CapCut e file

| Regola | Perché |
|--------|--------|
| Gli effetti sonori si prendono dalla libreria di CapCut copiandoli da un progetto che li usa già (`sfx.py --da-progetto`), con i volumi di quel progetto | il file sta già nella cache, non c'è niente da importare |
| L'outro si decide per cliente: a volte non c'è e il video chiude sulla chiamata all'azione | |
| Prima di liberare spazio si cancellano solo video e audio dei progetti finiti con gli originali al sicuro altrove; testi, MANIFEST, profili e stili restano | servono per i video successivi della stessa serie |
