"""LLM clients with automatic provider fallback.

Providers are tried in PROVIDER_ORDER (best first). If the primary errors
(401 / 429 / 503 / timeout), the next provider takes over automatically:

  groq   — openai/gpt-oss-120b. Fastest (~0.3s), reliable tool-calling, no
           <think> leak. Free tier throttles at 8000 TPM, so under load it
           spills to the fallbacks below.
  nvidia — meta/llama-3.3-70b-instruct. Free NIM, instruct model (clean tool
           calls). Occasional 503 congestion.
  ollama — qwen2.5:7b local. Unlimited/free, no throttle, slow — guaranteed
           last resort so a run never dies just because the cloud is down.

Set LLM_PROVIDER in .env to force a single provider (skips the chain); otherwise
the full fallback chain is used.
"""
import os
import re

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

load_dotenv()

# Best first. A single LLM_PROVIDER override pins the chain to one entry.
#   openai — gpt-4o-mini. Paid (~$0.04/run) but 200k TPM (25x Groq free), so no
#            throttle: full runs finish in ~40s and CVs are actually tailored.
#   groq/nvidia/ollama — free fallbacks if OpenAI is unset or errors.
_DEFAULT_ORDER = ["openai", "groq", "nvidia", "ollama"]
_override = os.getenv("LLM_PROVIDER", "").lower().strip()
PROVIDER_ORDER = [_override] if _override in _DEFAULT_ORDER else _DEFAULT_ORDER

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def strip_think(text: str) -> str:
    """Defensive scrub for reasoning-model chain-of-thought. Normally a no-op
    for instruct models, but guards CV text / scoring inputs if a provider
    ever emits <think>...</think>."""
    if not text:
        return ""
    text = _THINK_RE.sub("", text)
    if "</think>" in text:
        text = text.split("</think>")[-1]
    return text.strip()


def _build(provider: str):
    if provider == "openai":
        return ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("Open_AI"), temperature=0)
    if provider == "groq":
        return ChatGroq(model="openai/gpt-oss-120b", api_key=os.getenv("GROQ_API"), temperature=0)
    if provider == "nvidia":
        return ChatNVIDIA(model="meta/llama-3.3-70b-instruct", api_key=os.getenv("NVIDIA_API"),
                          temperature=0, timeout=90)
    if provider == "ollama":
        return ChatOllama(model="qwen2.5:7b", temperature=0)
    raise ValueError(f"Unknown provider: {provider}")


# One chat model per provider, in priority order.
CHAT_MODELS = [_build(p) for p in PROVIDER_ORDER]

# Plain calls (filter, ATS validation): LangChain wires the fallback chain so a
# failed .invoke() transparently retries on the next provider.
llm = CHAT_MODELS[0].with_fallbacks(CHAT_MODELS[1:]) if len(CHAT_MODELS) > 1 else CHAT_MODELS[0]

# The ReAct tailor agent needs a raw model it can .bind_tools() on, so it can't
# use a fallback-wrapped runnable directly. AGENT_MODELS exposes the ordered
# raw models; tailor_cv_node builds an agent per model and tries them in order.
agent_llm = CHAT_MODELS[0]
AGENT_MODELS = CHAT_MODELS
