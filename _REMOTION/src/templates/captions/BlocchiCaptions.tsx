/**
 * SOTTOTITOLI A BLOCCHI (lo stesso stile dei progetti CapCut, da sottotitoli_capcut.py)
 * - blocchi attaccati, testo già maiuscolo e già andato a capo da sottotitoli_capcut.blocchi()
 * - bianco con bordo nero, opzionale colore sulla parola che si sta dicendo
 * Uso: <BlocchiCaptions blocchi={...} aspetto={...} />, tempi in secondi sulla timeline montata.
 */
import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { loadFont as inter } from "@remotion/google-fonts/Inter";
import { loadFont as montserrat } from "@remotion/google-fonts/Montserrat";
import { loadFont as poppins } from "@remotion/google-fonts/Poppins";
import type { Blocco, StileBlocchi } from "../../montaggio/tipi";

const FONT = {
  Inter: inter("normal", { weights: ["800", "900"] }).fontFamily,
  Montserrat: montserrat("normal", { weights: ["800", "900"] }).fontFamily,
  Poppins: poppins("normal", { weights: ["800", "900"] }).fontFamily,
};

const pulisci = (t: string) => t.replace(/[^\p{L}\p{N}'’]/gu, "").toUpperCase();

export const BlocchiCaptions: React.FC<{ blocchi: Blocco[]; aspetto: StileBlocchi }> = ({ blocchi, aspetto }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const b = blocchi.find((x) => t >= x.da && t < x.a);
  if (!b) return null;

  // la parola attiva è l'ultima già iniziata: si cerca nel testo del blocco per posizione
  const attiva = aspetto.evidenza ? b.parole.filter((p) => p[1] <= t).length - 1 : -1;
  let k = 0;
  const righe = b.testo.split("\n").map((riga) =>
    riga
      .trim()
      .split(/\s+/)
      .filter(Boolean)
      .map((w) => {
        const i = k++;
        const on = i === attiva && b.parole[i] && pulisci(b.parole[i][0]) === pulisci(w);
        const blu = !!aspetto.colore_blu && (/\p{N}/u.test(w) || w === "€" || (aspetto.parole_blu ?? []).includes(pulisci(w)));
        return { w, on, blu };
      }),
  );

  const s = aspetto.bordo_px;
  return (
    <div
      style={{
        position: "absolute",
        left: 60,
        right: 60,
        top: b.y ?? aspetto.y,
        transform: "translateY(-50%)",
        textAlign: "center",
        fontFamily: FONT[aspetto.font],
        fontWeight: aspetto.peso,
        fontSize: aspetto.dimensione,
        lineHeight: 1.12,
        letterSpacing: "-0.01em",
        color: aspetto.colore,
        WebkitTextStroke: `${s * 2}px ${aspetto.bordo}`,
        paintOrder: "stroke fill",
      }}
    >
      {righe.map((r, i) => (
        <div key={i}>
          {r.map(({ w, on, blu }, j) => (
            <span key={j} style={{ color: on ? aspetto.evidenza! : blu ? aspetto.colore_blu : undefined }}>
              {w}
              {j < r.length - 1 ? " " : ""}
            </span>
          ))}
        </div>
      ))}
    </div>
  );
};
