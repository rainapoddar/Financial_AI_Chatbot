import ollama


SYSTEM = """
You are a Financial Portfolio Assistant.

Rules
1. Never guess or invent any number.
2. Use ONLY the data given to you in "Financial Data" below.
3. Never calculate anything yourself - Python has already calculated it.
4. If the Financial Data says information is not available, tell the user
   clearly that this report does not contain that information. Do not make
   up a substitute number.
5. Answer in a short, professional, friendly tone (2-4 sentences).
"""


def ask_llama(question, context):
    """
    Wraps a Python-computed fact (in `context`) into a natural sentence.
    If Ollama isn't installed/running, falls back to returning the raw
    context so the app keeps working instead of crashing.
    """
    try:
        response = ollama.chat(
            model="llama3",
            messages=[
                {"role": "system", "content": SYSTEM},
                {
                    "role": "user",
                    "content": f"Question:\n{question}\n\nFinancial Data:\n{context}",
                },
            ],
        )
        return response["message"]["content"]
    except Exception:
        # Ollama not available -> just show the computed fact plainly.
        return context   