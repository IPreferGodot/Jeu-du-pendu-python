# Don't start the game if we are in the subprocess
if __name__ != "__mp_main__":
    import game
    game.main()