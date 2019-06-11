# Image2CoCo3
Python utility for converting image files for use with HSCREEN 2 graphics on the Tandy Color Computer 3

Image2CoCo3_2.py	Python 2.XX version of script
Image2CoCo3_3.py	Python 3.XX version of script
makedisk.bat		Windows batch file for creating a disk image from the
			output either python script using Toolshed "decb.exe"
decb.exe		Toolshed utility for creating and manipulating DECB
			CoCo disk images. This is not my work. It comes out 
			of the Toolshed open source distribution.
readme.txt		This file


Both python scripts require the following python libraries in order to work:

numpy 		Only "inf" constant is used by this script. You could just 
		assign a really large number to a variable called inf instead of 
		importing this library if you really don't want to install numpy. 
		But in my experience, this is one of the most useful python 
		libraries out there, so you might as well just install it.
struct 		Should be part of the standard python distribution. Used for 
		getting the image data ready and saving it as the .BIN files.
pillow		Python Image Library. Used for resizing the image to CoCo size, 
		and quantizing the image palette to the closest 16 color subset
		of the appropriate CoCo palette.
operator	I'm using the "add" module from this in a map() call.


Update 31-May-19: Corrected a bug in both scripts that prevented "no dithering"
from working correctly.

These scripts will take an arbitrary image in just about any standard format, 
of any size and aspect ratio, and convert it to be viewable on a CoCo 3 using 
the HSCREEN 2 (320x192, 16 color) graphics mode. NOTE: the image file must be 
in the same directory as this python script for the script to operate correctly. 
I do not have any path handling. The program scales the image to fit on HSCREEN 
2, asking for stretch and/or positioning info if the image has a different 
aspect ratio than the screen. It then dithers the image using a 16 color subset 
of the CoCo 3 color palette. Then it outputs four .BIN files (one for each 8kB 
bank required for an HSCREEN 2 screen), and a Super ECB BASIC program which is 
suitable for loading and displaying the image. The .BAS program includes the 
PALETTE needed for proper display of the image, and is commented to make it 
easier to understand what it is doing. 

To create a .DSK image suitable for loading on the CoCo, if you are using 
Windows, you can either drag and drop the .BAS program onto the "makedisk.bat" 
batch file that should be included with this distribution, or call "makedisk 
MYPIC.BAS" from the command line, assuming that all of the files are in the 
same directory as the ToolShed "decb.exe" utility. A similar script could 
easily be constructed for a Linux or Mac system. 

I originally wrote the script in order to create a fancy title screen for a 
game I was writing, so I didn't add a lot of bells and whistles to the load/
display program. Since each image is 32kB, four separate images could be saved 
on one 35 track disk image if desired (or more on a larger disk image), and the 
.BAS file could easily be modified to load any of the images from a selection 
menu, or even cycle through the images like a slideshow. Feel free to modify it 
as you see fit.

