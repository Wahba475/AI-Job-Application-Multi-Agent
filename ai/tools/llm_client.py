from langchain_ollama import ChatOllama
from dotenv import load_dotenv

load_dotenv()

# Direct LLM calls (no tool use needed) — local Ollama, no rate limits
llm = ChatOllama(
    model="qwen2.5:7b",
    temperature=0
)

# Agent LLM — same model
agent_llm = ChatOllama(
    model="qwen2.5:7b",
    temperature=0
)
