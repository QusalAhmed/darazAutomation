import re


def to_md(text):
    return re.sub(r'([\[*_])', r'\\\1', text)


def simplified_text(input_string):
    pattern = r'[^\w\s\➛\u0980-\u09FF[\]]+'
    cleaned_string = re.sub(pattern, '', input_string).strip()
    return cleaned_string.lower()
