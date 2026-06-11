# Prompt — Interação Arrastar e Soltar

## Objetivo
Gerar a estrutura de interação digital para atividades de arrastar e soltar (drag and drop) ou associação.

## Entrada esperada
```json
{
  "activity": {
    "expected_answer": "string",
    "activity_type": "association | drag_drop"
  },
  "profile": {
    "main_difficulties": ["string"]
  }
}
```

## Regras de geração
1. Máximo de 6 itens arrastáveis.
2. Máximo de 3 zonas de destino.
3. Feedback imediato por item (correto/incorreto).
4. Instrução principal em CAIXA ALTA.
5. Se `main_difficulties` incluir "atividades com muitas etapas", reduza para 3 itens.
6. Inclua mensagens de feedback positivo e de encorajamento.

## Saída JSON obrigatória
```json
{
  "interaction_options": [
    {
      "type": "drag_and_drop",
      "instructions": "string em CAIXA ALTA",
      "items": ["string"],
      "zones": ["string"],
      "feedback_correct": "string",
      "feedback_incorrect": "string"
    }
  ]
}
```

## Exemplo de saída
```json
{
  "interaction_options": [
    {
      "type": "drag_and_drop",
      "instructions": "ARRASTE CADA ANIMAL PARA O LUGAR ONDE ELE VIVE.",
      "items": ["Peixe", "Golfinho", "Cachorro", "Gato"],
      "zones": ["Água", "Terra"],
      "feedback_correct": "Muito bem! Você acertou!",
      "feedback_incorrect": "Tente novamente. Você consegue!"
    }
  ]
}
```
