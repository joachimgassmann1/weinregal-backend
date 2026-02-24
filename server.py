#!/usr/bin/env python3
"""
Weinregal Backend – GPT-4 Vision Weinetikett-Analyse
Für Render.com Deployment
"""
import os, json, base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app, origins="*")

# API-Key aus Umgebungsvariable (Render Secret)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
client = OpenAI(api_key=OPENAI_API_KEY, base_url="https://api.openai.com/v1")

SYSTEM_PROMPT = """Du bist ein Weinexperte und analysierst Fotos von Weinetiketten.
Antworte AUSSCHLIESSLICH mit einem validen JSON-Objekt – kein Markdown, kein Text davor oder danach.

Extrahiere folgende Informationen aus dem Weinetikett:

{
  "name": "Vollständiger Weinname",
  "producer": "Produzent / Weingut",
  "vintage": 2019,
  "region": "Weinregion (z.B. Bordeaux, Toskana)",
  "country": "Land (z.B. Frankreich, Italien, Deutschland)",
  "type": "red",
  "ripeness": "peak",
  "grape": "Rebsorte(n) falls erkennbar",
  "alcohol": "Alkoholgehalt falls erkennbar (z.B. 13.5%)",
  "description": "2-3 Sätze über diesen Wein: Charakter, Aromen, Stil",
  "food_pairing": "Passende Speisen",
  "serving_temp": "Empfohlene Trinktemperatur (z.B. 16-18°C)",
  "aging_potential": "Lagerpotenzial (z.B. 5-10 Jahre)",
  "estimated_price": 0,
  "confidence": 0.95
}

Regeln:
- vintage: Jahrgang als Zahl, null wenn nicht erkennbar
- type: Nur "red", "white", "rose" oder "sparkling"
- ripeness: "young" wenn < 3 Jahre alt, "peak" wenn 3-10 Jahre, "mature" wenn > 10 Jahre
- estimated_price: Geschätzter Marktpreis in EUR (0 wenn unbekannt)
- confidence: Wie sicher du dir bist (0.0 - 1.0)
- Alle Texte auf DEUTSCH
- Falls kein Weinetikett erkennbar: setze "name" auf "Unbekannter Wein" und confidence auf 0.1
"""

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": "1.0"})

@app.route("/analyze", methods=["POST"])
def analyze_wine():
    try:
        if not OPENAI_API_KEY:
            return jsonify({"error": "OPENAI_API_KEY nicht gesetzt"}), 500

        data = request.get_json()
        if not data or "image" not in data:
            return jsonify({"error": "Kein Bild übermittelt"}), 400

        image_data = data["image"]
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}",
                                "detail": "high"
                            }
                        },
                        {
                            "type": "text",
                            "text": "Analysiere dieses Weinetikett und gib alle Informationen als JSON zurück."
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.2
        )

        raw = response.choices[0].message.content.strip()

        # Markdown-Blöcke entfernen falls vorhanden
        if "```" in raw:
            parts = raw.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("{"):
                    raw = part
                    break

        wine_data = json.loads(raw)

        # Defaults setzen
        defaults = {
            "name": "Unbekannter Wein", "producer": "", "vintage": None,
            "region": "", "country": "", "type": "red", "ripeness": "peak",
            "grape": "", "alcohol": "", "description": "", "food_pairing": "",
            "serving_temp": "", "aging_potential": "", "estimated_price": 0, "confidence": 0.5
        }
        for k, v in defaults.items():
            wine_data.setdefault(k, v)

        if wine_data["type"] not in ["red","white","rose","sparkling"]:
            wine_data["type"] = "red"
        if wine_data["ripeness"] not in ["peak","young","mature"]:
            wine_data["ripeness"] = "peak"

        return jsonify({"success": True, "wine": wine_data})

    except json.JSONDecodeError as e:
        return jsonify({"error": f"JSON-Parse-Fehler: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)
