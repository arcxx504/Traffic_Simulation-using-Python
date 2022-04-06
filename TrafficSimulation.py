import random
import time
import threading
import pygame
import sys


# Declarations for Traffic Signals
signals = []
num_signals = 3

GreenLight = {0: 5, 1: 5, 2: 5}
RedLight = 100
YellowLight = 3
GreenCurrent = 0    # Indicating which signal post light is Green
YellowCurrent = 0   # If the Yellow light is active or not
NextGreen = (GreenCurrent + 1) % num_signals    # Indicate the next green signal

# Coordinates for the traffic signal posts and the timer
Traffic_light_co_ord = [(500, 375), (1350, 225), (1030, 650)]
Signal_Tout_co_ord = [(520, 390), (1370, 240), (1050, 665)]

# Coordinates for the vehicles to start from
x = {'EB': 0, 'WB': 1900, 'NB': 1060}   # (EastBound, WestBound, NorthBound) vehicles
y = {'EB': 400, 'WB': 240, 'NB': 1075}
vehicleTypes = {0: 'bike', 1: 'car', 2: 'bus', 3: 'truck'}  # Types of Vehicles used in this simulation
speed = {'bike': 3, 'car': 2.75, 'bus': 2.2, 'truck': 1.9}  # Vehicle Average speeds
directionNumbers = {0: 'EB', 1: 'WB', 2: 'NB'}
vehicles = {'EB': {0: [], 'crossed': 0}, 'WB': {0: [], 'crossed': 0}, 'up': {0: [], 'crossed': 0}}
# vehicles = {'EB': {0: [], 1: [], 2: [], 'crossed': 0}, 'WB': {0: [], 1: [], 2: [], 'crossed': 0}, 'NB': {0: [], 1: [], 2: [], 'crossed': 0}}

# Coordinates of stop lines at the signal post before the intersection
stopLines = {'EB': 550, 'WB': 1360, 'NB': 650}
defaultStop = {'EB': 530, 'WB': 1380, 'NB': 670}
stopGap = 20    # between vehicles
moveGap = 20    # between vehicles

vehiclesTurned = {'EB': [], 'WB': [], 'NB': []}
vehiclesNotTurned = {'EB': [], 'WB': [], 'NB': []}
rotationAngle = 5
mid = {'EB': {'x': 1050, 'y': 400}, 'WB': {'x': 880, 'y': 250}, 'NB': {'x': 1050, 'y': 250}}


pygame.init()
simulation = pygame.sprite.Group()


class TrafficSignal:
    def __init__(self, red, yellow, green):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.signalText = ""


class Vehicle(pygame.sprite.Sprite):
    def __init__(self, vehicleClass, direction_number, direction, will_turn):
        pygame.sprite.Sprite.__init__(self)
        self.vehicleClass = vehicleClass
        self.speed = speed[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.x = x[direction]
        self.y = y[direction]
        self.willTurn = will_turn
        vehicles[direction][0].append(self)
        self.item = len(vehicles[direction][0]) - 1
        self.crossed = 0
        self.turned = 0
        self.rotateAngle = 0
        self.crossedIndex = 0
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.originalImage = pygame.image.load(path)
        self.image = pygame.image.load(path)

        if len(vehicles[direction][0]) > 1 and vehicles[direction][0][self.item - 1].crossed == 0:
            if direction == 'EB':
                self.stop = vehicles[direction][0][self.item - 1].stop - vehicles[direction][0][self.item - 1].image.get_rect().width - stopGap
            elif direction == 'WB':
                self.stop = vehicles[direction][0][self.item - 1].stop + vehicles[direction][0][self.item - 1].image.get_rect().width + stopGap
            elif direction == 'NB':
                self.stop = vehicles[direction][0][self.item - 1].stop + vehicles[direction][0][self.item - 1].image.get_rect().height + stopGap
        else:
            self.stop = defaultStop[direction]

        # New starting and stopping coordinates
        if direction == 'EB':
            flag = self.image.get_rect().width + stopGap
            x[direction] -= flag
        elif direction == 'WB':
            flag = self.image.get_rect().width + stopGap
            x[direction] += flag
        elif direction == 'NB':
            flag = self.image.get_rect().height + stopGap
            y[direction] += flag

        simulation.add(self)

    def render(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def move(self):
        if self.direction == 'EB':
            '''if self.crossed == 0 and self.x + self.image.get_rect().width > stopLines[self.direction]:
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if self.willTurn == 0:
                    vehiclesNotTurned[self.direction].append(self)
                    self.crossedIndex = len(vehiclesNotTurned[self.direction]) - 1'''
            if self.willTurn == 1:
                if self.crossed == 0 or self.x + self.image.get_rect().width < mid[self.direction]['x']:
                    if ((self.x + self.image.get_rect().width <= self.stop or (
                            currentGreen == 0 and currentYellow == 0) or self.crossed == 1) and (
                            self.index == 0 or self.x + self.image.get_rect().width < (
                            vehicles[self.direction][self.lane][self.index - 1].x - movingGap) or
                            vehicles[self.direction][self.lane][self.index - 1].turned == 1)):
                        self.x += self.speed
                else:
                    if (self.turned == 0):
                        self.rotateAngle += rotationAngle
                        self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x += 2
                        self.y += 1.8
                        if (self.rotateAngle == 90):
                            self.turned = 1
                            vehiclesTurned[self.direction][self.lane].append(self)
                            self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                    else:
                        if (self.crossedIndex == 0 or ((self.y + self.image.get_rect().height) < (
                                vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].y - movingGap))):
                            self.y += self.speed
            else:
                if (self.crossed == 0):
                    if ((self.x + self.image.get_rect().width <= self.stop or (
                            currentGreen == 0 and currentYellow == 0)) and (
                            self.index == 0 or self.x + self.image.get_rect().width < (
                            vehicles[self.direction][self.lane][self.index - 1].x - movingGap))):
                        self.x += self.speed
                else:
                    if ((self.crossedIndex == 0) or (self.x + self.image.get_rect().width < (
                            vehiclesNotTurned[self.direction][self.lane][self.crossedIndex - 1].x - movingGap))):
                        self.x += self.speed


def initialize():
    signalpost1 = TrafficSignal(0, YellowLight, GreenLight[0])
    signals.append(signalpost1)
    signalpost2 = TrafficSignal(signalpost1.yellow + signalpost1.green, YellowLight, GreenLight[1])
    signals.append(signalpost2)
    signalpost3 = TrafficSignal(RedLight, YellowLight, GreenLight[2])
    signals.append(signalpost3)
    repeat()


def repeat():
    global GreenCurrent, YellowCurrent, NextGreen
    while signals[GreenCurrent].green > 0:  # while the timer of current green signal is not zero
        updatevalues()
        time.sleep(1)
    YellowCurrent = 1  # set yellow signal on
    # reset stop coordinates of lanes and vehicles
    '''for i in range(0, 2):
        for vehicle in vehicles[directionNumbers[currentGreen]][i]:
            vehicle.stop = defaultStop[directionNumbers[currentGreen]]'''
    while signals[GreenCurrent].yellow > 0:  # while the timer of current yellow signal is not zero
        updatevalues()
        time.sleep(1)
    YellowCurrent = 0  # set yellow signal off
    signals[GreenCurrent].green = GreenLight[GreenCurrent]
    signals[GreenCurrent].yellow = YellowLight
    signals[GreenCurrent].red = RedLight

    GreenCurrent = NextGreen  # set next signal as green signal
    NextGreen = (GreenCurrent + 1) % num_signals  # set next green signal
    signals[NextGreen].red = signals[GreenCurrent].yellow + signals[GreenCurrent].green  # set the red time of next to next signal as (yellow time + green time) of next signal
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


class Main:
    thread1 = threading.Thread(name="initialization", target=initialize, args=())  # initialization
    thread1.daemon = True
    thread1.start()

    # Colours
    black = (0, 0, 0)
    white = (255, 255, 255)

    # Screensize
    screenWidth = 1800
    screenHeight = 1000
    screenSize = (screenWidth, screenHeight)

    # Setting background image i.e. image of intersection
    background = pygame.image.load('Images/3way_intersection.png')

    screen = pygame.display.set_mode(screenSize)
    # pygame.display.set_caption("SIMULATION")

    # Loading signal images and font
    redSignal = pygame.image.load('Images/signals/Signal_Red.png')
    yellowSignal = pygame.image.load('Images/signals/Signal_Yellow.png')
    greenSignal = pygame.image.load('Images/signals/Signal_Green.png')
    font = pygame.font.Font(None, 30)

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
        signalTexts = ["", "", "", ""]

        # display signal timer
        for i in range(0, num_signals):
            signalTexts[i] = font.render(str(signals[i].signalText), True, white, black)
            screen.blit(signalTexts[i], Signal_Tout_co_ord[i])

        # display the vehicles
        '''
        for vehicle in simulation:
            screen.blit(vehicle.image, [vehicle.x, vehicle.y])
            vehicle.move()
            '''
        pygame.display.update()


Main()