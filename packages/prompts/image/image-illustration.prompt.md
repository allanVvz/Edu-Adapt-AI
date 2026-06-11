# Prompt — Geração de Imagens Ilustrativas

## Objetivo
Criar prompts para geração de imagens que apoiem visualmente a atividade adaptada.

## Entrada esperada
```json
{
  "activity": {
    "title": "string",
    "activity_type": "string",
    "expected_answer": "string"
  },
  "profile": {
    "resources_to_avoid": ["string"],
    "preferred_modalities": ["string"]
  }
}
```

## Regras de geração
1. Gere no mínimo 2 opções de imagem.
2. Use estilo minimalista quando `resources_to_avoid` incluir "muitas cores".
3. Fundo sempre branco ou neutro.
4. Elementos grandes e sem poluição visual.
5. Sem texto na imagem.
6. Estilo AAC quando o perfil for "comunicação não verbal".
7. Cada prompt deve descrever apenas um elemento principal.

## Saída JSON obrigatória
```json
{
  "image_options": [
    {
      "id": "img_1",
      "description": "descrição em português do que a imagem deve mostrar",
      "prompt": "english prompt for image generation API"
    }
  ]
}
```

## Exemplo de saída
```json
{
  "image_options": [
    {
      "id": "img_1",
      "description": "Peixe nadando em fundo azul neutro, estilo simples",
      "prompt": "Simple cartoon fish swimming, neutral blue background, minimal style, no text, educational illustration"
    },
    {
      "id": "img_2",
      "description": "Cachorro em fundo branco, estilo pictograma",
      "prompt": "Simple dog pictogram, white background, AAC style, clear outline, no text"
    }
  ]
}
```
