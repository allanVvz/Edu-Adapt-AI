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

## Regra de seguranca didatica

Fração conceitual nao e divisao armada.

Exemplo:

- `1/2`, `metade`, `pizza inteira`, `partes iguais` representam conceito de fração.
- Esses termos nao devem gerar `math_formatting`.
- Uma divisao so deve ser formatada como conta quando a atividade explicita uma operacao, por exemplo `24 / 6`, `24 ÷ 6` ou `24 dividido por 6`.

Essa regra existe para impedir o erro de transformar a atividade "Fração: a metade da pizza" em uma conta `1 ÷ 2`, que nao corresponde ao objetivo pedagogico.

## Validacao educacional obrigatoria

O servico `apps/api/app/services/educational_validation_service.py` roda depois da geracao e depois da formatacao matematica.

Ele verifica:

- cálculo sem relação com objetivo conceitual;
- fração representada como operação;
- pictogramas ambiguos em escolhas de metade/inteira;
- consistencia entre label visivel e resposta correta.

Quando o erro e corrigivel, o servico corrige o `output_data` e registra um check com `severity: fixed`.

Quando houver erro bloqueante, o servico registra `severity: blocker`, marca `validation.approved = false` e a publicacao deve falhar.

## Quando a tool e chamada

A chamada automatica acontece dentro de `normalized_output_data`, em `apps/api/app/services/static_url_service.py`.

Fluxo:

1. Endpoint busca `ActivityAdaptation.output_data`.
2. Endpoint busca a `Activity` relacionada.
3. Endpoint chama `normalized_output_data(output_data, api_base_url, activity=...)`.
4. `normalized_output_data` chama `enhance_math_output_data`.
5. `normalized_output_data` chama `apply_educational_quality_gate`.
6. O resultado ja sai com:
   - URLs estaticas corrigidas.
   - Blocos matematicos em `math_formatting`, quando aplicavel.
   - Correcoes/flags educacionais em `validation.educational_quality`.

## Fluxo de criacao

Novas adaptacoes passam pelo quality gate antes de serem salvas:

- `POST /activities/{activity_id}/adapt`
- `POST /adaptations/{adaptation_id}/reprocess`

Publicacao tambem valida:

- `POST /adaptations/{adaptation_id}/publish`

Se houver `blocker`, a adaptacao volta para `review` e nao e publicada.

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

Nao reconhece como divisao:

- `1/2`;
- `1/4`;
- qualquer fração compacta usada como resposta ou alternativa.

## Persistencia

O bloco `math_formatting` e gerado dinamicamente no retorno da API. Isso preserva os dados originais da adaptacao no banco e permite melhorar o detector sem migrar registros antigos.

Se no futuro for necessario persistir o bloco, o ponto correto e chamar `enhance_math_output_data` antes de salvar novas adaptacoes em `routes/adaptations.py` ou nos seeds.

## Correcao retroativa

Para aplicar a validacao educacional nos registros existentes:

```bash
python -m app.scripts.apply_educational_quality_gate
```

Esse script:

- percorre todas as `ActivityAdaptation`;
- carrega a `Activity` relacionada;
- aplica `apply_educational_quality_gate`;
- salva somente quando o JSON muda.

Use esse script apos qualquer melhoria nas regras de validacao para corrigir dados antigos sem recriar atividades.

## Testes

Cobertura adicionada em `apps/api/tests/test_math_formatting.py`:

- deteccao e formatacao de soma;
- suporte a subtracao, multiplicacao e divisao;
- garantia de que `1/2` nao vira divisao;
- renderizacao PDF com bloco matematico.

Cobertura adicionada em `apps/api/tests/test_educational_validation.py`:

- remocao de calculo indevido em atividade de fração;
- normalizacao de pictogramas de metade/inteira;
- preservacao da resposta correta apos normalizacao.
