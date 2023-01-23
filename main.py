from path_rectifier import resource_path as res_path
import pygame, sys, word_chooser, os
from pygame.locals import QUIT, WINDOWSIZECHANGED as WINDOW_SIZE_CHANGED, KEYDOWN, USEREVENT, TEXTINPUT, KMOD_ALT, KMOD_CTRL, KMOD_SHIFT, K_KP_ENTER, K_LEFT, K_RIGHT, K_DOWN, K_UP, K_SPACE
from pygame.math import Vector2
from word_chooser import Word
from math import cos

IN_CODESPACE = os.environ.get("CODESPACES", False)

if __name__ == "__main__":
    if word_chooser.HAS_LAROUSSE:
        word_chooser.multiprocessing.freeze_support()

    print("Initializing pygame...", end="\r")
    pygame.init()
    print("Initializing pygame : OK")

    word_chooser.init_process()


    # ----------------- Constants ------------------
    # colors
    BACKGROUND_COLOR = (248, 248, 255)
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)

    # game
    MAX_WRONG_GUESSES = 7
    DIFFICULTY_CHANGE = 1000

    # states
    STATE_PLAYING = 1
    STATE_WAITING_WORD = 2
    STATE_TRANSITION = 3 # Unused
    STATE_WIN_ANIMATION = 4
    STATE_LOOSE_ANIMATION = 5

    # Path
    FONT_PATH = res_path(r"assets\fonts\DotGothic16-Regular.ttf")

    # Pygame
    FRAME_TIME = int(1/60 * 1000) # In ms
    WINDOW_TITLE = "Jeu du pendu"

    WINDOW_ORIGINAL_SIZE = Vector2(960, 540)
    HANGMAN_ORIGINAL_SIZE = Vector2(400, 400)

    BIG_FONT_ORIGINAL_SIZE = 100
    SMALL_FONT_ORIGINAL_SIZE = 20
    BIG_FONT_SPACING = 10
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
            self.word: Word = Word("non initialisé", 0, ["La variable `word` a été initialisée, mais aucun mot n'a été choisi."])

            self.prechoosed_words: dict[int, list[word_chooser.Word]] = {} # Stocke les mots obtenus en arrière plan
            self.word_history: list[word_chooser.Word] = [] # Garde une trace des mots déjà montrés au joueur, par exemple au cas où il veuille en revoir la définition.

            # self.wrong_guesses = 0 # nombre de lettres incorrectes (mis par defaut à 0)
            # self.found_letters = [] # liste des lettres correctement devinée
            # self.guessed_letters = [] # liste des lettres déjà essayées

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

            self.wrong_letters_pos = Vector2(7*self.scale, screen_height - SMALL_FONT_HEIGHT*self.scale)


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
        if word.difficulty in _g.prechoosed_words:
            _g.prechoosed_words[word.difficulty].append(word)
        else:
            _g.prechoosed_words[word.difficulty] = [word]

        if _g.state == STATE_WAITING_WORD and word.difficulty == _g.current_difficulty:
            new_game()


    def draw_hangman() -> None:
        """Aplique les images par rapport au nombre d'erreurs."""
        SCREEN.blit(layout.hangman_images[min(_g.word.wrong_guesses, MAX_WRONG_GUESSES - 1)], layout.hangman_pos)


    def draw_word(x: int|None = None,  y: int|None = None) -> None:
        """Dessine le mot à deviner sur l'écran, avec les lettres correctes montrées et celles incorrectes transformées en "_"."""
        if x == None:
            x, y = layout.word_pos

        for letter_surface in layout.letters:
            SCREEN.blit(letter_surface, (x, y + cos((pygame.time.get_ticks() + x*3)/500)*10*layout.letter_scale))
            x += layout.letter_width


    def draw_wrong_letters() -> None:
        SCREEN.blit(layout.small_font.render(str(_g.word.wrong_letters), True, RED), layout.wrong_letters_pos)


    def draw_waiting_for_word() -> None:
        SCREEN.fill(WHITE)
        msg = layout.small_font.render("En attente d'un mot...", True, BLACK)
        # SCREEN.blit(msg, vec_minus(SCREEN.get_rect().center, msg.get_rect().center))
        SCREEN.blit(msg, msg.get_rect(center=SCREEN.get_rect().center).topleft)
        pygame.display.flip()


    def check_win() -> bool:
        # Vérifie si le joueur a gagné ou perdu
        if set(_g.word.found_letters) == _g.word.letter_set:
            _g.state = STATE_WIN_ANIMATION
            if not IN_CODESPACE:
                SOUND_WIN.play()
            pygame.time.set_timer(ANIMATION_END, 3_000, 1)
            layout.update_letter()
            return True
        return False

    def check_loose() -> bool:
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
        # global wrong_guesses

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
        # global word, definitions
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

        # global wrong_guesses, current_difficulty, state

        _g.current_difficulty += DIFFICULTY_CHANGE * has_won

        # wrong_guesses = 0
        # guessed_letters.clear()
        # found_letters.clear()

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
        """Fusion des versions de Xenozk et IPreferGodot."""

        # global state

        pygame.display.set_caption(WINDOW_TITLE)
        layout.update()

        new_game()

        if not IN_CODESPACE:
            # Brouillon musique adaptative
            pygame.mixer.music.load(res_path(r"assets/music/Level 1.ogg"))
            pygame.mixer.music.set_endevent(MUSIC_END)
            pygame.mixer.music.play()
            pygame.mixer.music.queue(res_path(r"assets/music/Transition 1-2.ogg"))
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
                    if _g.state == STATE_WAITING_WORD:
                        draw_waiting_for_word()
                elif what == MUSIC_END:
                    pygame.mixer.music.queue(res_path(r"assets/music/Level 2.ogg"))
                elif what == ANIMATION_END:
                    if _g.state == STATE_LOOSE_ANIMATION:
                        new_game(-1)
                    elif _g.state == STATE_WIN_ANIMATION:
                        new_game(1)
                elif what == TEXTINPUT:
                    if _g.state == STATE_PLAYING:
                        char = event.text
                        #if char.isalpha(): # pour etre sur que la touche soit une lettre
                        handle_input(char)
                elif what ==KEYDOWN:
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
                        elif event.key == K_UP:
                            new_game(0)

                        # Manually input next_word
                        elif event.key == K_DOWN:
                            _g.forced_next_word = Word(input("Entrez le prochain mot que vous voulez : "), -1, ["Inputed through developper mode."])
                            new_game(0)


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
                    draw_word(*layout.word_pos)

                    draw_wrong_letters()

                    if _g.dev_mode: # On affiche des informations supplémentaires si le mode développeur est activé
                        SCREEN.blit(layout.small_font.render(_g.word.rich_word, True, BLACK), (7*layout.scale, 0))

                    pygame.display.flip()

                # Update l'écran


    main()