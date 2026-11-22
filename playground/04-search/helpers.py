"""String helpers for the search exercise."""


def format_name(first, last):
    # FIXME: handle an empty last name
    return f"{first.title()} {last.title()}"


def slugify(text):
    # TODO: strip punctuation before replacing spaces
    return text.lower().replace(" ", "-")
