import random
import time
import threading
import pygame
import sys
import logging
import os


# Declarations for Traffic Signals
signals = []
num_signals = 3
pedestrian_signals = []
num_ped_signals = 2
ped_green = {0: 15}
ped_red = 0
PedLight = 0
GreenLight = {0: 10, 1: 10, 2: 15}
RedLight = 15
YellowLight = 5
GreenCurrent = 0    # Indicating which signal post light is Green
YellowCurrent = 0   # If the Yellow light is active or not
NextGreen = (GreenCurrent + 1) % num_signals    # Indicate the next green signal
simulation_Time = 100
Elapsed_Time = 0
# Coordinates for the traffic signal posts and the timer
Traffic_light_co_ord = [(510, 600), (1130, 350)]
Signal_Tout_co_ord = [(530, 615), (1150, 365)]
Ped_signal_lights = [(505, 225), (1135, 225), (505, 725), (1135, 725)]
Elapsed_Time_co_ord = (90,60)

# Coordinates for the vehicles to start from
x = {'EB': [0, 0, 0, 0], 'WB': [1900, 1900, 1900, 1900]}  # (EastBound, WestBound) vehicles
y = {'EB': [515, 520, 610, 690], 'WB': [420, 420, 360, 270]}

# Coordinates for the pedestrians to start from
pedx = {'NB': [535, 535], 'SB': [1150, 1150]}  # (EastBound, WestBound) vehicles
pedy = {'NB': [1000, 1000], 'SB': [0, 0]}

vehicleTypes = {0: 'bike', 1: 'car', 2: 'bus', 3: 'truck'}  # Types of Vehicles used in this simulation
speed = {'bike': 8, 'car': 7.5, 'bus': 7, 'truck': 7}  # Vehicle Average speeds
directionNumbers = {0: 'EB', 1: 'WB'}
vehicles = {'EB': {0: [], 1: [], 2: [], 3: [], 'crossed': 0, 'turned': 0}, 'WB': {0: [], 1: [], 2: [], 3: [], 'crossed': 0, 'turned': 0}}
pedestrians = {'NB': {0: [], 'crossed': 0}, 'SB': {0: [], 'crossed': 0}}
# Coordinates of stop lines at the signal post before the intersection
stopLines = {'EB': 490, 'WB': 1200}
defaultStop = {'EB': 480, 'WB': 1210}
stopGap = 20    # between vehicles
moveGap = 20    # between vehicles
pedStopLines = {'NB': 770, 'SB': 240}
pedDefaultStop = {'NB': 780, 'SB': 230}
pedStopGap = 10

vehiclesTurned = {'EB': {1:[], 2: [], 3: []}, 'WB': {1:[], 2: [], 3: []}}
vehiclesNotTurned = {'EB': {1: [], 2: []}, 'WB': {1: [], 2: []}}
rotationAngle = 30
logger = logging.getLogger()
handler = logging.FileHandler('Logs/SimulationLogs.txt')
logger.addHandler(handler)

log = open('Logs/SimulationLogs.txt', 'w')
pygame.init()
simulation = pygame.sprite.Group()


class TrafficSignal:
    def __init__(self, red, yellow, green):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.signalText = ""


class PedSignals:
    def __init__(self, pedred, pedgreen):
        self.pedRed = pedred
        self.pedGreen = pedgreen


class Pedestrian(pygame.sprite.Sprite):
    def __init__(self, ped_lane, ped_direction_num, ped_direction):
        pygame.sprite.Sprite.__init__(self)
        self.ped_lane = ped_lane
        self.ped_direction_num = ped_direction_num
        self.ped_direction = ped_direction
        self.pedx = pedx[ped_direction][ped_lane]
        self.pedy = pedy[ped_direction][ped_lane]
        self.item = len(pedestrians[ped_direction][ped_lane]) - 1
        self.pedcrossed = 0
        path = "images/" + direction + "/" + pedestrian + ".png"
        self.ped_image = pygame.image.load(path)
        if len(pedestrians[ped_direction][ped_lane]) > 1 and pedestrians[ped_direction][ped_lane][self.item - 1].pedcrossed == 0:
            if direction == 'NB':
                self.pedstop = pedestrians[ped_direction][ped_lane][self.item - 1].pedstop + pedestrians[ped_direction][ped_lane][self.item - 1].image.get_rect().height + pedStopGap
            elif direction == 'SB':
                self.pedstop = pedestrians[ped_direction][ped_lane][self.item - 1].pedstop - pedestrians[ped_direction][ped_lane][self.item - 1].image.get_rect().height - pedStopGap
        else:
            self.pedstop = pedDefaultStop[ped_direction]

        if direction == 'NB':
            temp = self.image.get_rect().height + pedStopGap
            pedy[ped_direction][ped_lane] += temp
        elif direction =='SB':
            temp = self.image.get_rect().height + pedStopGap
            pedy[ped_direction][ped_lane] -= temp
        pedsimulation.add(self)

    def pedrender(self, screen):
        screen.blit(self.ped_image, (self.pedx, self.pedy))

    def pedmove(self):
        if self.ped_direction == 'NB':
            if self.pedcrossed == 0 and self.pedy < pedStopLines[self.ped_direction]:
                self.pedcrossed = 1
            if ((self.pedy >= self.pedstop or self.pedcrossed == 1 or (ped_green ==  and currentYellow == 0)) and (
                    self.index == 0 or self.y > (
                    vehicles[self.direction][self.lane][self.index - 1].y + vehicles[self.direction][self.lane][
                self.index - 1].image.get_rect().height + movingGap))):
                self.y -= self.speed

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
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.originalImage = pygame.image.load(path)
        self.image = pygame.image.load(path)

        if len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.item - 1].crossed == 0:
            if direction == 'EB':
                # if vehicles[direction][lane][self.item - 1].turned == 1:
                #     self.stop = defaultStop[direction]
                # else:
                self.stop = vehicles[direction][lane][self.item - 1].stop - vehicles[direction][lane][self.item - 1].image.get_rect().width - stopGap
            elif direction == 'WB':
                self.stop = vehicles[direction][lane][self.item - 1].stop + vehicles[direction][lane][self.item - 1].image.get_rect().width + stopGap
        else:
            self.stop = defaultStop[direction]

        # New starting and stopping coordinates
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
        if self.direction == 'EB':
            if self.crossed == 0 and self.x + self.image.get_rect().width > stopLines[self.direction]:
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                # if self.will_turn == 0:
                #     vehiclesStraight[self.direction][self.lane].append(self)
                #     self.crossedIndex = len(vehiclesStraight[self.direction][self.lane]) - 1
            if self.willTurn == 1 and self.lane == 1:
                if self.x >= stopLines[self.direction]:
                    self.uTurn = True

                if self.uTurn == True:
                    if self.turned == 0:
                        self.rotateAngle += rotationAngle
                        self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                        if (self.rotateAngle < 90):
                            self.y -= 15
                            self.x += 15
                        else:
                            self.y -= 15
                            self.x -= 15
                        if (self.rotateAngle == 180):
                            self.turned = 1
                            self.uTurn = False
                            vehicles[self.direction]['turned'] += 1
                            vehiclesTurned[self.direction][self.lane].append(self)
                            self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1

            if (self.x + self.image.get_rect().width <= self.stop or self.crossed == 1 or (
                    GreenCurrent == 0 and YellowCurrent == 0)) and (self.item == 0 or self.x + self.image.get_rect().width < (
                    vehicles[self.direction][self.lane][self.item - 1].x - moveGap) or vehicles[self.direction][self.lane][self.item-1].turned==1):
                if self.turned == 1:
                    self.x -= self.speed
                else:
                    self.x += self.speed

        elif self.direction == 'WB':
            if self.crossed == 0 and self.x <= stopLines[self.direction]:
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1

            if self.willTurn == 1 and self.lane == 1:
                if self.x <= stopLines[self.direction]:
                    self.uTurn = True

                if self.uTurn == True:
                    if self.turned == 0:
                        self.rotateAngle += rotationAngle
                        self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                        if self.rotateAngle < 90:
                            self.y += 15
                            self.x -= 15
                        else:
                            self.y += 20
                            self.x += 20
                        if self.rotateAngle == 180:
                            self.turned = 1
                            self.uTurn = False
                            vehicles[self.direction]['turned'] += 1
                            vehiclesTurned[self.direction][self.lane].append(self)
                            self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
            if (self.x >= self.stop or self.crossed == 1 or (GreenCurrent == 1 and YellowCurrent == 0)) and (self.item == 0 or self.x > (
                    vehicles[self.direction][self.lane][self.item - 1].x + vehicles[self.direction][self.lane][self.item - 1].image.get_rect().width + moveGap) or vehicles[self.direction][self.lane][self.item-1].turned == 1):
                if self.turned == 1:
                    self.x += self.speed
                else:
                    self.x -= self.speed


def initialize():

    signal_post1 = TrafficSignal(0, YellowLight, GreenLight[0])
    signals.append(signal_post1)
    signal_post2 = TrafficSignal(signal_post1.yellow + signal_post1.green, YellowLight, GreenLight[1])
    signals.append(signal_post2)
    ped_signals = PedSignals(signal_post2.green + signal_post2.yellow, ped_green[0])
    signals.append(ped_signals)
    repeat()


def repeat():
    global GreenCurrent, YellowCurrent, NextGreen, PedLight
    signalcounter = 0
    while signals[GreenCurrent].green > 0:  # while the timer of current green signal is not zero
        updatevalues()
        time.sleep(1)
    YellowCurrent = 1  # set yellow signal on
    signalcounter += 1
    # reset stop coordinates of lanes and vehicles
    for i in range(0, 3):
        for vehicle in vehicles[directionNumbers[GreenCurrent]][i]:
            vehicle.stop = defaultStop[directionNumbers[GreenCurrent]]
    while signals[GreenCurrent].yellow > 0:  # while the timer of current yellow signal is not zero
        updatevalues()
        time.sleep(1)
    YellowCurrent = 0  # set yellow signal off
    # Reset all signals to default time
    signals[GreenCurrent].green = GreenLight[GreenCurrent]
    signals[GreenCurrent].yellow = YellowLight
    signals[GreenCurrent].red = RedLight
    GreenCurrent = NextGreen  # Next Green signal
    NextGreen = (GreenCurrent + 1) % num_signals  # set next green signal as green
    signals[NextGreen].red = signals[GreenCurrent].yellow + signals[GreenCurrent].green  # set the red time of next to next signal as (yellow time + green time) of next signal
    if signalcounter % 2 == 0:
        PedLight = 10
    repeat()


def updatevalues():
    for i in range(0, num_signals):
        if i == GreenCurrent:
            if YellowCurrent == 0:
                signals[i].green -= 1
            else:
                signals[i].yellow -= 1
        else:
            signals[i].red -= 1


def generate_vehicles():
    while True:
        vehicle_type = random.randint(0, 3)
        will_turn = 0
        lane_number = 1
        temp = random.randint(0, 100)
        temp2 = random.randint(0, 30)
        if temp < 30:
            lane_number = 1
            if temp2 < 15:
                will_turn = 1
        elif temp >= 30 and (vehicle_type == 0 or vehicle_type == 1):
            lane_number = 2
        elif temp >= 30 and (vehicle_type == 2 or vehicle_type == 3):
            lane_number = 3

        if temp % 2 == 0:
            direction_number = 0
        else:
            direction_number = 1

        Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number], will_turn)
        #Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number],1)

        time.sleep(1)


def simTime():
    global simulation_Time,Elapsed_Time
    while True:
        Elapsed_Time +=1
        time.sleep(1)
        if Elapsed_Time == simulation_Time:
            os._exit(1)


class Main:
    thread1 = threading.Thread(name="initialization", target=initialize, args=())  # initialization
    thread1.daemon = True
    thread1.start()

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
    # pygame.display.set_caption("SIMULATION")

    # Loading signal images and font
    redSignal = pygame.image.load('Images/signals/Signal_Red.png')
    yellowSignal = pygame.image.load('Images/signals/Signal_Yellow.png')
    greenSignal = pygame.image.load('Images/signals/Signal_Green.png')
    pedGreen = pygame.image.load('Images/pedestrianSignal_green.png')
    pedRed = pygame.image.load('Images/pedestrianSignal_red.png')
    font = pygame.font.Font(None, 30)

    thread2 = threading.Thread(name="generateVehicles", target=generate_vehicles, args=())  # Generating vehicles
    thread2.daemon = True
    thread2.start()

    thread3 = threading.Thread(name="simTime", target=simTime, args=())
    thread3.daemon = True
    thread3.start()



    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        screen.blit(background, (0, 0))   # display background in simulation
        for i in range(0, num_signals):  # display signal and set timer according to current status: green, yello, or red
            if i == GreenCurrent:
                if YellowCurrent == 1:
                    signals[i].signalText = signals[i].yellow
                    screen.blit(yellowSignal, Traffic_light_co_ord[i])
                else:
                    signals[i].signalText = signals[i].green
                    screen.blit(greenSignal, Traffic_light_co_ord[i])
            else:
                if signals[i].red <= 10:
                    signals[i].signalText = signals[i].red
                else:
                    signals[i].signalText = ""
                screen.blit(redSignal, Traffic_light_co_ord[i])
        signalTexts = ["", ""]

        # display signal timer
        for i in range(0, num_signals):
            signalTexts[i] = font.render(str(signals[i].signalText), True, white, black)
            screen.blit(signalTexts[i], Signal_Tout_co_ord[i])

        # display elapsed time
        text = font.render(("Run_Time: " + str(Elapsed_Time)), True, black, white)
        screen.blit(text, Elapsed_Time_co_ord)

        # display the vehicles

        for vehicle in simulation:
            screen.blit(vehicle.image, [vehicle.x, vehicle.y])
            vehicle.move()

        pygame.display.update()


Main()