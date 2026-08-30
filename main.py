import os
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserMessage(BaseModel):
    message: str
    history: list = []

@app.get("/")
def home():
    return {
        "status": "Servidor do Aquele Abraço Ativo",
        "groq_key_detectada": bool(os.getenv("GROQ_API_KEY")),
        "gemini_key_detectada": bool(os.getenv("GEMINI_API_KEY"))
    }

@app.post("/api/chat")
def chat(payload: UserMessage):
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    system_prompt = (
        "Você é o 'Aquele Abraço', um assistente empático de regulação emocional e acolhimento. "
        "Ouça o usuário com carinho, ajude-o a encontrar o autoperdão, a paz e a resiliência. "
        "Responda de forma profunda, inédita e humana. Nunca repita frases robóticas ou fixas. "
        "Nunca dê diagnósticos médicos nem receitas de remédios."
    )

    # 1. TENTATIVA GROQ (Modelo ativo: llama-3.1-8b-instant)
    if groq_key:
        try:
            messages = [{"role": "system", "content": system_prompt}]
            for msg in payload.history[-6:]:
                role = "user" if msg.get("sender") == "user" else "assistant"
                messages.append({"role": role, "content": msg.get("text", "")})
            messages.append({"role": "user", "content": payload.message})

            url_groq = "https://api.groq.com/openai/v1/chat/completions"
            headers_groq = {
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json"
            }
            data_groq = {
                "model": "llama-3.1-8b-instant",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 300
            }

            res = requests.post(url_groq, headers=headers_groq, json=data_groq, timeout=10)
            if res.status_code == 200:
                bot_reply = res.json()['choices'][0]['message']['content']
                return {"response": bot_reply}
            else:
                print(f"[ERRO GROQ {res.status_code}]: {res.text}")
        except Exception as e:
            print(f"[EXCEÇÃO GROQ]: {e}")

    # 2. TENTATIVA GEMINI (Modelo ativo: gemini-2.0-flash)
    if gemini_key:
        try:
            contents = [
                {"role": "user", "parts": [{"text": f"Instrução: {system_prompt}"}]},
                {"role": "model", "parts": [{"text": "Compreendido."}]}
            ]
            for msg in payload.history[-6:]:
                role = "user" if msg.get("sender") == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg.get("text", "")}]})
            contents.append({"role": "user", "parts": [{"text": payload.message}]})

            url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
            res = requests.post(url_gemini, headers={"Content-Type": "application/json"}, json={"contents": contents}, timeout=10)
            if res.status_code == 200:
                bot_reply = res.json()['candidates'][0]['content']['parts'][0]['text']
                return {"response": bot_reply}
            else:
                print(f"[ERRO GEMINI {res.status_code}]: {res.text}")
        except Exception as e:
            print(f"[EXCEÇÃO GEMINI]: {e}")

    # 3. FALLBACK DE SEGURANÇA
    return {
        "response": "Estou aqui escutando você. As chaves de inteligência em nuvem estão sendo sincronizadas no servidor, mas você pode continuar desabafando."
    }
