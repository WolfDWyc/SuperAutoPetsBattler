

def concat_strings_horizontally(strings, separator):
    """
    Concatenates strings horizontally.

    :param strings: list of strings
    :param separator: string
    :return: string
    """
    string_lines = []
    # Merge player strings hortizontally 
    max_length = len(max((max(player_string.split("\n"), key=len) for player_string in strings), key=len))
    for line in zip(*(player_string.split("\n") for player_string in strings)):
        line = [line_part.ljust(max_length) for line_part in line]
        string_lines.append(separator.join(line))

    return "\n".join(string_lines)