import threading
import time
from typing import Callable, List, Optional, Sequence

import numpy as np

from colony.drone import Drone
from colony.datatype import Vector3

# TODO: Monitor distance between every drones, if below threshold issue a BOROSORO warning
# TODO: If failsafe triggers, handle that

class Swarm:
    def __init__(self, connections: Sequence[str], reference: Vector3):
        self.num_drones = len(connections)
        self.connections = connections
        self.reference = reference
        self.drones: List[Drone] = []
        self.active_drones: List[Drone] = []
        self.rouge_drones: List[Drone] = []

    def connect(self):

        print("Connecting to Swarm")
        for idx, conn in enumerate(self.connections):
            drone = Drone(conn, idx)
            drone.connect()
            self.drones.append(drone)
            time.sleep(0.1)
        print("Connecting to drones -> DONE")


    def disconnect(self):
        print("Disconnecting from Swarm")
        for drone in self.drones:
            drone.disconnect()
            time.sleep(0.1)
        print("Disconnecting to Swarm -> DONE")

    def do_parallel(self, procedure: Callable[[Drone], None], delay: Optional[float] = None):

        parallel_threads = list(map(lambda drone: threading.Thread(target=procedure,args=(drone,),daemon=True,),self.drones,))

        for thread in parallel_threads:
            thread.start()

            if delay is not None:
                time.sleep(delay)

        for thread in parallel_threads:
            thread.join()

    def do_serial(self, procedure: Callable[[Drone], None]):
        for drone in self.drones:
            procedure(drone)


if __name__ == "__main__":
    LAT_REF = 23.9475462
    LON_REF = 90.3808038

    connection_strings = [
        "tcp:127.0.0.1:5762"]#,
        #"tcp:127.0.0.1:5772",
        #"tcp:127.0.0.1:5782",
    #]
    swarm = Swarm(connection_strings, np.asarray((LAT_REF, LON_REF, 0.0)))
    swarm.connect()
    # swarm.do_parallel(lambda d: d.set_gcs_failsafe())
    swarm.do_parallel(lambda drone: drone.set_mode("GUIDED"))
    swarm.do_parallel(lambda drone: drone.arm())
    swarm.do_parallel(lambda drone: drone.takeoff(5))
    time.sleep(10)
    swarm.do_serial(lambda drone: drone.comeback(), delay=1.0)
    swarm.disconnect()
