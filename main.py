from search import multiSearch
from similars import similar_artists
import threading

def main():
    thread1 = threading.Thread(target=multiSearch)
    thread2 = threading.Thread(target=similar_artists)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    multiSearch()

if __name__ == "__main__":
    main()
