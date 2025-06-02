# src/main_cli.py
import uuid
from core.graph import compiled_graph
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
        current_input_state = {"question": user_input, "chat_history": chat_history.copy()}

        final_answer = None
        generated_query = None
        print("\nAI is thinking...")
        for step in compiled_graph.stream(current_input_state, config=config, stream_mode="updates"):
            # print(f"Step: {step}") # For debugging
            if "write_query" in step:
                generated_query = step["write_query"]["query"]
                print(f"\nGenerated SQL:\n{generated_query}")
            elif "generate_answer" in step:
                final_answer_content = step["generate_answer"].get("answer")
                if final_answer_content:
                    final_answer = final_answer_content
                    print(f"AI: {final_answer}")

        if final_answer:
            chat_history.append(HumanMessage(content=user_input))
            ai_response = f"SQL Query: {generated_query} \nAnswer: {final_answer}" if generated_query else final_answer
            chat_history.append(AIMessage(content=ai_response))
        else:
            print("AI: I couldn't process that. Please try again.")

if __name__ == "__main__":
    run_chat_session()