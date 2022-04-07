import datetime
import random
import time
import threading
import pygame
import sys
import logging
import os


# Variables for Traffic Signals
signals = []
num_signals = 3     # Total number of signals used in the simulation
GreenLight = {0: 10, 1: 10, 2: 15}      # Green light time for each signal
RedLight = 60
YellowLight = 5
GreenCurrent = 0    # Indicating which signal post light is currently Green
YellowCurrent = 0   # If the Yellow light for the signal post is active or not
NextGreen = (GreenCurrent + 1) % num_signals    # Indicate the next green signal
simulation_Time = 50   # Total simulation time
Elapsed_Time = 0    # Time elapsed

# Coordinates for the traffic signal posts, signal timer and the simulation timer
Traffic_light_co_ord = [(510, 600), (1130, 350), (515, 762), (1135, 200)]
Signal_Tout_co_ord = [(530, 615), (1150, 365), (490, 777), (1115, 215)]
Elapsed_Time_co_ord = (90, 60)

# Coordinates for the vehicles to start from
x = {'EB': [0, 0, 0, 0], 'WB': [1900, 1900, 1900, 1900]}  # (EB:EastBound, WB:WestBound) vehicles
y = {'EB': [515, 520, 610, 690], 'WB': [420, 420, 360, 270]}

vehicleTypes = {0: 'bike', 1: 'car', 2: 'bus', 3: 'truck'}  # Types of Vehicles used in this simulation
speed = {'bike': 8, 'car': 7.5, 'bus': 7, 'truck': 7, 'pedestrian': 5}  # Average speeds for all the actors used
directionNumbers = {0: 'EB', 1: 'WB'}
vehicles = {'EB': {0: [], 1: [], 2: [], 3: [], 'crossed': 0, 'turned': 0}, 'WB': {0: [], 1: [], 2: [], 3: [], 'crossed': 0, 'turned': 0}}
EB_uturn_counter = 0
WB_uturn_counter = 0

# Coordinates of stop lines at the signal post before the intersection
stopLines = {'EB': 490, 'WB': 1200}
defaultStop = {'EB': 480, 'WB': 1210}
stopGap = 20    # Distance between vehicles at the signal
moveGap = 20    # distance between vehicles when making a U-turn

vehiclesTurned = {'EB': {1:[], 2: [], 3: []}, 'WB': {1:[], 2: [], 3: []}}   # Turned vehicles count
rotationAngle = 20  # Rotation angle for the vehicle per iteration

# Variables for pedestrians
ped_directionNumbers = {0: 'NB', 1: 'SB'}   # NB: North bound, SB:south bound pedestrians
#   starting coordinated for pedestrians
ped_x = {'NB': 530, 'SB': 1150}
ped_y = {'NB': 1000, 'SB': 0}
pedestrians = {'NB': {0: [], 'crossed': 0}, 'SB': {0: [], 'crossed': 0}}    # pedestrians count
ped_stopLines = {'NB': 770, 'SB': 240}      # stopping distance behind the signal post
ped_defaultStopLines = {'NB': 780, 'SB': 230}
ped_stopGap = 10    # distance between the stopped pedestrians at the signal
#   counters for Simulation Stats
lane1_counter = 0
lane2_counter = 0
lane3_counter = 0
ped_NB_counter = 0
ped_SB_counter = 0
Total_ped_counter = 0
bike_counter = 0
car_counter = 0
bus_counter = 0
truck_counter = 0
vehicle_total_counter = 0
EB_counter = 0
WB_counter = 0

# Running the pygame library
pygame.init()
simulation = pygame.sprite.Group()      # For Vehicles
simulation2 = pygame.sprite.Group()     # For Pedestrians

# Log file initialization
LogFileName = datetime.datetime.now().strftime("%y%m%d_%H_%M_%S") + 'Traffic simulation.txt'
logging.basicConfig(filename=LogFileName, filemode='w', format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger()


class TrafficSignal:
    def __init__(self, red, yellow, green):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.signalText = ""


class Pedestrians(pygame.sprite.Sprite):
    def __init__(self, ped_direction_num, ped_direction):
        pygame.sprite.Sprite.__init__(self)
        self.pedDirection = ped_direction
        self.pedDirectionNum = ped_direction_num
        self.pedx = ped_x[ped_direction]
        self.pedy = ped_y[ped_direction]
        pedestrians[ped_direction][0].append(self)
        self.item = len(pedestrians[ped_direction][0]) - 1
        self.speed = speed['pedestrian']
        self.crossed = 0
        path = "images/" + ped_direction + "/" + "pedestrian.png"
        self.image = pygame.image.load(path)

        # To specify the pedestrians queueing order
        if len(pedestrians[ped_direction][0]) > 1 and pedestrians[ped_direction][0][self.item - 1].crossed == 0:
            if ped_direction == 'NB':
                self.stop = pedestrians[ped_direction][0][self.item - 1].stop + pedestrians[ped_direction][0][self.item - 1].image.get_rect().height + ped_stopGap
            elif ped_direction == 'SB':
                self.stop = pedestrians[ped_direction][0][self.item - 1].stop - pedestrians[ped_direction][0][self.item - 1].image.get_rect().height - ped_stopGap
        else:
            self.stop = ped_defaultStopLines[ped_direction]

        # New start and Stop Coordinates for pedestrians
        if ped_direction == 'NB':
            temp = self.image.get_rect().height + ped_stopGap
            ped_y[ped_direction] += temp
        elif ped_direction == 'SB':
            temp = self.image.get_rect().height + ped_stopGap
            ped_y[ped_direction] -= temp
        simulation2.add(self)

    def render(self, screen):
        screen.blit(self.image, (self.pedx, self.pedy))

    def ped_move(self):
        #   Check: if pedestrians have crossed the stop line before the red signal appeared
        #   If condition for people starting at the south or North junction

        #   Check: if the pedestrian has crossed the stop line and the pedestrian signal is green(not yellow yet)
        #   Check: To check is the pedestrian first in the queue or later +/- stop gap between them based on SB/NB
        #   If yes, then he is free to cross the road
        if self.pedDirection == 'NB':
            if self.crossed == 0 and self.pedy < ped_stopLines[self.pedDirection]:
                self.crossed = 1    # if yes, then crossed = 1
            if (self.pedy >= self.stop or (self.crossed == 1) or (GreenCurrent == 2 and YellowCurrent == 0)) and (self.item == 0 or self.pedy > (pedestrians[self.pedDirection][0][self.item - 1].pedy + pedestrians[self.pedDirection][0][self.item - 1].image.get_rect().height + ped_stopGap)):
                self.pedy -= self.speed
        elif self.pedDirection == 'SB':
            if self.crossed == 0 and self.pedy + self.image.get_rect().height > ped_stopLines[self.pedDirection]:
                self.crossed = 1
            if (self.pedy + self.image.get_rect().height <= self.stop or (self.crossed ==1) or (GreenCurrent == 2 and YellowCurrent == 0)) and (self.item == 0 or self.pedy + self.image.get_rect().height < (pedestrians[self.pedDirection][0][self.item - 1].pedy - ped_stopGap)):
                self.pedy += self.speed


class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction, will_turn):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speed[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.willTurn = will_turn
        vehicles[direction][lane].append(self)
        self.item = len(vehicles[direction][lane]) - 1
        self.crossed = 0
        self.turned = 0
        self.uTurn = 0
        self.rotateAngle = 0
        self.crossedIndex = 0
        path = "images/" + direction + "/" + vehicleClass + ".png"      # Location: Vehicle Images
        self.originalImage = pygame.image.load(path)
        self.image = pygame.image.load(path)

        #   Vehicle queueing order at the stop line for both East and West bound vehicles
        if len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.item - 1].crossed == 0:
            if direction == 'EB':
                self.stop = vehicles[direction][lane][self.item - 1].stop - vehicles[direction][lane][self.item - 1].image.get_rect().width - stopGap
            elif direction == 'WB':
                self.stop = vehicles[direction][lane][self.item - 1].stop + vehicles[direction][lane][self.item - 1].image.get_rect().width + stopGap
        else:
            self.stop = defaultStop[direction]

        #   New starting and stopping coordinates
        #   Check: Setting coordinates for the vehicles in the queue
        if direction == 'EB':
            if len(vehicles[direction][lane]) > 1:
                flag = self.image.get_rect().width + stopGap
                x[direction][lane] -= flag
            else:
                x[direction][lane] -= stopGap
        elif direction == 'WB':
            if len(vehicles[direction][lane]) > 1:
                flag = self.image.get_rect().width + stopGap
                x[direction][lane] += flag
            else:
                x[direction][lane] += stopGap
        simulation.add(self)

    def render(self, screen):
        screen.blit(self.image, (self.x, self.y))
        
    def move(self):
        global WB_uturn_counter, EB_uturn_counter, EB_counter, WB_counter
        if self.direction == 'EB':
            EB_counter += 1
            if self.crossed == 0 and self.x + self.image.get_rect().width > stopLines[self.direction]:
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
            if self.willTurn == 1 and self.lane == 1:   # Only vehicles in lane1 are allowed to turn
                if self.x >= stopLines[self.direction]:
                    vehicles[self.direction]['turned'] += 1
                    self.uTurn = 1

                if self.uTurn == 1:
                    if self.turned == 0:
                        self.rotateAngle += rotationAngle
                        self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                        if self.rotateAngle < 90: # shifting coordinates 20 degrees at a time
                            self.y -= 10
                            self.x += 15
                        else:
                            self.y -= 10
                            self.x -= 15
                        if self.rotateAngle == 180:   # Check: if the vehicle has made a uTurn
                            self.turned = 1
                            self.uTurn = 0
                            EB_uturn_counter +=1
                            #   Keeping track of vehicles that turned
                            vehiclesTurned[self.direction][self.lane].append(self)
                            self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
            #   Code to let vehicles make a free choice to go straight or make a uTurn
            if (self.x + self.image.get_rect().width <= self.stop or self.crossed == 1 or (
                    GreenCurrent == 0 and YellowCurrent == 0)) and (self.item == 0 or self.x + self.image.get_rect().width < (
                    vehicles[self.direction][self.lane][self.item - 1].x - moveGap) or vehicles[self.direction][self.lane][self.item-1].turned == 1):
                if self.turned == 1:
                    self.x -= self.speed
                else:
                    self.x += self.speed

        elif self.direction == 'WB':
            WB_counter += 1
            if self.crossed == 0 and self.x <= stopLines[self.direction]:
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1

            if self.willTurn == 1 and self.lane == 1:
                if self.x <= stopLines[self.direction]:
                    vehicles[self.direction]['turned'] += 1
                    self.uTurn = True

                if self.uTurn is True:
                    if self.turned == 0:
                        self.rotateAngle += rotationAngle
                        self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                        if self.rotateAngle < 90:
                            self.y += 15
                            self.x -= 20
                        else:
                            self.y += 10
                            self.x += 20
                        if self.rotateAngle == 180:
                            self.turned = 1
                            self.uTurn = 0
                            WB_uturn_counter += 1
                            vehiclesTurned[self.direction][self.lane].append(self)
                            self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
            if (self.x >= self.stop or self.crossed == 1 or (GreenCurrent == 1 and YellowCurrent == 0)) and (self.item == 0 or self.x > (
                    vehicles[self.direction][self.lane][self.item - 1].x + vehicles[self.direction][self.lane][self.item - 1].image.get_rect().width + moveGap) or vehicles[self.direction][self.lane][self.item-1].turned == 1):
                if self.turned == 1:
                    self.x += self.speed
                else:
                    self.x -= self.speed


def initialize():
    #   Initializing the signal order
    logger.info('Initializing the signal sequence')
    signal_post1 = TrafficSignal(0, YellowLight, GreenLight[0])
    signals.append(signal_post1)
    signal_post2 = TrafficSignal(signal_post1.yellow + signal_post1.green, YellowLight, GreenLight[1])
    signals.append(signal_post2)
    signals_post3 = TrafficSignal(RedLight, YellowLight, GreenLight[2])
    signals.append(signals_post3)

    repeat()


def repeat():
    #   Recursive function between the signal orders
    global GreenCurrent, YellowCurrent, NextGreen
    while signals[GreenCurrent].green > 0:  # while the timer of current green signal is not zero
        update_signal_timers()
        time.sleep(1)
    YellowCurrent = 1  # set yellow signal on
    # reset stop coordinates of lanes and vehicles
    for i in range(0, 3):
        if GreenCurrent == 2:
            continue
        for vehicle in vehicles[directionNumbers[GreenCurrent]][i]:
            vehicle.stop = defaultStop[directionNumbers[GreenCurrent]]
    while signals[GreenCurrent].yellow > 0:  # while the timer of current yellow signal is not zero
        update_signal_timers()
        time.sleep(1)
    YellowCurrent = 0  # set yellow signal off
    if GreenCurrent == 0:
        logging.info(f'Signalpost 1 is active')
    # Reset all signals to default time
    signals[GreenCurrent].green = GreenLight[GreenCurrent]
    signals[GreenCurrent].yellow = YellowLight
    signals[GreenCurrent].red = RedLight
    GreenCurrent = NextGreen  # Next Green signal
    NextGreen = (GreenCurrent + 1) % num_signals  # set next green signal as green
    # set the red time of next to next signal as (yellow time + green time) of next signal
    signals[NextGreen].red = signals[GreenCurrent].yellow + signals[GreenCurrent].green
    repeat()


def update_signal_timers():
    for i in range(0, num_signals):
        if i == GreenCurrent:
            if YellowCurrent == 0:
                signals[i].green -= 1
            else:
                signals[i].yellow -= 1
        else:
            signals[i].red -= 1


def generate_vehicles():
    global lane1_counter, lane2_counter, lane3_counter, bike_counter, car_counter, bus_counter, truck_counter, vehicle_total_counter
    while True:
        vehicle_type = random.randint(0, 3)     # Randomizing the vehicles entering the lanes
        if vehicle_type == 0:
            bike_counter += 1
        elif vehicle_type == 1:
            car_counter += 1
        elif vehicle_type == 2:
            bus_counter += 1
        elif vehicle_type == 3:
            truck_counter += 1
        will_turn = 0
        lane_number = 1
        temp = random.randint(0, 100)
        temp2 = random.randint(0, 30)
        #   To let vehicles that want to take a uTurn
        if temp < 30:
            lane_number = 1
            lane1_counter += 1
            if temp2 < 10:
                will_turn = 1
        #   Allowing only 0:bikes and 1: cars to enter second lane
        elif temp >= 30 and (vehicle_type == 0 or vehicle_type == 1):
            lane_number = 2
            lane2_counter += 1
        #   Allowing only 2:buses and 3:trucks to enter third lane
        elif temp >= 30 and (vehicle_type == 2 or vehicle_type == 3):
            lane_number = 3
            lane3_counter += 1
        #   To randomize the number of vehicle staring from east or west junctions
        if temp % 2 == 0:
            direction_number = 0    # East Bound vehicles
        else:
            direction_number = 1    # West Bound vehicles
        vehicle_total_counter += 1
        Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number], will_turn)
        time.sleep(1)


def Logging():
    logger.info('------------------------------------------------------------------')
    logger.info(f'The simulation has stopped after {Elapsed_Time} seconds')
    logger.info('--------------------Simulation breakdown-------------------')
    logger.info('--------Vehicle Stats-----------')
    logger.info(f'{vehicle_total_counter} vehicles were generated in total')
    logger.info(f'{EB_counter} vehicles travelled East')
    logger.info(f'{WB_counter} vehicles travelled West')
    logger.info(f'{bike_counter} of the total vehicles generated were bikes')
    logger.info(f'{car_counter} of the total vehicles generated were cars')
    logger.info(f'{bus_counter} of the total vehicles generated were buses')
    logger.info(f'{truck_counter} of the total vehicles generated were trucks')
    logger.info(f'{lane1_counter} vehicles entered Lane 1')
    logger.info(f'{lane2_counter} vehicles entered Lane 2')
    logger.info(f'{lane3_counter} vehicles entered Lane 3')
    logger.info(f'{EB_uturn_counter} vehicles made a uTurn in the East bound direction')
    logger.info(f'{WB_uturn_counter} vehicles made a uTurn in the West bound direction')
    logger.info('--------Pedestrian Stats-----------')
    logger.info(f'{Total_ped_counter} pedestrians crossed in total')
    logger.info(f'{ped_NB_counter} pedestrians in total travelled North')
    logger.info(f'{ped_SB_counter} pedestrians in total travelled South')


def generate_pedestrians():
    global ped_NB_counter, ped_SB_counter, Total_ped_counter
    while True:
        temp = random.randint(0, 20)
        ped_direction_num = 0
        if temp < 10:
            ped_direction_num = 0
            ped_NB_counter += 1
        elif temp <= 20:
            ped_direction_num = 1
            ped_SB_counter += 1
        Total_ped_counter += 1
        Pedestrians(ped_direction_num, ped_directionNumbers[ped_direction_num])
        time.sleep(1)


#   To simulate the Elapsed time
def sim_time():
    global simulation_Time, Elapsed_Time
    while True:
        Elapsed_Time += 1
        time.sleep(1)
        if Elapsed_Time == simulation_Time:     # Terminate the simulation
            Logging()
            os._exit(1)



class Main:
    thread1 = threading.Thread(name="initialization", target=initialize, args=())  # initialization Thread
    thread1.daemon = True
    thread1.start()
    logger.info('Thread1: The initialization class has begun')

    # Colours
    black = (0, 0, 0)
    white = (255, 255, 255)

    # Screensize
    screenWidth = 1700
    screenHeight = 1000
    screenSize = (screenWidth, screenHeight)

    # Setting background image i.e. image of intersection
    background = pygame.image.load('Images/Road.png')

    screen = pygame.display.set_mode(screenSize)

    # Loading signal images and font
    redSignal = pygame.image.load('Images/signals/Signal_Red.png')
    yellowSignal = pygame.image.load('Images/signals/Signal_Yellow.png')
    greenSignal = pygame.image.load('Images/signals/Signal_Green.png')
    pedgreenSignal = pygame.image.load('Images/signals/pedestrianSignal_green.png')
    pedredSignal = pygame.image.load('Images/signals/pedestrianSignal_red.png')
    font = pygame.font.Font(None, 30)

    thread2 = threading.Thread(name="generateVehicles", target=generate_vehicles, args=())  # Generating vehicles
    thread2.daemon = True
    thread2.start()
    logger.info('Thread2: Starting to generate vehicles')

    thread3 = threading.Thread(name="simTime", target=sim_time, args=())     # Simulation Time
    thread3.daemon = True
    thread3.start()
    logger.info('Simulation time has started')

    thread4 = threading.Thread(name="generatePedestrians", target=generate_pedestrians, args=())  # generate Pedestrians
    thread4.daemon = True
    thread4.start()
    logger.info('pedestrians started')

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                Logging()
                sys.exit()

        screen.blit(background, (0, 0))   # display background in simulation
        # display signal and set timer according to current status: green, yellow, or red
        for i in range(0, num_signals):
            if i == GreenCurrent:
                if YellowCurrent == 1:
                    signals[i].signalText = signals[i].yellow
                    if i == 2:      # To make both the Pedestrian signals run simultaneously
                        screen.blit(pedredSignal, Traffic_light_co_ord[i])
                        screen.blit(pedredSignal, Traffic_light_co_ord[i+1])
                    else:
                        screen.blit(yellowSignal, Traffic_light_co_ord[i])
                else:
                    signals[i].signalText = signals[i].green
                    if i == 2:
                        screen.blit(pedgreenSignal, Traffic_light_co_ord[i])
                        screen.blit(pedgreenSignal, Traffic_light_co_ord[i+1])
                    else:
                        screen.blit(greenSignal, Traffic_light_co_ord[i])
            else:
                if signals[i].red <= 10:
                    signals[i].signalText = signals[i].red
                else:
                    signals[i].signalText = ""
                if i == 2:
                    screen.blit(pedredSignal, Traffic_light_co_ord[i])
                    screen.blit(pedredSignal, Traffic_light_co_ord[i+1])
                else:
                    screen.blit(redSignal, Traffic_light_co_ord[i])
        signalTexts = ["", "", ""]

        # display signal timer
        for i in range(0, num_signals):
            signalTexts[i] = font.render(str(signals[i].signalText), True, white, black)
            if i == 2:
                screen.blit(signalTexts[i], Signal_Tout_co_ord[i])
                screen.blit(signalTexts[i], Signal_Tout_co_ord[i+1])
            else:
                screen.blit(signalTexts[i], Signal_Tout_co_ord[i])

        # display elapsed time
        text = font.render(("Run_Time: " + str(Elapsed_Time)), True, black, white)
        screen.blit(text, Elapsed_Time_co_ord)

        # display the vehicles
        for vehicle in simulation:
            screen.blit(vehicle.image, [vehicle.x, vehicle.y])
            vehicle.move()
        # display the pedestrians
        for person in simulation2:
            screen.blit(person.image, [person.pedx, person.pedy])
            person.ped_move()

        pygame.display.update()


Main()