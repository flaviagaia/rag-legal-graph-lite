"""Legal Graph Lite: hierarquia + adjacência + remissão + vigência num grafo leve.

O capstone da mini-série sobre estrutura no RAG jurídico. Em vez de um banco de
grafos, um grafo leve em memória (dicionários) sobre os dispositivos da norma. Cada
nó conhece:

- o PAI (hierarquia: inciso -> artigo)            -> graphrag-hierarquia-normativa
- a ORDEM no documento (adjacência: vizinhos)     -> rag-chunk-adjacency
- as REMISSÕES no texto ("art. N")  (cross-ref)   -> rag-cross-reference
- a VIGÊNCIA (vigente/inicio/fim/revogado_por)    -> rag-controle-vigencia

O recuperador plano devolve só o melhor match. O Legal Graph Lite (a) filtra os
revogados e (b) expande o melhor match VÁLIDO com pai + vizinhos + dispositivos
citados, reconstruindo a unidade de sentido que a norma deixou distribuída.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_REF = re.compile(r"art\.?\s*(\d+)", re.IGNORECASE)


@dataclass(frozen=True)
class No:
    id: str
    rotulo: str
    parent: str | None
    ordem: int
    texto: str
    vigente: bool
    inicio: int
    fim: int | None
    revogado_por: str | None


class LegalGraph:
    def __init__(self, nos: list[No]) -> None:
        self.nos = sorted(nos, key=lambda n: n.ordem)
        self.por_id = {n.id: n for n in self.nos}
        self.por_ordem = {n.ordem: n for n in self.nos}
        # número do artigo -> id (para resolver remissões "art. N")
        self._num_para_id: dict[int, str] = {}
        for n in self.nos:
            m = re.search(r"Art\.?\s*(\d+)", n.rotulo)
            if m and n.parent is None:
                self._num_para_id.setdefault(int(m.group(1)), n.id)
        self._vec = TfidfVectorizer(ngram_range=(1, 2), strip_accents="unicode")
        self._mat = self._vec.fit_transform(f"{n.rotulo} {n.texto}" for n in self.nos)

    # --- arestas ---
    def parent(self, n: No) -> No | None:
        return self.por_id.get(n.parent) if n.parent else None

    def filhos(self, n: No) -> list[No]:
        return [x for x in self.nos if x.parent == n.id]

    def vizinhos(self, n: No) -> list[No]:
        out = []
        for d in (-1, 1):
            viz = self.por_ordem.get(n.ordem + d)
            if viz is not None:
                out.append(viz)
        return out

    def remissoes(self, n: No) -> list[No]:
        out = []
        for num in (int(x) for x in _REF.findall(n.texto)):
            alvo_id = self._num_para_id.get(num)
            if alvo_id and alvo_id != n.id:
                out.append(self.por_id[alvo_id])
        return out

    # --- recuperação ---
    def _ranked(self, query: str) -> list[No]:
        sims = cosine_similarity(self._vec.transform([query]), self._mat).ravel()
        return [self.nos[i] for i in sims.argsort()[::-1]]

    def flat(self, query: str) -> str:
        """Vector search plano: só o melhor match (ignora estrutura e vigência)."""
        return self._ranked(query)[0].texto

    def expand(self, query: str) -> str:
        """Filtra revogados e expande o melhor VÁLIDO com pai + vizinhos + remissões."""
        validos = [n for n in self._ranked(query) if n.vigente]
        if not validos:
            return ""
        top = validos[0]
        sel: dict[str, No] = {top.id: top}
        for f in self.filhos(top):  # se o top é o caput, traz os incisos
            sel.setdefault(f.id, f)
        pai = self.parent(top)
        if pai is not None:
            sel[pai.id] = pai
            for f in self.filhos(pai):  # irmãos completam o caput
                sel.setdefault(f.id, f)
        for viz in self.vizinhos(top):
            sel.setdefault(viz.id, viz)
        for ref in self.remissoes(top):
            sel.setdefault(ref.id, ref)
        # também segue remissões dos nós já trazidos pela hierarquia
        for n in list(sel.values()):
            for ref in self.remissoes(n):
                sel.setdefault(ref.id, ref)
        # mantém só vigentes e ordena pelo documento
        vis = [n for n in sel.values() if n.vigente]
        return " ".join(n.texto for n in sorted(vis, key=lambda n: n.ordem))


def load_grafo(path: Path) -> LegalGraph:
    data = json.loads(path.read_text(encoding="utf-8"))
    return LegalGraph([No(**n) for n in data["nodes"]])


def completude(contexto: str, spans: list[str]) -> float:
    return sum(s in contexto for s in spans) / len(spans)


def cita_revogada(grafo: LegalGraph, contexto: str) -> bool:
    """O contexto contém o texto de algum nó revogado?"""
    return any((not n.vigente) and n.texto in contexto for n in grafo.nos)
