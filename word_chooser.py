DEBUG = False
SUB_PROCESS_PREFIX = " -sub- "

print("Wordchooser : Importing...", end="\r")
import pandas
from path_rectifier import *
print("Wordchooser : Importing : OK")


HAS_LAROUSSE = False
try:
    from larousse_api import larousse
    HAS_LAROUSSE = True
except:
    print("Le module larousse-api n'est pas installé")


connection_parent: "None|multiprocessing.connection.Connection" = None
_connection_child: "None|multiprocessing.connection.Connection" = None
process: "None|multiprocessing.Process" = None

if HAS_LAROUSSE:
    import multiprocessing, multiprocessing.connection # (import connection just for type hint)


print("Wordchooser : Loading words...", end="\r")
words: pandas.DataFrame = pandas.read_csv(resource_path(r"assets/data/words.csv"))
print("Wordchooser : Loading words : OK")

WORDS_COUNT = len(words)
DOWN_RANGE_MAX: int = WORDS_COUNT - 500 # Valeur maximale du bas de la plage aléatoire
UP_RANGE_MIN: int = 500  # Valeur minimale du bas de la plage aléatoire
RANGE = 1000

DEFAULT_MAX_ATTEMPTS = 10

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
ALLOWED_LETTERS = [chr(ascii_decimal) for ascii_decimal in range(97, 123)] # Pick all letters from a to z


class Word():
    """Store a word, with some informations about it."""
    def __init__(self, rich_word: str, difficulty: int, definitions: list[str]|None = None) -> None:
        self.raw_word: str = rich_word.lower() # The word, but as shown when searched
        for special_char, new_char in LETTER_CORRESPONDANCE.items():
            self.raw_word = self.raw_word.replace(special_char, new_char)
        self.letter_set = set(self.raw_word)

        self.difficulty: int = difficulty

        self.rich_word: str = rich_word # The word with it's special characters
        self.definitions: list[str] = ["Installez larousse-api pour avoir accès aux définitions des mots."]
        # self.has_definitions: bool = False

        if definitions:
            self.definitions = definitions
            # self.has_definitions = True

        self.wrong_guesses = 0 # Nombre de lettres incorrectes (mis par defaut à 0)
        self.found_letters = [] # Liste des lettres correctement devinée
        self.guessed_letters = [] # Liste des lettres déjà essayées

    def __str__(self) -> str:
        return self.raw_word

    def __repr__(self) -> str:
        return f"<{self.rich_word} ({self.raw_word}) {self.difficulty}>"

# print(repr(Word("à l'œuf", 0)))

class WordRequest():
    def __init__(self, difficulty: int, max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> None:
        self.difficulty: int = difficulty
        self.max_attempts: int = max_attempts

    def __str__(self) -> str:
        return f"WordRequest ({self.difficulty})"


def cap(value: int, minimum: int, maximum: int) -> int:
    """Cappe la valeur entre les bornes `minimum` et `maximum`"""
    return min(max(value, minimum), maximum)


def get_word(difficulty: int, max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> str:
    """Choisit aléatoirement un mot dont l'indice est est situé entre `difficulty - word_chooser.RANGE` et `difficulty + word_chooser.RANGE`"""

    down_range = cap(difficulty - RANGE, 0, DOWN_RANGE_MAX)
    up_range = cap(difficulty + RANGE, UP_RANGE_MIN, WORDS_COUNT)

    if DEBUG:
        print(difficulty, " → ", down_range, "-", up_range, sep="")

    attempts = 0
    while attempts < max_attempts:
        word = words.iloc[down_range:up_range].sample(1).iloc[0]["word"]

        if HAS_LAROUSSE:
            try:
                definitions = larousse.get_definitions(word)
            except: # Handle Internet errors such as MaxRetryError
                definitions = []

            if definitions:
                return Word(word, difficulty, definitions)
        else:
            return Word(word, difficulty)

        print("[W] This word is not in the larousse dictionnary :", word)
        attempts += 1

    print("[E] No word within the Larousse was found. Returning the last found word.")
    return Word(word, difficulty)


def process_loop(connection: "multiprocessing.connection.Connection") -> None:
    """Start the subprocess infinite loop."""

    # On remplace print() pour mieux le différencier avec celui du processus parent
    global print
    default_print = print
    def print(*args, **kwargs):
        default_print(SUB_PROCESS_PREFIX, end="")
        default_print(*args, **kwargs)

    messages: list[str|WordRequest] = []

    print("Started main loop")
    while True:
        connection.poll(None) # Wait for a message
        while connection.poll() : # Loop in case multiple messages were send.
            message = connection.recv()
            if message == "close":
                print("Closing")
                return
            elif message == "clear":
                messages.clear()
            else:
                messages.append(message)

        if len(messages) > 3:
            print("Many unsatisfied messages :", len(messages))

        while messages:
            message = messages.pop(0)
            if isinstance(message, WordRequest):
                word = get_word(message.difficulty, message.max_attempts)
                connection.send(word)
                print("A word was found :", repr(word))
            else:
                print("[W] Unknow message passed trough pipe :", message)


def get_word_async(difficulty: int, max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> str:
    """Si larousse-api est installé, demande au programme parallèle de chercher un mot sur le larousse."""

    if not HAS_LAROUSSE:
        return Exception("larousse-api is not installed, use `get_word()` instead")
    if not connection_parent:
        return Exception("Initialisez d'abord le processus parallèle avec `init_process()`")

    connection_parent.send(WordRequest(difficulty, max_attempts))


def terminate() -> None:
    if not process:
        print("`terminate()` is unnecessary as no process has been created.")
        return

    connection_parent.send("close")
    for _ in range(30):
        process.join(1)
        if not process.is_alive():
            break
    else:
        print("Forcing the sub process to close !")
        process.terminate()
        process.join()

    connection_parent.close()
    _connection_child.close()


def init_process() -> None:
    """Call this to create the new process. This prevent the new process to create a process wich would create a process wich would etc..."""

    global process, connection_parent, _connection_child

    if not HAS_LAROUSSE:
        print("Starting a process is not necessary : larousse-api is not installed.")
        return
    if process:
        print("[E] Process was already created.")
        return

    print("Initializing process...", end="\r")

    connection_parent, _connection_child = multiprocessing.Pipe(duplex=True)
    process = multiprocessing.Process(target=process_loop, args=(_connection_child,), )
    process.start()

    print("Initializing process : OK")


if True and __name__ == "__main__":
    pass
    # for i in range(-1000, len(words) + 1001, 1000):
    #     print(i, ":", get_word(i))

    # get_word_async(0)
    # print("i'am first")

    # while word_queue.empty():
    #     print("empty")

    # print(word_queue.get())
    # word_queue.close()

    # if HAS_LAROUSSE:
    #     init_process()