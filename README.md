# Image2CoCo3
<h2>Brief Description</h2>
<h3>Python utility for converting image files for use with PMODE graphics on the Tandy Color Computers</h3>

<h2>Files</h2>
<dl>
  <dt><strong>Image2CoCo3_2.py</strong></dt>
  <dd>Python 2.XX version of script</dd>
  <dt><strong>Image2CoCo3_3.py</strong></dt>
  <dd>Python 3.XX version of script</dd>
  <dt><strong>Img2CC3.pyw</strong></dt>
  <dd>Python 3.XX version of script with full Tkinter GUI</dd>
  <dt><strong>makedisk.bat</strong></dt>
  <dd>Windows batch file for creating a disk image from the
	output either python script using Toolshed "decb.exe"</dd>
</dl>

You will also want to get `decb.exe` from the 
<a href="http://toolshed.sourceforge.net/ToolShed.html">Toolshed utility</a> for 
creating and manipulating DECB CoCo disk images. This is not my work, but I 
highly recommend it for creating and manipulating CoCo disk images and files.

<h2>Libraries Needed</h2>
Both command line scripts require the following python libraries in order to work:

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

In addition to those needed for the command line version, the GUI version requires
the following libraries as well:

<dl>
  <dt><strong>tkinter</strong></dt>
  <dd>Required for creating the GUI</dd>
  <dt><strong>os</strong></dt>
  <dd>Required for deleting temporary files</dd>
  <dt><strong>base64</strong></dt>
  <dd>Required for generating the window icon file without having to have it 
	as a separate file.</dd>
</dl>

<h2>Updates</h2>
Update 31-May-19: Corrected a bug in both scripts that prevented "no dithering"
from working correctly.

<h2>Complete Description</h2>

These scripts will take an arbitrary image in just about any standard format, 
of any size and aspect ratio, and convert it to be viewable on a CoCo 2 using 
the user's choice of `PMODE` graphics mode. The program scales the image to fit 
on the selected `PMODE` graphics screen, asking for stretch and/or positioning 
info if the image has a different aspect ratio than the screen. It then dithers 
the image using the correct colors from the selected `PMODE`. Two color `PMODE`s
will automatically be convereted to greyscale before dithering. The program will
automatically select the best `SCREEN` for color images to best match the image
colors. Then it outputs a single `.BIN` file, and an ECB BASIC program which is 
suitable for loading and displaying the image. The `.BAS` program includes 
commenting to make it easier to understand what it is doing.

To create a `.DSK` image suitable for loading on the CoCo, if you are using 
Windows, you can either drag and drop the `.BAS` program onto the `makedisk2.bat` 
batch file that should be included with this distribution, or call `makedisk2 
MYPIC.BAS` from the command line, assuming that all of the files are in the 
same directory as the ToolShed `decb.exe` utility. A similar script could 
easily be constructed for a Linux or Mac system. 

I originally wrote the script in order to create a fancy title screen for a 
game I was writing, so I didn't add a lot of bells and whistles to the load/
display program. Feel free to modify it as you see fit.
