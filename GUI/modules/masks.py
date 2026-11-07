DIGITS = "0123456789"


def only_digits(text: str | None):
    return "".join(character for character in text or "" if character in DIGITS)


def signed_digits(text: str | None):
    text = text or ""
    return ("-" if text.startswith("-") else "") + only_digits(text)


def cpf_mask(text: str | None):
    digits = only_digits(text)[:11]
    result = ".".join(part for part in (digits[:3], digits[3:6], digits[6:9]) if part)
    if len(digits) > 9:
        result += "-" + digits[9:]
    return result


def money_mask(text: str | None):
    result = ""
    hasComma = False
    decimals = 0
    for character in text or "":
        if character == "." and not hasComma:
            character = ","  # quem digita 1.5 quer dizer 1,50
        if character in DIGITS:
            if hasComma:
                if decimals == 2:
                    continue
                decimals += 1
            result += character
        elif character == "," and not hasComma:
            hasComma = True
            result += character
    return result
