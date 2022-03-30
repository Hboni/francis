import multiprocessing

from src.app import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
