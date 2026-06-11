# Prompt — Adaptação de Texto

## Objetivo
Simplificar e reescrever o enunciado de uma atividade escolar para torná-lo acessível ao perfil pedagógico do aluno.

## Entrada esperada
```json
{
  "activity": {
    "title": "string",
    "statement": "string",
    "question": "string",
    "activity_type": "string"
  },
  "profile": {
    "name": "string",
    "reading_level": "initial | basic | intermediate | advanced",
    "main_difficulties": ["string"],
    "recommended_strategies": ["string"]
  }
}
```

## Regras de geração
1. Use frases curtas (máximo 8 palavras por frase).
2. Use vocabulário cotidiano — evite palavras abstratas.
3. Separe cada instrução em uma linha própria.
4. Use voz ativa ("Observe", "Circule", "Arraste").
5. Se o perfil tiver `reading_level: initial`, use apenas CAIXA ALTA.
6. Preserve o objetivo pedagógico original.
7. Não inclua mais de 3 instruções por bloco.
8. Evite os recursos listados em `profile.resources_to_avoid`.

## Saída JSON obrigatória
```json
{
  "text_adaptations": [
    {
      "version": 1,
      "content": "string com o texto adaptado"
    }
  ]
}
```

## Exemplo de entrada
```json
{
  "activity": {
    "statement": "Classifique os animais em terrestres e aquáticos.",
    "question": "Onde cada animal vive?"
  },
  "profile": {
    "reading_level": "initial",
    "main_difficulties": ["enunciados longos"]
  }
}
```

## Exemplo de saída
```json
{
  "text_adaptations": [
    {
      "version": 1,
      "content": "OBSERVE OS ANIMAIS.\n\nCOLOQUE CADA ANIMAL NO LUGAR CERTO.\n\nONDE ELE VIVE?"
    }
  ]
}
```
