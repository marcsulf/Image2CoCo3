# Image2CoCo3
<h1>Brief Description</h1>
<h3>Python utility for converting image files for use with HSCREEN 2 graphics on the Tandy Color Computer 3</h3>

<h1>Files</h1>
<dl>
  <dt><strong>Image2CoCo3_2.py</strong></dt>
  <dd>Python 2.XX version of script</dd>
  <dt><strong>Image2CoCo3_3.py</strong></dt>
  <dd>Python 3.XX version of script</dd>
  <dt><strong>makedisk.bat</strong></dt>
  <dd>Windows batch file for creating a disk image from the
	output either python script using Toolshed "decb.exe"</dd>
</dl>

You will also want to get `decb.exe` from the 
<a href="http://toolshed.sourceforge.net/ToolShed.html">Toolshed utility</a> for 
creating and manipulating DECB CoCo disk images. This is not my work, but I 
highly recommend it for creating and manipulating CoCo disk images and files.

<h1>Libraries Needed</h1>
Both python scripts require the following python libraries in order to work:

<dl>
  <dt><strong>numpy</strong></dt>
  <dd>Only "inf" constant is used by this script. You could just 
		assign a really large number to a variable called inf instead of 
		importing this library if you really don't want to install numpy. 
		But in my experience, this is one of the most useful python 
		libraries out there, so you might as well just install it.</dd>
  <dt><strong>struct</strong></dt>
  <dd>Should be part of the standard python distribution. Used for 
		getting the image data ready and saving it as the .BIN files.</dd>
  <dt><strong>pillow</strong></dt>
  <dd>Python Image Library. Used for resizing the image to CoCo size, 
		and quantizing the image palette to the closest 16 color subset
		of the appropriate CoCo palette.</dd>
  <dt><strong>operator</strong></dt>
  <dd>I'm using the "add" module from this in a map() call.</dd>
</dl>

<h1>Updates</h1>
Update 31-May-19: Corrected a bug in both scripts that prevented "no dithering"
from working correctly.

<h1>Complete Description</h1>

<p>These scripts will take an arbitrary image in just about any standard format, 
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

<p>To create a .DSK image suitable for loading on the CoCo, if you are using 
Windows, you can either drag and drop the .BAS program onto the "makedisk.bat" 
batch file that should be included with this distribution, or call "makedisk 
MYPIC.BAS" from the command line, assuming that all of the files are in the 
same directory as the ToolShed "decb.exe" utility. A similar script could 
easily be constructed for a Linux or Mac system. 

<p>I originally wrote the script in order to create a fancy title screen for a 
game I was writing, so I didn't add a lot of bells and whistles to the load/
display program. Since each image is 32kB, four separate images could be saved 
on one 35 track disk image if desired (or more on a larger disk image), and the 
.BAS file could easily be modified to load any of the images from a selection 
menu, or even cycle through the images like a slideshow. Feel free to modify it 
as you see fit.

