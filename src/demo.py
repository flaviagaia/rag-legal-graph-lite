"""Demo: vector flat vs Legal Graph Lite (~1s).

    python src/demo.py
"""

from __future__ import annotations

from pathlib import Path

from legalgraph import cita_revogada, completude, load_grafo

ROOT = Path(__file__).parent.parent

# Cada consulta exercita um sinal estrutural (ou nenhum, no caso de controle).
CONSULTAS = [
    ("Quais os requisitos para adesao ao Programa Alfa?",
     ["cinquenta alunos", "gestor responsavel", "prefeito"], "hierarquia + remissão"),
    ("Qual o valor do repasse por aluno?",
     ["100,00"], "vigência (não citar revogada)"),
    ("Em que meses ocorre o repasse?",
     ["marco", "agosto"], "auto-suficiente (controle)"),
]


def main() -> None:
    g = load_grafo(ROOT / "data" / "resolucao.json")

    print("=" * 80)
    print("Legal Graph Lite: hierarquia + adjacência + remissão + vigência")
    print("=" * 80)

    soma = {"flat": 0.0, "graph": 0.0}
    rev = {"flat": 0, "graph": 0}
    for q, spans, sinal in CONSULTAS:
        cf = g.flat(q)
        cg = g.expand(q)
        soma["flat"] += completude(cf, spans)
        soma["graph"] += completude(cg, spans)
        rev["flat"] += cita_revogada(g, cf)
        rev["graph"] += cita_revogada(g, cg)
        print(f"\nP: {q}   [{sinal}]")
        print(f"   flat        (completude {completude(cf, spans):.0%}): {cf}")
        print(f"   graph-lite  (completude {completude(cg, spans):.0%}): {cg}")

    n = len(CONSULTAS)
    print("\n" + "-" * 80)
    print(f"Completude média:        flat {soma['flat']/n:.0%}   |   "
          f"graph-lite {soma['graph']/n:.0%}")
    print(f"Citações de revogada:    flat {rev['flat']}/{n}      |   "
          f"graph-lite {rev['graph']}/{n}")
    print("(graph-lite filtra revogados e expande pai + vizinhos + remissões)")


if __name__ == "__main__":
    main()
