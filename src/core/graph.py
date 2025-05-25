from langgraph.graph import START, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from .graph_components import State, write_query, execute_query, generate_answer

def create_sql_qa_graph():
    graph_builder = StateGraph(State)
    graph_builder.add_node("write_query", write_query)
    graph_builder.add_node("execute_query", execute_query)
    graph_builder.add_node("generate_answer", generate_answer)

    graph_builder.add_edge(START, "write_query")
    graph_builder.add_edge("write_query", "execute_query")
    graph_builder.add_edge("execute_query", "generate_answer")
    # No explicit end node needed if generate_answer is the last step in the sequence.

    memory = InMemorySaver()
    graph = graph_builder.compile(checkpointer=memory)
    return graph

compiled_graph = create_sql_qa_graph()