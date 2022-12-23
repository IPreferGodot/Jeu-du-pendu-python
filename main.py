import pygame, sys, os, time
from word_chooser import choose_word
from pygame.locals import QUIT

def resource_path(relative_path):
    try:
    # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS  # type: ignore
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

pygame.init()

BACKGROUND_COLOR = 70,  70,  70

DISPLAYSURF = pygame.display.set_mode((400, 400))
pygame.display.set_caption("Hangman")

# ----- XenozK Version -----------------------------

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
    image = pygame.image.load(resource_path(f"assets/hangman/hangman{i}.png"))
    image = pygame.transform.scale(image, (hangman_largeur, hangman_longeur))
    hangman_images.append(image)



test = 0
while True:
    print(choose_word(1000))
    DISPLAYSURF.fill(BACKGROUND_COLOR)
    test += 1
    test %= 4
    DISPLAYSURF.blit(hangman_images[test], hangman_images[0].get_rect())

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    pygame.display.update()
    time.sleep(0.6)