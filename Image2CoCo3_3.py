# -*- coding: utf-8 -*-
"""
Created on Thu May 16 14:39:45 2019
Last Modified Thu May 28, 2019

@author: marcsulf

This script will take an arbitrary image in just about any standard format, of any size and aspect ratio, and convert it to be viewable on a CoCo 3
using the HSCREEN 2 (320x192, 16 color) graphics mode. NOTE: the image file must be in the same directory as this python script for the script to
operate correctly. I do not have any path handling. The program scales the image to fit on HSCREEN 2, asking for stretch and/or positioning info
if the image has a different aspect ratio than the screen. It then dithers the image using a 16 color subset of the CoCo 3 color palette. Then it 
outputs four .BIN files (one for each 8kB bank required for an HSCREEN 2 screen), and a Super ECB BASIC program which is suitable for loading and 
displaying the image. The .BAS program includes the PALETTE needed for proper display of the image, and is commented to make it easier to 
understand what it is doing. 

To create a .DSK image suitable for loading on the CoCo, if you are using Windows, you can just drag and drop the .BAS program onto the 
"makedisk.bat" batch file that should be included with this distribution, assuming that all of the files are in the same directory as the ToolShed 
"decb.exe" utility. A similar script could easily be constructed for a Linux or Mac system.  I originally wrote the script in order to create a 
fancy title screen for a game I was writing, so I didn't add a lot of bells and whistles to the load/display program. Since each image is 32kB, 
four separate images could be saved on one 35 track disk image if desired (or more on a larger disk image), and the .BAS file could easily be 
modified to load any of the images from a selection menu, or even cycle through the images like a slideshow. Feel free to modify it as you see fit.

Values for color palettes on CoCo were found here:
    http://exstructus.com/blog/2017/coco3-colour-palette/
"""
from PIL import Image
import struct
from operator import add
from numpy import inf

"""
This function takes a dictionary (Choices), and a string (Question) as inputs. For the dictionary, the keys are the selection choices, and the 
definitions are a 2-tuple. The first value in the 2-tuple is the return value for the menu, and the second value is a description of the choice.
The string is the prompt question that is displayed asking the user for input.
"""
def MenuChoice(Choices,Question):
    tablen = 8
    while True:
        options=Choices.keys()
        maxlen=0
        for entry in options:
            if len(entry)>maxlen:
                maxlen=len(entry)
        tabs = int(1.0*(maxlen+1)/tablen)+1
        print()
        for entry in options: 
            tabsentry = int(1.0*(len(entry)+1)/tablen)
            space = ":"+"\t"*(tabs-tabsentry)
            print (entry+space+ Choices[entry][1])
        Choice = input(Question)
        if Choice in options:
            return Choices[Choice][0]
            break
        else:
            print("Invalid input!")

#Coco HSCREEN 2 width, height, and palette size
CCMaxW = 320
CCMaxH = 192
CCPalSize = 16
CCRatio = 1.0*CCMaxH/CCMaxW

"""
Python list with the lines used in the BASIC CoCo display program. This is mostly a copy from "300 Peeks, Pokes, and Execs for the CoCo 3".
It is corrected for a missing "NEXT" statement and commented. Once the name and palette are found, this will be exported into a .BAS file.
"""
CCDispProg = ["""10 POKE 65497,0'SPEED UP""","""20 CLEAR 200,&H6000'SET MEM LOC TO START DATA LOAD""",'30 A$="','"',"""40 FOR H=1TO4'LOOP THROUGH 4 IMAGE FILES""","""50 POKE &HFFA3,48+H-1'SET MEM BANK FOR APPROPRIATE FILE""","""60 LOADM A$+STR$(H)'LOAD IMAGE FILE""",'70 NEXT',"""80 POKE &HFFA3,123'GO BACK TO ORIGINAL MEM BANK""","""90 CLEAR 200,&H7FFF'RESET TOP OF BASIC""","""100 POKE &HE6C6,18:POKE &HE6C7,18'DISABLE HCLS DURING HSCREEN""","""120 FOR S=0TO15'LOOP THROUGH PALETTE SLOTS""","""130 READ C'LOAD COLOR FOR THAT SLOT""","""140 PALETTE S,C'STORE COLOR IN SLOT""",'150 NEXT',"""160 HSCREEN 2'DISPLAY THE IMAGE""","""170 A$=INKEY$:IF A$="" THEN 170'WAIT FOR KEYPRESS TO EXIT""","""175 RGB:POKE 65496,0'RESET PALETTE, SLOW DOWN AND EXIT""",'180 DATA ']

"""
Useful constants for processing BMP files. 
BytesPerPalette is B,G,R, and a zero byte
The 9 BMP HeadVals are "BM", File Size, Reserved, DataStart, HeaderSize, W, H, Planes, bpp
LHead is the head size in bytes
Offset is used to get to the right spot in the file after extracting the 9 HeadVals in the struct
"""
bitsPerByte = 8
BytesPerPalette = 4
HeadVals = 9
BMPHeaderFormat="<2s6I2H"
LHead = struct.calcsize(BMPHeaderFormat)
Offset = LHead-HeadVals

"""
Useful constants for the CoCo bin file format
ImagefileHead (top of each file), and ImagefileFoot (bottom of each file) were extracted from the HSCREEN 2 graphics files saved from the CoCo 3
using the save program found in "300 Peeks, Pokes, and Execs for the CoCo 3", and corrected to add the missing "NEXT" statement.
The HSCREEN 2 screen has to be spread across 4 different 8KB banks, which is easiest to do by splitting it into 4 different bin files
These four files each have a size of exactly 8KB, which is stored in LImageFileMax
In addtion to the actual image data, an additional 2KB of zeros are tacked on to the bottom of the data to make it fit exactly into the 4 8KB banks
Those extra zeros are stored in TailData, and TailColor and LTailData are used to create it
"""
ImagefileHead=b"\x00\x20\x00\x60\x00"
ImagefileFoot=b"\xff\x00\x00\x00\x00"
LImagefileMax = 8192
TailColor = 0
LTailData = 2048
TailData = struct.pack('B',TailColor+(TailColor<<4))*LTailData

"""
***************************************************************************************************************
These are the input variables for using this script
***************************************************************************************************************
"""
filename=input("""Please provide the filename of the image file.
Note: 6 characters or less for the base of the name is best: """)
while True:
    Choice = input("Will you be displaying the picture on an (R)GB (recommended) or (C)MP monitor? ")
    if Choice[0].upper()=="R":
        #These names are found in "CoCo 3 Secrets Revealed"
        CCNames = ["Black","Dark Blue","Dark Green","Dark Cyan","Dark Red","Dark Magenta","Brown","Dark Grey","Medium Blue","Bright Blue","Light Blue/Cyan","Light Blue","Indigo","Medium Blue/Purple","Medium Sky Blue","Medium Peacock","Medium Green","Medium Green/Cyan","Bright Green","Medium Yellow/Green","Light Yellow/Green","Light Green/Cyan","Bright Yellow/Green","Light Green","Pale Green/Cyan","Peacock","Light Green/Cyan","Bright Cyan","Light Peacock","Pale Peacock","Pale Green/Cyan","Light Cyan","Medium Red","Medium Red/Magenta","Yellow/Orange","Light Red","Bright Red","Light Red/Magenta","Orange","Pale Red/Magenta","Medium Blue/Magenta","Blue/Purple","Light Magenta","Purple","Light Purple","Bright Magenta","Pale Blue/Magenta","Pale Purple","Medium Yellow","Light Yellow","Light Yellow/Green","Pale Yellow/Green","Light Yellow/Orange","Medium Yellow","Bright Yellow","Pale Yellow","Light Grey","Pale Blue","Pale Cyan","Pale Blue/Cyan","Pale Red","Pale Magenta","Very Pale Yellow","White"]
        #These color palette values were found here at http://exstructus.com/blog/2017/coco3-colour-palette/
        R_CC = [0,0,0,0,85,85,85,85,0,0,0,0,85,85,85,85,0,0,0,0,85,85,85,85,0,85,0,0,85,85,85,85,170,170,170,170,255,255,255,255,170,170,170,170,255,255,255,255,170,170,170,170,255,255,255,255,170,170,170,170,255,255,255,255]
        G_CC = [0,0,85,85,0,0,85,85,0,0,85,85,0,0,85,85,170,170,255,255,170,170,255,255,170,255,255,255,170,170,255,255,0,0,85,85,0,0,85,85,0,0,85,85,0,0,85,85,170,170,255,255,170,170,255,255,170,170,255,255,170,170,255,255]
        B_CC = [0,85,0,85,0,85,0,85,170,255,170,255,170,255,170,255,0,85,0,85,0,85,0,85,170,255,170,255,170,255,170,255,0,85,0,85,0,85,0,85,170,255,170,255,170,255,170,255,0,85,0,85,0,85,0,85,170,255,170,255,170,255,170,255]
        break
    elif Choice[0].upper()=="C":
        CCDispProg[17]="""175 CMP:POKE 65496,0'RESET PALETTE, SLOW DOWN AND EXIT"""
        #These names are found in "CoCo 3 Secrets Revealed"
        CCNames = ["Black","Light Green/Cyan","Dark Green","Light Yellow/Green","Light Yellow","Brown","Light Red","Dark Red","Medium Red/Magenta","Dark Magenta","Medium Sky Blue","Indigo","Dark Blue","Light Blue/Cyan","Dark Cyan","Light Peacock","Dark Grey","Medium Green/Cyan","Bright Green","Bright Yellow/Green","Medium Yellow","Yellow/Orange","Medium Red","Light Red/Magenta","Light Purple","Medium Blue/Magenta","Light Magenta","Medium Blue/Purple","Medium Blue","Light Blue","Pale Green/Cyan","Light Green/Cyan","Light Grey","Medium Yellow/Green","Medium Green","Light Yellow/Green","Bright Yellow","Light Yellow/Orange","Orange","Bright Red","Pale Blue/Magenta","Bright Magenta","Blue/Purple","Medium Peacock","Bright Blue","Peacock","Bright Cyan","Pale Green/Cyan","White","Pale Cyan","Light Green","Pale Yellow/Green","Pale Yellow","Medium Yellow","Pale Red/Magenta","Pale Red","Pale Purple","Pale Magenta","Purple","Pale Blue","Pale Peacock","Light Cyan","Pale Blue/Cyan","Very Pale Yellow"]
        #These color palette values were found here at http://exstructus.com/blog/2017/coco3-colour-palette/
        R_CC = [0,14,12,21,51,86,108,118,113,92,61,21,1,5,12,13,50,29,49,86,119,158,179,192,186,165,133,94,23,16,23,25,116,74,102,142,179,219,243,252,251,230,198,155,81,61,52,57,253,137,161,189,215,240,253,253,251,237,214,183,134,121,116,255]
        G_CC = [0,78,69,53,33,4,1,1,12,24,31,35,37,51,67,77,50,149,141,123,103,77,55,39,35,43,53,63,100,119,137,148,116,212,204,186,164,137,114,97,88,89,96,109,156,179,199,211,253,230,221,207,192,174,158,148,143,144,150,162,196,212,225,255]
        B_CC = [0,20,18,14,10,10,12,19,76,135,178,196,148,97,29,20,50,38,36,32,28,25,24,78,143,207,248,249,228,174,99,46,116,58,52,48,44,41,68,132,202,250,250,250,251,243,163,99,254,104,83,77,82,105,142,188,237,251,251,251,252,240,183,255]
        break
    else:
        print("Invalid input!")        
#creates a list of the (R,G,B) triplets for each Color Computer color
CC_Colors = [i for i in zip(R_CC,G_CC,B_CC)]
ColorNameChoices={}
i=0
for name in CCNames:
    if i<10:
        key="0"+str(i)
    else:
        key=str(i)
    ColorNameChoices[key]=(CC_Colors[i],CCNames[i])
    i+=1
# open the source image, put it in RGB mode, and find its size and aspect ratio
image = Image.open(filename)
image = image.convert("RGB")
(width,height) = image.size
ratio = 1.0*height/width
#If the image isn't the same aspect ratio as HSCREEN 2, tell the script how to position the image on HSCREEN 2
VPosChoices = {"t":(0,"Top"),"c":(1,"Center"),"b":(2,"Bottom")}
HPosChoices = {"l":(0,"Left"),"c":(1,"Center"),"r":(2,"Right")}
HPos = 1 #0 = left, 1 = center, 2 = right
VPos = 1 #0 = top, 1 = center, 2 = bottom
Stretch = 0 # If this is 1, the image will be stretched to fill the screen
while not(ratio==CCRatio):
    Choice = input("""The image is not the same aspect ratio as the screen. 
Do you want to strech the image to fill the screen? """)
    if Choice[0].upper()=="Y":
        HPos = 1 #0 = left, 1 = center, 2 = right
        VPos = 1 #0 = top, 1 = center, 2 = bottom
        Stretch = 1 # If this is 1, the image will be stretched to fill the screen
        break
    elif Choice[0].upper()=="N":
        Stretch = 0
        while True:
            Choice1 = input("""Do you want to change the background color [default: black]? """)
            if Choice1[0].upper()=="Y":
                #Color used for the background color on the screen if the image doesn't fill the full screen
                BackColor = MenuChoice(ColorNameChoices,"Select a background color from the list: ")
                break
            elif Choice1[0].upper()=="N":
                #Color used for the background color on the screen if the image doesn't fill the full screen
                BackColor = '#000000' 
                break
            else:
                print("Invalid input!")        
        if ratio < CCRatio:
            HPos = 1 #0 = left, 1 = center, 2 = right
            VPos = MenuChoice(VPosChoices,"How would you like to position the image on the screen? ")
        else:
            VPos = 1 #0 = left, 1 = center, 2 = right
            HPos = MenuChoice(HPosChoices,"How would you like to position the image on the screen? ")
        break
    else:
        print("Invalid input!")
while True:
    Choice = input("""Dithering (recommended) interleaves colors from the available palette to approximate other colors. 
Do you want to dither the image to match the colors more closely? """)
    if Choice[0].upper()=="Y":
        ditherValue = Image.FLOYDSTEINBERG
        break
    elif Choice[0].upper()=="N":
        ditherValue = Image.NONE
        break
    else:
        print("Invalid input!")        
"""
***************************************************************************************************************
"""

#useful variations of the filename used for saving the various files needed
name = filename.split(".")[0]
name = name.upper()[:8]
truncname = name[:6]

#Combined Palette, with full 256*3 palette used by PIL
#flatten the 64 RGB triplets into a single list
CCcomb =[]
for i in CC_Colors:
    CCcomb.extend(i)

#pad with zeros to the full 256*3 length
CCcomb+= [0, ] * 192 * 3 

#The following lines are used to import the image file, and convert it to an 320x192x16color image based on the available CoCo colors
# a palette image used to store the CoCo colors
pimage = Image.new("P", (1, 1), 0)
pimage.putpalette(CCcomb)
#Resize the image to fit on HSCREEN 2, maintaining the image aspect ratio
if Stretch==1:
    image = image.resize((CCMaxW,CCMaxH),Image.ANTIALIAS)
elif ratio<CCRatio:
    image = image.resize((CCMaxW,int(ratio*CCMaxW)),Image.ANTIALIAS)
else:
    image = image.resize((int(CCMaxH/ratio),CCMaxH),Image.ANTIALIAS)
#Store the size of the resized image
(width,height) = image.size
#if the image aspect ratio doesn't match HSCREEN 2 aspect ratio, find the offsets to place the image on HSCREEN 2 based on the two inputs HPos and VPos
#Then create an image file filled with BackColor, and the paste the image into this image at the appropriate offset location
if Stretch==0 and not(width==CCMaxW and height==CCMaxH):
    if width==CCMaxW:
        HOff = 0
        if VPos == 0:
            VOff = 0
        elif VPos == 1:
            VOff = int((CCMaxH-height)/2)
        else:
            VOff = CCMaxH-height
    else:
        VOff = 0
        if HPos == 0:
            HOff = 0
        elif HPos == 1:
            HOff = int((CCMaxW-width)/2)
        else:
            HOff = CCMaxW-width
    image2 = image
    image = Image.new("RGB",(CCMaxW,CCMaxH),BackColor)
    image.paste(image2,(HOff,VOff))
#dither the image based on the CoCo available colors, and find the best 16 color palette to represent this image, then save the results to a BMP file
if ditherValue==Image.FLOYDSTEINBERG:
    imagep = image.quantize(palette=pimage)
else:
    imagep = image.convert(dither=ditherValue,palette=pimage)
imagep = imagep.quantize(colors=CCPalSize)
imagep.save(name+'.BMP')#NOTE: despite this only using 16 colors, a full 256 color palette is stored. The 16 colors used are in the first 16 slots, then padded with zeros

#These lines load the BMPfile into a string called fileContent, and then extract the header data into a tuple called data
with open(name+'.BMP', mode='rb') as file: # b is important -> binary
    fileContent = file.read()
L=len(fileContent)
data=struct.unpack(BMPHeaderFormat+"B"*(L-LHead),fileContent)

#This loads the important header data (DataStart=the byte where image data starts, W=image width in pixels, H=image height in pixels, and bpp=bits per pixel).
Null,Null,Null,DataStart,Null,W,H,Null,bpp=data[:HeadVals]

#Bpp is bytes per pixel representing the image. ImgRowWidth is the width in bytes of an image row, and LImage is the total length in bytes of the image data
Bpp = 1.0*bpp/bitsPerByte
ImgRowWidth = int(W*Bpp)
LImage = H*ImgRowWidth

"""
BMP data starts at the bottom of the image and goes up by rows. CoCo image data starts at the top and goes down by rows
The BMP file created from PIL uses a full byte per pixel, while a CoCo image only uses a nibble per pixel.
This section reverses the row order, and crunches the bytes in the BMP down to nibbles, then packs them together again
"""
ImageContent = b""
for row in range(H): #go through the data one row at a time
    rowStart = DataStart+row*ImgRowWidth #find the start of the row data
    rowData = fileContent[rowStart:rowStart+ImgRowWidth] #grab the row data
    if bpp==8: #makes sure the BMP is actually stored as 8 bit color
        A=list(struct.unpack('B'*len(rowData),rowData)) #unpack the row data as bytes in a list
        B=list(map(add,[i<<4 for i in A[::2]],A[1::2])) #Shift the bits in the even bytes by 4 places, then add that to the odd bytes to pack two pixels into one byte
        rowData = b''#clear the 1 Bpp row data
        rowData =b"".join([struct.pack('B',i) for i in B]) #store the new 0.5 Bpp row data as a string
    ImageContent = rowData+ImageContent #and put that row data at the top of the image
ImageContent+=TailData #tack on the 2KB of zeros to complete the CoCo image data

#This section creates the 4 CoCo .BIN files used that comprise the HSCREEN 2 image
fileImages = []
for i in range(4):
    fileImage=ImagefileHead+ImageContent[i*LImagefileMax:(i+1)*LImagefileMax]+ImagefileFoot #grab the appropriate 8KB chunk of image data, and tack the CoCo image file header and footer to that data
    fileImages.append(fileImage) #store that data in the list fileImages used for the image file data. This is not really needed, but could be used later for something...
    with open(truncname+" "+str(i+1)+".BIN",'wb') as outfile: #open the .BIN file
        outfile.write(fileImage) #and store the data there

#These numbers are useful for finding the color vales for the CoCo Palette
PaletteSize = 2**bpp #this is the palette size in the BMP, not the CoCo. Should be 256
LPalette = BytesPerPalette*PaletteSize #This is the size in bytes of the BMP palette data
PaletteStart = DataStart-LPalette-Offset #this is where the palette data starts in data
Palette = data[PaletteStart:DataStart-Offset-1]#so this is the actual BMP palette

#This loop extracts the R,G,and B values from the BMP palette into separate lists, ignoring the zero byte for each entry
i=0
R=[]
G=[]
B=[]
for num in Palette:
    if i%BytesPerPalette==0:
        B.append(num)
    elif (i-1)%BytesPerPalette==0:
        G.append(num)
    elif (i-2)%BytesPerPalette==0:
        R.append(num)
    i+=1

#This zips the R,G,B values for each color into 3-tuples
BMPPAL=[i for i in zip(R,G,B)]

#This loop finds the CoCo available color that best matches each BMP Palette entry
CCPal = []
for color in BMPPAL: #for each BMP color
    mindist=inf #initialize the best distance as infinity
    i=0
    bestslot = 64 #assign the initial best color as a non-existant CoCo color
    for slot in CC_Colors: #go through each CoCo color
        dist=(color[0]-slot[0])**2+(color[1]-slot[1])**2+(color[2]-slot[2])**2 #find how far BMP color is from CoCo color
        if dist<mindist: #if it is closer than the current best, then it is the new best
            bestslot = i #make the current color the best one
            mindist = dist #set the current distance to the best distance
        i+=1
    CCPal.append(bestslot) #append the best color to the palette

#truncate the Palette at the 16 non-dummy colors
CCPalTrunc = CCPal[:CCPalSize]
#convert the palette color numbers into a string that is usable for the BASIC program
PalStr = str(CCPalTrunc)[1:-1]

#Now that the name and palette data are found, assemble the basic program into a text file
with open(name+".BAS",'w+') as outfile:
    for line in CCDispProg:
        if line=='30 A$="':
            line+=truncname
        elif line=='180 DATA ':
            line+=PalStr+'\r'
        else:
            line+='\r'
        outfile.write(line)
