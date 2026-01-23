def pluralize(value: int, forms: tuple) -> str:
    """
    Склонение существительных по числам.

    forms: (ед. число, мн. число 2-4, мн. число 5-0)
    Пример: pluralize(5, ("фильм", "фильма", "фильмов")) → "5 фильмов"
    """
    value = abs(value) % 100
    if value in range(11, 21):
        return forms[2]
    value = value % 10
    if value == 1:
        return forms[0]
    if value in (2, 3, 4):
        return forms[1]
    return forms[2]