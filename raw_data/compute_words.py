"""
    Ce programme n'est pas destiné à être exécuter avec le jeu, mais en amont pour établir le fichier assets\data\words.csv
    Il écrit son résultat dans computed_words.csv pour ne pas écraser les mots actuels, et laissé ce choix à la personne qui l'a lancé.
"""

import pandas as pd
from math import sqrt

words = pd.read_csv(r"raw_data\manually_cleaned.csv")

# Convertit la chaîne de caractères en nombre flottant
words["freqfilms2"] = words["freqfilms2"].astype("float")
words["freqlivres"] = words["freqlivres"].astype("float")

# Compté une fois avec une petite boucle dont le résultat est copié collé ici :
LETTER_OCCURENCES = {'a': 29432, 'b': 6447, 'c': 14855, 'i': 32493, 's': 17067, 'n': 25556, 't': 25990, 'e': 54787, 'm': 12495, 'r': 32077, 'l': 17522, 'o': 22929, 'd': 8261, 'q': 2959, 'u': 17261, 'g': 7264, 'y': 1903, 'h': 5861, 'j': 693, 'k': 560, 'z': 481, 'f': 4765, 'x': 1457, 'v': 3743, 'p': 10236, ' ': 22, 'w': 94}

# Les mêmes que dans word_chooser.py (On n'importe pas car ça ralentit trop)
LETTER_CORRESPONDANCE =  {
    'é': "e",
    'â': "a",
    'è': "e",
    'ê': "e",
    'î': "i",
    'û': "u",
    'ç': "c",
    'ï': "i",
    'ô': "o",
    'ö': "o",
    'ë': "e",
    'ü': "u",
    'à': "a",
    'ã': "a",
    "'": '',
    'œ': "oe"
}

# Contient les colonnes du .csv
col_word, col_difficulty, col_nature = [], [], []

# Si leur partie respective est décommentée, contient les différentes natures de mot et le nombre d'occurences des lettres.
all_nature, all_letters = [], {}

for i, ligne in words.iterrows():
    # La difficultée contient la monyenne de la fréquence dans les films et les livres.
    difficulty = float(ligne["freqfilms2"]) + ligne["freqlivres"] / 2

    # On trouve les *différentes* lettres du mot (pas de doublon)
    letter_used = []
    for char in ligne["Word"]:
        # On remplace les lettres accentuées par leur correspondance si elle existe.
        for letter in LETTER_CORRESPONDANCE.get(char, char):
            if not letter in letter_used:
                letter_used.append(letter)

    # Plus les lettres du mot sont des lettres courantes, plus le mot devient facile, et plus il a de lettres différentes aussi.
    for letter in letter_used:
        difficulty += LETTER_OCCURENCES[letter]**2 / 1000000

    # On limite le nombre de chiffres après la virgule pour ne pas rendre le .csv trop lourd.
    difficulty = float('%.3f'%(difficulty))


    col_difficulty.append(difficulty)
    col_word.append(ligne["Word"])
    col_nature.append(ligne["cgram"][:3])

    # Decommentez pour savoir quelles natures de mot sont présentes.
    if not ligne["cgram"] in all_nature:
        all_nature.append(ligne["cgram"])

    # Décommentez pour reconter le nombre d'occurence des lettres.
    for char in ligne["Word"]:
        for letter in LETTER_CORRESPONDANCE.get(char, char):
            if letter in all_letters:
                all_letters[letter] += 1
            else:
                all_letters[letter] = 1

#
print("all_letters :", all_letters)
print("all_nature :", all_nature)

# On construit la DataFrame finale
sorted_words = pd.DataFrame({
    "difficulty": pd.Series(col_difficulty),
    "word": pd.Series(col_word),
    "nature": pd.Series(col_nature)
})

# On trie par difficulté pouvoir utiliser l'indice comme difficulté
sorted_words.sort_values("difficulty", ascending=False, ignore_index=True, inplace=True)

# Un petit aperçu du résultat
print("sorted_words :\n", sorted_words)

# On ne garder que le nécessaire et on sauvegarde en .csv
sorted_words.drop("difficulty", axis=1).to_csv(r"raw_data\computed_words.csv", index=False)


if __name__ == "__main__" and input("Voulez vous voir un graphique du nombre de mots en fonction de la difficulté ?\nY/N : ").lower() == "y":
    import matplotlib.pyplot as plt

    sorted_words['difficulty'].plot.line(y="difficulty")

    plt.show()