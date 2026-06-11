# Prompt — Validação de Adaptação

## Objetivo
Avaliar a qualidade pedagógica e acessibilidade de uma adaptação gerada, retornando scores e recomendação de aprovação.

## Entrada esperada
```json
{
  "original_activity": {
    "statement": "string",
    "question": "string",
    "expected_answer": "string"
  },
  "adaptation": {
    "text_adaptations": [],
    "image_options": [],
    "audio_options": [],
    "interaction_options": []
  },
  "profile": {
    "name": "string",
    "main_difficulties": [],
    "recommended_strategies": [],
    "resources_to_avoid": []
  }
}
```

## Critérios de avaliação (1–5)

| Critério | Descrição |
|----------|-----------|
| `clarity_score` | O texto adaptado é claro e compreensível? |
| `accessibility_score` | A adaptação atende às necessidades do perfil? |
| `pedagogical_score` | O objetivo pedagógico original foi preservado? |
| `difficulty_score` | A dificuldade ficou adequada para o perfil? |

## Regras de aprovação
- `approved: true` se `clarity_score >= 3` e `accessibility_score >= 3` e `pedagogical_score >= 4`
- `approved: false` em qualquer outro caso — incluir `rejection_reasons`

## Saída JSON obrigatória
```json
{
  "validation": {
    "clarity_score": 1-5,
    "accessibility_score": 1-5,
    "pedagogical_score": 1-5,
    "difficulty_score": 1-5,
    "approved": true | false,
    "rejection_reasons": [],
    "notes": "string"
  }
}
```

## Motivos de reprovação possíveis
```
audio_ruim, imagem_inadequada, adaptacao_ruim, dificuldade_inadequada,
nao_preserva_objetivo, layout_confuso, atividade_muito_facil,
atividade_muito_dificil, erro_pedagogico, erro_tecnico
```
