# Kit di montaggio per Claude Code

Una cartella che insegna a Claude Code a montare video verticali parlati: tagli jump cut senza voci estranee,
b-roll veri o generati, sottotitoli a tempo, grafiche animate, musica, e un collaudo con i numeri prima della
consegna. Lavora in tre modi: scrive direttamente il progetto CapCut, renderizza il video con Remotion, oppure fa i
tagli in CapCut e il resto in Remotion.

## Cosa ti serve

| Cosa | Note |
|------|------|
| Un Mac | il metodo CapCut usa percorsi, catture di finestra e clic di macOS |
| Claude Code | https://claude.com/claude-code |
| Homebrew (facoltativo) | https://brew.sh. Se c'è, lo script installa da solo ffmpeg, uv e Node; se non c'è, ti dice come installarli a mano |
| CapCut per Mac | gli strumenti sono collaudati sulla **9.5.0**. Quando CapCut propone un aggiornamento, rimandalo finché il primo video con la nuova versione non è stato controllato |
| Google Chrome | serve per cercare i b-roll su Pexels |
| Un account fal.ai con credito | trascrizioni, b-roll generati, musica, voce fuori campo. Si paga a consumo: le trascrizioni costano poco, le animazioni video (Veo, Kling) sono la spesa più alta, guarda i prezzi su fal.ai prima di generarne tante |

## Installazione

1. Accetta l'invito al repo che ti arriva per email da GitHub. Il repo è privato: senza invito non si vede.
2. Collega GitHub al Terminale, una volta sola. Con Homebrew:
   ```bash
   brew install gh
   gh auth login        # GitHub.com, HTTPS, accesso dal browser
   ```
   Senza Homebrew va bene anche GitHub Desktop (https://desktop.github.com), che clona il repo dal menu File.
3. Scarica il kit sul Desktop e lancia l'installazione:
   ```bash
   gh repo clone infomiliaragency-maker/editing-kit ~/Desktop/EDITING_KIT
   cd ~/Desktop/EDITING_KIT
   ./installa.sh
   ```
   Controlla ffmpeg, uv, Node, CapCut, Chrome e Claude Code, installa con Homebrew quello che manca (se c'è e gli
   dici di sì), installa le dipendenze di Remotion (circa 600 MB) e crea il file `.env`.
4. Apri `.env` e incolla la chiave fal dopo `FAL_KEY=` (la crei su https://fal.ai/dashboard/keys). La chiave Gemini
   serve solo per un motore di voce fuori campo, puoi lasciarla vuota.
5. Rilancia `./installa.sh` finché non dice "Tutto pronto".

## Aggiornamenti

Quando ti dicono che il kit è cambiato:

```bash
cd ~/Desktop/EDITING_KIT
git pull
./installa.sh
```

Il tuo `.env`, la cartella `CLIENTI/` e `node_modules` non sono nel repo, quindi un aggiornamento non li tocca. Le
tue decisioni vanno in `01_DECISIONI/LOG_DECISIONI.md`, le preferenze di un cliente nel suo `PROFILO.md`: sono i
posti giusti, e restano tuoi. Se modifichi skill o strumenti, al `git pull` successivo git può segnalare un conflitto
su quei file: in quel caso chiedi a Claude di risolverlo tenendo le tue modifiche.

### Se ffmpeg non ha i filtri `zscale` o `subtitles`

Servono per convertire il girato HDR dell'iPhone e per le anteprime con i sottotitoli. Se quello di Homebrew non li
ha, scarica un ffmpeg statico completo (ffmpeg e ffprobe, per Apple Silicon o Intel a seconda del Mac), mettili in
`~/.local/bin/` e rendili eseguibili con `chmod +x`. Gli strumenti li cercano anche lì.

### Permessi di macOS

Servono solo se vuoi che Claude crei i progetti, importi i media o esporti da CapCut al posto tuo. In Impostazioni
di Sistema, Privacy e sicurezza, dai al Terminale (o all'app da cui lanci Claude Code) **Accessibilità** e
**Registrazione schermo**. Claude tocca CapCut solo quando è in primo piano e solo quando gli dai il via; se usi il
Mac si ferma.

## Il primo cliente

1. Crea `CLIENTI/<NomeCliente>/` e copiaci `CLIENTI/_TEMPLATE/PROFILO.md`. Claude ti chiederà quello che manca: nome
   di chi parla, stile dei sottotitoli, outro.
2. In CapCut prepara un **progetto modello**: una clip del girato del cliente con correzione colore intelligente a
   0.8, velocità 1.03, "Migliora voce" a 75, riduzione rumore e "Normalizza loudness" spente. Gli strumenti copiano
   color e audio da lì su ogni video nuovo. Scrivi il nome del progetto nel profilo.
3. Il girato va in `~/Downloads/<nome video>/`: CapCut non apre i file sul Desktop. Claude ne tiene una copia nella
   cartella del video.

## Come si usa

```bash
cd ~/Desktop/EDITING_KIT
claude
```

Poi scrivi `/editing` e passa la cartella del girato. Prima di ogni video nuovo Claude ti chiede con quale metodo
montarlo. Le altre skill (`/editing-tagli`, `/editing-broll`, `/editing-capcut`, `/editing-sottotitoli`,
`/editing-remotion`, `/editing-verifica`) si attivano da sole, oppure le chiami per nome.

Tre cose da sapere:

- **Claude non ascolta l'audio, lo misura.** Ogni consegna arriva con i numeri dei controlli e con l'elenco di cosa
  non è stato ascoltato. L'ascolto finale è tuo.
- **Quando non ti piace qualcosa, dillo con le tue parole.** Claude scrive la decisione in
  `01_DECISIONI/LOG_DECISIONI.md` e la applica ai video dopo. Le regole di partenza stanno in
  `01_DECISIONI/REGOLE.md`: una tua decisione vince su quelle.
- **Non cancella niente.** Prima di ogni scrittura su CapCut fa un backup del progetto nella cartella del video, e le
  versioni scartate restano in `_build/`.

## Cosa c'è nella cartella

| Cartella | Cosa |
|----------|------|
| `CLAUDE.md` | le regole che Claude segue sempre |
| `.claude/skills/` | le 7 skill `/editing*` |
| `_TOOLS/` | gli strumenti Python, guida in `_TOOLS/LEGGIMI.md` |
| `_REMOTION/` | il progetto Remotion con i modelli di sottotitoli, zoom, transizioni e grafiche |
| `01_DECISIONI/` | regole di partenza e decisioni tue |
| `CLIENTI/` | i tuoi clienti, uno per cartella (`_TEMPLATE` è il modello) |
| `00_INDICE.md` | stato dei video, lo aggiorna Claude |

## Facoltativo

- **Skill HyperFrames** per grafiche animate a sé (titoli, card, motion graphic) da inserire come clip: sono
  pubbliche su https://github.com/heygen-com/hyperframes, si installano in `.claude/skills/` seguendo il README del
  progetto.
- **rclone** per scaricare e caricare file da Google Drive (`brew install rclone`, poi `rclone config`).
- **Voce fuori campo con Chatterbox**: serve un file di 10-15 s di voce pulita da imitare, da indicare come
  `"riferimento"` in `testo.json` (dettagli in `uv run _TOOLS/voiceover.py --help`). Gli altri motori non ne hanno
  bisogno.

## Licenze

Remotion è gratuito per chi lavora da solo e per aziende fino a 3 persone; oltre serve la licenza aziendale
(https://www.remotion.dev/license). Le clip Pexels sono libere per uso commerciale. La musica generata con
`musica.py` è originale.
