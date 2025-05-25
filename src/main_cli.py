# src/main_cli.py
import uuid
from .core.graph import compiled_graph
from langchain_core.messages import HumanMessage, AIMessage

def run_chat_session():
    conversation_id = str(uuid.uuid4())
    print(f"Starting new chat session with ID: {conversation_id}")
    config = {"configurable": {"thread_id": conversation_id}}
    chat_history = []

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting chat.")
            break

        # Prepare current state for the graph
        current_input_state = {"question": user_input, "chat_history": chat_history.copy()} # Pass a copy

        final_answer = None
        print("\nAI is thinking...")
        for step in compiled_graph.stream(current_input_state, config=config, stream_mode="updates"):
            # print(f"Step: {step}") # For debugging
            if "generate_answer" in step: # Or however your final answer node is named
                final_answer_content = step["generate_answer"].get("answer")
                if final_answer_content:
                    final_answer = final_answer_content
                    print(f"AI: {final_answer}")

        if final_answer:
            chat_history.append(HumanMessage(content=user_input))
            chat_history.append(AIMessage(content=final_answer))
        else:
            print("AI: I couldn't process that. Please try again.")

if __name__ == "__main__":
    # Ensure your config.py loads .env for API keys if you run this directly
    # from .config import load_env_vars # if you have such a function
    # load_env_vars()
    run_chat_session()