# Don't start the game if we are in the subprocess
if __name__ != "__mp_main__":
    import game
    game.word_chooser.multiprocessing.freeze_support()
    game.word_chooser.init_process()
    game.main()