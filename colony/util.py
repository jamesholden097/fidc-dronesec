import time
from tqdm import tqdm
import threading

def wait_while(method, delay=0.2):

    bar = [
        " [=     ]",
        " [ =    ]",
        " [  =   ]",
        " [   =  ]",
        " [    = ]",
        " [     =]",
        " [    = ]",
        " [   =  ]",
        " [  =   ]",
        " [ =    ]",
    ]
    i = 0

    while method():
        print(bar[i % len(bar)], end="\r")
        time.sleep(delay)
        i += 1

def t_bar(t):
    t = int(t)
    def timer(t):
        for i in tqdm(range(t * 100)):
            time.sleep(0.001)
            
    t1 = threading.Thread(target=timer,args=(t,),daemon=True)
    t1.start()
    #t1.join()

if __name__ == "__main__":
    t_bar(5)
    try:
        while True:
            print(time.time())
            time.sleep(0.5)
    except Exception:
        print("HO HO HO")
