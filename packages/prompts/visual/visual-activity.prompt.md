# Prompt — Modalidade Visual

## Objetivo
Gerar a estrutura de layout visual da atividade para exibição em cartões, colunas ou pictogramas.

## Entrada esperada
```json
{
  "activity": {
    "title": "string",
    "statement": "string",
    "activity_type": "association | drag_drop | multiple_choice"
  },
  "profile": {
    "preferred_modalities": ["string"]
  }
}
```

## Regras de geração
1. Use layout de duas colunas para atividades de associação.
2. Use cartões individuais para múltipla escolha.
3. Inclua versão de impressão A4.
4. Instruções em CAIXA ALTA para perfis com `reading_level: initial`.
5. Espaçamento generoso entre elementos.
6. No máximo 4 elementos por linha.

## Saída JSON obrigatória
```json
{
  "visual_modality": {
    "type": "card_columns | cards | multiple_choice",
    "title": "string",
    "instructions": "string",
    "columns": [{"label": "string", "items": []}],
    "print_version": {
      "format": "A4",
      "layout": "two_columns | single_column",
      "font_size": "large",
      "high_contrast": true,
      "answer_space": true
    }
  }
}
```
