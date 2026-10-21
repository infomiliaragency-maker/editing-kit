---
name: editing-verifica
description: Collaudo di un montaggio (CapCut, Remotion o ibrido) prima di passarlo all'utente, e forma del resoconto. Usa quando l'utente chiede "/editing-verifica", "è pronto?", "controlla il montaggio", "posso esportare?", o alla fine di ogni lavoro delle skill editing prima di dire che è fatto. Controlla con i numeri voci nei tagli, progetto CapCut, b-roll, volti, sottotitoli, testo contro lo script, anteprima; restituisce PASS o FAIL con la lista di cosa correggere e scrive il resoconto con quello che l'utente deve fare e quello che non è stato ascoltato.
---

# Verifica prima di consegnare

Claude non ascolta: misura. Un montaggio è pronto quando ogni riga qui sotto ha un numero, e il resoconto dice
chiaramente che l'ascolto finale spetta all'utente.

## Controlli

```bash
cd _TOOLS
```

| # | Controllo | Come | Passa se |
|---|-----------|------|----------|
| 1 | Voce di chi detta nei tagli | `python3 tagli.py verifica _build/tagli.json --analisi _build/analisi` | 0 ms di altezza da chi detta fuori dalla voce; suono residuo solo fondo fra -79 e -76 dB |
| 2 | Confini stretti guardati | spettrogrammi finali dei tagli a margine zero e delle fini rifinite (`spettrogrammi.py --stretto`) | nessuna energia dell'altra voce dentro il taglio |
| 3 | Progetto CapCut | `python3 capcut.py stato "<progetto>"` | stesse tracce in tutte le copie, principale contigua, durate a fotogramma intero, riferimenti orfani 0, nessuna clip più corta del tratto usato, nessun media mancante, "Migliora voce" su tutti i tagli del parlato, nessuna riga "NORMALIZZAZIONE LOUDNESS ATTIVA" |
| 4 | Tempi dei tagli nel progetto | confronto dei `source_timerange` della traccia principale con `_build/tagli.json` | scarto 0 ms |
| 5 | Movimento dei b-roll | `python3 movimento_broll.py` sul tratto usato di ogni clip | nessuna sotto 1 |
| 6 | Salti del volto | confini b-roll contro i tagli del girato | nessun confine entro 0.2 s da un taglio fuori dal taglio stesso |
| 7 | Dimostrazioni coperte | fotogrammi dell'anteprima nei tratti in cui il frontman mostra qualcosa | scoperte |
| 8 | Testo | ritrascrizione dell'audio del montato (`trascrivi.py`) contro lo script e contro `sottotitoli_blocchi.json` | tutte le frasi, nessuna presa doppia, differenze spiegate; i punti dove due trascrizioni non coincidono sono segnalati |
| 9 | Sottotitoli | prima parola rispetto all'inizio del blocco sulla trascrizione del punto 8 | media intorno a 0.05 s, massimo sotto 0.15, nessun blocco che chiude prima della sua ultima parola |
| 10 | Volti | `uv run volti.py` sull'anteprima o sull'export, provino con i volti evidenziati | nessun sottotitolo, cartellino o scheda sopra un viso |
| 11 | Anteprima | `python3 anteprima.py ...` (CapCut) o `remotion.py render --anteprima`, provino con un fotogramma per b-roll e per grafica | b-roll, grafiche e sottotitoli al posto giusto, outro in coda |
| 12 | Durata | timeline contro durata attesa | nessun buco né sovrapposizione |
| 13 | Musica, se c'è | livello per secondo del mix | sotto il parlato, dissolvenze lunghe, nessun salto brusco |

Con il metodo Remotion i controlli 3 e 4 si fanno su `montaggio.json` e `parlato.json` invece che sul progetto.
Un solo FAIL e non si consegna: si corregge e si rifà il controllo. Se un controllo non si può fare, si scrive perché.

## Documenti

- `MANIFEST.md` della cartella del video aggiornato (modello in `CLIENTI/_TEMPLATE/VIDEO/MANIFEST.md`): metodo,
  versione, regole, tabella delle verifiche, b-roll, sottotitoli, file.
- Versioni scartate in `_build/versione_N_<motivo>/`, backup del progetto con etichetta. Niente cancellato.
- `00_INDICE.md` con lo stato del video; decisioni nuove dell'utente in `01_DECISIONI/LOG_DECISIONI.md`.

## Resoconto all'utente

In italiano, diretto, niente trattini lunghi e niente formule. Contiene:

1. cosa è cambiato rispetto a quello che ha visto, e perché;
2. i numeri delle verifiche che contano per quella richiesta, in una tabella breve con prima e dopo;
3. i punti dove il risultato può non piacergli (per esempio tagli a margine zero dove le voci erano attaccate, punti
   poco comprensibili) e cosa si può fare lì;
4. **cosa deve fare in CapCut**, se il metodo lo prevede: aprire il progetto, aspettare "Enhance voice applied" se
   l'audio è stato riscritto, rinominare il progetto se il nome è tornato quello della cartella, ascoltare prima di
   esportare;
5. **cosa non è stato ascoltato**: la verifica è sui dati, voce e musica vanno ascoltate dall'utente;
6. dove stanno anteprima, export, backup e MANIFEST.
