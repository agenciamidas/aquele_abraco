import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI()

# Libera o acesso para o aplicativo do celular se conectar
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class UserMessage(BaseModel):
    message: str
    history: list = []

@app.get("/")
def home():
    return {"status": "Servidor do Aquele Abraço em Execução!"}

@app.post("/api/chat")
def chat(payload: UserMessage):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Chave GEMINI_API_KEY não encontrada no servidor.")

    # Diretriz e RAG do Agente Aquele Abraço
    system_instruction = (
        "Você é o 'Aquele Abraço', um assistente empático de regulação emocional e acolhimento. "
        "Ouça o usuário com carinho, ajude-o a encontrar o autoperdão, a paz e a resiliência. "
        "Responda de forma profunda, inédita e humana. Nunca repita frases robóticas ou fixas. "
        "Nunca dê diagnósticos médicos nem receitas de remédios."
    )

    # Constrói o histórico da conversa
    contents = []
    # Instrução do sistema como primeira mensagem do modelo
    contents.append({"role": "user", "parts": [{"text": f"Instruções do Sistema: {system_instruction}"}]})
    contents.append({"role": "model", "parts": [{"text": "Entendido. Estou pronto para acolher o usuário com empatia e profundidade."}]})

    for msg in payload.history[-6:]:
        role = "user" if msg.get("sender") == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg.get("text", "")}]})

    contents.append({"role": "user", "parts": [{"text": payload.message}]})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {"Content-Type": "application/json"}
    data = {"contents": contents}

    try:
        response = requests.post(url, headers=headers, json=data)
        res_json = response.json()
        bot_reply = res_json['candidates'][0]['content']['parts'][0]['text']
        return {"response": bot_reply}
    except Exception as e:
        print("Erro no Gemini:", e)
        raise HTTPException(status_code=500, detail="Erro ao processar no Gemini.")