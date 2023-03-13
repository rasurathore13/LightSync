from PIL import Image, ImageDraw
import numpy as np
import cv2
import pyautogui
import colorsys
from tuyapy import TuyaApi
import tuyapy
import json
import time
import os
import json

from PIL import Image
from sklearn.cluster import KMeans
import numpy as np




def get_colors(image_file, numcolors=1, resize=150):
    # Resize image to speed up processing
    img = Image.open(image_file)
    img = img.copy()
    img.thumbnail((resize, resize))

    # Reduce to palette
    paletted = img.convert('P', palette=Image.ADAPTIVE, colors=numcolors)

    # Find dominant colors
    palette = paletted.getpalette()
    #print(palette)
    color_counts = sorted(paletted.getcolors(), reverse=True)
    #print(color_counts)
    colors = list()
    for i in range(numcolors):
        palette_index = color_counts[i][1]
        dominant_color = palette[palette_index*3:palette_index*3+3]
        colors.append(tuple(dominant_color))

    return colors

def save_palette(colors, swatchsize=20, outfile="palette.png" ):
    num_colors = len(colors)
    palette = Image.new('RGB', (swatchsize*num_colors, swatchsize))
    draw = ImageDraw.Draw(palette)

    posx = 0
    for color in colors:
        draw.rectangle([posx, 0, posx+swatchsize, swatchsize], fill=color) 
        posx = posx + swatchsize

    del draw
    palette.save(outfile, "PNG")



def read_config():
    print('---------------------- Reading Config ----------------------')
    with open("config.json", "r") as config_file:
        config_data = config_file.read()
        config = json.loads(config_data)
        print('----------------------Finshed Reading Config ----------------------')
        return config

def rgb_to_hsv(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    cmax, cmin = max(r, g, b), min(r, g, b)
    delta = cmax - cmin

    if delta == 0:
       return (0, round(s*100),100)
    elif cmax == r:
        h = ((g - b) / delta) % 6
    elif cmax == g:
        h = ((b - r) / delta) + 2
    else:
        h = ((r - g) / delta) + 4

    h = round(h * 60)
    if h < 0:
        h += 360

    if cmax == 0:
        s = 0
    else:
        s = delta / cmax

    s = round(s * 100)
    v = round(cmax * 100)

    return (h, s, v)


if __name__ == '__main__':

    #---------------------- Initializing Section ----------------------
    cwd = os.getcwd()
    cwd = cwd.replace('\\', '\\\\')

    config = read_config()
    
    capture_path = cwd + '\\\\capture.png'
    color_pallet_path = cwd + '\\\\ColorPallet.png'
    
    device_id = config['device_id']

    while True:
        try:
            api = TuyaApi()
            api.init(config['email'], config['password'], config['phone_code'], config['application'])
        except tuyapy.tuyaapi.TuyaAPIException as e:
                print('Error -> We can not authenticate twice in a minute.')
                print("Waiting 15 secs to retry authentication.")
                print('')
                time.sleep(15)
                continue
        else:
            break
    #---------------------- Initialization Done ----------------------

    #---------------------- Starting the loop to take screebshots and updadte the smart bulb ----------------------
    #print(api.discover_devices())
    while True:
        image = pyautogui.screenshot()
        image = cv2.cvtColor(np.array(image),
                            cv2.COLOR_RGB2BGR)
        cv2.imwrite(capture_path, image)
        test_ai_to_get_background_color(capture_path)
        input_file = capture_path
        try:
            colors = get_colors(input_file)
            #save_palette(colors, outfile = colour_pallet_path)
            r,g,b = colors[0][0], colors[0][1], colors[0][2]
            print('The original RGB Value r - {}, g - {}, b - {}'.format(round(r),round(g),round(b)))

            h, s, v = colorsys.rgb_to_hsv(r,g,b)
            
            r, g, b = r/255, g/255, b/255
            
            hsv = {
                'hue' : h*360,
                'saturation': s,
                'brightness' : max(r,g,b)*100
            }
            
            #print('The converted HSV Value H - {}, S - {}, V - {}'.format(round(hsv['hue'],2),round(hsv['saturation'],2),round(hsv['brightness'],2)))
            response = api.device_control(device_id,  'colorSet', {'color': hsv})            
            try:
                if str(response[1]['header']['code']).upper() == 'SUCCESS':
                    continue
                else:
                    print(response)
            except Exception as ex:
                print(ex)
            print(response[1]['header']['code'])
        except Exception as e:
            print(e)

        