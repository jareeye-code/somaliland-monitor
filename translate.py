"""English -> Somali. Uses Claude if ANTHROPIC_API_KEY set, else deep-translator (Google), else returns None."""
import json
import config

_client = None
def _claude():
    global _client
    if _client is None:
        import anthropic
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client

def to_somali(text: str):
    if not text or not text.strip(): return text
    if config.ANTHROPIC_API_KEY:
        try:
            r = _claude().messages.create(model=config.ANTHROPIC_MODEL, max_tokens=1500,
                system="Translate the user's text into natural Somali (Af-Soomaali). Output only the translation.",
                messages=[{"role": "user", "content": text}])
            return r.content[0].text.strip()
        except Exception as e:
            print("  [warn] claude translate:", e)
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source="auto", target="so").translate(text[:4500])
    except Exception as e:
        print("  [warn] fallback translate:", e)
        return None

def to_somali_batch(texts):
    return [to_somali(t) for t in texts]
