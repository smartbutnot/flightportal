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

FONT=terminalio.FONT

try:
    from secrets import secrets
except ImportError:
    print("Secrets including geo are kept in secrets.py, please add them there!")
    raise

#How often to query fr24 - quick enough to catch a plane flying over, not so often as to cause any issues, hopefully
QUERY_DELAY=30
#Area and altidude to search for flights, see secrets file
BOUNDS_BOX=secrets["bounds_box"]
MAX_ALTITUDE=secrets["max_altitude"]

#Colours and timings
ROW_ONE_COLOUR=0xEE82EE
ROW_TWO_COLOUR=0x4B0082
ROW_THREE_COLOUR=0xFFA500
PLANE_COLOUR=0x4B0082
#Time in seconds to wait between scrolling one label and the next
PAUSE_BETWEEN_LABEL_SCROLLING=3
#speed plane animation will move - pause time per pixel shift in seconds
PLANE_SPEED=0.04
#speed text labels will move - pause time per pixel shift in seconds
TEXT_SPEED=0.04

#URLs
FLIGHT_SEARCH_HEAD="https://data-live.flightradar24.com/zones/fcgi/feed.js?bounds="
FLIGHT_SEARCH_TAIL="&faa=1&satellite=1&mlat=1&flarm=1&adsb=1&gnd=0&air=1&vehicles=0&estimated=0&maxage=14400&gliders=0&stats=0&ems=1&limit=1"
FLIGHT_SEARCH_URL=FLIGHT_SEARCH_HEAD+BOUNDS_BOX+FLIGHT_SEARCH_TAIL
FLIGHT_DETAILS_HEAD="https://api.flightradar24.com/common/v1/flight/list.json?&fetchBy=flight&page=1&limit=1&maxage=14400&query="

#can be used to get more flight details with a fr24 flight ID, but matrixportal runs out of memory with json that big
#FLIGHT_DETAILS_HEAD="https://data-live.flightradar24.com/clickhandler/?flight="

#Request headers
rheaders = {
     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0",
     "cache-control": "no-store, no-cache, must-revalidate, post-check=0, pre-check=0",
     "accept": "application/json"
}

#Top level matrixportal object
matrixportal = MatrixPortal(
    headers=rheaders,
    status_neopixel=board.NEOPIXEL,
    debug=False
)


#Little plane to scroll across when we find a flight overhead
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

#We can fit three rows of text on a panel, one label for each
flight_label = adafruit_display_text.label.Label(
    FONT,
    color=ROW_ONE_COLOUR,
    text="")
flight_label.x = 1
flight_label.y = 4

route_label = adafruit_display_text.label.Label(
    FONT,
    color=ROW_TWO_COLOUR,
    text="")
route_label.x = 1
route_label.y = 15

aircraft_label = adafruit_display_text.label.Label(
    FONT,
    color=ROW_THREE_COLOUR,
    text="")
aircraft_label.x = 1
aircraft_label.y = 25

g = displayio.Group()
g.append(flight_label)
g.append(route_label)
g.append(aircraft_label)
matrixportal.display.show(g)

#Scroll the plane bitmap right to left (so same direction as scrolling text)
def plane_animation():
    matrixportal.display.show(planeG)
    for i in range(matrixportal.display.width+24,-12,-1):
            planeG.x=i
            time.sleep(PLANE_SPEED)
            #matrixportal.display.refresh(minimum_frames_per_second=0)

#Scroll a label, start at the right edge of the screen and go left one pixel at a time
#Until the right edge of the label reaches the left edge of the screen
def scroll(line):
    line.x=matrixportal.display.width
    for i in range(matrixportal.display.width+1,0-line.bounding_box[2],-1):
        line.x=i
        time.sleep(TEXT_SPEED)
        #matrixportal.display.refresh(minimum_frames_per_second=0)
        

#Populate the labels, then scroll longer versions of the text
#Keeps the info on the screen as long as the search loop keeps finding the same plane
#Call clear_flight to blank out the display
def display_flight(sf,lf,sr,lr,sa,la):

    matrixportal.display.show(g)
    flight_label.text=sf
    route_label.text=sr
    aircraft_label.text=sa
    time.sleep(PAUSE_BETWEEN_LABEL_SCROLLING)
    
    flight_label.x=matrixportal.display.width+1
    flight_label.text=lf
    scroll(flight_label)
    flight_label.text=sf
    flight_label.x=1
    time.sleep(PAUSE_BETWEEN_LABEL_SCROLLING)
    
    route_label.x=matrixportal.display.width+1
    route_label.text=lr
    scroll(route_label)
    route_label.text=sr
    route_label.x=1
    time.sleep(PAUSE_BETWEEN_LABEL_SCROLLING)
    
    aircraft_label.x=matrixportal.display.width+1
    aircraft_label.text=la
    scroll(aircraft_label)
    aircraft_label.text=sa
    aircraft_label.x=1
    time.sleep(PAUSE_BETWEEN_LABEL_SCROLLING)

#Blank the display when a flight is no longer found
def clear_flight():
    flight_label.text=route_label.text=aircraft_label.text=""


#Optional: look up plane types from a list based on https://www.avcodes.co.uk/acrtypes.asp
def get_aircraft_name(icao_code):
    if icao_code:
        with open("icao.csv") as f:
            for line in f:
                key=line.split(',')[1]
                val=line.split(',')[2]
                if key==icao_code:
                    return val
    return None


#Take a flight number found overhead and look up route details
#FR24 can find multiple versions of a flight, we take the first one
def get_flight_details(fn):
    if fn:
        matrixportal.url=FLIGHT_DETAILS_HEAD+fn
        try:
            details=json.loads(matrixportal.fetch())
        except (RuntimeError, OSError, HttpError) as e:
            print("Error--------------------------------------------------")
            print(e)
            return None, None, None
        #HttpError: Code 520:
        try:
            flight_data = matrixportal.network.json_traverse(details, ["result"])
            flight_data_response=flight_data["response"]["data"][0]
            if flight_data_response:
                a=flight_data_response["airline"]["name"]
                o=flight_data_response["airport"]["origin"]["name"]
                o_shorter=o.replace(" Airport","")
                d=flight_data["response"]["data"][0]["airport"]["destination"]["name"]
                d_shorter=d.replace(" Airport","")
                #t=flight_data_response["time"]["scheduled"]["departure"]
                return a,o_shorter,d_shorter
        except (KeyError, ValueError,TypeError) as e:
            print("Unexpected JSON")
            return None,None,None
    return None,None,None

#Look for flights overhead
def get_flights():
    matrixportal.url=FLIGHT_SEARCH_URL
    try:
        response = json.loads(matrixportal.fetch())
    except (RuntimeError,OSError, HttpError) as e:
        print("Error--------------------------------------")
        print(e)
        return None, None, None, None, None
    if len(response)==3:
        #print ("Flight found.")
        for flight_id, flight_info in response.items():
            #json has three main fields, we want the one that's a flight ID
            if not (flight_id=="version" or flight_id=="full_count"):
                if len(flight_info)>13:
                    # Check if the flight is currently under the max altitude allowed.
                    current_altitude=flight_info[4]
                    if int(current_altitude)<int(MAX_ALTITUDE):
                        fn=flight_info[13]
                        fc=flight_info[8]
                        an=get_aircraft_name(fc)
                        #an=""
                        oc=flight_info[11]
                        dc=flight_info[12]
                        return fn,an,oc,dc,fc
    else:
        #print("No flights returned.")
        return None,None,None,None,None

#Actual doing of things
last_flight=''
while True:

    #print("Get flights...")
    flight_number,aircraft_name,origin_code,destination_code,flight_code=get_flights()

    if not flight_number==last_flight:
        clear_flight()
        if flight_number:
            print("new flight found, clear display")

            last_flight=flight_number

            airline,origin,destination=get_flight_details(flight_number)


            if airline:
                flight=airline
            else:
                flight=flight_number
        
            if origin_code and destination_code:
                short_route=origin_code+"-"+destination_code
            else:
                short_route=''

            if origin and destination:
                route=origin+" - "+destination
            else: 
                route=short_route
        
            if aircraft_name:
                aircraft=aircraft_name
            else:
                aircraft=flight_code
        
            print(flight+" : "+route+" : "+aircraft)
            plane_animation()
            display_flight(flight_number,flight,short_route,route,flight_code,aircraft)
        else:
            print("no flight found, clear display")
    else:
        print("same flight found, so keep showing it")
    
    time.sleep(QUERY_DELAY)

