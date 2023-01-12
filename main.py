from path_rectifier import *
import pygame, sys, word_chooser, os
from pygame.locals import QUIT, WINDOWSIZECHANGED as WINDOW_SIZE_CHANGED, KEYDOWN, USEREVENT
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
    BACKGROUND_COLOR = (248,248,255)
    # SIZE REDUCED
    # WINDOW_SIZE = (1920, 1080)
    WINDOW_SIZE = (960, 540)
    # SIZE REDUCED
    # HANGMAN_SIZE = (800, 800)
    HANGMAN_SIZE = (400, 400)
    # SIZE REDUCED
    # HANGMAN_POS = (150, 300)
    SCREEN = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
    FONT = pygame.font.Font(resource_path(r"assets\fonts\DynaPuff.ttf"), 100)
    FONT_SMALL = pygame.font.Font(resource_path(r"assets\fonts\DynaPuff.ttf"), 20)
    MAX_ERRORS: int = 7
    HANGMAN_IMAGES: list[pygame.Surface] = [
        pygame.transform.scale(
            pygame.image.load(resource_path(f"assets/img/sprites/hangman/hangman{idx}.png")),
            HANGMAN_SIZE
        )
        for idx in range(MAX_ERRORS)
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

    # ------------------- Events -------------------
    MUSIC_END = USEREVENT + 1
    ANIMATION_END = MUSIC_END + 1

    # ----------------- Variables ------------------
    prechoosed_words: dict[int, list[word_chooser.Word]] = {} # Stocke les mots obtenus en arrière plan
    word_history: list[word_chooser.Word] = [] # Garde une trace des mots déjà montrés au joueur, par exemple au cas où il veuille en revoir la définition
    state: int = STATE_WAITING_WORD

    current_difficulty: int = 0

    word = "nonchoisi"
    definitions = ["Installez larousse-api pour avoir accès aux définitions des mots."]
    errors = 0 # nombre de lettres incorrectes (mis par defaut à 0)
    correct_letters = [] # liste des lettres correctement devinée
    already_guessed = [] # liste des lettres déjà essayées

    # Elements position
    hangman_pos = (75, 150)




    # ----------------- Functions ------------------
    def vec_minus(a: tuple, b: tuple) -> tuple:
        """Substract to tuple like 2D vectors."""
        return a[0]-b[0], a[1]-b[1]

    def is_state(*wanted_states: int) -> bool:
        """Return True if the actual state is one of the wanted states."""
        return state in wanted_states


    def update_elements_pos(width: int, height: int) -> None:
        global hangman_pos
        hangman_pos = (width // 2 - HANGMAN_SIZE[0] // 2, height - HANGMAN_SIZE[1])


    def add_prechoosed_word(word: word_chooser.Word) -> None:
        global state

        if word.difficulty in prechoosed_words:
            prechoosed_words[word.difficulty].append(word)
        else:
            prechoosed_words[word.difficulty] = [word]

        if state == STATE_WAITING_WORD and word.difficulty == current_difficulty:
            new_game()


    def draw_hangman() -> None:
        """Aplique les images par rapport au nombre d'erreurs."""
        SCREEN.blit(HANGMAN_IMAGES[min(errors, len(HANGMAN_IMAGES) - 1)], hangman_pos)


    # SIZE REDUCED
    # def draw_word(x: int = 960,  y: int = 240) -> None:
    def draw_word(x: int = 72,  y: int = 120) -> None:
        """Dessine le mot à deviner sur l'écran, avec les lettres correctes montrées et cells incorrectes transformées en "_"."""
        for letter in word:
            found = letter in correct_letters

            text = FONT.render(
                # Déssine un "_" si la lettre n'as pas été devinée
                letter if found or state == STATE_LOOSE_ANIMATION else "_",
                True,
                GREEN if state == STATE_WIN_ANIMATION else BLACK if found or state == STATE_PLAYING else RED
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
        global errors
        if guess in word:
            # Met la lettre correcte  dans la liste correct_letters
            correct_letters.append(guess)
        else:
            # Ajoute 1 au nombre de lettres incorrectes et met la lettre dans la liste des déjà devinées (mais fausses)
            errors += 1
            already_guessed.append(guess)


    def set_word(new_word: word_chooser.Word) -> None:
        """Change les variables globales lorsqu'un nouveau mot est choisi."""
        global word, definitions

        word_history.append(new_word)

        word = new_word.word
        definitions = new_word.definitions

    def new_game(has_won: int = 0) -> None:
        """Start a new round.

        `has_won` :
            -1 : loosed
            0 : was not a round end
            1 : won"""

        print("Starting a new round with has_won =", has_won)

        global errors, current_difficulty, state

        current_difficulty += DIFFICULTY_CHANGE * has_won

        errors = 0
        already_guessed.clear()
        correct_letters.clear()

        if word_chooser.HAS_LAROUSSE:
            # Prend le mot trouvé à l'avance
            if prechoosed_words.get(current_difficulty, None): # Vérifie s'il y a un mot préchoisit (ni None ni liste vide)
                set_word(prechoosed_words[current_difficulty].pop())
            else:
                word_chooser.get_word_async(current_difficulty)
                state = STATE_WAITING_WORD
                draw_waiting_for_word()
                return # Empêche state = STATE_PLAYING, ainsi que d'appeler les mots par prévoyances, qui seraient réappelés sinon au prochain appel

            # Demande les mots en cas de défaite ou de victoire à l'avance
            win_difficulty, loose_difficulty = current_difficulty + DIFFICULTY_CHANGE, current_difficulty - DIFFICULTY_CHANGE
            if not prechoosed_words.get(win_difficulty, None):
                word_chooser.get_word_async(win_difficulty)
            if not prechoosed_words.get(loose_difficulty, None):
                word_chooser.get_word_async(loose_difficulty)
        else:
            set_word(word_chooser.get_word(current_difficulty))

        state = STATE_PLAYING


    def main() -> None:
        """Fusion des versions de Xenozk et IPreferGodot."""

        global state

        update_elements_pos(*pygame.display.get_window_size())

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
                    update_elements_pos(event.x, event.y)
                elif what == MUSIC_END:
                    pygame.mixer.music.queue(resource_path(r"assets/music/Level 2.ogg"))
                elif what == ANIMATION_END:
                    if state == STATE_LOOSE_ANIMATION:
                        new_game(-1)
                    elif state == STATE_WIN_ANIMATION:
                        new_game(1)
                elif state == STATE_PLAYING and what == KEYDOWN:
                    key = event.unicode # Prend la touche.

                    if key.isalpha(): # pour etre sur que la touche soit une lettre
                        key = key.lower() # met la touche en minuscule

                        if key not in already_guessed: # Vérifie que la lettre n'as pas déjà été utilisée
                            handle_input(key)
                            # Check si le joueur a gagné ou perdu
                            if set(word) == set(correct_letters):
                                # met le message et quitte le jeu après un temps impparti si le joueur a gagné
                                # text = FONT.render("Gagné !", True, BLACK)
                                # SCREEN.blit(text, (960, 540))
                                # pygame.display.flip()
                                state = STATE_WIN_ANIMATION
                                pygame.time.set_timer(ANIMATION_END, 3_000)
                                # pygame.time.wait(3000)
                                # new_game(1)
                                # pygame.event.post(pygame.event.Event(QUIT))
                            elif errors == len(HANGMAN_IMAGES):
                                # même chose mais s'l a perdu
                                # text = FONT.render("Perdu...", True, BLACK)
                                # SCREEN.blit(text, (960, 540))
                                # pygame.display.flip()
                                state = STATE_LOOSE_ANIMATION
                                pygame.time.set_timer(ANIMATION_END, 3_000)
                                # correct_letters.clear()
                                # correct_letters.extend(set(word))
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
                                #correct_letters = list(word)

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