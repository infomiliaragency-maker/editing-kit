/**
 * SOTTOTITOLI DINAMICI (parole a tempo davanti, parola chiave enorme dietro la persona). Provati e bocciati: il
 * default resta "blocchi"; si propongono solo con un riferimento e un'anteprima breve.
 * Due livelli, tutti e due dai blocchi di sempre (sottotitoli_blocchi.json):
 * - <DinamiciCaptions>: davanti. Minuscolo, le parole entrano una alla volta sul loro tempo con un piccolo rimbalzo;
 *   le parole chiave (aspetto.parole_blu) in serif corsivo, più grandi e nel colore del cliente.
 * - <ParolaDietro>: la parola chiave enorme DIETRO la persona. Va montata fra il girato e il ritaglio della persona con
 *   canale alfa (lo fa Montaggio.tsx), quindi serve il ritaglio: `_TOOLS/remotion.py montaggio --sottotitoli dinamici`
 *   legge <video>/dietro.json.
 * Tutte le parole restano comunque leggibili davanti: quella dietro è un accento, non sostituisce il sottotitolo.
 */
import React from "react";
import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { loadFont as inter } from "@remotion/google-fonts/Inter";
import { loadFont as playfair } from "@remotion/google-fonts/PlayfairDisplay";
import type { Blocco, ParolaDietroT, StileBlocchi } from "../../montaggio/tipi";

const SANS = inter("normal", { weights: ["800", "900"] }).fontFamily;
playfair("italic", { weights: ["600"] });
const SERIF = playfair("normal", { weights: ["600"] }).fontFamily;

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const pulisci = (t: string) => t.replace(/[^\p{L}\p{N}'’]/gu, "").toUpperCase();

export const DinamiciCaptions: React.FC<{ blocchi: Blocco[]; aspetto: StileBlocchi }> = ({ blocchi, aspetto }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const b = blocchi.find((x) => t >= x.da && t < x.a);
  if (!b) return null;
  const esce = interpolate((b.a - t) * fps, [0, 3], [0.2, 1], clamp);
  const dim = aspetto.dimensione * 1.3;
  let k = 0;
  const righe = b.testo.split("\n").map((riga) =>
    riga.trim().split(/\s+/).filter(Boolean).map((w) => {
      const i = k++;
      // la prima parola parte con il blocco, le altre sul loro tempo
      const t0 = i === 0 ? b.da : Math.max(b.da, b.parole[i]?.[1] ?? b.da);
      const chiave = (aspetto.parole_blu ?? []).includes(pulisci(w)) || /\p{N}/u.test(w);
      return { w, t0, chiave };
    }),
  );
  return (
    <div style={{ position: "absolute", left: 50, right: 50, top: b.y ?? aspetto.y, transform: "translateY(-50%)", textAlign: "center", opacity: esce,
      fontFamily: SANS, fontWeight: 800, fontSize: dim, lineHeight: 1.16, letterSpacing: "-0.015em", color: "#FFFFFF" }}>
      {righe.map((r, i) => (
        <div key={i} style={{ display: "flex", justifyContent: "center", alignItems: "baseline", gap: "0.26em", flexWrap: "nowrap" }}>
          {r.map(({ w, t0, chiave }, j) => {
            const dt = (t - t0) * fps;
            const s = spring({ frame: Math.max(0, dt), fps, config: { damping: 12, stiffness: 220, mass: 0.55 } });
            const op = dt < 0 ? 0 : Math.min(1, 0.35 + dt / 3);
            return (
              <span key={j} style={{ display: "inline-block", opacity: op, transform: `translateY(${(1 - s) * 30}px) scale(${0.7 + 0.3 * s})`,
                transformOrigin: "50% 80%", whiteSpace: "nowrap",
                textShadow: "0 3px 0 rgba(0,0,0,0.38), 0 8px 30px rgba(0,0,0,0.62), 0 0 3px rgba(0,0,0,0.7)",
                ...(chiave
                  ? { fontFamily: SERIF, fontStyle: "italic", fontWeight: 600, fontSize: dim * 1.3, color: aspetto.colore_blu ?? "#FFFFFF", letterSpacing: "0",
                      lineHeight: 1 }
                  : {}) }}>
                {w.toLowerCase()}
              </span>
            );
          })}
        </div>
      ))}
    </div>
  );
};

// parola enorme dietro la persona: sta in una Sequence lunga quanto la sua comparsa
export const ParolaDietro: React.FC<{ d: ParolaDietroT; colore: string }> = ({ d, colore }) => {
  const f = useCurrentFrame();
  const { durationInFrames: D } = useVideoConfig();
  const entra = interpolate(f, [0, 14], [0, 1], { ...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1) });
  const via = interpolate(f, [D - 7, D], [1, 0], clamp);
  return (
    <div style={{ position: "absolute", left: -60, right: -60, top: d.y, textAlign: "center", whiteSpace: "nowrap",
      transform: `translateY(-50%) scale(${1.22 - 0.22 * entra + (f / D) * 0.04})`, opacity: Math.min(entra * 1.4, 1) * via,
      fontFamily: SANS, fontWeight: 900, fontSize: d.dimensione, lineHeight: 1, letterSpacing: `${-0.03 + (1 - entra) * 0.08}em`, textTransform: "uppercase",
      color: colore, textShadow: "0 10px 60px rgba(0,0,0,0.35)" }}>
      {d.testo}
    </div>
  );
};
