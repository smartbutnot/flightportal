# flightportal
Project for displaying the details of planes overhead on an Adafruit MatrixPortal and LED matrix

(video sped up to make the file fit, the speeds and delays are configurable anyway)

https://user-images.githubusercontent.com/103124527/206902629-1f31bd41-d8a8-415e-a35a-625efb20b3d6.MOV

Uses an Adafruit MatrixPortal and a 64x32 LED/RGB Matrix (P4), and some fairly hacked-together FlightRadar24 API-style scraping to display the details of flights passing overhead. That code being unoffical, it may break at any time!

To make one you will need:

1. A MatrixPortal (https://www.adafruit.com/product/4745)
2. A P4, 64x32 RGB matrix panel (I get mine from Aliexpress)
3. The case I designed (https://www.thingiverse.com/thing:5701517)
4. An adafruit acrylic diffuser (https://www.adafruit.com/product/4749) - available various places
5. 6 M5 screws
6. Optional: Uglu dashes to stick the diffuser on, the case holds mine on pretty well though (https://www.protapes.com/products/uglu-600-dashes-sheets)

Prep the portal as detailed here (https://learn.adafruit.com/adafruit-matrixportal-m4/prep-the-matrixportal), put the code, secrets and icao files on, put your wifi details and the geo box you want to search in the secrets file, and you should be good to go!

I soldered a connection straight onto the panel's power port as below, because there's plenty of power for this amount of pixels coming straight through the USB c connection on the MatrixPortal. YOu should also be able to use the power lead that will come with the panel to do this.

![IMG_2125](https://user-images.githubusercontent.com/103124527/206903066-7af5c076-101e-4598-b3ba-0f64766e4162.jpg)
![IMG_2126_small](https://user-images.githubusercontent.com/103124527/206903084-42378ce0-b8d8-4810-a18a-f35b9a509752.jpg)
![IMG_2127_small](https://user-images.githubusercontent.com/103124527/206903089-16d0f7f7-2dc0-4082-a012-0e1c9999a63a.jpg)
![IMG_2128_small](https://user-images.githubusercontent.com/103124527/206903092-0a131b80-cd20-4c8c-b892-9b0a5c1d544b.jpg)
