# Strumenti

Uno per compito, ognuno con `--help`. Si lanciano dalla cartella `_TOOLS/`. Quelli con l'intestazione
`# /// script` si lanciano con `uv run` (installa da solo numpy, librosa, matplotlib, opencv, pyobjc), gli altri con
`python3`. Servono ffmpeg e ffprobe nel PATH, con i filtri `zscale` e `subtitles` (vedi `INSTALLA.md`).
Le chiavi si leggono con `chiavi.py` dal `.env` del kit.

| Strumento | Come si lancia | Cosa sapere |
|-----------|----------------|-------------|
| `trascrivi.py` | `python3` | Scribe v2 su fal, con `--diarizza` separa i parlanti. Se il json esiste già non ritrascrive. Il file si converte in mp3 mono e si carica sullo storage di fal: i data URI su file lunghi falliscono |
| `voci.py` | `uv run` | livelli ogni 5 ms (analisi a 48 kHz, 240 campioni esatti) e altezza ogni 10 ms; `parlanti` dà le statistiche per parlante. Con un iPhone: fondo intorno a -85 dB, frontman picchi -25 dB e 156 Hz, chi detta -35 dB e 268 Hz |
| `spettrogrammi.py` | `uv run` | pagine normali e strette (`--stretto`, 0.8 s, griglia a 20 ms), da leggere come immagini |
| `tagli.py` | `python3` | `calcola` dai confini ai tagli (rifinitura, margini, fotogrammi interi), `verifica` sui tagli |
| `movimento_broll.py` | `python3` | sotto 1 sembra una foto, 1-3 lento, oltre 4 si muove. Si misura il tratto usato (`--da`, `--durata`) |
| `capcut.py` | `python3` | `lista`, `stato`, `backup`, `chiudi`, `prepara`, `taglia`, `broll`, `spegni-loudness`. `stato` dice che un progetto è coerente con sé stesso, **non che è ancora quello che avevi scritto**: prima di riscrivere si confrontano durate dei tagli con `tagli.json`, tempi dei sottotitoli con `sottotitoli_blocchi.json` e b-roll con `piano_broll.json`; dove lo scarto supera mezzo fotogramma (0,017 s) ci ha messo le mani l'utente, e si chiede |
| `controlla_collegamenti.py` | `python3` | **va lanciato dopo ogni "Link media"**: CapCut può agganciare una ripresa al file sbagliato lasciando giusti tempi e punti di attacco, e `stato` non se ne accorge |
| `link_media.py` | `uv run` | ricollega i media mancanti di un progetto dall'interfaccia, uno alla volta |
| `ripara_voce.py` | `python3` | riattacca "Migliora voce" ai segmenti prendendolo da un backup, quando CapCut l'ha tolto aprendo il progetto con i media mancanti |
| `riallinea_broll.py` | `python3` | dopo i ritocchi dell'utente ai tagli riporta i b-roll sulle loro frasi. Quelli spostati a mano li lascia fermi e li segnala. Rilanciato dopo la scrittura deve dire 0 da spostare |
| `sottotitoli_capcut.py` | `python3` | `proposta`, `ricalcola`, `riallinea`, `scrivi`. Tempi dalle trascrizioni Scribe delle riprese, nessun blocco a cavallo di un taglio |
| `evidenzia_sottotitoli.py` | `python3` | parole chiave colorate dentro i blocchi CapCut, riscrivendo la lista `styles` del testo. Rilanciarlo è sicuro |
| `transizioni.py` | `python3` | dissolvenza "Mix" sui jump cut senza spostare i tempi, più dissolvenza audio per lato. Salta e segnala le giunzioni senza materiale oltre il taglio |
| `sfx.py` | `python3` | effetti sonori della libreria di CapCut copiati da un progetto che li usa già (`--da-progetto`), con i suoi volumi |
| `anteprima.py` | `python3` | anteprima 540p con ffmpeg: girato, b-roll, sottotitoli, audio esatto in PCM. `--piano` mostra un piano b-roll non ancora scritto. Color e "Migliora voce" li applica solo CapCut: qui l'audio è il grezzo |
| `genera_broll.py` | `python3` | `fotogramma`, `ritaglia`, `immagine`, `ingrandisci-immagine`, `anima` (Veo o Kling), `ingrandisci-video` (Topaz). Lezioni nell'`--help` |
| `stock.py` | `uv run` | `cerca` su Pexels con Chrome senza finestra (serve Google Chrome installato), provino numerato; `prepara` scarica, ritaglia a 9:16 e misura. Criteri nell'`--help` |
| `volti.py` | `uv run` | riquadri dei volti ogni 0,25 s su un video verticale (YuNet di OpenCV, il modello si scarica da solo). Qualche falso volto sui bordi: guardare il provino |
| `musica.py` | `python3` | musica strumentale originale su fal (Stable Audio 2.5). La traccia va misurata secondo per secondo: può finire prima della durata chiesta |
| `voiceover.py` | `uv run` | voce fuori campo, cinque motori (vedi `--help`). `disegna` crea una voce Gemini da una descrizione e la salva in `_modelli/voci/gemini_voci.json` |
| `ui_capcut.py` | `uv run` | interfaccia di CapCut: cattura della sola finestra, clic, tasti. Si ferma da solo se davanti c'è un'altra app. Prima di digitare si controlla con una cattura che il dialogo sia aperto; prima di ogni clic su una riga della home si ricattura, perché l'ordine cambia dopo ogni import |
| `remotion.py` | `python3` | metodo Remotion: `parlato`, `da-capcut`, `sottotitoli`, `montaggio`, `render`, `studio` (skill `editing-remotion`) |
| `chiavi.py` | | lettura delle chiavi: variabile d'ambiente, poi `.env` del kit, poi `~/.claude/settings.json` (server MCP fal-ai) |

## Formato dei file fra uno strumento e l'altro

`confini.json` (input di `tagli.py calcola`), una voce per frase nell'ordine del montaggio:

```json
{"ripresa": "IMG_8598", "voce_da": 24.63, "voce_a": 28.46, "testo": "Il nostro nome...", "fine_fissa": false}
```

`tagli.json` (output di `tagli.py`, input di `capcut.py taglia` e `remotion.py parlato`): come sopra più `da`, `a`,
`margine_testa`, `margine_coda`. I tempi sono secondi nella ripresa sorgente.

`piano_broll.json` (input di `capcut.py broll` e `remotion.py montaggio`), tempi in secondi sulla timeline montata:

```json
{"clip": "B11_chiude-cartella_9x16.mp4", "da": 16.29, "a": 20.67, "offset": 0.4}
```

`piano_sfx.json` (input di `sfx.py scrivi`):

```json
[{"effetto": "Woosh", "da": 21.72}, {"effetto": "Metallic Riser", "da": 52.14, "volume": 0.45}]
```

`musica.json` (letto da `remotion.py montaggio`): `{"file": "...", "offset": 0, "punti": [[secondi, volume 0-1], ...]}`.

Analisi di `voci.py`: `<ripresa>_livelli.json` (`rms_db` ogni 5 ms) e `<ripresa>_altezza.json` (`f0_hz` ogni
10 ms, 0 senza voce), nella stessa cartella.

## Cosa non c'è

- Scelta automatica delle prese: si fa confrontando la trascrizione diarizzata con lo script (skill `editing-tagli`).
- Il modello Kokoro per `voiceover.py --motore kokoro` (340 MB): si scarica dalle release di `kokoro-onnx` in
  `_modelli/kokoro/` solo se serve.
