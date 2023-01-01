
import random
import pygame

pygame.init()

window_size = (1920, 1080)
screen = pygame.display.set_mode(window_size)

# le titre 
pygame.display.set_caption("Hangman")

# type d'écriture et la taille
font = pygame.font.Font(None, 144)

# pas perdre de temps avec certaine couleur 
black = (0, 0, 0)
white = (255, 255, 255)

# toutes les images des hungmans de base c'etait autre chose mais ça me bloquais trop pour rien donc j'ai juste fait cela
hangman_images = [
    pygame.image.load("hangman0.png"),
    pygame.image.load("hangman1.png"),
    pygame.image.load("hangman2.png"),
    pygame.image.load("hangman3.png"),
    pygame.image.load("hangman4.png"),
    pygame.image.load("hangman5.png"),
    pygame.image.load("hangman6.png"),
]
#Pour ça oublie c'etait juste pour faire ce que t'avais fait mais t'as mieux fait et plus complexe
with open('text.txt', 'r') as f:
    words = f.read().split()

word = random.choice(words)

# nombre de guesses incorrect mis par defaut à 0
incorrect_guesses = 0

# liste des lettres correctement deviné
correct_letters = []

# liste des lettres déja essayer 
already_guessed = []

def draw_hangman():
    """aplique les images par rapport au nombres d'erreurs."""
    screen.blit(pygame.transform.scale(hangman_images[incorrect_guesses], (800, 800)), (150, 300))

def draw_word():
    """dessine le mot a deviné sur l'écran, avec les lettres correct montré et incorrect caché en _."""
    x = 960
    y = 240
    for letter in word:
        if letter in correct_letters:
            # met la lettre si elle a été corréctement deviné
            text = font.render(letter, True, black)
            screen.blit(text, (x, y))
            x += 144
        else:
            # reddésine un _ si la lettre n'as pas été deviné
            text = font.render("_", True, black)
            screen.blit(text, (x, y))
            x += 144

def handle_input(guess):
    """gère les entrées du joueur et met a jour l'état du jeu en fonction de la touche."""
    global incorrect_guesses
    if guess in word:
        # met la lettre correcte  dans la liste correct_letters
        correct_letters.append(guess)
    else:
        # ajoute 1 au nombre incorrecte et met la lettre dans la liste des deja deviné (mais faut)
        incorrect_guesses += 1
        already_guessed.append(guess)

def main():
    """Loop principal"""
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

main()

pygame.quit()
