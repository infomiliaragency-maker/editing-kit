/**
 * TRANSIZIONI CON SOUND EFFECT
 * - "swoosh": whip pan orizzontale con motion blur direzionale + SFX whoosh
 * - "flash":  lampo di luce calda (light leak) + SFX camera shutter
 *
 * Uso:
 *   <TransitionStage transitions={TR}> ...tutti i layer video... </TransitionStage>
 *   <TransitionOverlays transitions={TR} />   (sopra i video, sotto i sottotitoli)
 * Tempi in secondi = istante esatto del taglio.
 */
import React from "react";
import { AbsoluteFill, Audio, Easing, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

export type Transition = { at: number; kind: "swoosh" | "flash"; dir?: 1 | -1 };

const HALF = 9; // frame prima e dopo il taglio (con 6 erano troppo rapide)
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const SFX = {
  // swoosh.wav: sintetizzato (aria che sale + tonfo di whoosh.wav sul taglio), picco a 0.30s
  swoosh: { file: "sfx/swoosh.wav", lead: 9, volume: 0.6 },
  flash: { file: "sfx/shutter-modern.wav", lead: 2, volume: 0.5 },
};

// Restituisce la transizione attiva e la posizione p ∈ [-1, 1] (0 = istante del taglio)
const useActive = (transitions: Transition[]) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  for (const tr of transitions) {
    const d = frame - Math.round(tr.at * fps);
    if (d >= -HALF && d < HALF) return { tr, p: d / HALF };
  }
  return null;
};

export const TransitionStage: React.FC<{ transitions: Transition[]; children: React.ReactNode }> = ({ transitions, children }) => {
  const { width } = useVideoConfig();
  const a = useActive(transitions);
  let transform = "none";
  let blurX = 0;
  let brightness = 1;

  if (a?.tr.kind === "swoosh") {
    const dir = a.tr.dir ?? -1;
    // Prima del taglio accelera via, dopo il taglio rientra decelerando
    const x =
      a.p < 0
        ? interpolate(a.p, [-1, 0], [0, 0.22], { ...clamp, easing: Easing.in(Easing.cubic) })
        : interpolate(a.p, [0, 1], [-0.22, 0], { ...clamp, easing: Easing.out(Easing.cubic) });
    const k = 1 - Math.abs(a.p);
    transform = `translateX(${dir * x * width}px) scale(${1 + 0.18 * k})`;
    blurX = 70 * Math.pow(k, 1.4);
  }
  if (a?.tr.kind === "flash") {
    brightness = 1 + 0.9 * Math.pow(1 - Math.abs(a.p), 2);
  }

  return (
    <AbsoluteFill>
      <svg width="0" height="0" style={{ position: "absolute" }}>
        <filter id="tr-hblur" x="-20%" y="0" width="140%" height="100%">
          <feGaussianBlur stdDeviation={`${blurX} 0`} />
        </filter>
      </svg>
      <AbsoluteFill
        style={{
          transform,
          filter: `${blurX > 0.5 ? "url(#tr-hblur) " : ""}brightness(${brightness})`,
        }}
      >
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const TransitionOverlays: React.FC<{ transitions: Transition[] }> = ({ transitions }) => {
  const { fps } = useVideoConfig();
  const a = useActive(transitions);
  const k = a ? 1 - Math.abs(a.p) : 0;

  return (
    <>
      {a?.tr.kind === "flash" && (
        <AbsoluteFill style={{ pointerEvents: "none" }}>
          {/* Light leak caldo che attraversa il frame */}
          <AbsoluteFill
            style={{
              mixBlendMode: "screen",
              opacity: Math.pow(k, 0.8),
              background: `radial-gradient(ellipse 90% 70% at ${30 + 40 * (a.p + 1) / 2}% 35%, rgba(255,246,230,1) 0%, rgba(255,186,110,0.9) 35%, rgba(255,110,60,0.35) 65%, rgba(0,0,0,0) 85%)`,
            }}
          />
          {/* Picco bianco di 2-3 frame sul taglio */}
          <AbsoluteFill style={{ background: "white", opacity: Math.max(0, (k - 0.6) / 0.4) * 0.85 }} />
        </AbsoluteFill>
      )}
      {transitions.map((tr, i) => {
        const s = SFX[tr.kind];
        return (
          <Sequence key={i} from={Math.max(0, Math.round(tr.at * fps) - s.lead)} durationInFrames={Math.round(fps * 0.8)} layout="none">
            <Audio src={staticFile(s.file)} volume={s.volume} />
          </Sequence>
        );
      })}
    </>
  );
};
