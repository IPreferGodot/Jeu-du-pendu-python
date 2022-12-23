DEBUG = False

print("Importing...")
import pandas


words: pandas.DataFrame = pandas.read_csv(r"assets/data/words.csv")
print("Loaded words.")

DOWN_RANGE_MAX: int = len(words) - 500 # Valeur maximale du bas de la plage aléatoire
UP_RANGE_MIN: int = 500  # Valeur minimale du bas de la plage aléatoire
WORDS_COUNT = len(words)
RANGE = 1000


def cap(value: int, minimum: int, maximum: int) -> int:
    """Cappe la valeur entre les bornes `minimum` et `maximum`"""
    return min(max(value, minimum), maximum)


def choose_word(difficulty: int) -> str:
    """Choisit aléatoirement un mot dont l'indice est est situé entre `difficulty - word_chooser.RANGE` et `difficulty + word_chooser.RANGE`"""

    down_range = cap(difficulty - RANGE, 0, DOWN_RANGE_MAX)
    up_range = cap(difficulty + RANGE, UP_RANGE_MIN, WORDS_COUNT)

    if DEBUG:
        print(difficulty, " → ", down_range, "-", up_range, sep="")

    return words.iloc[down_range:up_range].sample(1).iloc[0]["word"]



if True and __name__ == "__main__":
    for i in range(-1000, len(words) + 1001, 1000):
        print(i, ":", choose_word(i))