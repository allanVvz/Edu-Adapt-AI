# Fluxo de formatacao de matematica

Este documento descreve como as atividades de Matematica ganham blocos de calculo legiveis, centralizados e com numeros grandes.

## Objetivo

Atividades de soma, subtracao, multiplicacao e divisao precisam aparecer em formato visual de conta armada, tanto na tela do aluno quanto no PDF. A formatacao nao deve depender de cada seed ou de cada geracao de IA escrever HTML ou layout manualmente.

## Ponto central do fluxo

O servico central e `apps/api/app/services/math_formatting_service.py`.

Ele recebe:

- `output_data`: JSON da adaptacao.
- `activity`: metadados da atividade, como disciplina, titulo, enunciado, pergunta e resposta esperada.

Ele devolve o mesmo `output_data`, acrescido de `math_formatting` quando detectar uma conta.

## Quando a tool e chamada

A chamada automatica acontece dentro de `normalized_output_data`, em `apps/api/app/services/static_url_service.py`.

Fluxo:

1. Endpoint busca `ActivityAdaptation.output_data`.
2. Endpoint busca a `Activity` relacionada.
3. Endpoint chama `normalized_output_data(output_data, api_base_url, activity=...)`.
4. `normalized_output_data` chama `enhance_math_output_data`.
5. O resultado ja sai com:
   - URLs estaticas corrigidas.
   - Blocos matematicos em `math_formatting`, quando aplicavel.

## Endpoints cobertos

Aluno:

- `GET /student/activities/{adaptation_id}`
- `GET /student/activities/{adaptation_id}/pdf`
- `GET /student/activities/export-all-pdf`

Professor/admin:

- `GET /adaptations/{adaptation_id}`
- `GET /adaptations/{adaptation_id}/pdf`

## Contrato do JSON

Exemplo gerado automaticamente:

```json
{
  "math_formatting": {
    "version": 1,
    "source": "auto_math_formatting",
    "layout": "centered_large_numbers",
    "blocks": [
      {
        "type": "addition",
        "label": "Soma",
        "symbol": "+",
        "operands": [54, 35],
        "result": "89",
        "rows": [
          { "kind": "operand", "operator": "", "value": " 54" },
          { "kind": "operand", "operator": "+", "value": "35" },
          { "kind": "line", "operator": "", "value": "---" },
          { "kind": "result", "operator": "", "value": " 89" }
        ],
        "steps": [
          "Some 54 com 35.",
          "Resultado: 89."
        ]
      }
    ]
  }
}
```

## Renderizacao

Tela do aluno:

- Arquivo: `apps/web/app/(student)/student/activities/[id]/page.tsx`
- Componente: `MathFormattingPanel`
- Layout: bloco centralizado, fonte monoespacada, numeros grandes e linha de resultado.

PDF:

- Arquivo: `apps/api/app/services/pdf_service.py`
- Metodo: `_draw_math_formatting`
- Layout: tabela centralizada, fonte `Courier-Bold`, linha horizontal e passos curtos.

## Operacoes suportadas

O detector reconhece:

- Soma: `54 + 35`, `54 mais 35`, problemas com `ganhou`, `recebeu`, `comprou`.
- Subtracao: `66 - 10`, `66 menos 10`, problemas com `deu`, `gastou`, `perdeu`, `tirou`.
- Multiplicacao: `12 x 8`, `12 * 8`, `12 vezes 8`.
- Divisao: `24 / 6`, `24 ÷ 6`, `24 dividido por 6`.

## Persistencia

O bloco `math_formatting` e gerado dinamicamente no retorno da API. Isso preserva os dados originais da adaptacao no banco e permite melhorar o detector sem migrar registros antigos.

Se no futuro for necessario persistir o bloco, o ponto correto e chamar `enhance_math_output_data` antes de salvar novas adaptacoes em `routes/adaptations.py` ou nos seeds.

## Testes

Cobertura adicionada em `apps/api/tests/test_math_formatting.py`:

- deteccao e formatacao de soma;
- suporte a subtracao, multiplicacao e divisao;
- renderizacao PDF com bloco matematico.
