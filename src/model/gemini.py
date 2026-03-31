import json
from google import genai

class GeminiHelper:
    def __init__(self):
        config = wiz.config("ai")
        self._api_key = config.gemini.api_key
        self._model_name = config.gemini.model
        self._client = genai.Client(api_key=self._api_key)

    def ask(self, prompt, system_instruction=None):
        config = None
        if system_instruction:
            config = {"system_instruction": system_instruction}
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=prompt,
            config=config
        )
        return response.text

    def ask_json(self, prompt, system_instruction=None):
        text = self.ask(prompt, system_instruction=system_instruction)
        if text is None:
            return None
        try:
            cleaned = text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned = "\n".join(lines)
            return json.loads(cleaned)
        except Exception:
            # JSON 파싱 실패 시 None 반환 (raw 텍스트 반환하지 않음)
            return None

Model = GeminiHelper()
