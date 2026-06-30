# Memoria do Projeto

## Contos e textos de apoio

- O sistema agora possui a entidade `Story`, usada para contos e textos de apoio reutilizaveis.
- `Activity.story_id` vincula uma atividade a no maximo um conto/texto de apoio.
- Um mesmo conto pode ser reutilizado por varias atividades.
- Na tela do aluno, o conto aparece embutido antes da atividade, sempre visivel, sem modal.
- O audio do conto usa `Story.audio_options`; se houver `audio_url`, a UI toca o MP3. Se nao houver, usa leitura do navegador como fallback.
- O endpoint `POST /stories/{story_id}/generate-audio` gera MP3 para contos usando a chave OpenAI do professor.

## PDF

- O PDF individual inclui o conto/texto de apoio antes da atividade vinculada.
- O export geral agrupa atividades pelo mesmo conto/texto:
  - primeiro vem o bloco `BLOCO DE CONTO`;
  - depois, as atividades vinculadas ao bloco;
  - atividades sem conto ficam em um bloco separado: `ATIVIDADES SEM CONTO`.
- O renderer converte instrucoes digitais para acoes de papel quando necessario, por exemplo arrastar vira recortar/colar.
- Pictogramas em emoji sao rasterizados para PNG para evitar falhas de fonte no PDF.

## Vinculos seed atuais

- `O Coelho e a Chuva`
  - `Personagens do conto: O Coelho e a Chuva`
  - `Sequencia de acontecimentos: O Coelho e a Chuva`
- `A manha da Ana`
  - `Ordenar a historia da Ana`
- `A horta da escola`
  - `Interpretar um texto curto`
- `Carta de Carlos para Ana`
  - `Carta pessoal: remetente e destinatario`
- `A anedota do detetive`
  - `Anedota: texto curto com humor`

## Cuidados

- Nao vincular atividades conceituais puras ao conto apenas por compartilharem exemplos, como pontuacao, ortografia ou gramatica.
- `Pontuacao: ponto final e exclamacao` nao pertence ao conto `O Coelho e a Chuva`.
- Em atividades `seq`, preservar `correct_answer` declarado no seed; so gerar gabarito pela ordem dos itens quando nao houver gabarito explicito.
