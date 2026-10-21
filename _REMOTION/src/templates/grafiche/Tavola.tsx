/**
 * TAVOLA: la tavola dei numeri a tutto schermo, animata. Ogni elemento entra sulla parola che lo nomina.
 * Codici del brand dal tema: fondo, testo, accento (la keyword colorata). Una sola famiglia, Inter.
 * - etichetta:  micro-label maiuscola con spaziatura, nel colore d'accento
 * - barra:      linea sottile che si riempie fino a `barra` (0-1)
 * - firma:      riga discreta in alto ("Nome Cognome · Ruolo")
 * - titolo:     righe grandi in ExtraBold maiuscolo che salgono da una maschera; *parola* = nel colore d'accento
 * - righe:      voce a sinistra, valore grande a destra (frecce comprese); `forte` = valore nel colore d'accento
 * - elenco:     numero d'accento e testo, una voce per parola detta
 * - accendi:    istante in cui la riga `forte` o quella indicata si evidenzia con un fondo d'accento
 * `apertura`: nessuna entrata, il primo fotogramma è già la tavola piena (copertina del reel).
 * Il contenuto sta fra 300 e `fondo_contenuto` px (default 1400): sotto restano i sottotitoli.
 */
import React from "react";
import { AbsoluteFill, Audio, Easing, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { loadFont as caricaInter } from "@remotion/google-fonts/Inter";

const INTER = caricaInter("normal", { weights: ["500", "600", "700", "800"] }).fontFamily;

export type TemaTavola = { fondo: string; testo: string; accento: string };
export type GraficaTavola = {
  tipo: "tavola";
  da: number;
  a: number;
  apertura?: boolean;
  etichetta?: string;
  barra?: number;
  firma?: string;
  // una riga può avere il suo istante ({testo, at}); le altre entrano in cascata dopo `at`
  titolo?: { righe: (string | { testo: string; at: number })[]; at: number; dimensione?: number; prima_piccola?: boolean; maiuscolo?: boolean };
  righe?: { at: number; voce: string; valore: string; forte?: boolean }[];
  elenco?: { at: number; numero: string; testo: string }[];
  accendi?: { at: number; riga: number };
  fondo_contenuto?: number;
  suoni?: boolean;
};

const FPS = 30;
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const morbida = Easing.bezier(0.22, 1, 0.36, 1);
const su = (f: number, da: number, durata: number) => interpolate(f, [da, da + durata], [0, 1], { ...clamp, easing: morbida });
// Tempi come in Grafiche.tsx ("troppo veloci, non danno il tempo di essere letti"): entrata 0,6 s, uscita 0,47 s
const ENTRATA = 18;
const USCITA = 14;
const MARGINE = 88;

// "*parola*" nel colore d'accento
const Testo: React.FC<{ t: string; accento: string }> = ({ t, accento }) => (
  <>
    {t.split(/(\*[^*]+\*)/).map((p, i) =>
      p.startsWith("*") ? <span key={i} style={{ color: accento }}>{p.slice(1, -1)}</span> : <React.Fragment key={i}>{p}</React.Fragment>,
    )}
  </>
);

export const Tavola: React.FC<{ g: GraficaTavola; t: TemaTavola }> = ({ g, t }) => {
  const f = useCurrentFrame();
  const { durationInFrames: D } = useVideoConfig();
  const at = (s: number) => Math.round((s - g.da) * FPS);
  const entra = g.apertura ? 1 : su(f, 0, ENTRATA);
  const esce = interpolate(f, [D - USCITA, D], [1, 0], { ...clamp, easing: Easing.in(Easing.cubic) });
  const op = Math.min(entra, esce);
  // con l'apertura tutto è già al suo posto dal fotogramma 0
  const k = (da: number, durata = ENTRATA) => (g.apertura ? 1 : su(f, da, durata));
  const fondoContenuto = g.fondo_contenuto ?? 1400;
  const suoni = g.suoni ?? true;
  const dim = g.titolo?.dimensione ?? 128;

  return (
    <AbsoluteFill style={{ opacity: op }}>
      <AbsoluteFill style={{ background: t.fondo }} />
      {/* alone appena percepibile, come nella copertina: stacca il blocco dal fondo piatto */}
      <div style={{ position: "absolute", left: -180, top: 560, width: 1000, height: 900, opacity: k(4, 30),
        background: `radial-gradient(closest-side, ${t.accento}22, ${t.accento}00 78%)` }} />

      {g.firma && (
        <div style={{ position: "absolute", top: 170, left: MARGINE, fontFamily: INTER, fontWeight: 700, fontSize: 24, letterSpacing: "0.18em",
          textTransform: "uppercase", color: `${t.testo}4D`, opacity: k(2) }}>{g.firma}</div>
      )}
      <div style={{ position: "absolute", top: 230, left: MARGINE, width: 1080 - 2 * MARGINE, height: 3, background: `${t.testo}1F` }}>
        <div style={{ height: "100%", background: t.accento, width: `${(g.barra ?? 0.2) * 100 * k(6, 26)}%` }} />
      </div>

      <div style={{ position: "absolute", top: 300, bottom: 1920 - fondoContenuto, left: MARGINE, right: MARGINE, display: "flex",
        flexDirection: "column", justifyContent: "center", fontFamily: INTER, color: t.testo }}>
        {g.etichetta && (
          <div style={{ fontWeight: 700, fontSize: 30, textTransform: "uppercase", color: t.accento, marginBottom: 60, opacity: k(4, 16),
            letterSpacing: `${0.22 + (1 - k(4, 26)) * 0.18}em` }}>{g.etichetta}</div>
        )}

        {g.titolo &&
          g.titolo.righe.map((r, i) => {
            const piccola = g.titolo!.prima_piccola && i === 0;
            const testo = typeof r === "string" ? r : r.testo;
            const p = k(typeof r === "string" ? at(g.titolo!.at) + i * 5 : at(r.at), 22);
            return (
              <div key={i} style={{ overflow: "hidden", padding: "0.06em 0", margin: "-0.06em 0" }}>
                <div style={{ fontWeight: 800, fontSize: piccola ? dim * 0.62 : dim, lineHeight: 1.08, letterSpacing: "-0.025em",
                  textTransform: g.titolo!.maiuscolo === false ? "none" : "uppercase",
                  whiteSpace: "nowrap", color: piccola ? `${t.testo}B3` : t.testo, marginBottom: piccola ? 14 : 0,
                  transform: `translateY(${(1 - p) * 105}%)`, opacity: Math.min(1, p * 1.5) }}>
                  <Testo t={testo} accento={t.accento} />
                </div>
              </div>
            );
          })}

        {g.righe?.map((r, i) => {
          const p = k(at(r.at));
          const luce = g.accendi && g.accendi.riga === i ? su(f, at(g.accendi.at), 14) : 0;
          return (
            <div key={i} style={{ position: "relative", display: "flex", alignItems: "baseline", justifyContent: "space-between", padding: "26px 0",
              opacity: p, transform: `translateX(${(1 - p) * 48}px)` }}>
              <div style={{ position: "absolute", left: -24, right: -24, top: 4, bottom: 4, borderRadius: 14, background: `${t.accento}29`,
                border: `2px solid ${t.accento}`, opacity: luce }} />
              <div style={{ position: "relative", fontWeight: 500, fontSize: 42, color: r.forte || luce > 0.5 ? t.testo : `${t.testo}9E` }}>{r.voce}</div>
              <div style={{ position: "relative", fontWeight: 800, fontSize: 76, letterSpacing: "-0.02em", color: r.forte ? t.accento : t.testo }}>
                <Testo t={r.valore} accento={t.accento} />
              </div>
              {i < (g.righe!.length - 1) && (
                <div style={{ position: "absolute", left: 0, bottom: 0, height: 1, width: `${100 * k(at(r.at) + 6, 20)}%`, background: `${t.testo}17` }} />
              )}
            </div>
          );
        })}

        {g.elenco?.map((v, i) => {
          const p = k(at(v.at));
          return (
            <div key={i} style={{ display: "flex", alignItems: "baseline", gap: 40, padding: "30px 0", opacity: p, transform: `translateX(${(1 - p) * 48}px)`,
              borderBottom: i < g.elenco!.length - 1 ? `1px solid ${t.testo}17` : "none" }}>
              <div style={{ fontWeight: 800, fontSize: 84, color: t.accento, minWidth: 64, lineHeight: 1 }}>{v.numero}</div>
              <div style={{ fontWeight: 800, fontSize: 66, letterSpacing: "-0.02em", lineHeight: 1.1 }}><Testo t={v.testo} accento={t.accento} /></div>
            </div>
          );
        })}
      </div>

      {suoni && !g.apertura && <Audio src={staticFile("sfx/whoosh.wav")} volume={0.16} />}
      {suoni &&
        [...(g.righe ?? []), ...(g.elenco ?? [])].map((r, i) => (
          <Sequence key={i} from={Math.max(0, at(r.at))} layout="none"><Audio src={staticFile("sfx/switch.wav")} volume={0.18} /></Sequence>
        ))}
    </AbsoluteFill>
  );
};
