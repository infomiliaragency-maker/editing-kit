import "./index.css";
import { Composition } from "remotion";
import { Montaggio, calcolaMontaggio } from "./montaggio/Montaggio";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Modello generico: props {m: montaggio.json} passate da _TOOLS/remotion.py */}
      <Composition
        id="Montaggio"
        component={Montaggio}
        calculateMetadata={calcolaMontaggio}
        durationInFrames={90}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{ m: null }}
      />
    </>
  );
};
