# rag-legal-graph-lite

O capstone: hierarquia + adjacência + remissão + vigência num **grafo leve** em
memória, sem banco de grafos. A síntese da mini-série sobre estrutura no RAG jurídico.

> **Em uma frase:** em vez de um banco de grafos, um grafo leve (dicionários) sobre os
> dispositivos da norma; o recuperador filtra os revogados e expande o melhor trecho
> válido com o pai, os vizinhos e os dispositivos citados, reconstruindo a unidade de
> sentido que a lei deixou distribuída.

> *Legal Graph Lite: a small in-memory graph over the law's provisions. Each node
> knows its parent (hierarchy), its position (adjacency), its references (cross-ref)
> and its validity (versioning). The retriever drops repealed nodes and expands the
> best valid hit with parent + neighbors + cited articles. No graph database, no GPU.*

---

## A ideia

Quatro repos anteriores trataram um sinal estrutural cada:

- **Hierarquia** (`graphrag-hierarquia-normativa`): o inciso fora do caput engana; recupere o pai.
- **Adjacência** (`rag-chunk-adjacency`): a segmentação corta o sentido; traga os vizinhos.
- **Cross-reference** (`rag-cross-reference`): a norma remete a outra; siga o link.
- **Vigência** (`rag-controle-vigencia`): a versão antiga não some; não cite a revogada.

Cada um, isolado, é uma correção barata. O **Legal Graph Lite** junta os quatro num
grafo só: cada dispositivo é um nó que conhece o `parent` (hierarquia), a `ordem`
(adjacência), as remissões no texto (cross-reference) e a `vigência`. É o ponto de
melhor custo-benefício antes de partir para um banco de grafos dedicado.

## Como funciona (o técnico)

```
flat(query)   = melhor match por similaridade (ignora estrutura e vigência)

expand(query):
    validos = [n por similaridade se n.vigente]      # 1) filtra revogados
    top     = validos[0]
    sel = {top} ∪ filhos(top) ∪ {pai(top)} ∪ irmãos  # 2) hierarquia
              ∪ vizinhos(top)                          #    adjacência
              ∪ remissões(top e dos nós já trazidos)   #    cross-reference
    retorna textos de sel, só vigentes, ordenados pelo documento
```

O grafo é montado de uma estrutura simples (cada nó tem `parent`, `ordem`,
`vigente`/`inicio`/`fim`/`revogado_por`; as remissões saem do texto por regex). Tudo
em memória, com dicionários. Complexidade: a busca top-1 mais uma expansão local de
poucos nós (vizinhança no grafo).

## Resultado (determinístico, offline)

Resolução fictícia do Programa Alfa, com caput + incisos, um par revogada/vigente,
uma remissão (art. 3º II → art. 8º) e um artigo auto-suficiente (controle).

| Consulta                                   | Sinal               | flat | graph-lite |
| ------------------------------------------ | ------------------- | ---- | ---------- |
| Requisitos para adesão (caput + art. 8º)   | hierarquia + remissão | 0%   | **100%**   |
| Valor do repasse por aluno                 | vigência            | 0%   | **100%**   |
| Meses do repasse (artigo auto-suficiente)  | controle            | 100% | 100%       |
| **Completude média**                       |                     | **33%** | **100%** |
| **Citações de norma revogada**             |                     | **1/3** | **0/3**  |

O caso de controle (artigo que já se basta) fica 100% nos dois: o grafo expande, mas
**não remove** o que já estava certo. E o flat cita a norma revogada (R$ 80) onde o
graph-lite traz a vigente (R$ 100).

Rode você mesmo:

```bash
pip install -r requirements.txt
python src/demo.py
python -m pytest -q
```

## Como explicar em 30 segundos

"A lei não é uma lista de trechos soltos; é um grafo: artigo e inciso, vizinhos,
remissões, versões. Eu monto esse grafo leve na memória, jogo fora o que está
revogado e, em vez de devolver só o trecho que casou, devolvo ele com o pai, os
vizinhos e os artigos que ele cita. A resposta para de sair pela metade, e não
preciso de banco de grafos."

## Quando NÃO usar

O grafo lite resolve a maior parte das dores de estrutura com custo quase zero. Ele
**não** substitui um banco de grafos quando você precisa de escala (milhões de nós),
consultas Cypher complexas ou extração de comunidades estilo GraphRAG. A regra: comece
lite; só pague o banco de grafos quando a necessidade aparecer. Esse contraste (lite em
memória vs Neo4j vs GraphRAG completo) é o tema dos posts seguintes da série.

## Limitações honestas

- Corpus pequeno e fictício, escolhido para cada sinal aparecer com clareza.
- O parser de remissões é regex simples (`art. N`); remissões reais ("§ 2º do art.
  7º", "Lei nº X", "artigo anterior") exigem um parser dedicado (ver `rag-ingestao-legislacao`).
- A expansão é de 1 nível por relação; em produção controla-se profundidade e número
  de nós trazidos para não inflar o contexto.
- Completude usa presença de spans (substring), proxy de "a informação está no
  contexto"; não mede a geração.

## Referências científicas (crédito aos autores)

- **Lewis et al. (2020).** *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* NeurIPS.
- **Edge et al. (2024).** *From Local to Global: A Graph RAG Approach to Query-Focused Summarization.* arXiv:2404.16130.
- **Gao et al. (2024).** *Retrieval-Augmented Generation for Large Language Models: A Survey.* arXiv:2312.10997.
- **Yan et al. (2024).** *Corrective Retrieval Augmented Generation (CRAG).* arXiv:2401.15884. Filtrar o recuperado (aqui, por vigência).
- Corpus fictício; nenhuma relação com dados reais.

Bibliografia completa do portfólio em `REFERENCIAS.md`.

---

Part of my LinkedIn series on efficient RAG → [Flávia Gaia](https://www.linkedin.com/in/flavia-gaia/)
