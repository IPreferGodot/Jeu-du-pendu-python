from path_rectifier import *
import pygame, sys, word_chooser, os
from pygame.locals import QUIT, WINDOWSIZECHANGED as WINDOW_SIZE_CHANGED, KEYDOWN, USEREVENT, TEXTINPUT
from pygame.math import Vector2
from word_chooser import Word
from math import cos

IN_CODESPACE = os.environ.get("CODESPACES", False)

if __name__ == "__main__":
    if word_chooser.HAS_LAROUSSE:
        word_chooser.multiprocessing.freeze_support()

    print("Initializing pygame...", end="\r")
    pygame.init()
    pygame.display.set_caption("Pendu")
    print("Initializing pygame : OK")

    word_chooser.init_process()


    # ----------------- Constants ------------------
    # Pygame
    FRAME_TIME = int(1/60 * 1000) # In ms
    BACKGROUND_COLOR = (248, 248, 255)
    # SIZE REDUCED
    # WINDOW_ORIGINAL_SIZE = (1920, 1080)
    WINDOW_ORIGINAL_SIZE = Vector2(960, 540)
    # SIZE REDUCED
    # HANGMAN_ORIGINAL_SIZE = (800, 800)
    HANGMAN_ORIGINAL_SIZE = Vector2(400, 400)
    # SIZE REDUCED
    # HANGMAN_POS = (150, 300)
    SCREEN = pygame.display.set_mode(WINDOW_ORIGINAL_SIZE, pygame.RESIZABLE)
    FONT = pygame.font.Font(resource_path(r"assets\fonts\DotGothic16-Regular.ttf"), 100)
    FONT_SMALL = pygame.font.Font(resource_path(r"assets\fonts\DotGothic16-Regular.ttf"), 20)
    MAX_WRONG: int = 7
    HANGMAN_ORIGINAL_IMAGES: list[pygame.Surface] = [
        pygame.transform.scale(
            pygame.image.load(resource_path(f"assets/img/sprites/hangman/hangman{idx}.png")),
            HANGMAN_ORIGINAL_SIZE
        )
        for idx in range(MAX_WRONG)
    ]

    # colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)

    # game
    DIFFICULTY_CHANGE = 1000
    STATE_PLAYING = 1
    STATE_WAITING_WORD = 2
    STATE_TRANSITION = 3 # Unused
    STATE_WIN_ANIMATION = 4
    STATE_LOOSE_ANIMATION = 5

    # ------------------- Events -------------------
    MUSIC_END = USEREVENT + 1
    ANIMATION_END = MUSIC_END + 1

    # ----------------- Variables ------------------
    class Globals():
        """
        Contient les variables "globales" du programme.
        Permet de mieux distinguer quelles variables sont globales ou locales, si le mot-clé `global` est éloigné.
        """

        def __init__(self) -> None:
            self.state: int = STATE_WAITING_WORD
            self.current_difficulty: int = 0
            self.word = Word("non initialisé", 0, ["La variable `word` a été initialisée, mais aucun mot n'a été choisi."])

            self.prechoosed_words: dict[int, list[word_chooser.Word]] = {} # Stocke les mots obtenus en arrière plan
            self.word_history: list[word_chooser.Word] = [] # Garde une trace des mots déjà montrés au joueur, par exemple au cas où il veuille en revoir la définition.

            # self.wrong_guesses = 0 # nombre de lettres incorrectes (mis par defaut à 0)
            # self.found_letters = [] # liste des lettres correctement devinée
            # self.guessed_letters = [] # liste des lettres déjà essayées

    _g = Globals()


    class Layout():
        """
        Contient les informations relatives à la taille et la position des éléments à l'écran.
        """

        def __init__(self) -> None:
            self.scale = 1

            self.hangman_pos = (75, 150)
            self.hangman_size = HANGMAN_ORIGINAL_SIZE
            self.hangman_images = [] # On ne copie pas HANGMAN_ORIGINAL_IMAGES car la liste contiendrait les références aux mêmes surfaces

            self.update()

        def update(self, screen_width: int = None, screen_height: int = None) -> None:
            if screen_width == None:
                screen_width, screen_height = pygame.display.get_window_size()

            # On choisi la taille la plus grande possible qui ne dépasse pas verticalement/horizontalement
            self.scale = min(screen_width / WINDOW_ORIGINAL_SIZE.x, screen_height / WINDOW_ORIGINAL_SIZE.y)

            self.hangman_size = HANGMAN_ORIGINAL_SIZE * self.scale
            self.hangman_pos = (screen_width / 2 - self.hangman_size.x / 2, screen_height - self.hangman_size.y)
            self.hangman_images.clear()
            for original_surface in HANGMAN_ORIGINAL_IMAGES:
                self.hangman_images.append(pygame.transform.scale(original_surface, self.hangman_size))

    layout = Layout()


    # ----------------- Functions ------------------
    def vec_minus(a: tuple, b: tuple) -> tuple:
        """Substract to tuple like 2D vectors."""
        return a[0]-b[0], a[1]-b[1]


    def is_state(*wanted_states: int) -> bool:
        """Return True if the actual state is one of the wanted states."""
        return _g.state in wanted_states


    def add_prechoosed_word(word: word_chooser.Word) -> None:
        if word.difficulty in _g.prechoosed_words:
            _g.prechoosed_words[word.difficulty].append(word)
        else:
            _g.prechoosed_words[word.difficulty] = [word]

        if _g.state == STATE_WAITING_WORD and word.difficulty == _g.current_difficulty:
            new_game()


    def draw_hangman() -> None:
        """Aplique les images par rapport au nombre d'erreurs."""
        SCREEN.blit(layout.hangman_images[min(_g.word.wrong_guesses, MAX_WRONG - 1)], layout.hangman_pos)


    # SIZE REDUCED
    # def draw_word(x: int = 960,  y: int = 240) -> None:
    def draw_word(x: int = 72,  y: int = 120) -> None:
        """Dessine le mot à deviner sur l'écran, avec les lettres correctes montrées et celles incorrectes transformées en "_"."""
        for letter in _g.word.raw_word:
            found = letter in _g.word.found_letters

            text = FONT.render(
                # Déssine un "_" si la lettre n'as pas été devinée
                letter if found or _g.state == STATE_LOOSE_ANIMATION else "_",
                True,
                GREEN if _g.state == STATE_WIN_ANIMATION else BLACK if found or _g.state == STATE_PLAYING else RED
            )

            SCREEN.blit(text, (x, y + cos((pygame.time.get_ticks() + x*3)/500)*10))
            x += text.get_size()[0] + 10


    def draw_waiting_for_word() -> None:
        SCREEN.fill(WHITE)
        msg = FONT_SMALL.render("En attente d'un mot...", True, BLACK)
        # SCREEN.blit(msg, vec_minus(SCREEN.get_rect().center, msg.get_rect().center))
        SCREEN.blit(msg, msg.get_rect(center=SCREEN.get_rect().center).topleft)
        pygame.display.flip()


    def handle_input(guess: str) -> None:
        """Gère les entrées du joueur et met a jour l'état du jeu en fonction de la touche."""
        # global wrong_guesses

        _g.word.guessed_letters.append(guess)
        if guess in _g.word.letter_set:
            # Met la lettre correcte  dans la liste found_letters
            _g.word.found_letters.append(guess)
        else:
            # Ajoute 1 au nombre de lettres incorrectes et met la lettre dans la liste des déjà devinées (mais fausses)
            _g.word.wrong_guesses += 1


    def set_word(new_word: word_chooser.Word) -> None:
        """Change les variables globales lorsqu'un nouveau mot est choisi."""
        # global word, definitions

        _g.word_history.append(new_word)
        _g.word = new_word

    def new_game(has_won: int = 0) -> None:
        """
        Start a new round.

        `has_won` :
            -1 : loosed
            0 : was not a round end
            1 : won
        """

        print("Starting a new round with has_won =", has_won)

        # global wrong_guesses, current_difficulty, state

        _g.current_difficulty += DIFFICULTY_CHANGE * has_won

        # wrong_guesses = 0
        # guessed_letters.clear()
        # found_letters.clear()

        if word_chooser.HAS_LAROUSSE:
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
        else:
            set_word(word_chooser.get_word(_g.current_difficulty))

        _g.state = STATE_PLAYING


    def main() -> None:
        """Fusion des versions de Xenozk et IPreferGodot."""

        # global state

        layout.update()

        new_game()

        # Brouillon musique adaptative
        if not IN_CODESPACE:
            pygame.mixer.music.load(resource_path(r"assets/music/Level 1.ogg"))
            pygame.mixer.music.set_endevent(MUSIC_END)
            pygame.mixer.music.play()
            pygame.mixer.music.queue(resource_path(r"assets/music/Transition 1-2.ogg"))
            pygame.mixer.music.set_volume(0.5)

        next_frame: int = pygame.time.get_ticks() - 1

        print("\n======================= Main loop start =======================\n")
        while True:
            for event in pygame.event.get():
                what = event.type
                if what == QUIT:
                    pygame.quit()
                    word_chooser.terminate()
                    sys.exit()
                elif what == WINDOW_SIZE_CHANGED:
                    layout.update(event.x, event.y)
                elif what == MUSIC_END:
                    pygame.mixer.music.queue(resource_path(r"assets/music/Level 2.ogg"))
                elif what == ANIMATION_END:
                    if _g.state == STATE_LOOSE_ANIMATION:
                        new_game(-1)
                    elif _g.state == STATE_WIN_ANIMATION:
                        new_game(1)
                elif _g.state == STATE_PLAYING and what == KEYDOWN:
                    key = event.unicode # Prend la touche.

                    if key.isalpha(): # pour etre sur que la touche soit une lettre
                        key = key.lower() # met la touche en minuscule

                        if key not in _g.word.guessed_letters and key in word_chooser.ALLOWED_LETTERS: # Vérifie que la lettre n'as pas déjà été utilisée
                            handle_input(key)
                            # Check si le joueur a gagné ou perdu
                            if set(_g.word.found_letters) == _g.word.letter_set:
                                # met le message et quitte le jeu après un temps impparti si le joueur a gagné
                                # text = FONT.render("Gagné !", True, BLACK)
                                # SCREEN.blit(text, (960, 540))
                                # pygame.display.flip()
                                _g.state = STATE_WIN_ANIMATION
                                pygame.time.set_timer(ANIMATION_END, 3_000)
                                # pygame.time.wait(3000)
                                # new_game(1)
                                # pygame.event.post(pygame.event.Event(QUIT))
                            elif _g.word.wrong_guesses == MAX_WRONG:
                                # même chose mais s'l a perdu
                                # text = FONT.render("Perdu...", True, BLACK)
                                # SCREEN.blit(text, (960, 540))
                                # pygame.display.flip()
                                _g.state = STATE_LOOSE_ANIMATION
                                pygame.time.set_timer(ANIMATION_END, 3_000)
                                # found_letters.clear()
                                # found_letters.extend(set(word))
                                # clear l'écran
                                # SCREEN.fill(BACKGROUND_COLOR)
                                # met les images et le mot à deviner
                                # draw_hangman()
                                # draw_word()
                                # pygame.display.flip()
                                # pygame.time.wait(3000)
                                # new_game(-1)
                                # pygame.event.post(pygame.event.Event(QUIT))
                                #montre le mots
                                #found_letters = list(word)

            # On vide les mots préchoisis si le multiprocessing est activé
            if word_chooser.connection_parent:
                while word_chooser.connection_parent.poll():
                    add_prechoosed_word(word_chooser.connection_parent.recv())

            # Mise à jour de la fenêtre
            if pygame.time.get_ticks() >= next_frame:
                if pygame.time.get_ticks() - next_frame > FRAME_TIME:
                    print("latency :", pygame.time.get_ticks() - next_frame)
                next_frame = pygame.time.get_ticks() + FRAME_TIME

                if is_state(STATE_PLAYING, STATE_WIN_ANIMATION, STATE_LOOSE_ANIMATION):
                    # clear l'écran
                    SCREEN.fill(BACKGROUND_COLOR)
                    # met les images et le mot à deviner
                    draw_hangman()
                    draw_word()
                    pygame.display.flip()

                # Update l'écran


    main()