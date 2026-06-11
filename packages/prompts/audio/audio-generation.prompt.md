# Prompt — Geração de Áudio

## Objetivo
Criar roteiros de narração claros e pausados para geração de áudio TTS (Text-to-Speech).

## Entrada esperada
```json
{
  "activity": {
    "statement": "string",
    "question": "string"
  },
  "profile": {
    "autonomy_level": "low | medium | high",
    "main_difficulties": ["string"]
  }
}
```

## Regras de geração
1. Use pausas explícitas com `\n\n` entre blocos.
2. Fale diretamente com o aluno ("Observe", "Agora responda").
3. Se `autonomy_level: low`, use tom calmo e pausado com mais repetições.
4. Repita a instrução principal no final.
5. Máximo de 3 blocos de fala por roteiro.
6. Não inclua caracteres especiais nem formatação markdown.
7. Evite ironia, sarcasmo ou duplo sentido.

## Saída JSON obrigatória
```json
{
  "audio_options": [
    {
      "id": "audio_1",
      "script": "string com o roteiro completo",
      "voice_style": "calmo e pausado | claro e objetivo"
    }
  ]
}
```

## Exemplo de entrada
```json
{
  "activity": {
    "statement": "Observe os animais e associe cada um ao ambiente onde vive.",
    "question": "Onde cada animal vive?"
  },
  "profile": { "autonomy_level": "low" }
}
```

## Exemplo de saída
```json
{
  "audio_options": [
    {
      "id": "audio_1",
      "script": "Preste atenção.\n\nObserve os animais.\n\nAgora coloque cada animal no lugar certo.\n\nOnde cada animal vive?",
      "voice_style": "calmo e pausado"
    }
  ]
}
```
