import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class UserMessage(BaseModel):
    message: str
    history: list = []

@app.get("/")
def home():
    return {"status": "Servidor Aquele Abraço (Groq + Gemini) Operacional!"}

@app.post("/api/chat")
def chat(payload: UserMessage):
    system_instruction = (
        "Você é o 'Aquele Abraço', um assistente empático de regulação emocional e acolhimento. "
        "Ouça o usuário com carinho, ajude-o a encontrar o autoperdão, a paz e a resiliência. "
        "Responda de forma profunda, inédita e humana. Nunca repita frases robóticas ou fixas. "
        "Nunca dê diagnósticos médicos nem receitas de remédios."
    )

    # 1. TENTA PROCESSAR PRIMEIRO NO GROQ (Llama 3 - Ultrarrápido)
    if GROQ_API_KEY:
        try:
            messages = [{"role": "system", "content": system_instruction}]
            for msg in payload.history[-6:]:
                role = "user" if msg.get("sender") == "user" else "assistant"
                messages.append({"role": role, "content": msg.get("text", "")})
            messages.append({"role": "user", "content": payload.message})

            url_groq = "https://api.groq.com/openai/v1/chat/completions"
            headers_groq = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            data_groq = {
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 300
            }

            res = requests.post(url_groq, headers=headers_groq, json=data_groq, timeout=8)
            if res.status_code == 200:
                bot_reply = res.json()['choices'][0]['message']['content']
                return {"response": bot_reply, "engine": "Groq-Llama3"}
        except Exception as e:
            print("Groq instável, ativando fallback do Gemini...", e)

    # 2. FALLBACK SE O GROQ FALHAR -> USA O GOOGLE GEMINI
    if GEMINI_API_KEY:
        try:
            contents = [
                {"role": "user", "parts": [{"text": f"Instrução: {system_instruction}"}]},
                {"role": "model", "parts": [{"text": "Compreendido."}]}
            ]
            for msg in payload.history[-6:]:
                role = "user" if msg.get("sender") == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg.get("text", "")}]})
            contents.append({"role": "user", "parts": [{"text": payload.message}]})

            url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            res = requests.post(url_gemini, headers={"Content-Type": "application/json"}, json={"contents": contents}, timeout=8)
            if res.status_code == 200:
                bot_reply = res.json()['candidates'][0]['content']['parts'][0]['text']
                return {"response": bot_reply, "engine": "Google-Gemini"}
        except Exception as e:
            print("Erro no Gemini também:", e)

    raise HTTPException(status_code=500, detail="Serviços de Inteligência temporariamente indisponíveis.")
