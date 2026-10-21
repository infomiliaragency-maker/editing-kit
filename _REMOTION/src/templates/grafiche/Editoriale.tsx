/**
 * GRAFICHE EDITORIALI, al posto dei cartellini a pillola bocciati come "cose semplici, banali".
 * Tipografia grande sopra il girato invece dei cartellini: serif corsivo, lettere che salgono da una maschera,
 * filetti e pennellata che si disegnano. Colori e font dal tema del cliente. Quattro tipi:
 * - "titolo":    parola grande con sopratitolo e pennellata sotto (prima, dopo, il risultato)
 * - "capitolo":  numero a filo, filetto verticale, titolo su una o due righe; `compatto` per i tratti con volti
 * - "firma":     monogramma in un cerchio che si disegna, nome e riga sotto (un sottopancia elegante)
 * - "passaggio": lama di luce che attraversa lo schermo su un taglio (`at` = il taglio)
 * `y` è sempre la distanza dall'alto in px: si sceglie dove non ci sono volti né sottotitoli.
 */
import React from "react";
import { AbsoluteFill, Audio, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { loadFont as caricaPlayfair } from "@remotion/google-fonts/PlayfairDisplay";
import { loadFont as caricaInter } from "@remotion/google-fonts/Inter";

export type TemaEd = { accento: string; titoli: string; corpo: string };
export type GraficaEd =
  | { tipo: "titolo"; da: number; a: number; testo: string; sopra?: string; y: number; allinea?: "sinistra" | "centro"; dimensione?: number }
  | { tipo: "capitolo"; da: number; a: number; numero?: string; sopra?: string; titolo: string; y: number; compatto?: boolean }
  | { tipo: "firma"; da: number; a: number; monogramma: string; nome: string; riga: string; y: number }
  | { tipo: "passaggio"; da: number; a: number };

caricaPlayfair("italic", { weights: ["500"] });
const SERIF = caricaPlayfair("normal", { weights: ["500"] }).fontFamily;
const SANS = caricaInter("normal", { weights: ["500", "600"] }).fontFamily;

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const esce = Easing.bezier(0.16, 1, 0.3, 1);
const su = (f: number, da: number, durata: number) => interpolate(f, [da, da + durata], [0, 1], { ...clamp, easing: esce });
const OMBRA = "0 4px 28px rgba(0,0,0,0.55), 0 1px 3px rgba(0,0,0,0.5)";

const useUscita = (n = 13) => {
  const f = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return { f, via: interpolate(f, [durationInFrames - n, durationInFrames], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) }) };
};

// riga di testo che sale lettera per lettera da dietro una maschera
const Riga: React.FC<{ testo: string; f: number; da: number; passo?: number; stile: React.CSSProperties }> = ({ testo, f, da, passo = 1.6, stile }) => (
  <div style={{ overflow: "hidden", padding: "0.12em 0.18em 0.24em", margin: "-0.12em -0.18em -0.24em", whiteSpace: "nowrap", ...stile }}>
    {[...testo].map((c, i) => {
      const p = su(f, da + i * passo, 20);
      return (
        <span key={i} style={{ display: "inline-block", transform: `translateY(${(1 - p) * 112}%) rotate(${(1 - p) * 5}deg)`, opacity: Math.min(1, p * 1.6),
          filter: `blur(${(1 - p) * 5}px)` }}>{c === " " ? " " : c}</span>
      );
    })}
  </div>
);

// alone scuro morbido dietro il testo, senza bordi: sfuma in tutte le direzioni
const Velo: React.FC<{ top: number; alto: number; op: number; lato?: boolean }> = ({ top, alto, op, lato }) => (
  <div style={{ position: "absolute", left: 0, right: 0, top: top - alto * 0.25, height: alto * 1.5, opacity: op,
    background: lato
      ? "radial-gradient(ellipse 95% 50% at 12% 50%, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0.28) 40%, rgba(0,0,0,0) 72%)"
      : "radial-gradient(ellipse 75% 50% at 50% 50%, rgba(0,0,0,0.45) 0%, rgba(0,0,0,0) 72%)" }} />
);

const Titolo: React.FC<{ g: Extract<GraficaEd, { tipo: "titolo" }>; t: TemaEd }> = ({ g, t }) => {
  const { f, via } = useUscita();
  const centro = g.allinea === "centro";
  const dim = g.dimensione ?? 190;
  const penn = su(f, 12 + g.testo.length * 1.6, 26);
  return (
    <AbsoluteFill>
      <Velo top={g.y - 150} alto={dim + 380} op={su(f, 0, 14) * (1 - via)} lato={!centro} />
      <div style={{ position: "absolute", left: 72, right: 72, top: g.y, opacity: 1 - via, transform: `translateY(${-via * 36}px)`,
        display: "flex", flexDirection: "column", alignItems: centro ? "center" : "flex-start" }}>
        {g.sopra && (
          <div style={{ display: "flex", alignItems: "center", gap: 22, marginBottom: 6 }}>
            <div style={{ height: 2, width: 84 * su(f, 0, 22), background: t.accento }} />
            <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 30, color: t.accento, textTransform: "uppercase", textShadow: OMBRA,
              letterSpacing: 9 + (1 - su(f, 2, 26)) * 16, opacity: su(f, 2, 16) }}>{g.sopra}</div>
            {centro && <div style={{ height: 2, width: 84 * su(f, 0, 22), background: t.accento }} />}
          </div>
        )}
        <div style={{ position: "relative" }}>
          <Riga testo={g.testo} f={f} da={5} stile={{ fontFamily: SERIF, fontStyle: "italic", fontWeight: 500, fontSize: dim, lineHeight: 1.05,
            color: "#FFFFFF", textShadow: OMBRA, letterSpacing: "-0.01em" }} />
          <svg viewBox="0 0 600 40" preserveAspectRatio="none" style={{ position: "absolute", left: "2%", right: 0, bottom: -dim * 0.1, width: "96%", height: dim * 0.2,
            overflow: "visible" }}>
            <path d="M4 26 C 110 6, 250 34, 380 16 S 560 10, 596 22" fill="none" stroke={t.accento} strokeWidth={5} strokeLinecap="round"
              pathLength={1} strokeDasharray={1} strokeDashoffset={1 - penn} vectorEffect="non-scaling-stroke" />
          </svg>
        </div>
      </div>
      <Audio src={staticFile("sfx/whoosh.wav")} volume={0.22} />
    </AbsoluteFill>
  );
};

const Capitolo: React.FC<{ g: Extract<GraficaEd, { tipo: "capitolo" }>; t: TemaEd }> = ({ g, t }) => {
  const { f, via } = useUscita();
  const k = g.compatto ? 0.74 : 1;
  const righe = g.titolo.split("\n");
  const alto = (g.sopra ? 50 : 0) + righe.length * 92 * k + 30;
  const n = su(f, 0, 22);
  return (
    <AbsoluteFill>
      <Velo top={g.y - 90} alto={alto + 200} op={su(f, 0, 14) * (1 - via)} lato />
      <div style={{ position: "absolute", left: 72, top: g.y, display: "flex", alignItems: "stretch", gap: 30 * k, opacity: 1 - via,
        transform: `translateX(${-via * 50}px)` }}>
        {g.numero && (
          <div style={{ overflow: "hidden", display: "flex", alignItems: "center" }}>
            <div style={{ fontFamily: SERIF, fontWeight: 500, fontSize: 230 * k, lineHeight: 0.86, color: "rgba(243,217,164,0.16)",
              WebkitTextStroke: `${g.compatto ? 2.5 : 3}px ${t.accento}`, filter: "drop-shadow(0 3px 14px rgba(0,0,0,0.45))", transform: `translateY(${(1 - n) * 100}%)`, letterSpacing: "-0.03em" }}>{g.numero}</div>
          </div>
        )}
        <div style={{ width: 2, background: t.accento, transform: `scaleY(${su(f, 6, 24)})`, transformOrigin: "top" }} />
        <div style={{ display: "flex", flexDirection: "column", justifyContent: "center" }}>
          {g.sopra && (
            <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 28 * (g.compatto ? 0.8 : 1), color: t.accento, textTransform: "uppercase", textShadow: OMBRA,
              letterSpacing: 8 + (1 - su(f, 8, 26)) * 12, opacity: su(f, 8, 16), marginBottom: 8 }}>{g.sopra}</div>
          )}
          {righe.map((r, i) => (
            <Riga key={i} testo={r} f={f} da={10 + i * 6} passo={1.1} stile={{ fontFamily: SERIF, fontStyle: "italic", fontWeight: 500, fontSize: 86 * k,
              lineHeight: 1.08, color: "#FFFFFF", textShadow: OMBRA }} />
          ))}
        </div>
      </div>
      <Audio src={staticFile("sfx/switch.wav")} volume={0.22} />
    </AbsoluteFill>
  );
};

const Firma: React.FC<{ g: Extract<GraficaEd, { tipo: "firma" }>; t: TemaEd }> = ({ g, t }) => {
  const { f, via } = useUscita();
  const R = 54;
  const giro = su(f, 0, 30);
  return (
    <AbsoluteFill>
      <Velo top={g.y - 80} alto={300} op={su(f, 0, 14) * (1 - via)} lato />
      <div style={{ position: "absolute", left: 72, top: g.y, display: "flex", alignItems: "center", gap: 28, opacity: 1 - via,
        transform: `translateX(${-via * 50}px)` }}>
        <div style={{ position: "relative", width: R * 2 + 8, height: R * 2 + 8 }}>
          <svg width={R * 2 + 8} height={R * 2 + 8} style={{ transform: "rotate(-90deg)" }}>
            <circle cx={R + 4} cy={R + 4} r={R} fill="rgba(0,0,0,0.28)" stroke={t.accento} strokeWidth={2.5} pathLength={1} strokeDasharray={1}
              strokeDashoffset={1 - giro} />
          </svg>
          <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: SERIF, fontStyle: "italic",
            fontSize: 46, color: "#FFFFFF", opacity: su(f, 14, 16), transform: `scale(${0.8 + 0.2 * su(f, 14, 20)})` }}>{g.monogramma}</div>
        </div>
        <div>
          <Riga testo={g.nome} f={f} da={10} passo={1.1} stile={{ fontFamily: SERIF, fontStyle: "italic", fontWeight: 500, fontSize: 66, lineHeight: 1.08,
            color: "#FFFFFF", textShadow: OMBRA }} />
          <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 10 }}>
            <div style={{ height: 2, width: 46 * su(f, 16, 20), background: t.accento }} />
            <div style={{ fontFamily: SANS, fontWeight: 500, fontSize: 27, color: t.accento, textTransform: "uppercase", textShadow: OMBRA,
              letterSpacing: 5 + (1 - su(f, 18, 24)) * 10, opacity: su(f, 18, 16) }}>{g.riga}</div>
          </div>
        </div>
      </div>
      <Audio src={staticFile("sfx/switch.wav")} volume={0.2} />
    </AbsoluteFill>
  );
};

// lama di luce da sinistra a destra: il taglio cade a metà della sua durata
const Passaggio: React.FC<{ t: TemaEd }> = ({ t }) => {
  const f = useCurrentFrame();
  const { durationInFrames: D } = useVideoConfig();
  const x = interpolate(f, [0, D], [-45, 125], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const forza = interpolate(f, [0, D * 0.5, D], [0, 1, 0], clamp);
  return (
    <AbsoluteFill style={{ mixBlendMode: "screen" }}>
      <div style={{ position: "absolute", top: -100, bottom: -100, left: `${x}%`, width: "34%", transform: "skewX(-12deg)", filter: "blur(26px)", opacity: forza,
        background: `linear-gradient(90deg, rgba(255,255,255,0) 0%, ${t.accento} 45%, #FFFFFF 50%, ${t.accento} 55%, rgba(255,255,255,0) 100%)` }} />
      <AbsoluteFill style={{ background: "#FFF6E6", opacity: forza * 0.22 }} />
      <Audio src={staticFile("sfx/whoosh.wav")} volume={0.3} />
    </AbsoluteFill>
  );
};

export const GraficaEditoriale: React.FC<{ g: GraficaEd; t: TemaEd }> = ({ g, t }) => {
  if (g.tipo === "titolo") return <Titolo g={g} t={t} />;
  if (g.tipo === "capitolo") return <Capitolo g={g} t={t} />;
  if (g.tipo === "firma") return <Firma g={g} t={t} />;
  return <Passaggio t={t} />;
};
