import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from legalgraph import cita_revogada, completude, load_grafo  # noqa: E402

G = load_grafo(ROOT / "data" / "resolucao.json")

Q_REQ = "Quais os requisitos para adesao ao Programa Alfa?"
SPANS_REQ = ["cinquenta alunos", "gestor responsavel", "prefeito"]
Q_VALOR = "Qual o valor do repasse por aluno?"


def test_arestas_basicas():
    art3 = G.por_id["art3"]
    art3_ii = G.por_id["art3_ii"]
    assert {f.id for f in G.filhos(art3)} == {"art3_i", "art3_ii"}
    assert G.parent(art3_ii).id == "art3"
    assert {n.id for n in G.remissoes(art3_ii)} == {"art8"}  # "art. 8"
    assert {n.id for n in G.vizinhos(art3_ii)} == {"art3_i", "art5_old"}


def test_flat_incompleto_e_pode_citar_revogada():
    # hierarquia/remissão: flat traz só o caput, sem os incisos nem o art. 8
    assert completude(G.flat(Q_REQ), SPANS_REQ) < 1.0
    # vigência: flat traz a norma revogada (R$ 80)
    cf = G.flat(Q_VALOR)
    assert cita_revogada(G, cf) is True
    assert "80,00" in cf


def test_graph_lite_completa_via_hierarquia_e_remissao():
    cg = G.expand(Q_REQ)
    assert completude(cg, SPANS_REQ) == 1.0


def test_graph_lite_respeita_vigencia():
    cg = G.expand(Q_VALOR)
    assert cita_revogada(G, cg) is False
    assert "100,00" in cg
    assert "80,00" not in cg


def test_graph_lite_nao_atrapalha_auto_suficiente():
    q, spans = "Em que meses ocorre o repasse?", ["marco", "agosto"]
    assert completude(G.flat(q), spans) == 1.0
    assert completude(G.expand(q), spans) == 1.0


def test_agregado():
    consultas = [
        (Q_REQ, SPANS_REQ),
        (Q_VALOR, ["100,00"]),
        ("Em que meses ocorre o repasse?", ["marco", "agosto"]),
    ]
    n = len(consultas)
    flat_c = sum(completude(G.flat(q), s) for q, s in consultas) / n
    graph_c = sum(completude(G.expand(q), s) for q, s in consultas) / n
    flat_rev = sum(cita_revogada(G, G.flat(q)) for q, _ in consultas)
    graph_rev = sum(cita_revogada(G, G.expand(q)) for q, _ in consultas)
    assert graph_c == 1.0 and graph_c > flat_c
    assert flat_rev >= 1 and graph_rev == 0
