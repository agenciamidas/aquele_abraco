import os
import re
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

def clean_response(text: str) -> str:
    """Remove as tags <think>...</think> dos modelos de raciocínio."""
    if not text:
        return ""
    # Remove qualquer bloco entre <think> e </think>
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned.strip()

def get_working_groq_models(groq_key: str):
    if not groq_key:
        return []
    try:
        url = "https://api.groq.com/openai/v1/models"
        headers = {"Authorization": f"Bearer {groq_key}"}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            models = [m["id"] for m in data.get("data", []) if "id" in m]
            if models:
                return models
    except Exception as e:
        print(f"[DISCOVERY GROQ ERRO]: {e}")
    return ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

def get_working_gemini_models(gemini_key: str):
    if not gemini_key:
        return []
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            models = []
            for m in data.get("models", []):
                methods = m.get("supportedGenerationMethods", [])
                if "generateContent" in methods:
                    name = m["name"].replace("models/", "")
                    models.append(name)
            if models:
                return models
    except Exception as e:
        print(f"[DISCOVERY GEMINI ERRO]: {e}")
    return ["gemini-3.6-flash"]

@app.get("/")
def home():
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    return {
        "status": "Servidor do Aquele Abraço Ativo",
        "groq_key_detectada": bool(groq_key),
        "gemini_key_detectada": bool(gemini_key),
        "groq_modelos_disponiveis": get_working_groq_models(groq_key),
        "gemini_modelos_disponiveis": get_working_gemini_models(gemini_key)
    }

@app.post("/api/chat")
def chat(payload: UserMessage):
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    system_prompt = (
        "Você é o 'Aquele Abraço', um assistente empático de regulação emocional e acolhimento. "
        "Ouça o usuário com carinho, ajude-o a encontrar o autoperdão, a paz e a resiliência. "
        "Responda de forma profunda, inédita e humana em português. Nunca repita frases robóticas ou fixas. "
        "Nunca exiba etapas de raciocínio técnico nem tags de sistema. "
        "Nunca dê diagnósticos médicos nem receitas de remédios."
    )

    # 1. TENTATIVA GROQ
    if groq_key:
        groq_models = get_working_groq_models(groq_key)
        messages_groq = [{"role": "system", "content": system_prompt}]
        for msg in payload.history[-6:]:
            role = "user" if msg.get("sender") == "user" else "assistant"
            messages_groq.append({"role": role, "content": msg.get("text", "")})
        messages_groq.append({"role": "user", "content": payload.message})

        url_groq = "https://api.groq.com/openai/v1/chat/completions"
        headers_groq = {
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json"
        }

        for model_name in groq_models:
            try:
                data_groq = {
                    "model": model_name,
                    "messages": messages_groq,
                    "temperature": 0.7,
                    "max_tokens": 400
                }
                res = requests.post(url_groq, headers=headers_groq, json=data_groq, timeout=12)
                if res.status_code == 200:
                    raw_reply = res.json()['choices'][0]['message']['content']
                    final_reply = clean_response(raw_reply)
                    if final_reply:
                        return {"response": final_reply}
                else:
                    print(f"[ERRO GROQ {model_name} - {res.status_code}]: {res.text}")
            except Exception as e:
                print(f"[EXCEÇÃO GROQ {model_name}]: {e}")

    # 2. TENTATIVA GEMINI
    if gemini_key:
        gemini_models = get_working_gemini_models(gemini_key)
        if "gemini-3.6-flash" not in gemini_models:
            gemini_models.insert(0, "gemini-3.6-flash")

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
                res = requests.post(url_gemini, headers={"Content-Type": "application/json"}, json={"contents": contents}, timeout=15)
                if res.status_code == 200:
                    raw_reply = res.json()['candidates'][0]['content']['parts'][0]['text']
                    final_reply = clean_response(raw_reply)
                    if final_reply:
                        return {"response": final_reply}
                else:
                    print(f"[ERRO GEMINI {g_model} - {res.status_code}]: {res.text}")
            except Exception as e:
                print(f"[EXCEÇÃO GEMINI {g_model}]: {e}")

    return {
        "response": "Estou aqui com você. Pode continuar desabafando no seu tempo."
    }
