from langgraph.graph import START, StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from .graph_components import State, write_query, execute_query, generate_answer
from .config import DEFAULT_MAX_RETRIES_FOR_QUERY_EXECUTION
# --- Conditional Edge Logic ---
def should_retry_or_proceed(state: State) -> str:
    """
    Determines the next step after query execution.
    - If an error occurred and retries are not exhausted, go back to 'write_query'.
    - Otherwise (success or retries exhausted), proceed to 'generate_answer'.
    """
    error_message = state.get("error_message")
    retry_count = state.get("retry_count", 0)

    if error_message and retry_count < DEFAULT_MAX_RETRIES_FOR_QUERY_EXECUTION:
        print(f"Execution failed (attempt {retry_count}/{DEFAULT_MAX_RETRIES_FOR_QUERY_EXECUTION}). Retrying query generation.")
        return "retry_write_query"
    else:
        if error_message and retry_count >= DEFAULT_MAX_RETRIES_FOR_QUERY_EXECUTION:
            print(f"Execution failed after {retry_count} attempts. Proceeding to generate answer with error.")
        elif not error_message:
            print("Execution successful or no error to retry. Proceeding to generate answer.")
        return "proceed_to_answer"


def create_sql_qa_graph():
    graph_builder = StateGraph(State)

    graph_builder.add_node("write_query", write_query)
    graph_builder.add_node("execute_query", execute_query)
    graph_builder.add_node("generate_answer", generate_answer)

    graph_builder.add_edge(START, "write_query")

    # Conditional logic after execute_query
    graph_builder.add_conditional_edges(
        "execute_query",
        should_retry_or_proceed,
        {
            "retry_write_query": "write_query",
            "proceed_to_answer": "generate_answer"
        }
    )

    graph_builder.add_edge("write_query", "execute_query")
    graph_builder.add_edge("generate_answer", END)

    memory = InMemorySaver()
    graph = graph_builder.compile(checkpointer=memory)
    return graph

compiled_graph = create_sql_qa_graph()