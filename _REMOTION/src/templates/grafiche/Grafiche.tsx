/**
 * GRAFICHE ANIMATE sopra il montato, da <video>/grafiche.json (le legge _TOOLS/remotion.py montaggio).
 * Tre tipi, colori e font dal "tema" del cliente:
 * - "nome":      sottopancia con nome e ruolo, entra da sinistra
 * - "etichetta": cartellino numerato sopra un b-roll
 * - "scheda":    grafica a tutto schermo con titolo e voci che compaiono sulle parole (tempi dalla trascrizione)
 * Ogni comparsa ha il suo effetto sonoro, a volume basso sotto la voce.
 */
import React from "react";
import { AbsoluteFill, Audio, Easing, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { loadFont as caricaMarcellus } from "@remotion/google-fonts/Marcellus";
import { loadFont as caricaRubik } from "@remotion/google-fonts/Rubik";
import { loadFont as caricaInter } from "@remotion/google-fonts/Inter";
import { GraficaEditoriale, type GraficaEd } from "./Editoriale";
import { Tavola, type GraficaTavola } from "./Tavola";
import { loadFont as caricaPlayfair } from "@remotion/google-fonts/PlayfairDisplay";

const FONT: Record<string, string> = {
  Marcellus: caricaMarcellus("normal", { weights: ["400"] }).fontFamily,
  Rubik: caricaRubik("normal", { weights: ["400", "500", "700"] }).fontFamily,
  Inter: caricaInter("normal", { weights: ["400", "600", "800"] }).fontFamily,
  "Playfair Display": caricaPlayfair("normal", { weights: ["500"] }).fontFamily,
};

export type Tema = { fondo: string; testo: string; accento: string; accento_scuro: string; titoli: string; corpo: string };
export type Grafica =
  // y: distanza dall'alto in px, per spostare l'elemento quando al suo posto c'è un volto
  | { tipo: "nome"; da: number; a: number; nome: string; ruolo: string; y?: number }
  | { tipo: "etichetta"; da: number; a: number; numero?: string; testo: string; y?: number }
  | { tipo: "scheda"; da: number; a: number; titolo: string; titolo_at: number; sopratitolo?: string;
      voci: { at: number; numero: string; testo: string }[] }
  | GraficaEd // titolo, capitolo, firma, passaggio: tipografia grande, in Editoriale.tsx
  | GraficaTavola; // tavola dei numeri a tutto schermo, in Tavola.tsx

const FPS = 30;
const fr = (s: number) => Math.round(s * FPS);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
// Tempi di entrata e uscita: a 0,3 s erano "troppo veloci, non danno il tempo di essere letti"
const ENTRATA = 18; // 0,6 s
const USCITA = 14; // 0,47 s
const morbida = Easing.bezier(0.22, 1, 0.36, 1);
const rampa = (f: number, da: number, durata: number) =>
  interpolate(f, [da, da + durata], [0, 1], { ...clamp, easing: morbida });

const SFX = { entra: "sfx/whoosh.wav", voce: "sfx/switch.wav", tocco: "sfx/mouse-click.wav" };

// entrata morbida e uscita negli ultimi 8 fotogrammi
const useEntrataUscita = (ritardo = 0) => {
  const f = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  void fps;
  const in_ = rampa(f, ritardo, ENTRATA);
  const out = interpolate(f, [durationInFrames - USCITA, durationInFrames], [1, 0], { ...clamp, easing: Easing.in(Easing.cubic) });
  return { in_, out };
};

const Nome: React.FC<{ g: Extract<Grafica, { tipo: "nome" }>; t: Tema }> = ({ g, t }) => {
  const { in_, out } = useEntrataUscita();
  const linea = interpolate(in_, [0, 1], [0, 1]);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 70, top: g.y ?? 1345, opacity: out, transform: `translateX(${(1 - in_) * -80}px)` }}>
        <div style={{ background: t.fondo, borderRadius: 18, padding: "22px 34px 24px 30px", boxShadow: "0 10px 40px rgba(0,0,0,0.25)",
          borderLeft: `8px solid ${t.accento}`, opacity: in_ }}>
          <div style={{ fontFamily: FONT[t.titoli], fontSize: 46, color: t.testo, lineHeight: 1.1 }}>{g.nome}</div>
          <div style={{ height: 2, width: 90 * linea, background: t.accento, margin: "12px 0 10px" }} />
          <div style={{ fontFamily: FONT[t.corpo], fontSize: 30, color: t.accento_scuro, letterSpacing: 1 }}>{g.ruolo}</div>
        </div>
      </div>
      <Audio src={staticFile(SFX.entra)} volume={0.25} />
    </AbsoluteFill>
  );
};

const Etichetta: React.FC<{ g: Extract<Grafica, { tipo: "etichetta" }>; t: Tema }> = ({ g, t }) => {
  const { in_, out } = useEntrataUscita();
  return (
    <AbsoluteFill style={{ alignItems: "center" }}>
      <div style={{ position: "absolute", top: g.y ?? 1000, opacity: out * in_, transform: `translateY(${(1 - in_) * 24}px) scale(${0.92 + 0.08 * in_})`,
        display: "flex", alignItems: "center", gap: 22, background: t.fondo, borderRadius: 999, padding: g.numero ? "18px 40px 18px 18px" : "18px 44px",
        boxShadow: "0 10px 40px rgba(0,0,0,0.3)" }}>
        {g.numero && (
          <div style={{ width: 74, height: 74, borderRadius: 999, background: t.accento, color: t.testo, display: "flex",
            alignItems: "center", justifyContent: "center", fontFamily: FONT[t.corpo], fontWeight: 500, fontSize: 40 }}>{g.numero}</div>
        )}
        <div style={{ fontFamily: FONT[t.corpo], fontWeight: 500, fontSize: 40, color: t.testo }}>{g.testo}</div>
      </div>
      <Audio src={staticFile(SFX.tocco)} volume={0.35} />
    </AbsoluteFill>
  );
};

const Scheda: React.FC<{ g: Extract<Grafica, { tipo: "scheda" }>; t: Tema }> = ({ g, t }) => {
  const f = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const t0 = g.da;
  const fondo = interpolate(f, [0, ENTRATA, durationInFrames - USCITA, durationInFrames], [0, 1, 1, 0], clamp);
  const molla = (s: number) => rampa(f, fr(s - t0), ENTRATA);
  const tit = molla(g.titolo_at);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: t.fondo, opacity: fondo }} />
      {/* contenuto ancorato in alto: sotto, a 1238 px, restano i sottotitoli ("chi lo vede non
          sempre ha l'audio attivo") */}
      <AbsoluteFill style={{ opacity: fondo, alignItems: "center", justifyContent: "flex-end", paddingBottom: 770 }}>
        {g.sopratitolo && (
          <div style={{ fontFamily: FONT[t.corpo], fontSize: 36, letterSpacing: 8, color: t.accento_scuro, textTransform: "uppercase",
            opacity: tit }}>{g.sopratitolo}</div>
        )}
        <div style={{ fontFamily: FONT[t.titoli], fontSize: 116, color: t.testo, marginTop: 18, opacity: tit,
          transform: `translateY(${(1 - tit) * 40}px)` }}>{g.titolo}</div>
        <div style={{ height: 3, background: t.accento, width: 160 * tit, margin: "44px 0 56px" }} />
        <div style={{ display: "flex", flexDirection: "column", gap: 44, width: 880 }}>
          {g.voci.map((v, i) => {
            const p = molla(v.at);
            return (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 34, opacity: p, transform: `translateX(${(1 - p) * 60}px)` }}>
                <div style={{ minWidth: 140, fontFamily: FONT[t.corpo], fontWeight: 500, fontSize: 108, color: t.accento_scuro, textAlign: "center", lineHeight: 1 }}>{v.numero}</div>
                <div style={{ fontFamily: FONT[t.corpo], fontSize: 56, color: t.testo, lineHeight: 1.2 }}>{v.testo}</div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
      <Audio src={staticFile(SFX.entra)} volume={0.3} />
      {g.voci.map((v, i) => (
        <Sequence key={i} from={fr(v.at - t0)} layout="none"><Audio src={staticFile(SFX.voce)} volume={0.3} /></Sequence>
      ))}
    </AbsoluteFill>
  );
};

export const Grafiche: React.FC<{ grafiche: Grafica[]; tema: Tema }> = ({ grafiche, tema }) => (
  <>
    {grafiche.map((g, i) => (
      <Sequence key={i} from={fr(g.da)} durationInFrames={fr(g.a) - fr(g.da)}>
        {g.tipo === "nome" && <Nome g={g} t={tema} />}
        {g.tipo === "etichetta" && <Etichetta g={g} t={tema} />}
        {g.tipo === "scheda" && <Scheda g={g} t={tema} />}
        {g.tipo === "tavola" && <Tavola g={g} t={tema} />}
        {(g.tipo === "titolo" || g.tipo === "capitolo" || g.tipo === "firma" || g.tipo === "passaggio") && <GraficaEditoriale g={g} t={tema} />}
      </Sequence>
    ))}
  </>
);
