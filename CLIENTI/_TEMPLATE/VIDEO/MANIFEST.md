# <Titolo del video>, montaggio

Cliente, serie, data. Metodo (CapCut, Remotion, ibrido). Chi parla. Script di riferimento.

Progetto CapCut: cartella `<cartella>` (il nome scritto nel file CapCut lo riporta al nome della cartella: va
rinominato a mano). Girato in `~/Downloads/<nome video>/` (copia in `GIRATO/`), b-roll in `~/Downloads/<nome video>/BROLL/`.
**Quella cartella non va cancellata**, altrimenti il progetto perde i media.

Durata: parlato più outro.

## Riprese

| Ripresa | Durata | Fondo | Parlanti (frontman, chi detta) |
|---------|--------|-------|-------------------------------|

## Tagli

Versioni e perché sono state rifatte:

| Versione | Cosa faceva | Perché è stata rifatta |
|----------|-------------|------------------------|

Regole e numeri della versione consegnata (margini, tagli con voci attaccate, prese cambiate).

## B-roll

| Da | A | Clip | Sopra cosa | Movimento | Provenienza |
|----|---|------|------------|-----------|-------------|

## Sottotitoli

Numero di blocchi, stile, blocchi corretti a mano, verifica dei tempi sull'audio del progetto.

## Verifiche

| Controllo | Risultato |
|-----------|-----------|
| Suono fuori dalla voce del frontman dentro i tagli (`tagli.py verifica`) | |
| Altezza da chi detta fuori dalla voce | |
| Progetto: copie, riferimenti orfani, clip più corte del tratto, media mancanti (`capcut.py stato`) | |
| Sottotitoli: prima parola dopo l'inizio del blocco, media e massimo | |
| Testo del montato contro lo script e contro i sottotitoli | |
| Volti coperti da grafiche o sottotitoli (`volti.py`) | |

## Cosa deve fare l'utente in CapCut

## File

| File | Cosa |
|------|------|
| `ANTEPRIMA_540p.mp4` | anteprima da `anteprima.py`: tagli, b-roll e tempi. Color e audio elaborati li applica solo CapCut |
| `VERIFICA_montaggio.jpg` | un fotogramma per ogni b-roll |
| `sottotitoli_blocchi.json`, `sottotitoli.srt` | testi e tempi dei sottotitoli |
| `BROLL_USATI/` | copie delle clip usate |
| `_build/` | analisi, trascrizioni, confini, tagli, piano b-roll, spettrogrammi di controllo, versioni precedenti |
| `_BACKUP_CAPCUT_*` | il progetto prima di ogni scrittura |
