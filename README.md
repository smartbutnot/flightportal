# flightportal
Project for displaying the details of planes overhead on an Adafruit MatrixPortal and LED matrix

(video sped up to make the file fit, the speeds and delays are configurable anyway)

https://user-images.githubusercontent.com/103124527/206902629-1f31bd41-d8a8-415e-a35a-625efb20b3d6.MOV

Uses an Adafruit MatrixPortal and a 64x32 LED/RGB Matrix (P4), and some fairly hacked-together FlightRadar24 API-style scraping to display the details of flights passing overhead. That code being unofficial, it may break at any time!

To make one you will need:

1. A [MatrixPortal M4](https://www.adafruit.com/product/4745)
2. A P4, 64x32 RGB matrix panel (I get mine from Aliexpress, also [available from Adafruit](https://www.adafruit.com/product/2278))
3. The [3D printed case](https://www.thingiverse.com/thing:5701517) I designed
4. [Adafruit acrylic diffuser](https://www.adafruit.com/product/4749) - available various places
5. 6 M3 screws (sorry, said M5 before but was looking at the wrong ones, my bad. Think mine are 8mm long, little bit more would be OK, shorter probably a problem)
6. Optional: [Uglu dashes](https://www.protapes.com/products/uglu-600-dashes-sheets) to stick the diffuser on, the case holds mine on pretty well though

## Software setup

You can automate the library installation via [CircUp](https://github.com/adafruit/circup), easily installed via [uv](https://github.com/astral-sh/uv).

> [!CAUTION]
> If you do not use CircUp, you will need to manually copy the libraries and their dependencies listed in step 3 below to the CIRCUITPY drive.


1. Prep the portal as detailed in the [Adafruit MatrixPortal guide](https://learn.adafruit.com/adafruit-matrixportal-m4/prep-the-matrixportal).
2. Install [CircUp](https://github.com/adafruit/circup), the CircuitPython library manager:

   ```shell
   uv tool install circup
   ```

3. Connect the MatrixPortal to your computer and install the required libraries:

   ```shell
   circup install adafruit_fakerequests adafruit_requests adafruit_bitmap_font adafruit_io adafruit_matrixportal adafruit_minimqtt adafruit_display_text adafruit_portalbase
   ```

4. Copy `code.py` and `settings.toml` to the root of the `CIRCUITPY` drive.
5. Edit `settings.toml` with your Wi-Fi details and the geographic bounding box you want to search.

The portal should now be ready to run. If you'd like to change the layout, colours or the flight info displayed, have a look at `code.py`; these are configurable near the top of the file.

For power, the easiest thing is to use the cable that came with your matrix panel, as long as it has two prongs that go to the screws on the matrixportal. All that's needed is for the portal to connect to the power port on the panel - we're not using much power here (I clock it at about 2w). Any decent usb power supply connected to the portal should do it.

![IMG-2179](https://user-images.githubusercontent.com/103124527/208709167-dd4b6ff2-4c80-4e38-840f-e5b958e2ed78.jpg)

I soldered a connection straight onto the panel's power port as below, for neatness, but that's completely optional.

![IMG_2125](https://user-images.githubusercontent.com/103124527/206903066-7af5c076-101e-4598-b3ba-0f64766e4162.jpg)
![IMG_2126_small](https://user-images.githubusercontent.com/103124527/206903084-42378ce0-b8d8-4810-a18a-f35b9a509752.jpg)
![IMG_2127_small](https://user-images.githubusercontent.com/103124527/206903089-16d0f7f7-2dc0-4082-a012-0e1c9999a63a.jpg)
![IMG_2128_small](https://user-images.githubusercontent.com/103124527/206903092-0a131b80-cd20-4c8c-b892-9b0a5c1d544b.jpg)

## Debugging over serial

If the MatrixPortal is in a reboot loop or does not display output, connect to its serial device at rate 115200 to observe the script's output.

### Using discotool (recommended)

[discotool](https://github.com/Neradoc/discotool) can assist with identifying the correct serial port and connecting to it automatically.


```shell
uv tool install discotool
```

> [!NOTE]
> As of writing, the latest discotool v0.5.8 has a [packaging issue](https://github.com/Neradoc/discotool/issues/18) that can cause `ModuleNotFoundError: No module named 'appdirs'` after installation with `uv tool`. If you encounter it, reinstall Discotool with the missing dependency:
>
> ```shell
> uv tool install --reinstall --with 'appdirs>=1.4.4' 'discotool==0.5.8'
> ```

Then connect your MatrixPortal over USB and monitor the serial output:

```shell
discotool repl
```

The output includes helpful messages about errors and the flights the portal sees. You can also paste the URLs shown in the output into a browser to check that they return flights.

`Ctrl+C` will interrupt the running script and allow you to enter Python REPL, `Ctrl+D` soft-reboots.

### Connecting manually

Without `discotool` to discover your MatrixPortal, tools like `putty` or `screen` can connect to the serial device the MatrixPortal exposes using baud rate 115200. Check Device Manager for COM ports on Windows or look at `/dev/tty.usbmodem*` devices on MacOS to identify the correct serial device to connect to.

See Adafruit's [Connecting to the Serial Console](https://learn.adafruit.com/welcome-to-circuitpython/kattni-connecting-to-the-serial-console) documentation for details.