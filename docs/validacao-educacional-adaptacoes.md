# Validacao educacional de adaptacoes

Este documento registra as regras que impedem adaptacoes didaticamente incoerentes de serem criadas, publicadas ou mantidas no banco.

## Incidente corrigido

URL analisada:

`http://localhost:3001/student/activities/e8bee2ff-497f-4c74-81a2-3de7e22f97bd`

Atividade:

- Titulo: `Fração: a metade da pizza`
- Objetivo: reconhecer a metade (`1/2`) de um todo.
- Tipo: multipla escolha/toque.

Problema encontrado:

- A formatacao matematica interpretou `1/2` como `1 ÷ 2`.
- O calculo armado nao correspondia ao objetivo da atividade.
- A alternativa `pizza inteira` estava representada como duas pizzas, o que sugere quantidade 2, nao uma pizza inteira.

Comparativo com a apostila:

- A busca na transcricao `C:\Repositores\Edu Adapt docs\apostila_matematica_transcricao_completa.md` nao encontrou ocorrencias de `pizza`, `metade`, `fração/fracao` ou `inteira`.
- Portanto, esta atividade e do seed TEA legado (`AT-MAT-02`), nao da apostila de matematica transcrita.
- A regra de validacao vale para ambos: apostila e atividades legadas.

## Regra inegociavel

Nem toda atividade de Matematica pede calculo armado.

Use calculo armado apenas quando a tarefa pedir uma operacao:

- soma;
- subtracao;
- multiplicacao;
- divisao.

Nao use calculo armado quando a tarefa for conceitual:

- reconhecer metade;
- identificar fração;
- comparar inteiro e parte;
- reconhecer forma geometrica;
- identificar medida, instrumento, calendario ou relogio sem operacao.

## Tool obrigatoria

Servico:

`apps/api/app/services/educational_validation_service.py`

Funcoes principais:

- `apply_educational_quality_gate(output_data, activity)`
- `educational_blockers(output_data)`

Responsabilidades:

- remover calculo indevido em atividade conceitual;
- normalizar pictogramas ambiguos;
- registrar checks em `validation.educational_quality`;
- impedir publicacao quando houver blocker.

## Onde roda no fluxo

Criacao:

- `POST /activities/{activity_id}/adapt`

Reprocessamento:

- `POST /adaptations/{adaptation_id}/reprocess`

Publicacao:

- `POST /adaptations/{adaptation_id}/publish`

Entrega ao aluno/professor:

- `normalized_output_data(...)`

Retroativo:

- `python -m app.scripts.apply_educational_quality_gate`

## Exemplo correto para pizza

Errado:

- `🍕🍕 Inteira`
- `1 ÷ 2`

Correto:

- `◐ Metade da pizza`
- `● Pizza inteira`
- sem bloco `math_formatting`

## Testes obrigatorios

Arquivos:

- `apps/api/tests/test_math_formatting.py`
- `apps/api/tests/test_educational_validation.py`

Casos cobertos:

- `1/2` nao vira divisao;
- calculo indevido em fração e removido;
- `pizza inteira` nao e representada como duas pizzas;
- resposta correta acompanha a normalizacao dos labels.
