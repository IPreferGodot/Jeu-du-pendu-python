from path_rectifier import *
import pygame, sys, time, word_chooser
from word_chooser import get_word_async as get_word
from pygame.locals import QUIT

if __name__ == "__main__":
    word_chooser.multiprocessing.freeze_support()
    print("initializing pygame...")
    pygame.init()
    print("initializing word_chooser...")
    word_chooser.init_process()

    # ----------------- Constants ------------------
    FRAME_TIME = 1/2
    BACKGROUND_COLOR = 70,  70,  70

    DISPLAYSURF = pygame.display.set_mode((400, 400))
    pygame.display.set_caption("Hangman")

    # ------------------- Events -------------------
    MUSIC_END = pygame.USEREVENT + 1

    # ----------------- Variables ------------------
    prechoosed_words: list[str] = []

    # --------------- XenozK Version ---------------

    # la taille de la page et le titre
    #window_size = (400, 400)
    #window_title = "Hangman"
    #screen = pygame.display.set_mode(window_size)
    #pygame.display.set_caption(window_title)

    # couleur du background
    bg_color = (255, 255, 255)

    # couleur du text
    font = pygame.font.Font(None, 32)
    text_color = (0, 0, 0)


    hangman_largeur = 200
    hangman_longeur = 300

    #prend les images
    hangman_images = []
    for i in range(4):
        image = pygame.image.load(resource_path(f"assets/img/sprites/hangman/hangman{i}.png"))
        image = pygame.transform.scale(image, (hangman_largeur, hangman_longeur))
        hangman_images.append(image)


    pygame.mixer.music.load(resource_path(r"assets/music/Level 1.ogg"))
    pygame.mixer.music.set_endevent(MUSIC_END)
    pygame.mixer.music.play()
    pygame.mixer.music.queue(resource_path(r"assets/music/Transition 1-2.ogg"))
    pygame.mixer.music.set_volume(0.5)

    test = 0
    next_frame = time.time() - 1

    while True:
        if time.time() > next_frame:
            next_frame = time.time() + FRAME_TIME
            DISPLAYSURF.fill(BACKGROUND_COLOR)
            test += 1
            test %= 4
            DISPLAYSURF.blit(hangman_images[test], hangman_images[0].get_rect())
            if test == 1:
                word_chooser.get_word_async(1000)
                print("prechoosed_words lenght :", len(prechoosed_words), "| word :", repr(prechoosed_words.pop()) if len(prechoosed_words)!=0 else "EMPTY")

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

        pygame.display.update()