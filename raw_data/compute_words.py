import pandas as pd
from math import sqrt
# test = pd.DataFrame({"colonneA": pd.Series(data=[111, 222, 333], index=["un", "deux", "trois"]), "colonneB": pd.Series([444, 555, 666])})
# test.to_csv("test.csv")

words = pd.read_csv(r"raw_data\manually_cleaned.csv")
words["freqfilms2"] = words["freqfilms2"].astype("float")
words["freqlivres"] = words["freqlivres"].astype("float")

letter_correspondance =  {
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

letter_occurences = {'a': 29432, 'b': 6447, 'c': 14855, 'i': 32493, 's': 17067, 'n': 25556, 't': 25990, 'e': 54787, 'm': 12495, 'r': 32077, 'l': 17522, 'o': 22929, 'd': 8261, 'q': 2959, 'u': 17261, 'g': 7264, 'y': 1903, 'h': 5861, 'j': 693, 'k': 560, 'z': 481, 'f': 4765, 'x': 1457, 'v': 3743, 'p': 10236, ' ': 22, 'w': 94} # copied from output

col_word, col_difficulty, col_nature = [], [], []

all_nature, all_letters = [], {}

for i, ligne in words.iterrows():
    # freqfilms2 freqlivres
    difficulty = float(ligne["freqfilms2"]) + ligne["freqlivres"] / 2

    letter_used = []
    for char in ligne["Word"]:
        for letter in letter_correspondance.get(char, char):
            if not letter in letter_used:
                letter_used.append(letter)

    for letter in letter_used:
        difficulty += letter_occurences[letter]**2 / 1000000

    difficulty = float('%.3f'%(difficulty))

    # difficulty = difficulty**(1/4)
    # difficulty = round(difficulty*10)/10

    # if difficulty > 10:
    #     difficulty = 3
    # elif difficulty > 10:
    #     difficulty = 2
    # else:
    #     difficulty = round(difficulty)

    col_difficulty.append(difficulty)

    col_word.append(ligne["Word"])
    col_nature.append(ligne["cgram"][:3])

    if not ligne["cgram"] in all_nature:
        all_nature.append(ligne["cgram"])

    for char in ligne["Word"]:
        for letter in letter_correspondance.get(char, char):
            if letter in all_letters:
                all_letters[letter] += 1
            else:
                all_letters[letter] = 1

# all_letters.sort()
print("all_letters :", all_letters)
print("all_nature :", all_nature)

sorted_words = pd.DataFrame({
    "difficulty": pd.Series(col_difficulty),
    "word": pd.Series(col_word),
    "nature": pd.Series(col_nature)
})

sorted_words.sort_values("difficulty", ascending=False, ignore_index=True, inplace=True)

print("sorted_words :\n", sorted_words)

sorted_words.drop("difficulty", axis=1).to_csv(r"raw_data\computed_words.csv", index=False)


import matplotlib.pyplot as plt


# y = sorted_words['difficulty']
# y.value_counts().sort_index().plot.line(x='Difficulty', y='Number of Occurrences')

sorted_words['difficulty'].plot.line(y="difficulty")

plt.show()