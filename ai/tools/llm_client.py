import os
import re
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

load_dotenv()

# Provider switch (set LLM_PROVIDER in .env):
#   "nvidia" (default) — meta/llama-3.3-70b-instruct on NVIDIA's free NIM
#      endpoint. Free, no card. An INSTRUCT model (not a reasoning model), so
#      it calls the finalize_cv tool reliably and never leaks <think> into the
#      CV — the two bugs that plagued nemotron. Occasional 503 congestion is
#      absorbed by the retry + original-CV fallback.
#   "groq"   — openai/gpt-oss-120b. Fastest, but free tier throttles at 8000 TPM;
#      use the paid Dev tier ($5 cap) for the demo.
#   "ollama" — qwen2.5:7b local. Unlimited/free, no throttle, slow on weak CPU.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "nvidia").lower()

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def strip_think(text: str) -> str:
    """Defensive scrub for reasoning-model chain-of-thought. gpt-oss isn't a
    thinking model by default so this is normally a no-op, but it guards
    against any <think>...</think> ever leaking into CV text or scoring inputs
    if the model or provider changes."""
    if not text:
        return ""
    text = _THINK_RE.sub("", text)
    if "</think>" in text:
        text = text.split("</think>")[-1]
    return text.strip()


def _make_llm():
    if LLM_PROVIDER == "groq":
        # Fastest; free tier throttles at 8000 TPM (use paid Dev tier for demo).
        return ChatGroq(model="openai/gpt-oss-120b", api_key=os.getenv("GROQ_API"), temperature=0)
    if LLM_PROVIDER == "ollama":
        # Unlimited/free local, no throttle, slow on weak CPU.
        return ChatOllama(model="qwen2.5:7b", temperature=0)
    # Default: NVIDIA free NIM, instruct model — reliable tool-calling, no leak.
    return ChatNVIDIA(
        model="meta/llama-3.3-70b-instruct",
        api_key=os.getenv("NVIDIA_API"),
        temperature=0,
        timeout=90,
    )


# Quality-sensitive calls (tailoring, filtering, ATS validation).
llm = _make_llm()

# Agent LLM — same model, used by the ReAct tailor agent.
agent_llm = _make_llm()

# Fast LLM — tiny local model for trivial classification if ever needed.
fast_llm = ChatOllama(model="qwen2.5:0.5b", temperature=0)
