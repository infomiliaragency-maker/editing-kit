# -*- coding: utf-8 -*-
"""Chiavi delle API usate dagli strumenti.

Si cercano in quest'ordine: variabile d'ambiente, file .env nella cartella del kit (una riga NOME=valore),
configurazione del server MCP fal-ai in ~/.claude/settings.json. Non si chiedono mai in chat.

  FAL_KEY         fal.ai: trascrizioni Scribe, b-roll, musica, voiceover su fal
  GEMINI_API_KEY  Google AI Studio: solo per il voiceover con il motore gemini-38
"""
import json, os, sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def leggi(nome):
    if os.environ.get(nome):
        return os.environ[nome]
    env = os.path.join(KIT, ".env")
    if os.path.exists(env):
        for riga in open(env, encoding="utf-8"):
            riga = riga.strip()
            if riga.startswith(nome + "="):
                v = riga.split("=", 1)[1].strip().strip('"').strip("'")
                if v:
                    return v
    if nome == "FAL_KEY":
        try:
            return json.load(open(os.path.expanduser("~/.claude/settings.json")))["mcpServers"]["fal-ai"]["env"]["FAL_KEY"]
        except (OSError, KeyError, ValueError):
            pass
    sys.exit(f"manca {nome}: va scritta nel file .env della cartella del kit ({env}), vedi INSTALLA.md")


def fal():
    return leggi("FAL_KEY")


def gemini():
    return leggi("GEMINI_API_KEY")
