import re

class TextCleaner:
    @staticmethod
    def clean(text: str) -> str:
        """
        Cleans and normalizes text:
        - Strips control and non-printable characters.
        - Replaces excessive newlines and tabs with single space or paragraph breaks.
        - Normalizes unicode quotation marks and hyphens.
        """
        if not text:
            return ""

        # Normalize unicode quotes and dashes
        text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
        text = text.replace("—", "-").replace("–", "-")

        # Remove control characters except standard whitespace
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)

        # Normalize spaces per line
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
        
        # Collapse multiple empty lines into a maximum of two
        cleaned_text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
        return cleaned_text.strip()

