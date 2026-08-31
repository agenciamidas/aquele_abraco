import os
import re
import json
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

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
    media: Optional[str] = None
    mimeType: Optional[str] = None

def get_working_groq_models(groq_key: str):
    if not groq_key: return []
    try:
        url = "https://api.groq.com/openai/v1/models"
        headers = {"Authorization": f"Bearer {groq_key}"}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return [m["id"] for m in res.json().get("data", []) if "id" in m]
    except Exception as e:
        print(f"[GROQ ERRO]: {e}")
    return ["llama-3.3-70b-versatile"]

def get_working_gemini_models(gemini_key: str):
    if not gemini_key: return []
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            models = []
            for m in res.json().get("models", []):
                if "generateContent" in m.get("supportedGenerationMethods", []):
                    models.append(m["name"].replace("models/", ""))
            return models
    except Exception as e:
        print(f"[GEMINI ERRO]: {e}")
    return ["gemini-1.5-flash", "gemini-1.5-pro"]

@app.get("/")
def home():
    return {"status": "Servidor do Aquele Abraço Ativo (Modo JSON Estrito)"}

@app.post("/api/chat")
def chat(payload: UserMessage):
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    has_media = bool(payload.media and payload.mimeType)

    # INSTRUÇÃO ESTRITA: OBRIGA A IA A RESPONDER APENAS EM JSON
    system_prompt = (
        "Você é o assistente empático 'Aquele Abraço'. "
        "REGRAS DE FORMATAÇÃO (CRÍTICAS): "
        "Você está PROIBIDO de gerar texto livre, rascunhos ou pensamentos. "
        "Você DEVE retornar APENAS um objeto JSON perfeitamente válido com DUAS chaves: "
        "1) 'portugues': (String) A sua resposta acolhedora, conversacional e direta em português nativo. Traduza e responda ao que o usuário disser/sinalizar. "
        "2) 'detected_libras': (Booleano) Use true SE o usuário enviou um vídeo se comunicando em língua de sinais ou gestos. Caso contrário, use false. "
        "Exemplo de saída esperada: {\"portugues\": \"Bom dia! Como está seu coração hoje?\", \"detected_libras\": true}"
    )

    # Função para limpar e extrair o JSON da resposta da IA
    def extract_json_response(raw_text):
        cleaned = re.sub(r'```json\n?|```', '', raw_text).strip()
        try:
            parsed = json.loads(cleaned)
            return {
                "response": parsed.get("portugues", "Estou aqui com você. Pode desabafar."),
                "detected_libras": parsed.get("detected_libras", False)
            }
        except json.JSONDecodeError:
            # Fallback de segurança extrema caso a IA falhe no formato
            clean_fallback = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
            return {"response": clean_fallback, "detected_libras": False}

    # 1. ROTEAMENTO DE TEXTO PURO VIA GROQ
    if groq_key and not has_media:
        groq_models = get_working_groq_models(groq_key)
        messages_groq = [{"role": "system", "content": system_prompt}]
        for msg in payload.history[-6:]:
            role = "user" if msg.get("sender") == "user" else "assistant"
            messages_groq.append({"role": role, "content": msg.get("text", "")})
        messages_groq.append({"role": "user", "content": payload.message})

        for model_name in groq_models:
            try:
                res = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                    json={"model": model_name, "messages": messages_groq, "temperature": 0.5, "response_format": {"type": "json_object"}},
                    timeout=12
                )
                if res.status_code == 200:
                    raw_reply = res.json()['choices'][0]['message']['content']
                    return extract_json_response(raw_reply)
            except Exception as e:
                print(f"[GROQ ERROR {model_name}]: {e}")

    # 2. ROTEAMENTO MULTIMODAL VIA GEMINI (Lê Vídeo e Imagem)
    if gemini_key:
        gemini_models = get_working_gemini_models(gemini_key)
        if "gemini-1.5-flash" not in gemini_models: gemini_models.insert(0, "gemini-1.5-flash")

        contents = [{"role": "user", "parts": [{"text": system_prompt}]}]
        for msg in payload.history[-6:]:
            role = "user" if msg.get("sender") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.get("text", "")}]})
        
        current_parts = []
        if has_media:
            raw_b64 = payload.media.split(",")[1] if "," in payload.media else payload.media
            current_parts.append({"inlineData": {"mimeType": payload.mimeType, "data": raw_b64}})
        current_parts.append({"text": payload.message})
        contents.append({"role": "user", "parts": current_parts})

        for g_model in gemini_models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{g_model}:generateContent?key={gemini_key}"
                res = requests.post(url, headers={"Content-Type": "application/json"}, json={"contents": contents}, timeout=25)
                if res.status_code == 200:
                    raw_reply = res.json()['candidates'][0]['content']['parts'][0]['text']
                    return extract_json_response(raw_reply)
            except Exception as e:
                print(f"[GEMINI ERROR {g_model}]: {e}")

    return {"response": "Estou aqui com você.", "detected_libras": False}
