from PIL import Image, ImageDraw
import numpy as np
import cv2
import pyautogui
import colorsys
from tuyapy import TuyaApi
import json
import os
   

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


if __name__ == '__main__':

    #---------------------- Initializing Section ----------------------
    cwd = os.getcwd()
    cwd = cwd.replace('\\', '\\\\')

    config = read_config()
    
    capture_path = cwd + '\\\\capture.png'
    color_pallet_path = cwd + '\\\\ColorPallet.png'
    
    device_id = config['device_id']

    api = TuyaApi()
    api.init(config['email'], config['username'], config['phone_code'], config['application'])
    #---------------------- Initialization Done ----------------------

    #---------------------- Starting the loop to take screebshots and updadte the smart bulb ----------------------
    while True:
        image = pyautogui.screenshot()
        image = cv2.cvtColor(np.array(image),
                            cv2.COLOR_RGB2BGR)
        cv2.imwrite(capture_path, image)

        input_file = capture_path
        try:
            colors = get_colors(input_file)
            #save_palette(colors, outfile = colour_pallet_path)
            r,g,b = colors[0][0], colors[0][1], colors[0][2]
            h, s, v = colorsys.rgb_to_hsv(r,g,b)
            hsv = {
                'hue' : h,
                'saturation': s,
                'brightness' : v
            }
            print(hsv)
            print(api.device_control(device_id,  'colorSet', {'color': hsv}))

        except Exception as e:
            print(e)