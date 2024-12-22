from threading import Thread
from threading import Semaphore
import time
import random

remote = Semaphore(1)   
mutex = Semaphore(1)    
outside = Semaphore(0)  
canal_atual = 0         
tv = 0                  
waiting = 0             

def myTimer(n):
    start = time.time()
    passed_time = 0

    while (passed_time < n):
        passed_time = time.time() - start

class Hospede():

    def __init__(self, canal, name, watch_time, rest_time):
        self.canal = canal
        self.name = name
        self.watch_time = watch_time
        self.rest_time = rest_time

    def check_tv_is_available(self):
        global tv, waiting

        if tv == 0:
            remote.release()
            if waiting > 0:
                outside.release(waiting)
                waiting = 0
    
    def watch(self):
        print(f'{self.name} está assistindo no canal {self.canal}')
        myTimer(self.watch_time)

    def check_tv(self):
        global canal_atual, tv, waiting

        while True:

            mutex.acquire()
            print(f'{self.name} chegou para assistir')

            if tv == 0:
                remote.acquire()
                canal_atual = self.canal
                print(f'{self.name} pegou o controle e pos no canal {self.canal}')

            if self.canal == canal_atual:
                
                tv+=1
                mutex.release()

                self.watch()

                mutex.acquire()
                tv-=1
                print(f'{self.name} saiu da TV')
                self.check_tv_is_available()
                mutex.release()
                myTimer(self.rest_time)

            else:
                waiting+=1
                mutex.release()
                print(f'{self.name} está esperando')
                outside.acquire()

hospede1 = Hospede(1, 'h1', 1, 1)
hospede2 = Hospede(2, 'h2', 2, 2)

t1 = Thread(target=hospede1.check_tv)
t2 = Thread(target=hospede2.check_tv)

t1.start()
t2.start()

t1.join()
t2.join()