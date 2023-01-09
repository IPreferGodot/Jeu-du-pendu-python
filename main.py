from path_rectifier import *
import pygame, sys, word_chooser, os
from pygame.locals import QUIT, KEYDOWN, USEREVENT
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
    HANGMAN_POS = (75, 150)
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

    # game
    DIFFICULTY_CHANGE = 1000
    STATE_PLAYING = 1
    STATE_WAITING_WORD = 2
    STATE_TRANSITION = 3

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


    # ----------------- Functions ------------------
    def vec_minus(a: tuple, b: tuple) -> tuple:
        return a[0]-b[0], a[1]-b[1]

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
        SCREEN.blit(HANGMAN_IMAGES[errors], HANGMAN_POS)


    # SIZE REDUCED
    # def draw_word(x: int = 960,  y: int = 240) -> None:
    def draw_word(x: int = 72,  y: int = 120) -> None:
        """Dessine le mot à deviner sur l'écran, avec les lettres correctes montrées et cells incorrectes transformées en "_"."""
        for letter in word:
            if letter in correct_letters:
                # Met la lettre si elle a été correctement devinée
                text = FONT.render(letter, True, BLACK)
                SCREEN.blit(text, (x, y + cos((pygame.time.get_ticks() + x*3)/500)*10))
                # SIZE REDUCED
                # x += 144
                x += 72
            else:
                # Redéssine un "_" si la lettre n'as pas été devinée
                text = FONT.render("_", True, BLACK)
                SCREEN.blit(text, (x, y + cos((pygame.time.get_ticks() + x*3)/500)*10))
                # SIZE REDUCED
                # x += 144
                x += 72


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
                elif what == MUSIC_END:
                    pygame.mixer.music.queue(resource_path(r"assets/music/Level 2.ogg"))
                elif state == STATE_PLAYING and what == KEYDOWN:
                    key = event.unicode # Prend la touche.

                    if key.isalpha(): # pour etre sur que la touche soit une lettre
                        key = key.lower() # met la touche en minuscule

                        if key not in already_guessed: # Vérifie que la lettre n'as pas déjà été utilisée
                            handle_input(key)
                            # Check si le joueur a gagné ou perdu
                            if set(word) == set(correct_letters):
                                # met le message et quitte le jeu après un temps impparti si le joueur a gagné
                                text = FONT.render("Gagné !", True, BLACK)
                                SCREEN.blit(text, (960, 540))
                                pygame.display.flip()
                                state = STATE_TRANSITION
                                # pygame.time.wait(3000)
                                new_game(1)
                                # pygame.event.post(pygame.event.Event(QUIT))
                            elif errors == len(HANGMAN_IMAGES):
                                # même chose mais s'l a perdu
                                text = FONT.render("Perdu...", True, BLACK)
                                SCREEN.blit(text, (960, 540))
                                pygame.display.flip()
                                state = STATE_TRANSITION
                                # pygame.time.wait(3000)
                                new_game(-1)
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

                if state == STATE_PLAYING:
                    # clear l'écran
                    SCREEN.fill(BACKGROUND_COLOR)
                    # met les images et le mot à deviner
                    draw_hangman()
                    draw_word()
                    pygame.display.flip()

                # Update l'écran

    '''
    def main_Xenozk() -> None:
        """Loop principale (Version de Xenozk)"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    # prend la touche.
                    key = event.unicode
                    # pour etre sur que la touche soit une lettre
                    if key.isalpha():
                        # met la touche en minuscule
                        key = key.lower()
                        # etre sur que la lettre n'as pas eté deja utiliser
                        if key not in already_guessed:
                            handle_input(key)
                            # Check si le joueur a gagné ou perdu
                            if set(word) == set(correct_letters):
                                # met le message et quitte le jeu après un temps apparti si le joueur a gagné
                                text = font.render("Gagné!", True, black)
                                screen.blit(text, (960, 540))
                                pygame.display.flip()
                                pygame.time.wait(3000)
                                running = False
                            elif incorrect_guesses == 7:
                                #meme chose mais si il a perdu
                                text = font.render("Perdu!", True, black)
                                screen.blit(text, (960, 540))
                                pygame.display.flip()
                                pygame.time.wait(3000)
                                running = False
                                #montre le mots
                                #correct_letters = list(word)
            # clear l'écran
            screen.fill((248,248,255))
            # met les images et le mot a étre deviner
            draw_hangman()
            draw_word()
            # Update l'écran
            pygame.display.flip()


    def main_old() -> None:
        """
        Version IPreferGodot construite à partir du premier jet de Xenozk.
        Ne contient aucun gameplay, juste des tests.
        """

        # Brouillon musique adaptative
        pygame.mixer.music.load(resource_path(r"assets/music/Level 1.ogg"))
        pygame.mixer.music.set_endevent(MUSIC_END)
        pygame.mixer.music.play()
        pygame.mixer.music.queue(resource_path(r"assets/music/Transition 1-2.ogg"))
        pygame.mixer.music.set_volume(0.5)

        test = 0
        next_frame = pygame.time.get_ticks() - 1

        DISPLAYSURF.fill(BACKGROUND_COLOR)
        pygame.display.flip()

        print("\n======================= Main loop start =======================\n")
        while True:
            if pygame.time.get_ticks() > next_frame:
                next_frame = pygame.time.get_ticks() + FRAME_TIME
                DISPLAYSURF.fill(BACKGROUND_COLOR)
                test += 1
                test %= 4
                DISPLAYSURF.blit(hangman_images[test], hangman_images[0].get_rect())
                pygame.display.update(hangman_images[0].get_rect())
                if test == 1:
                    word_chooser.get_word_async(1000)
                    print("prechoosed_words lenght :", len(prechoosed_words), "│ word :", repr(prechoosed_words.pop()) if len(prechoosed_words)!=0 else "EMPTY")

            # if word_chooser.word_queue:
            #     while not word_chooser.word_queue.empty():
            #         prechoosed_words.append(word_chooser.word_queue.get())

            if word_chooser.connection_parent:
                while word_chooser.connection_parent.poll():
                    prechoosed_words.append(word_chooser.connection_parent.recv())


            for event in pygame.event.get():
                what = event.type
                if what == QUIT:
                    pygame.quit()
                    word_chooser.terminate()
                    sys.exit()
                elif what == MUSIC_END:
                    pygame.mixer.music.queue(resource_path(r"assets/music/Level 2.ogg"))
    '''

    main()