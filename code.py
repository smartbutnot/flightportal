import time
from random import randrange
import board
import terminalio
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_portalbase.network import HttpError
import adafruit_requests as requests
import json

import adafruit_display_text.label
import board
import displayio
import framebufferio
import rgbmatrix
import terminalio
import gc

import busio
from digitalio import DigitalInOut
import neopixel
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_esp32spi import adafruit_esp32spi_wifimanager

from microcontroller import watchdog as w
from watchdog import WatchDogMode

w.timeout=16 # timeout in seconds
w.mode = WatchDogMode.RESET

FONT=terminalio.FONT

try:
    from secrets import secrets
except ImportError:
    print("Secrets including geo are kept in secrets.py, please add them there!")
    raise

# How often to query fr24 - quick enough to catch a plane flying over, not so often as to cause any issues, hopefully
QUERY_DELAY=30
#Area to search for flights, see secrets file
BOUNDS_BOX=secrets["bounds_box"]

# Colours and timings
ROW_ONE_COLOUR=0xEE82EE
ROW_TWO_COLOUR=0x4B0082
ROW_THREE_COLOUR=0xFFA500
PLANE_COLOUR=0x4B0082
# Time in seconds to wait between scrolling one label and the next
PAUSE_BETWEEN_LABEL_SCROLLING=3
# speed plane animation will move - pause time per pixel shift in seconds
PLANE_SPEED=0.04
# speed text labels will move - pause time per pixel shift in seconds
TEXT_SPEED=0.04

#URLs
FLIGHT_SEARCH_HEAD="https://data-live.flightradar24.com/zones/fcgi/feed.js?bounds="
FLIGHT_SEARCH_TAIL="&faa=1&satellite=1&mlat=1&flarm=1&adsb=1&gnd=0&air=1&vehicles=0&estimated=0&maxage=14400&gliders=0&stats=0&ems=1&limit=1"
FLIGHT_SEARCH_URL=FLIGHT_SEARCH_HEAD+BOUNDS_BOX+FLIGHT_SEARCH_TAIL
# Deprecated URL used to return less JSON than the long details URL, but can give ambiguous results
# FLIGHT_DETAILS_HEAD="https://api.flightradar24.com/common/v1/flight/list.json?&fetchBy=flight&page=1&limit=1&maxage=14400&query="

# Used to get more flight details with a fr24 flight ID from the initial search
FLIGHT_LONG_DETAILS_HEAD="https://data-live.flightradar24.com/clickhandler/?flight="

# Request headers
rheaders = {
     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0",
     "cache-control": "no-store, no-cache, must-revalidate, post-check=0, pre-check=0",
     "accept": "application/json"
}

esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
status_light = neopixel.NeoPixel(
    board.NEOPIXEL, 1, brightness=0.2
)
wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets, status_light,debug=False,attempts=1)

# Top level matrixportal object
matrixportal = MatrixPortal(
    headers=rheaders,
    esp=esp,
    rotation=0,
    debug=False
)

# Some memory shenanigans - the matrixportal doesn't do great at assigning big strings dynamically. So we create a big static array to put the JSON results in each time.
json_size=14336
json_bytes=bytearray(json_size)

# Little plane to scroll across when we find a flight overhead
planeBmp = displayio.Bitmap(12, 12, 2)
planePalette = displayio.Palette(2)
planePalette[1] = PLANE_COLOUR
planePalette[0] = 0x000000
planeBmp[6,0]=planeBmp[6,1]=planeBmp[5,1]=planeBmp[4,2]=planeBmp[5,2]=planeBmp[6,2]=1
planeBmp[9,3]=planeBmp[5,3]=planeBmp[4,3]=planeBmp[3,3]=1
planeBmp[1,4]=planeBmp[2,4]=planeBmp[3,4]=planeBmp[4,4]=planeBmp[5,4]=planeBmp[6,4]=planeBmp[7,4]=planeBmp[8,4]=planeBmp[9,4]=1
planeBmp[1,5]=planeBmp[2,5]=planeBmp[3,5]=planeBmp[4,5]=planeBmp[5,5]=planeBmp[6,5]=planeBmp[7,5]=planeBmp[8,5]=planeBmp[9,5]=1
planeBmp[9,6]=planeBmp[5,6]=planeBmp[4,6]=planeBmp[3,6]=1
planeBmp[6,9]=planeBmp[6,8]=planeBmp[5,8]=planeBmp[4,7]=planeBmp[5,7]=planeBmp[6,7]=1
planeTg= displayio.TileGrid(planeBmp, pixel_shader=planePalette)
planeG=displayio.Group(x=matrixportal.display.width+12,y=10)
planeG.append(planeTg)

# We can fit three rows of text on a panel, so one label for each. We'll change their text as needed
label1 = adafruit_display_text.label.Label(
    FONT,
    color=ROW_ONE_COLOUR,
    text="")
label1.x = 1
label1.y = 4

label2 = adafruit_display_text.label.Label(
    FONT,
    color=ROW_TWO_COLOUR,
    text="")
label2.x = 1
label2.y = 15

label3 = adafruit_display_text.label.Label(
    FONT,
    color=ROW_THREE_COLOUR,
    text="")
label3.x = 1
label3.y = 25

# text strings to go in the labels
label1_short=''
label1_long=''
label2_short=''
label2_long=''
label3_short=''
label3_long=''

# Add the labels to the display
g = displayio.Group()
g.append(label1)
g.append(label2)
g.append(label3)
matrixportal.display.show(g)

# Scroll the plane bitmap right to left (same direction as scrolling text)
def plane_animation():
    matrixportal.display.show(planeG)
    for i in range(matrixportal.display.width+24,-12,-1):
            planeG.x=i
            w.feed()
            time.sleep(PLANE_SPEED)
            #matrixportal.display.refresh(minimum_frames_per_second=0)

# Scroll a label, start at the right edge of the screen and go left one pixel at a time
# Until the right edge of the label reaches the left edge of the screen
def scroll(line):
    line.x=matrixportal.display.width
    for i in range(matrixportal.display.width+1,0-line.bounding_box[2],-1):
        line.x=i
        w.feed()
        time.sleep(TEXT_SPEED)
        #matrixportal.display.refresh(minimum_frames_per_second=0)
        

# Populate the labels, then scroll longer versions of the text
def display_flight():

    matrixportal.display.show(g)
    label1.text=label1_short
    label2.text=label2_short
    label3.text=label3_short
    time.sleep(PAUSE_BETWEEN_LABEL_SCROLLING)
    
    label1.x=matrixportal.display.width+1
    label1.text=label1_long
    scroll(label1)
    label1.text=label1_short
    label1.x=1
    time.sleep(PAUSE_BETWEEN_LABEL_SCROLLING)
    
    label2.x=matrixportal.display.width+1
    label2.text=label2_long
    scroll(label2)
    label2.text=label2_short
    label2.x=1
    time.sleep(PAUSE_BETWEEN_LABEL_SCROLLING)
    
    label3.x=matrixportal.display.width+1
    label3.text=label3_long
    scroll(label3)
    label3.text=label3_short
    label3.x=1
    time.sleep(PAUSE_BETWEEN_LABEL_SCROLLING)

# Blank the display when a flight is no longer found
def clear_flight():
    label1.text=label2.text=label3.text=""


# Take the flight ID we found with a search, and load details about it
def get_flight_details(fn):

    # the JSON from FR24 is too big for the matrixportal memory to handle. So we load it in chunks into our static array,
    # as far as the big "trails" section of waypoints at the end of it, then ignore most of that part. Should be about 9KB, we have 14K before we run out of room..
    global json_bytes
    global json_size
    byte_counter=0
    chunk_length=1024
    success=False

    # zero out any old data in the byte array
    for i in range(0,json_size):
        json_bytes[i]=0

    # Get the URL response one chunk at a time
    try:
        response=requests.get(url=FLIGHT_LONG_DETAILS_HEAD+fn,headers=rheaders)
        for chunk in response.iter_content(chunk_size=chunk_length):

            # if the chunk will fit in the byte array, add it
            if(byte_counter+chunk_length<=json_size):
                for i in range(0,len(chunk)):
                    json_bytes[i+byte_counter]=chunk[i]
            else:
                print("Exceeded max string size while parsing JSON")
                return False

            # check if this chunk contains the "trail:" tag which is the last bit we care about
            trail_start=json_bytes.find((b"\"trail\":"))
            byte_counter+=len(chunk)

            # if it does, find the first/most recent of the many trail entries, giving us things like speed and heading
            if not trail_start==-1:
                # work out the location of the first } character after the "trail:" tag, giving us the first entry
                trail_end=json_bytes[trail_start:].find((b"}"))
                if not trail_end==-1:
                    trail_end+=trail_start
                    # characters to add to make the whole JSON object valid, since we're cutting off the end
                    closing_bytes=b'}]}'
                    for i in range (0,len(closing_bytes)):
                        json_bytes[trail_end+i]=closing_bytes[i]
                    # zero out the rest
                    for i in range(trail_end+3,json_size):
                        json_bytes[i]=0
                    # print(json_bytes.decode('utf-8'))

                    # Stop reading chunks
                    print("Details lookup saved "+str(trail_end)+" bytes.")
                    return True
    # Handle occasional URL fetching errors            
    except (RuntimeError, OSError, HttpError) as e:
            print("Error--------------------------------------------------")
            print(e)
            return False

    #If we got here we got through all the JSON without finding the right trail entries
    print("Failed to find a valid trail entry in JSON")
    return False
    

# Look at the byte array that fetch_details saved into and extract any fields we want
def parse_details_json():

    global json_bytes

    try:
        # get the JSON from the bytes
        long_json=json.loads(json_bytes)

        # Some available values from the JSON. Put the details URL and a flight ID in your browser and have a look for more.

        flight_number=long_json["identification"]["number"]["default"]
        #print(flight_number)
        flight_callsign=long_json["identification"]["callsign"]
        aircraft_code=long_json["aircraft"]["model"]["code"]
        aircraft_model=long_json["aircraft"]["model"]["text"]
        #aircraft_registration=long_json["aircraft"]["registration"]
        airline_name=long_json["airline"]["name"]
        #airline_short=long_json["airline"]["short"]
        airport_origin_name=long_json["airport"]["origin"]["name"]
        airport_origin_name=airport_origin_name.replace(" Airport","")
        airport_origin_code=long_json["airport"]["origin"]["code"]["iata"]
        #airport_origin_country=long_json["airport"]["origin"]["position"]["country"]["name"]
        #airport_origin_country_code=long_json["airport"]["origin"]["position"]["country"]["code"]
        #airport_origin_city=long_json["airport"]["origin"]["position"]["region"]["city"]
        #airport_origin_terminal=long_json["airport"]["origin"]["info"]["terminal"]
        airport_destination_name=long_json["airport"]["destination"]["name"]
        airport_destination_name=airport_destination_name.replace(" Airport","")
        airport_destination_code=long_json["airport"]["destination"]["code"]["iata"]
        #airport_destination_country=long_json["airport"]["destination"]["position"]["country"]["name"]
        #airport_destination_country_code=long_json["airport"]["destination"]["position"]["country"]["code"]
        #airport_destination_city=long_json["airport"]["destination"]["position"]["region"]["city"]
        #airport_destination_terminal=long_json["airport"]["destination"]["info"]["terminal"]
        #time_scheduled_departure=long_json["time"]["scheduled"]["departure"]
        #time_real_departure=long_json["time"]["real"]["departure"]
        #time_scheduled_arrival=long_json["time"]["scheduled"]["arrival"]
        #time_estimated_arrival=long_json["time"]["estimated"]["arrival"]
        #latitude=long_json["trail"][0]["lat"]
        #longitude=long_json["trail"][0]["lng"]
        #altitude=long_json["trail"][0]["alt"]
        #speed=long_json["trail"][0]["spd"]
        #heading=long_json["trail"][0]["hd"]


        if flight_number:
            print("Flight is called "+flight_number)
        elif flight_callsign:
            print("No flight number, callsign is "+flight_callsign)
        else:
            print("No number or callsign for this flight.")


        # Set up to 6 of the values above as text for display_flights to put on the screen
        # Short strings get placed on screen, then longer ones scroll over each in sequence

        global label1_short
        global label1_long
        global label2_short
        global label2_long
        global label3_short
        global label3_long

        label1_short=flight_number
        label1_long=airline_name
        label2_short=airport_origin_code+"-"+airport_destination_code
        label2_long=airport_origin_name+"-"+airport_destination_name
        label3_short=aircraft_code
        label3_long=aircraft_model

        if not label1_short:
            label1_short=''
        if not label1_long:
            label1_long=''
        if not label2_short:
            label2_short=''
        if not label2_long:
            label2_long=''
        if not label3_short:
            label3_short=''
        if not label3_long:
            label3_long=''


        # optional filter example - check things and return false if you want

        # if altitude > 10000:
        #    print("Altitude Filter matched so don't display anything")
        #    return False

    except (KeyError, ValueError,TypeError) as e:
        print("JSON error")
        print (e)
        return False


    return True


def checkConnection():
    print("Check and reconnect WiFi")
    attempts=10
    attempt=1
    while (not esp.status == adafruit_esp32spi.WL_CONNECTED) and attempt<attempts:
        print("Connect attempt "+str(attempt)+" of "+str(attempts))
        print("Reset ESP...")
        w.feed()
        wifi.reset()
        print("Attempt WiFi connect...")
        w.feed()
        try:
            wifi.connect()
        except OSError as e:
            print(e.__class__.__name__+"--------------------------------------")
            print(e)
        attempt+=1
    if esp.status == adafruit_esp32spi.WL_CONNECTED:
        print("Successfully connected.")
    else:
        print("Failed to connect.")


# Look for flights overhead
def get_flights():
    matrixportal.url=FLIGHT_SEARCH_URL
    try:
        #response = json.loads(matrixportal.fetch())
        response=requests.get(url=FLIGHT_SEARCH_URL,headers=rheaders).json()
    except (RuntimeError,OSError, HttpError, ValueError, requests.OutOfRetries) as e:
        print(e.__class__.__name__+"--------------------------------------")
        print(e)
        checkConnection()
        return False
    if len(response)==3:
        #print ("Flight found.")
        for flight_id, flight_info in response.items():
            # the JSON has three main fields, we want the one that's a flight ID
            if not (flight_id=="version" or flight_id=="full_count"):
                if len(flight_info)>13:
                    return flight_id
    else:
        return False



# Actual doing of things - loop forever quering fr24, processing any results and waiting to query again

checkConnection()

last_flight=''
while True:

    #checkConnection()

    w.feed()

    #print("memory free: " + str(gc.mem_free()))

    #print("Get flights...")
    flight_id=get_flights()
    w.feed()
    

    if flight_id:
        if flight_id==last_flight:
            print("Same flight found, so keep showing it")
        else:
            print("New flight "+flight_id+" found, clear display")
            clear_flight()
            if get_flight_details(flight_id):
                w.feed()
                gc.collect()
                if parse_details_json():
                    gc.collect()
                    plane_animation()
                    display_flight()
                else:
                    print("error parsing JSON, skip displaying this flight")
            else:
                print("error loading details, skip displaying this flight")
            
            last_flight=flight_id
    else:
        #print("No flights found, clear display")
        clear_flight()
    
    time.sleep(5)


    for i in range(0,QUERY_DELAY,+5):
        time.sleep(5)
        w.feed()
    gc.collect()
