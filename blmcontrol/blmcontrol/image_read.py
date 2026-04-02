
import webcolors
import numpy as np
import cv2
import math

WIDTH = 42.0
CENTER = WIDTH / 2.0
RING_LENGTH = 50


def pixel_map(pixelCount):
    map = []
    for i in range(RING_LENGTH):
        c = float(i) / RING_LENGTH * math.pi * 2
        map.append([math.cos(c), math.sin(c)])
    for i in range(RING_LENGTH):
        c = float(i) / RING_LENGTH * math.pi * 2
        map.append([math.cos(c) * 0.8, math.sin(c) * 0.8])

    map.append([(29 - CENTER) / WIDTH, (8 - CENTER) / WIDTH])
    map.append([(23 - CENTER) / WIDTH, (13 - CENTER) / WIDTH])
    map.append([(17 - CENTER) / WIDTH, (17 - CENTER) / WIDTH])
    map.append([(16 - CENTER) / WIDTH, (21 - CENTER) / WIDTH])
    map.append([(18 - CENTER) / WIDTH, (21 - CENTER) / WIDTH])
    map.append([(15 - CENTER) / WIDTH, (24 - CENTER) / WIDTH])
    map.append([(17 - CENTER) / WIDTH, (24 - CENTER) / WIDTH])
    map.append([(14 - CENTER) / WIDTH, (27 - CENTER) / WIDTH])
    map.append([(16 - CENTER) / WIDTH, (27 - CENTER) / WIDTH])

    map.append([(13 - CENTER) / WIDTH, (33 - CENTER) / WIDTH])
    map.append([(19 - CENTER) / WIDTH, (29 - CENTER) / WIDTH])
    map.append([(24 - CENTER) / WIDTH, (25 - CENTER) / WIDTH])
    map.append([(22 - CENTER) / WIDTH, (25 - CENTER) / WIDTH])
    map.append([(25 - CENTER) / WIDTH, (22 - CENTER) / WIDTH])
    map.append([(23 - CENTER) / WIDTH, (22 - CENTER) / WIDTH])
    map.append([(27 - CENTER) / WIDTH, (18 - CENTER) / WIDTH])
    map.append([(25 - CENTER) / WIDTH, (18 - CENTER) / WIDTH])
    map.append([(28 - CENTER) / WIDTH, (15 - CENTER) / WIDTH])
    map.append([(25 - CENTER) / WIDTH, (15 - CENTER) / WIDTH])

    return map


def bgr_to_hex(bgr):
   rgb = list(bgr)
   rgb.reverse()
   return webcolors.rgb_to_hex(tuple(rgb))


def FindColors(image):
    color_hex = []
    for i in image:
        for j in i:
            j = list(j)
            color_hex.append(bgr_to_hex(tuple(j)))
    return set(color_hex)


START_ROW = 10
END_ROW = 10
START_COLUMN = 10
END_COLUMN = 10

source_pixel_map = pixel_map(10)
i = cv2.imread("tv_off.jpg")
#im = cv2.cvtColor(i, cv2.COLOR_BGR2HSV)
#cv2.imshow('Original image',i)
#cv2.imshow('HSV image',im)
#cv2.waitKey(0)
#cv2.destroyAllWindows()
im = i[:, :, :3] / 255.0

height = im.shape[0]
width = im.shape[1]
proportion = 0.9
map_height = height * proportion
map_width = width * proportion
x_offset = width / 2.0
y_offset = height / 2.0

def map_to_image(pixel):
    color = list(im[int(map_height * pixel[1] / 2.0 + y_offset), int(map_width * pixel[0] / 2.0 + x_offset), :])
    return [color[0], color[1], color[2]]

colors = list(map(map_to_image, source_pixel_map))
colors_string = str(colors)

color_list = FindColors(im)
print()

