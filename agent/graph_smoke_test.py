"""Smoke test: does LangGraph run a two-step graph on this PC (no language model)?"""
from typing import TypedDict

from langgraph.graph import END, StateGraph


class State(TypedDict):
    x: int
    log: list


def step_a(s):
    return {"x": s["x"] + 1, "log": s["log"] + ["a"]}


def step_b(s):
    return {"x": s["x"] * 2, "log": s["log"] + ["b"]}


graph = StateGraph(State)
graph.add_node("a", step_a)
graph.add_node("b", step_b)
graph.set_entry_point("a")
graph.add_edge("a", "b")
graph.add_edge("b", END)

print(graph.compile().invoke({"x": 1, "log": []}))
