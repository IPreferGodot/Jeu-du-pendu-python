# Importation des modules nécessaires à la mise en place du fichier de log
from path_rectifier import resource_path as res_path, BUNDLED
import sys, os, time

if BUNDLED:
    # On crée un fichier de log pour le .exe
    OUTPUT_FILE = open(os.path.join(os.path.dirname(sys.executable), f"{time.strftime(r'%d-%m-%Y %Hhs%Mm%Ss')} log.txt"), 'w', encoding="utf-8")
    sys.stdout = OUTPUT_FILE
    sys.stderr = OUTPUT_FILE

# Importation des autres modules
import pygame, word_chooser
from pygame.locals import QUIT, WINDOWSIZECHANGED as WINDOW_SIZE_CHANGED, KEYDOWN, USEREVENT, TEXTINPUT, KMOD_ALT, KMOD_CTRL, KMOD_SHIFT, K_KP_ENTER, K_LEFT, K_RIGHT, K_DOWN, K_UP, K_SPACE, K_BACKSPACE, K_RETURN, K_F4
from pygame.math import Vector2
from word_chooser import Word
from math import cos


print("Initializing pygame...", end="\r")
pygame.init()
print("Initializing pygame : OK")


# ----------------- Constants ------------------
IN_CODESPACE = os.environ.get("CODESPACES", False)

# colors
BACKGROUND_COLOR = (203, 219, 252)
BLACK = (34, 32, 52)
RED = (142, 0, 24)
GREEN = (72, 142, 58)

# game
MAX_WRONG_GUESSES = 7
DIFFICULTY_CHANGE = 1000
DIFFICULTY_LABEL = "Difficulté : "

# states
STATE_PLAYING = 1
STATE_WAITING_WORD = 2
STATE_TRANSITION = 3 # Unused
STATE_WIN_ANIMATION = 4
STATE_LOOSE_ANIMATION = 5
STATE_DEV_CHOOSE_WORD = 6

# Path
FONT_PATH = res_path(r"assets/fonts/DotGothic16-Regular.ttf")

# Pygame
FRAME_TIME = int(1/60 * 1000) # In ms
WINDOW_TITLE = "Jeu du pendu"

WINDOW_ORIGINAL_SIZE = Vector2(960, 540)
HANGMAN_ORIGINAL_SIZE = Vector2(400, 400)

BIG_FONT_ORIGINAL_SIZE = 100
SMALL_FONT_ORIGINAL_SIZE = 30
BIG_FONT_SPACING = 10
# /!\ BIG font height/width already contains spacements inside, but SMALL does not.
BIG_FONT_WIDTH, BIG_FONT_HEIGHT = Vector2(BIG_FONT_SPACING, BIG_FONT_SPACING*2) + pygame.font.Font(FONT_PATH, BIG_FONT_ORIGINAL_SIZE).size("a")
SMALL_FONT_WIDTH, SMALL_FONT_HEIGHT = pygame.font.Font(FONT_PATH, SMALL_FONT_ORIGINAL_SIZE).size("a")

SCREEN = pygame.display.set_mode(WINDOW_ORIGINAL_SIZE, pygame.RESIZABLE)

HANGMAN_ORIGINAL_IMAGES: list[pygame.Surface] = [
    pygame.transform.scale(
        pygame.image.load(res_path(f"assets/img/sprites/hangman/hangman{idx}.png")),
        HANGMAN_ORIGINAL_SIZE
    )
    for idx in range(MAX_WRONG_GUESSES)
]

# Sounds
if not IN_CODESPACE:
    SOUND_GOOD = pygame.mixer.Sound(res_path(r"assets/sounds/Good.ogg"))
    SOUND_BAD = pygame.mixer.Sound(res_path(r"assets/sounds/Bad.ogg"))
    SOUND_DISABLED = pygame.mixer.Sound(res_path(r"assets/sounds/Disabled.ogg"))
    SOUND_WIN = pygame.mixer.Sound(res_path(r"assets/sounds/Win.ogg"))
    SOUND_LOOSE = pygame.mixer.Sound(res_path(r"assets/sounds/Loose.ogg"))

    MUSICS = [res_path(f"assets/music/Level {i}.ogg") for i in range(3)]
    MUSIC_TRANSITIONS: dict[tuple[int, int], str] = {
        (0, 1): res_path(f"assets/music/Transition 0-1.ogg"),
        (1, 2): res_path(f"assets/music/Transition 1-2.ogg"),
        (0, 2): res_path(f"assets/music/Transition 0-2.ogg"),
        (1, 0): res_path(f"assets/music/Transition 1-0.ogg"),
        (2, 0): res_path(f"assets/music/Transition 2-0.ogg")
    }


# ------------------- Events -------------------
MUSIC_END = USEREVENT + 1
ANIMATION_END = MUSIC_END + 1
SAY_ALIVE = ANIMATION_END + 1


# ----------------- Variables ------------------
class Globals():
    """
    Contient les variables "globales" du programme.
    Permet de mieux distinguer quelles variables sont globales ou locales, si le mot-clé `global` est éloigné.
    """

    def __init__(self) -> None:
        self.state: int = STATE_WAITING_WORD
        self.current_difficulty: int = 0
        self.word: Word = Word("non initialisé", 0, ["La variable `word` a été initialisée, mais aucun mot n'a été choisi."])

        self.prechoosed_words: dict[int, list[word_chooser.Word]] = {} # Stocke les mots obtenus en arrière plan
        self.word_history: list[word_chooser.Word] = [] # Garde une trace des mots déjà montrés au joueur, par exemple au cas où il veuille en revoir la définition. (N'a pas été implémenté)

        self.music: int = 0

        self.dev_mode: bool = False
        self.forced_next_word: Word|None = None

_g = Globals()


class Layout():
    """
    Contient les informations relatives à la taille et la position des éléments à l'écran.
    """

    def __init__(self) -> None:
        self.scale: float = None
        self.letter_scale: float = None

        self.hangman_pos: Vector2 = None
        self.hangman_size: Vector2 = None
        self.hangman_images: list[pygame.Surface] = None

        self.big_font: pygame.font.Font = None
        self.small_font: pygame.font.Font = None
        self.letter_width: float = None
        self.word_pos: pygame.math.Vector2 = None

        self.unknown_letter: pygame.Surface = None
        self.letters: list[pygame.Surface] = None

        self.wrong_letters_pos: Vector2 = None
        self.difficulty_pos: Vector2 = None

        self.update()


    def update(self, screen_width: int|None = None, screen_height: int|None = None) -> None:
        if screen_width == None:
            screen_width, screen_height = pygame.display.get_window_size()

        # On choisi la taille la plus grande possible qui ne dépasse pas verticalement/horizontalement
        self.scale = min(screen_width / WINDOW_ORIGINAL_SIZE.x, screen_height / WINDOW_ORIGINAL_SIZE.y)
        self.update_letter()

        self.hangman_size = HANGMAN_ORIGINAL_SIZE * self.scale
        self.hangman_pos = (screen_width / 2 - self.hangman_size.x / 2, screen_height - self.hangman_size.y)
        self.hangman_images = [
            pygame.transform.scale(original_surface, self.hangman_size)
            for original_surface in HANGMAN_ORIGINAL_IMAGES
        ]

        self.wrong_letters_pos = Vector2(17*self.scale, screen_height - (SMALL_FONT_HEIGHT + 10)*self.scale)
        self.difficulty_pos = Vector2(screen_width - SMALL_FONT_WIDTH * len(DIFFICULTY_LABEL) * self.scale, screen_height - (SMALL_FONT_HEIGHT + 10)*self.scale)


    def update_letter(self, screen_width: int = None, screen_height: int = None) -> None:
        if screen_width == None:
            screen_width, screen_height = pygame.display.get_window_size()

        word_width = len(_g.word.raw_word if _g.state == STATE_PLAYING else _g.word.rich_word) * BIG_FONT_WIDTH + BIG_FONT_SPACING
        self.letter_scale = min(screen_width / word_width, screen_height / BIG_FONT_HEIGHT * 0.3)
        self.letter_width = BIG_FONT_WIDTH * self.letter_scale

        # self.word_pos = Vector2(screen_width/2 - word_width * self.letter_scale/2 + BIG_FONT_SPACING*self.letter_scale, BIG_FONT_SPACING * self.letter_scale)
        # ↓ = factorisation de ↑
        self.word_pos = Vector2(screen_width/2 - (word_width/2 - BIG_FONT_SPACING)*self.letter_scale, BIG_FONT_SPACING * self.letter_scale)

        self.big_font = pygame.font.Font(FONT_PATH, int(BIG_FONT_ORIGINAL_SIZE * self.letter_scale))
        self.small_font = pygame.font.Font(FONT_PATH, int(SMALL_FONT_ORIGINAL_SIZE * self.scale))

        self.unknown_letter = self.big_font.render("_", True, BLACK)
        self.update_prerendered_word()


    def update_prerendered_word(self) -> None:
        """Update the word with the right colors and underscores."""
        self.letters = []
        for letter in _g.word.raw_word if _g.state == STATE_PLAYING else _g.word.rich_word:
            found = _g.word.is_letter_found(letter)
            self.letters.append(
                self.big_font.render(
                    letter, True, GREEN if _g.state == STATE_WIN_ANIMATION else BLACK if found or _g.state == STATE_PLAYING else RED
                ) if found or _g.state == STATE_LOOSE_ANIMATION
                else self.unknown_letter
            )

layout = Layout()


# ----------------- Functions ------------------
# def vec_minus(a: tuple, b: tuple) -> tuple:
#     """Substract to tuple like 2D vectors."""
#     return a[0]-b[0], a[1]-b[1]


def is_state(*wanted_states: int) -> bool:
    """Return True if the actual state is one of the wanted states."""
    return _g.state in wanted_states


def add_prechoosed_word(word: word_chooser.Word) -> None:
    """Ajoute un mot à la liste des mots préchoisis par le processus enfant."""
    if word.difficulty in _g.prechoosed_words:
        _g.prechoosed_words[word.difficulty].append(word)
    else:
        _g.prechoosed_words[word.difficulty] = [word]

    if _g.state == STATE_WAITING_WORD and word.difficulty == _g.current_difficulty:
        new_game()


def draw_hangman() -> None:
    """Affiche la bonne image en fonction du nombre d'erreurs."""
    SCREEN.blit(layout.hangman_images[min(_g.word.wrong_guesses, MAX_WRONG_GUESSES - 1)], layout.hangman_pos)


def draw_word(x: int|None = None,  y: int|None = None) -> None:
    """Dessine le mot à deviner sur l'écran, avec les lettres correctes montrées et celles incorrectes transformées en "_"."""
    if x == None:
        x, y = layout.word_pos

    for letter_surface in layout.letters:
        SCREEN.blit(letter_surface, (x, y + cos((pygame.time.get_ticks() + x*3)/500)*10*layout.letter_scale))
        x += layout.letter_width


def draw_wrong_letters() -> None:
    """Affiche les lettres tentées mais qui n'étaient pas dans le mot."""
    SCREEN.blit(layout.small_font.render(",".join(_g.word.wrong_letters), True, RED), layout.wrong_letters_pos)


def draw_difficulty() -> None:
    """Affiche la difficulté actuelle."""
    shown_difficulty = str(int(_g.current_difficulty/DIFFICULTY_CHANGE))
    SCREEN.blit(layout.small_font.render(DIFFICULTY_LABEL + shown_difficulty, True, BLACK), layout.difficulty_pos - (SMALL_FONT_WIDTH * len(shown_difficulty) * layout.scale, 0))


def draw_waiting_for_word() -> None:
    """Affiche l'écran d'attente lorsqu'on attend un mot du processus enfant."""
    SCREEN.fill(BACKGROUND_COLOR)
    msg = layout.small_font.render("En attente d'un mot...", True, BLACK)
    # SCREEN.blit(msg, vec_minus(SCREEN.get_rect().center, msg.get_rect().center))
    SCREEN.blit(msg, msg.get_rect(center=SCREEN.get_rect().center).topleft)
    pygame.display.flip()


def check_win() -> bool:
    """Vérifie si le joueur a gagné, et agit en conséquence."""
    if set(_g.word.found_letters) == _g.word.letter_set:
        _g.state = STATE_WIN_ANIMATION
        if not IN_CODESPACE:
            SOUND_WIN.play()
        pygame.time.set_timer(ANIMATION_END, 3_000, 1)
        layout.update_letter()
        return True
    return False

def check_loose() -> bool:
    """Vérifie si le joueur a perdu, et agit en conséquence."""
    if _g.word.wrong_guesses == MAX_WRONG_GUESSES:
        _g.state = STATE_LOOSE_ANIMATION
        if not IN_CODESPACE:
            SOUND_LOOSE.play()
        pygame.time.set_timer(ANIMATION_END, 3_000, 1)
        layout.update_letter()
        return True
    return False


def handle_input(guess: str) -> None:
    """Gère les entrées du joueur et met a jour l'état du jeu en fonction de la touche."""

    guess = guess.lower() # met la touche en minuscule

    # Vérifie que la lettre n'as pas déjà été utilisée
    if guess in _g.word.guessed_letters:
        if not IN_CODESPACE:
            SOUND_DISABLED.play()
        return
    # Vérifie que c'est un lettre non accentuée
    if guess not in word_chooser.ALLOWED_LETTERS: return

    _g.word.guessed_letters.append(guess)
    if guess in _g.word.letter_set:
        # Met la lettre correcte  dans la liste found_letters
        _g.word.found_letters.append(guess)
        if not check_win():
            if not IN_CODESPACE:
                SOUND_GOOD.play()

        layout.update_prerendered_word()
    else:
        # Ajoute 1 au nombre de lettres incorrectes et met la lettre dans la liste des déjà devinées (mais fausses)
        _g.word.wrong_guesses += 1
        _g.word.wrong_letters.append(guess)
        if not check_loose():
            if not IN_CODESPACE:
                SOUND_BAD.play()


def set_word(new_word: word_chooser.Word) -> None:
    """Change les variables globales lorsqu'un nouveau mot est choisi."""
    _g.state = STATE_PLAYING

    _g.word_history.append(new_word)
    _g.word = new_word

    layout.update_letter()


def new_game(has_won: int = 0) -> None:
    """
    Start a new round.

    `has_won` :
        -1 : loosed
        0 : was not a round end
        1 : won
    """

    print("Starting a new round with has_won =", has_won)

    _g.current_difficulty += DIFFICULTY_CHANGE * has_won

    if _g.forced_next_word:
        set_word(_g.forced_next_word)
        _g.forced_next_word = None
    elif word_chooser.HAS_LAROUSSE:
        word_chooser.clear_queue() # Donne la prorité aux mots dont on a besoin maintenant plutôt que ceux dont on avait besoin.

        # Prend le mot trouvé à l'avance
        if _g.prechoosed_words.get(_g.current_difficulty, None): # Vérifie s'il y a un mot préchoisit (ni None ni liste vide)
            set_word(_g.prechoosed_words[_g.current_difficulty].pop())
        else:
            word_chooser.get_word_async(_g.current_difficulty)
            _g.state = STATE_WAITING_WORD
            draw_waiting_for_word()
            return # Empêche state = STATE_PLAYING, ainsi que d'appeler les mots par prévoyances, qui seraient réappelés sinon au prochain appel

        # Demande les mots en cas de défaite ou de victoire à l'avance
        win_difficulty, loose_difficulty = _g.current_difficulty + DIFFICULTY_CHANGE, _g.current_difficulty - DIFFICULTY_CHANGE
        if not _g.prechoosed_words.get(win_difficulty, None):
            word_chooser.get_word_async(win_difficulty)
        if not _g.prechoosed_words.get(loose_difficulty, None):
            word_chooser.get_word_async(loose_difficulty)

        # Il y a plus de chance de revenir à cette difficulté que de faire 2 victoires/2 défaites.
        word_chooser.get_word_async(_g.current_difficulty)
    else:
        set_word(word_chooser.get_word(_g.current_difficulty))


def main() -> None:
    """
    Boucle principale du jeu.
    Fusion des versions de Xenozk et IPreferGodot.
    """

    pygame.display.set_caption(WINDOW_TITLE)
    layout.update()

    new_game()

    if not IN_CODESPACE:
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.set_endevent(MUSIC_END)
        pygame.time.set_timer(MUSIC_END, 1, 1)

        # Précharge les musiques pour éviter un courte coupure lorsqu'on les joue pour la première fois.
        for music in MUSICS:
            pygame.mixer.music.load(music)
        for music in MUSIC_TRANSITIONS.values():
            pygame.mixer.music.load(music)

    next_frame: int = pygame.time.get_ticks() - 1
    had_latency: bool = False # Permet de n'afficher les chutes de FPS que s'il y a au moins 2 retards d'affilé. (ex : Déplacer la fenêtre gelait le programme, et affichait donc à chaque fois une chute de FPS)

    pygame.time.set_timer(SAY_ALIVE, 5_000)

    print("\n======================= Main loop start =======================\n")
    while True:
        for event in pygame.event.get():
            what = event.type
            if what == QUIT:
                pygame.quit()
                word_chooser.terminate()
                sys.exit()
            elif what == SAY_ALIVE:
                word_chooser.say_alive()
            elif what == WINDOW_SIZE_CHANGED:
                layout.update(event.x, event.y)
                if _g.state == STATE_WAITING_WORD:
                    draw_waiting_for_word()
            elif what == MUSIC_END:
                new_music = min(2, _g.word.wrong_guesses // 2) # On choisit la musique (max 3eme) en fonction de la "vie" restante
                if new_music == _g.music:
                    pygame.mixer.music.load(MUSICS[new_music])
                else:
                    # If it exist, load a transition, else directly play the new music
                    pygame.mixer.music.load(MUSIC_TRANSITIONS.get((_g.music, new_music), MUSICS[new_music]))
                    _g.music = new_music
                pygame.mixer.music.play()
            elif what == ANIMATION_END:
                if _g.state == STATE_LOOSE_ANIMATION:
                    new_game(-1)
                elif _g.state == STATE_WIN_ANIMATION:
                    new_game(1)
            elif what == TEXTINPUT:
                if _g.state == STATE_PLAYING:
                    handle_input(event.text)
                elif _g.state == STATE_DEV_CHOOSE_WORD:
                    _g.forced_next_word = Word(_g.forced_next_word.rich_word + event.text, -1, ["Inputed through developper mode."])
                    print(event)
            elif what == KEYDOWN:
                if is_state(STATE_WIN_ANIMATION, STATE_LOOSE_ANIMATION) and event.key == K_SPACE:
                    # Skip animation
                    pygame.time.set_timer(ANIMATION_END, 1, 1)

                # Shortcut to toggle the developper mode
                if event.key == K_KP_ENTER and event.mod & KMOD_ALT and event.mod & KMOD_CTRL and event.mod & KMOD_SHIFT:
                    _g.dev_mode = not _g.dev_mode
                    pygame.display.set_caption(WINDOW_TITLE + " (Developper mode)" if _g.dev_mode else WINDOW_TITLE)
                    print("Set developper mode to", _g.dev_mode)

                # Developper specific keybinds
                elif _g.dev_mode:
                    # Fast win
                    if event.key == K_RIGHT:
                        if event.mod & KMOD_SHIFT:
                            # Skip animation
                            new_game(1)
                        else:
                            _g.word.found_letters = _g.word.letter_set
                            check_win()

                    # Fast loose
                    elif event.key == K_LEFT:
                        if event.mod & KMOD_SHIFT:
                            # Skip animation
                            new_game(-1)
                        else:
                            _g.word.wrong_guesses = MAX_WRONG_GUESSES
                            check_loose()

                    # Fast choose a new word of the same difficulty
                    elif event.key == K_UP or event.key == K_RETURN:
                        new_game(0)

                    # Manually input next_word
                    elif event.key == K_DOWN:
                        if _g.state == STATE_DEV_CHOOSE_WORD:
                            new_game(0)
                        else:
                            _g.forced_next_word = Word("", -1, ["Inputed through developper mode."])
                            _g.state = STATE_DEV_CHOOSE_WORD

                    elif event.key == K_BACKSPACE and _g.state == STATE_DEV_CHOOSE_WORD:
                        _g.forced_next_word = Word(_g.forced_next_word.rich_word[:-1], -1, ["Inputed through developper mode."])

                    elif event.key == K_F4:
                        if event.mod & KMOD_SHIFT:
                            word_chooser.crash_subprocess()
                        else:
                            raise Exception("Fake crash created trough dev mode.")


        # On vide les mots préchoisis si le multiprocessing est activé
        if word_chooser.connection_parent:
            while word_chooser.connection_parent.poll():
                add_prechoosed_word(word_chooser.connection_parent.recv())

        # Mise à jour de la fenêtre
        if pygame.time.get_ticks() >= next_frame:
            if pygame.time.get_ticks() - next_frame > 1:
                if had_latency:
                    print("latency :", pygame.time.get_ticks() - next_frame)
                else:
                    had_latency = True
            else:
                had_latency = False
            next_frame = pygame.time.get_ticks() + FRAME_TIME

            if is_state(STATE_PLAYING, STATE_WIN_ANIMATION, STATE_LOOSE_ANIMATION):
                # clear l'écran
                SCREEN.fill(BACKGROUND_COLOR)
                # met les images et le mot à deviner
                draw_hangman()
                draw_word(*layout.word_pos)

                draw_wrong_letters()
                draw_difficulty()

                if _g.dev_mode: # On affiche des informations supplémentaires si le mode développeur est activé
                    SCREEN.blit(layout.small_font.render(_g.word.rich_word, True, BLACK), (7*layout.scale, 0))

                pygame.display.flip()
            elif _g.state == STATE_DEV_CHOOSE_WORD:
                SCREEN.fill(BACKGROUND_COLOR)
                SCREEN.blit(layout.small_font.render("Prochain mot : " + _g.forced_next_word.rich_word, True, BLACK), (7*layout.scale, 0))
                pygame.display.flip()


if __name__ == "__main__":
    if word_chooser.HAS_LAROUSSE:
        word_chooser.multiprocessing.freeze_support()
    word_chooser.init_process()
    main()
elif __name__ == "__mp_main__":
    # Ferme pygame si on a lancé ce script au lieu de start.py juste pour débugger un truc
    pygame.quit()