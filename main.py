from src.app import main
import multiprocessing


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
