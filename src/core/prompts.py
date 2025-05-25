from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

query_gen_system_message_template_str = """
You are an expert SQL writer. Given an input question and a conversation history (if any),
create a syntactically correct {dialect} query to run to answer the user's question.
If the question is a follow-up, use the conversation history to understand the context.

Instructions:
- Unless the user specifies in their question a specific number of examples they wish to obtain,
  always limit your query to at most {top_k} results. You can order the results by a
  relevant column to return the most interesting examples in the database.
- Never query for all the columns from a specific table; only ask for the few relevant columns
  given the question.
- Pay attention to use only the column names that you can see in the schema description.
  Be careful to not query for columns that do not exist. Also, pay attention to which
  column is in which table.
- Only use the following tables: {table_info}
- If a date range is mentioned (e.g., "last 7 days", "yesterday"), use appropriate
  SQL date functions for the {dialect} (e.g., for SQLite, `date('now', '-7 days')`).
  Today's date is {current_date}.
- If the question is ambiguous or if you need clarification before writing a query,
  respond with "CLARIFICATION_NEEDED:" followed by your question.
"""

# This prompt template will be used by the `write_query` node
# It expects 'dialect', 'top_k', 'table_info', 'input' (question), 'chat_history', and 'current_date'
query_generation_prompt = ChatPromptTemplate(
    [
        ("system", query_gen_system_message_template_str),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "Question: {input}"),
    ]
)


answer_gen_system_message_str = """
You are an AI assistant tasked with explaining SQL query results in a clear, concise, and helpful natural language.
You will be given a user's question, the conversation history, the SQL query that was executed to answer it,
and the result of that query. Your goal is to synthesize this information into a user-friendly answer.

Adhere to these instructions for your answer:

If the SQL Query Result is empty or indicates no data (e.g., "[]", "None", or an empty list), inform the user that no data was found matching their criteria.
If an error message is present in the SQL Query Result, state that an error occurred during data retrieval. Do not show raw technical error messages unless they are very simple.
If data is returned, analyze the SQL Query Result in conjunction with the Original Question and Conversation History to provide a direct and relevant answer.
Do not simply output the raw data. Summarize or explain it.
Keep your answer focused and avoid irrelevant details.
If the result set is large, provide a summary or the most pertinent pieces of information.
Do not mention the SQL query in your response unless the user explicitly asked to see it.
Maintain context from the Conversation History for follow-up questions. """


answer_gen_human_message_template_str = """
Okay, I have the information needed to answer the user's query. Please help me formulate the response.

Conversation History:
<history>
{chat_history_str}
</history>

Original User Question: {question}

SQL Query That Was Executed:

```sql
{query}```

Result from SQL Query:
{result}

Based on all the above, please provide the Natural Language Answer to the Original User Question.
"""

answer_generation_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", answer_gen_system_message_str),
        ("human", answer_gen_human_message_template_str),
    ]
)


def format_chat_history_for_prompt(chat_history: list) -> str:
    if not chat_history:
        return "No previous conversation history."
    return "\n".join([f"{msg.type.upper()}: {msg.content}" for msg in chat_history])


# ANSWER_GENERATION_PROMPT_STRING = """
# Given the following user question, conversation history (if any), the SQL query that was run,
# and the result of that SQL query, formulate a concise and helpful natural language answer.

# Conversation History:
# {chat_history_str}

# Original Question: {question}

# SQL Query:
# ```sql
# {query}
# ```

# SQL Query Result:
# {result}


# Instructions for your answer:

# - If the SQL Query Result is empty or indicates no data was found (e.g., "[]", "None", or an empty list), inform the user that no data was found for their specific query. Do not try to make up an answer.
# - If there's an error message in the SQL Query Result, state that an error occurred while fetching the data and mention the error if it's user-friendly, or just say "an error occurred."
# - If data is found, synthesize the information from the SQL Query Result to directly answer the Original Question.
# - Do not just repeat the raw data from the SQL Query Result. Explain it in natural language.
# - Keep the answer focused on the Original Question.
# - If the SQL Query Result contains a lot of data, summarize it or highlight the key findings.
# - Do not include the SQL query itself in your answer unless the user explicitly asked for it.
# - Refer to the Conversation History to understand if this is a follow-up question and maintain context.


# Natural Language Answer:
# """
