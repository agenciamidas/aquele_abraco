// cbtData.js
export const cbtDatabase = {
  "inicio": {
    "text": "Estou aqui com você. Como seu corpo ou sua mente estão se sentindo neste momento?",
    "options": [
      { "label": "🫀 Coração acelerado / Falta de ar", "target": "crise_fisica" },
      { "label": "🤯 Pensamentos acelerados / Barulho demais", "target": "sobrecarga_sensorial" },
      { "label": "🕳️ Tristeza profunda / Sensação de vazio", "target": "acolhimento_emocional" },
      { "label": "🎨 Quero apenas me distrair sem falar", "target": "redirecionar_arteterapia" }
    ]
  },
  "crise_fisica": {
    "text": "Sua respiração é a sua âncora. O seu corpo está reagindo a um alarme falso de perigo, mas você está em segurança agora.\n\nSiga o ritmo de respiração guiada abaixo:",
    "action": "TRIGGER_BREATHING_TOOL",
    "options": [
      { "label": "🎧 Ligar som para acalmar o coração", "target": "redirecionar_farmacia" },
      { "label": "Voltar ao início", "target": "inicio" }
    ]
  },
  "sobrecarga_sensorial": {
    "text": "Quando o mundo externo fica barulhento demais, precisamos diminuir a entrada de estímulos.\n\nTente fechar os olhos ou focar em um único ponto fixo.",
    "options": [
      { "label": "🔊 Ativar Ruído Rosa (Isolamento Sonoro)", "target": "redirecionar_farmacia" },
      { "label": "Voltar ao início", "target": "inicio" }
    ]
  },
  "acolhimento_emocional": {
    "text": "Você não precisa resolver tudo hoje ou agora. Permita-se apenas respirar e existir neste minuto.",
    "options": [
      { "label": "Escutar frequência 432Hz", "target": "redirecionar_farmacia" },
      { "label": "Desenhar na tela", "target": "redirecionar_arteterapia" },
      { "label": "Voltar", "target": "inicio" }
    ]
  },
  "redirecionar_farmacia": {
    "text": "Redirecionando para a Farmácia Acústica...",
    "action": "OPEN_AUDIO_PHARMACY"
  },
  "redirecionar_arteterapia": {
    "text": "Abrindo tela de desenho livre...",
    "action": "OPEN_ART_THERAPY"
  }
};
