---
name: editing
description: Orchestratore del montaggio dei video dei clienti, in CapCut, con Remotion o ibrido: prima di ogni montaggio nuovo chiede all'utente quale metodo usare. Usa quando l'utente dice "/editing", "monta il video", "fai il montaggio", "crea il progetto su CapCut", "fai i tagli", "metti i b-roll", "aggiungi l'outro", "fai i sottotitoli", "c'è ancora la voce di chi detta", oppure quando passa una cartella di girato di un cliente da montare. Conosce il flusso completo (riprese intere con color e audio, tagli sull'audio elaborato, b-roll, sottotitoli, outro, anteprima, verifica) e manda alle sotto-skill editing-tagli, editing-broll, editing-capcut, editing-remotion, editing-sottotitoli, editing-verifica. Lavora nella cartella EDITING_KIT.
---

# Editing video · orchestratore

Porti il girato di un cliente fino al video pronto da esportare, e conosci lo stato dei video in corso.

## Prima di fare qualsiasi cosa

1. Leggi `CLAUDE.md` della cartella del kit: le regole che non si discutono.
2. Leggi `01_DECISIONI/REGOLE.md` e `01_DECISIONI/LOG_DECISIONI.md`: cosa è già stato provato, deciso o bocciato.
   Una decisione del log vince su una regola di partenza.
3. Leggi `CLIENTI/<Cliente>/PROFILO.md`: chi parla, stile, librerie, progetto modello. Se non c'è, crealo da
   `CLIENTI/_TEMPLATE/PROFILO.md` e chiedi all'utente quello che non si può misurare (nomi, stile voluto, outro).
4. Se `.env` non c'è nella cartella del kit, fermati e rimanda a `INSTALLA.md`.
5. Guarda lo stato vero, mai a memoria:
   ```bash
   cd _TOOLS
   python3 capcut.py lista
   python3 capcut.py stato "<progetto>"
   ```
   Se CapCut è aperto e in primo piano, l'utente lo sta usando: niente interfaccia e niente scritture.

## Prima domanda: con che metodo

Prima di ogni montaggio nuovo, o di rifare un video da zero, **chiedi all'utente quale metodo usare** (con
AskUserQuestion), anche se il cliente ha sempre usato lo stesso.

| Metodo | Cosa esce | Skill |
|--------|-----------|-------|
| **CapCut** | progetto CapCut scritto dal file, che l'utente apre, ritocca ed esporta | il flusso qui sotto, `editing-capcut` |
| **Remotion** | file MP4 renderizzato, con zoom morbidi sui tagli, transizioni con effetto sonoro, sottotitoli e grafiche animate; nessun progetto da aprire | `editing-remotion` |
| **Ibrido** | tagli, velocità, color e "Migliora voce" in CapCut, poi Remotion sull'export per b-roll, zoom, sottotitoli, grafiche, musica e outro | `editing-capcut` fino all'export, poi `editing-remotion` |

Nella domanda metti il consiglio in prima posizione, con il motivo in una riga (criteri in `editing-remotion`).
Non serve chiedere per ritocchi su un video già avviato: si resta sul metodo con cui è nato, scritto nel suo
MANIFEST. Tagli, piano b-roll e sottotitoli sono gli stessi file per tutti i metodi: i passi 5, 7 e 8 non cambiano.

## Il flusso di un video (metodo CapCut)

| Passo | Cosa | Chi lo fa | Skill |
|-------|------|-----------|-------|
| 1 | Cartella del video da `CLIENTI/_TEMPLATE/VIDEO/`, girato in `~/Downloads/<nome video>/` (mai sul Desktop) e copia in `<cartella video>/GIRATO/` | Claude | |
| 2 | Progetto CapCut nuovo e import di girato, b-roll e outro | interfaccia: l'utente, o Claude solo con il suo via e CapCut in primo piano | `editing-capcut` |
| 3 | Riprese intere in timeline con color e "Migliora voce", normalizzazione loudness mai (`capcut.py prepara`), poi apertura finché CapCut ha elaborato | Claude scrive, CapCut elabora | `editing-capcut` |
| 4 | Export della timeline non tagliata (serve l'audio elaborato) | interfaccia | `editing-capcut` |
| 5 | Trascrizione con parlanti, scelta delle prese, confini sugli spettrogrammi, tagli, verifica | Claude | `editing-tagli` |
| 6 | Tagli nel progetto (`capcut.py taglia`) | Claude, CapCut chiuso | `editing-capcut` |
| 7 | B-roll: libreria, girato vero, stock, generazione; piano sulle frasi; b-roll e outro nel progetto | Claude | `editing-broll` |
| 8 | Sottotitoli: blocchi, rilettura, scrittura | Claude | `editing-sottotitoli` |
| 9 | Anteprima, verifica, MANIFEST, resoconto all'utente | Claude | `editing-verifica` |

Se l'utente ha già tagliato e sistemato il color, si parte dal passo 7 e i suoi tagli non si toccano.

## Dove mandare la richiesta

| Se l'utente chiede | Vai a |
|--------------------|-------|
| Tagli, prese, "si sente ancora la voce di chi detta", tagli troppo bruschi | `editing-tagli` |
| B-roll da trovare, generare, spostare; "sembra una foto", "sembra finto" | `editing-broll` |
| Scrivere nel progetto, outro, velocità, color, audio, stato del progetto, "CapCut elabora troppe features" | `editing-capcut` |
| Sottotitoli, stile, testi sbagliati, tempi | `editing-sottotitoli` |
| "È pronto?", controllo prima di esportare, resoconto | `editing-verifica` |
| Metodo Remotion o ibrido: render, zoom, transizioni, grafiche, musica, Studio | `editing-remotion` |
| Lo script da girare, il copy dell'inserzione | fuori da questa suite |

## Dove si salva

Tutto nella cartella del video: analisi, trascrizioni, confini, tagli, piano b-roll, spettrogrammi, anteprima,
backup del progetto, `MANIFEST.md`. Una decisione nuova dell'utente va in `01_DECISIONI/LOG_DECISIONI.md` con la
data; una cosa nuova sul cliente va nel suo `PROFILO.md`; lo stato del video in `00_INDICE.md`.

## Cosa NON si fa mai

- Scrivere un progetto con CapCut aperto, o senza backup, o senza aver controllato se l'utente l'ha toccato.
- Cliccare o digitare se CapCut non è in primo piano; catturare lo schermo intero o altre finestre; condividere
  qualcosa dall'interfaccia di CapCut.
- Dire che un taglio è pulito senza i numeri di `tagli.py verifica`, o far passare per ascoltato qualcosa di misurato.
- Cancellare file vecchi: le versioni scartate vanno in `_build/versione_N_<motivo>/`.
- Dedurre il nome di chi parla.
- Chiedere le chiavi in chat: stanno nel `.env` del kit.
