import sys
sys.path.append("..")
sys.path.append("./")


import uuid
import streamlit as st
from core.graph import compiled_graph # Your compiled LangGraph
from core.graph_components import State # Your state definition
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
load_dotenv()

st.title("text2SQL Wizard 🧙‍♂️")

# Initialize chat history in Streamlit's session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "langgraph_chat_history" not in st.session_state:
    st.session_state.langgraph_chat_history = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

# Display prior messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # If the message is from the assistant and has an SQL query, show it in an expander
        if message["role"] == "assistant" and message.get("sql_query"):
            with st.expander("View Generated SQL/Attempt"):
                st.code(message["sql_query"], language="sql", wrap_lines=True, line_numbers=True)

# Get user input
if prompt := st.chat_input("Ask a question about your data..."):
    st.session_state.messages.append({"role": "user", "content": prompt, "sql_query": None})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")

        # Prepare input for the graph
        graph_input = {
            "question": prompt,
            "chat_history": st.session_state.langgraph_chat_history.copy()
        }
        config = {"configurable": {"thread_id": st.session_state.conversation_id}}

        full_response = ""
        generated_sql_query = ""
        try:
            final_graph_output = None
            # Stream the graph execution
            for step in compiled_graph.stream(graph_input, config=config, stream_mode="values"):
                final_graph_output = step
            # Refined streaming to capture final answer:
            if final_graph_output:
                full_response = final_graph_output.get("answer", "Sorry, I couldn't formulate a final answer.")
                generated_sql_query = final_graph_output.get("query", "No SQL query information available.")
            else:
                full_response = "Sorry, there was an issue processing your request."
                generated_sql_query = "No graph output received."

            message_placeholder.markdown(full_response)

            # Display the SQL query in an expander if available
            if generated_sql_query:
                with st.expander("View Generated SQL/Attempt"):
                    st.code(generated_sql_query, language="sql", wrap_lines=True, line_numbers=True, )

        except Exception as e:
            full_response = f"An error occurred: {str(e)}"
            generated_sql_query = f"Error during execution: {str(e)}" # Store error as query info too
            st.error(full_response) # Show error in the main chat
            # Also display the error in the expander for consistency
            with st.expander("View Error Details"):
                st.code(generated_sql_query, language="text")


        # Add assistant response and SQL query to display chat history
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response,
            "sql_query": generated_sql_query
        })

        st.session_state.langgraph_chat_history.append(HumanMessage(content=prompt))
        st.session_state.langgraph_chat_history.append(AIMessage(content=full_response))
