def wrap_text(text, max_chars):
    """Wrap text to fit within max_chars per line, without splitting words"""
    # If the text is already short enough, return it unmodified as a single line
    if len(text) <= max_chars:
        return [text]
    # If the text is too long, wrap it to fit within the specified width, while
    # stripping unnecessary whitespace
    words = text.split(' ')
    wrapped_lines = []
    line = ''
    for word in words:
        # If adding the word would exceed max_chars
        if len(line) + len(word) + (1 if line else 0) > max_chars:
            if line:  # If there's already some text, start a new line
                wrapped_lines.append(line.strip())
                line = ''
        # If the word itself exceeds max_chars, place it in a new line
        if len(word) > max_chars:
            wrapped_lines.append(word)
        else:
            line += (word + ' ')

    if line:
        wrapped_lines.append(line.strip())

    return wrapped_lines
