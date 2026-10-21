/**
 * MODELLO SOTTOTITOLI "REF2" (da Reference Video 2)
 * - riga piccola, Poppins 400 bianco, compare parola per parola (fade + blur + leggero salita)
 * - sotto, frase chiave grande Poppins 800, entra da sfocata/ingrandita a nitida
 * - opzionale riquadro rosso dietro la frase chiave (red: true), si apre da sinistra
 * - posizione: all'altezza del petto (y ≈ 1170 su 1920)
 *
 * Uso: <Ref2Captions chunks={CHUNKS} />, tempi in secondi sulla timeline del video.
 */
import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { loadFont } from "@remotion/google-fonts/Poppins";

const { fontFamily } = loadFont("normal", { weights: ["400", "800"] });

export type CaptionChunk = {
  start: number;
  end: number;
  small: { t: string; at: number }[];
  big: { t: string; at: number };
  red: boolean;
};

export const REF2_RED = "#E3242B";

const ease = Easing.out(Easing.cubic);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// Larghezza utile 960px: riduce il corpo del testo grande quando la frase è lunga
const bigSize = (text: string) => Math.min(112, Math.floor(960 / (text.length * 0.56)));

const SmallWord: React.FC<{ t: string; at: number }> = ({ t, at }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = interpolate(frame - at * fps, [0, 5], [0, 1], { ...clamp, easing: ease });
  return (
    <span
      style={{
        display: "inline-block",
        marginRight: "0.26em",
        opacity: p,
        filter: `blur(${(1 - p) * 8}px)`,
        transform: `translateY(${(1 - p) * 8}px)`,
      }}
    >
      {t}
    </span>
  );
};

const ChunkView: React.FC<{ c: CaptionChunk; y: number }> = ({ c, y }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fb = frame - c.big.at * fps;
  const p = interpolate(fb, [0, 7], [0, 1], { ...clamp, easing: ease });
  const boxP = interpolate(fb, [2, 9], [0, 1], { ...clamp, easing: ease });
  const out = interpolate(frame, [c.end * fps - 3, c.end * fps], [1, 0], clamp);
  const size = bigSize(c.big.t);

  return (
    <div style={{ position: "absolute", left: 0, right: 0, top: y, opacity: out, textAlign: "center", fontFamily }}>
      <div
        style={{
          fontWeight: 400,
          fontSize: 48,
          letterSpacing: "-0.02em",
          color: "white",
          textShadow: "0 2px 10px rgba(0,0,0,0.55)",
          padding: "0 70px",
        }}
      >
        {c.small.map((w, i) => (
          <SmallWord key={i} t={w.t} at={w.at} />
        ))}
      </div>
      <div style={{ position: "relative", display: "inline-block", marginTop: -6 }}>
        {c.red && (
          <div
            style={{
              position: "absolute",
              left: -14,
              right: -14,
              top: "22%",
              bottom: "8%",
              background: REF2_RED,
              transformOrigin: "left center",
              transform: `scaleX(${boxP})`,
              boxShadow: "0 8px 24px rgba(0,0,0,0.35)",
            }}
          />
        )}
        <div
          style={{
            position: "relative",
            fontWeight: 800,
            fontSize: size,
            lineHeight: 1.1,
            letterSpacing: "-0.04em",
            wordSpacing: "0.12em",
            color: "white",
            whiteSpace: "nowrap",
            opacity: p,
            filter: `blur(${(1 - p) * 14}px)`,
            transform: `scale(${1.18 - 0.18 * p})`,
            textShadow: "0 4px 18px rgba(0,0,0,0.5)",
          }}
        >
          {c.big.t}
        </div>
      </div>
    </div>
  );
};

export const Ref2Captions: React.FC<{ chunks: CaptionChunk[]; y?: number }> = ({ chunks, y = 1170 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const c = chunks.find((x) => t >= x.start && t < x.end);
  return c ? <ChunkView key={c.start} c={c} y={y} /> : null;
};
