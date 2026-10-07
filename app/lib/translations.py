from flask_babel import _, pgettext


def translate_term(text, context=None):
    """Use a table-specific term when available, then the ordinary catalog."""
    if not text:
        return text
    if context:
        translation = pgettext(context, text)
        if translation != text:
            return translation
    return _(text)
