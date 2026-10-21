/**
 * MONTAGGIO GENERICO: un solo modello per ogni video, guidato da montaggio.json.
 * Il json e i media li prepara _TOOLS/remotion.py nella cartella del video (<video>/_remotion/public/).
 * Render: python3 _TOOLS/remotion.py render <cartella video>
 */
import React from "react";
import { AbsoluteFill, Audio, CalculateMetadataFunction, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { smoothZoom, ZOOM_CURVE } from "../templates/smoothZoom";
import { TransitionOverlays, TransitionStage } from "../templates/transitions";
import { Ref2Captions } from "../templates/captions/Ref2Captions";
import { BlocchiCaptions } from "../templates/captions/BlocchiCaptions";
import { DinamiciCaptions, ParolaDietro } from "../templates/captions/DinamiciCaptions";
import { Grafiche } from "../templates/grafiche/Grafiche";
import type { Montaggio as M } from "./tipi";

const FPS = 30;
const fr = (s: number) => Math.round(s * FPS);

const Parlato: React.FC<{ m: M }> = ({ m }) => {
  const frame = useCurrentFrame();
  const scale = m.zoom.attivo
    ? smoothZoom(frame / FPS, m.segmenti, { levels: m.zoom.livelli, rampS: m.zoom.rampa_s, driftPerSecond: m.zoom.deriva ?? 0.006 })
    : 1;
  return (
    <AbsoluteFill style={{ transform: `scale(${scale})`, transformOrigin: "50% 32%" }}>
      <OffthreadVideo src={staticFile(m.parlato.file)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      {m.sottotitoli.stile === "dinamici" && m.sottotitoli.dietro.map((d, i) => (
        // parola dietro la persona: sopra il girato, sotto il ritaglio della persona (stesso zoom del girato)
        <Sequence key={i} from={fr(d.da)} durationInFrames={fr(d.a) - fr(d.da)}>
          <ParolaDietro d={d} colore={m.sottotitoli.stile === "dinamici" ? m.sottotitoli.aspetto.colore_blu ?? "#FFFFFF" : "#FFFFFF"} />
          <OffthreadVideo transparent muted src={staticFile(d.file)} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

// b-roll muto a tutto schermo, con push-in lento sulla stessa curva dello zoom
const BRoll: React.FC<{ file: string; offset: number; pushIn: boolean }> = ({ file, offset, pushIn }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const zoom = pushIn ? interpolate(frame, [0, durationInFrames], [1.0, 1.08], { easing: ZOOM_CURVE }) : 1;
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <AbsoluteFill style={{ transform: `scale(${zoom})` }}>
        <OffthreadVideo muted startFrom={fr(offset)} src={staticFile(file)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const Montaggio: React.FC<{ m: M | null }> = ({ m }) => {
  if (!m) {
    return (
      <AbsoluteFill style={{ backgroundColor: "black", color: "white", fontSize: 48, padding: 80, justifyContent: "center" }}>
        Manca montaggio.json: lancia python3 _TOOLS/remotion.py studio &lt;cartella video&gt;
      </AbsoluteFill>
    );
  }
  const fineParlato = fr(m.parlato.durata);
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <TransitionStage transitions={m.transizioni}>
        <Sequence durationInFrames={fineParlato} layout="none">
          <Parlato m={m} />
        </Sequence>
        {m.broll.map((b, i) => (
          <Sequence key={i} from={fr(b.da)} durationInFrames={fr(b.a) - fr(b.da)}>
            <BRoll file={b.file} offset={b.offset} pushIn={b.push_in} />
          </Sequence>
        ))}
        {m.outro && (
          <Sequence from={fr(m.outro.da)} durationInFrames={fr(m.outro.durata)}>
            <OffthreadVideo src={staticFile(m.outro.file)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          </Sequence>
        )}
      </TransitionStage>
      <TransitionOverlays transitions={m.transizioni} />
      {m.musica && m.musica.punti.length > 1 && (
        <Audio src={staticFile(m.musica.file)} startFrom={fr(m.musica.offset)}
          volume={(f) => interpolate(f, m.musica!.punti.map((p) => fr(p[0])), m.musica!.punti.map((p) => p[1]),
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
      )}
      {m.grafiche && <Grafiche grafiche={m.grafiche.elenco} tema={m.grafiche.tema} />}
      <Sequence durationInFrames={fineParlato} layout="none">
        {m.sottotitoli.stile === "blocchi" && <BlocchiCaptions blocchi={m.sottotitoli.blocchi} aspetto={m.sottotitoli.aspetto} />}
        {m.sottotitoli.stile === "dinamici" && <DinamiciCaptions blocchi={m.sottotitoli.blocchi} aspetto={m.sottotitoli.aspetto} />}
        {m.sottotitoli.stile === "ref2" && <Ref2Captions chunks={m.sottotitoli.chunks} y={m.sottotitoli.y} />}
      </Sequence>
    </AbsoluteFill>
  );
};

export const calcolaMontaggio: CalculateMetadataFunction<{ m: M | null }> = async ({ props }) => ({
  durationInFrames: props.m ? fr(props.m.durata) : 90,
  fps: FPS,
});
