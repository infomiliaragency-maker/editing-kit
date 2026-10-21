// Forma di montaggio.json, scritto da _TOOLS/remotion.py. Tempi in secondi sulla timeline montata.
import type { Transition } from "../templates/transitions";
import type { CaptionChunk } from "../templates/captions/Ref2Captions";
import type { Grafica, Tema } from "../templates/grafiche/Grafiche";

// y: centro del blocco in px, solo se in quel tratto la posizione del cliente coprirebbe un volto
export type Blocco = { da: number; a: number; testo: string; parole: [string, number, number][]; y?: number };

export type StileBlocchi = {
  font: "Inter" | "Montserrat" | "Poppins";
  peso: number;
  dimensione: number;
  colore: string;
  bordo: string;
  bordo_px: number;
  evidenza: string | null; // colore della parola che si sta dicendo, null = nessuna
  y: number; // centro del blocco, in px su 1920
  colore_blu?: string; // keyword fisse del brand: cifre e parole_blu sempre in questo colore
  parole_blu?: string[];
};

// parola chiave enorme dietro la persona: `file` è il ritaglio della persona con canale alfa (webm) per quel tratto
export type ParolaDietroT = { da: number; a: number; testo: string; y: number; dimensione: number; file: string };

export type Montaggio = {
  titolo: string;
  durata: number;
  parlato: { file: string; durata: number };
  segmenti: { start: number; end: number }[];
  zoom: { attivo: boolean; livelli: number[]; rampa_s: number; deriva?: number }; // deriva: push-in dentro il pezzo, zoom al secondo (default 0.006)
  broll: { file: string; da: number; a: number; offset: number; push_in: boolean }[];
  transizioni: Transition[];
  outro: { file: string; da: number; durata: number } | null;
  grafiche?: { tema: Tema; elenco: Grafica[] }; // da <video>/grafiche.json, opzionale
  // musica di sottofondo, da <video>/musica.json: volume per punti [secondi, volume 0-1], interpolato fra un punto e l'altro
  musica?: { file: string; offset: number; punti: [number, number][] };
  sottotitoli:
    | { stile: "nessuno" }
    | { stile: "blocchi"; blocchi: Blocco[]; aspetto: StileBlocchi }
    | { stile: "dinamici"; blocchi: Blocco[]; aspetto: StileBlocchi; dietro: ParolaDietroT[] }
    | { stile: "ref2"; chunks: CaptionChunk[]; y: number };
};
