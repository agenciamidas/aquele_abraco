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

    # 1. TENTATIVA EM LOOP NO GROQ (Varre os modelos ativos até obter resposta)
    if groq_key:
        groq_models = [
            "llama-3.1-8b-instant",
            "llama-3.3-70b-versatile",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
        
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

        for model_name in groq_models:
            try:
                data_groq = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 300
                }
                res = requests.post(url_groq, headers=headers_groq, json=data_groq, timeout=12)
                if res.status_code == 200:
                    bot_reply = res.json()['choices'][0]['message']['content']
                    return {"response": bot_reply}
                else:
                    print(f"[ERRO GROQ {model_name} - {res.status_code}]: {res.text}")
            except Exception as e:
                print(f"[EXCEÇÃO GROQ {model_name}]: {e}")

    # 2. TENTATIVA EM LOOP NO GEMINI (Timeout estendido para 20s)
    if gemini_key:
        gemini_models = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-2.0-flash"
        ]

        contents = [
            {"role": "user", "parts": [{"text": f"Instrução: {system_prompt}"}]},
            {"role": "model", "parts": [{"text": "Compreendido."}]}
        ]
        for msg in payload.history[-6:]:
            role = "user" if msg.get("sender") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.get("text", "")}]})
        contents.append({"role": "user", "parts": [{"text": payload.message}]})

        for g_model in gemini_models:
            try:
                url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/{g_model}:generateContent?key={gemini_key}"
                res = requests.post(url_gemini, headers={"Content-Type": "application/json"}, json={"contents": contents}, timeout=20)
                if res.status_code == 200:
                    bot_reply = res.json()['candidates'][0]['content']['parts'][0]['text']
                    return {"response": bot_reply}
                else:
                    print(f"[ERRO GEMINI {g_model} - {res.status_code}]: {res.text}")
            except Exception as e:
                print(f"[EXCEÇÃO GEMINI {g_model}]: {e}")

    # 3. FALLBACK DE SEGURANÇA
    return {
        "response": "Estou aqui escutando você. As chaves de inteligência em nuvem estão sendo sincronizadas no servidor, mas você pode continuar desabafando."
    }
