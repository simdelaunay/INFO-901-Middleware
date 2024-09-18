from threading import Thread
from time import sleep
from typing import List

from Process import Process
import sys


def launch(nbProcessToCreate: int, runningTime: int): 
    def createProcess(x: int):
        processes.append(Process("P" + str(x), nbProcessToCreate))

    processes = []

    processes_launches: List[Thread] = []

    for i in range(nbProcessToCreate):
        processes_launches.append(Thread(target=createProcess, args=(i,)))

    for p in processes_launches:
        p.start()
    for p in processes_launches:
        p.join()

    sleep(runningTime)

    for p in processes:
        p.stop()


def getParam(pos: int, default: int, base=10) -> int:
    if len(sys.argv) > pos:
        return int(sys.argv[pos], base)
    return default


if __name__ == '__main__':
    launch(getParam(1, 3), getParam(2, 15))