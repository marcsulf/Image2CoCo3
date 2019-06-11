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

import struct
import os
import base64
from PIL import Image
from operator import add
from numpy import inf
import tkinter as tk
from tkinter import ttk
from tkinter.colorchooser import askcolor
from tkinter.filedialog import askopenfilename
from tkinter import messagebox as tkMB

class Img2CC3:
    #Coco HSCREEN 2 width, height, and palette size
    CCMaxW = 320
    CCMaxH = 192
    CCPalSize = 16
    CCRatio = 1.0*CCMaxH/CCMaxW
    #scaling for the preview window
    prevratio = 2
    prevW = int(CCMaxW/prevratio)
    prevH = int(CCMaxH/prevratio)
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
    
    def __init__(self,fullname,**kwargs):
        self.options = {
                'fullname' : fullname,
                'BackColor' : '#000000',
                'palette' : 0,
                'dither' : Image.FLOYDSTEINBERG,
                'Stretch' : 0,
                'HPos' : 1,
                'VPos' : 1 }
        self.fullname_init = fullname
        self.previmage=None
        self.init = True
        self.update(fullname=fullname)
        self.init = False

    def update(self, **kwargs):
        self.options.update(kwargs)
        if 'fullname' in kwargs.keys():
            if self.init:
                self.image = Image.new("RGB",(self.CCMaxW,self.CCMaxH),self.options['BackColor'])
            else:
                try:
                    self.image = Image.open(self.options['fullname'])
                    self.image = self.image.convert("RGB")
                    splitname = self.options['fullname'].split('/')
                    #useful variations of the filename used for saving the various files needed
                    self.filename = splitname[-1]
                    self.filepath = "/".join(splitname[:-1])
                    self.namebase = self.filename.split(".")[0]
                    self.name = self.namebase.upper()[:8]
                    self.truncname = self.namebase.upper()[:6]
                except:
                    tkMB.showwarning("Open file","Cannot open file "+self.options['fullname'])
                    self.options['fullname'] = self.fullname_init
                    return
            (self.width,self.height) = self.image.size
            self.ratio = 1.0*self.height/self.width

    def getprev(self):
            newimage = self.getimagep().convert("RGB")
            newimage=newimage.resize((self.prevW,self.prevH),Image.ANTIALIAS)
            newimage=newimage.convert("P")
            newimage.save(self.namebase+"_prev.gif")
            self.previmage = tk.PhotoImage(file=self.namebase+"_prev.gif")
            return self.previmage
    
    def getimagep(self):
        image=self.image
        #The following lines are used to import the image file, and convert it to an 320x192x16color image based on the available CoCo colors
        # a palette image used to store the CoCo colors
        pimage = Image.new("P", (1, 1), 0)
        pimage.putpalette(self.getpalette())
        #Resize the image to fit on HSCREEN 2, maintaining the image aspect ratio
        if self.options['Stretch']==1:
            image = image.resize((self.CCMaxW,self.CCMaxH),Image.ANTIALIAS)
        elif self.ratio<self.CCRatio:
            image = image.resize((self.CCMaxW,int(self.ratio*self.CCMaxW)),Image.ANTIALIAS)
        else:
            image = image.resize((int(self.CCMaxH/self.ratio),self.CCMaxH),Image.ANTIALIAS)
        #Store the size of the resized image
        (width,height) = image.size
        #if the image aspect ratio doesn't match HSCREEN 2 aspect ratio, find the offsets to place the image on HSCREEN 2 based on the two inputs HPos and VPos
        #Then create an image file filled with BackColor, and the paste the image into this image at the appropriate offset location
        if self.options['Stretch']==0 and not(width==self.CCMaxW and height==self.CCMaxH):
            if width==self.CCMaxW:
                HOff = 0
                if self.options['VPos'] == 0:
                    VOff = 0
                elif self.options['VPos'] == 1:
                    VOff = int((self.CCMaxH-height)/2)
                else:
                    VOff = self.CCMaxH-height
            else:
                VOff = 0
                if self.options['HPos'] == 0:
                    HOff = 0
                elif self.options['HPos'] == 1:
                    HOff = int((self.CCMaxW-width)/2)
                else:
                    HOff = self.CCMaxW-width
            newimage = image
            image = Image.new("RGB",(self.CCMaxW,self.CCMaxH),self.options['BackColor'])
            image.paste(newimage,(HOff,VOff))
        #dither the image based on the CoCo available colors, and find the best 16 color palette to represent this image, then save the results to a BMP file
        if self.options['dither']==Image.FLOYDSTEINBERG:
            imagep = image.quantize(palette=pimage)
        else:
            imagep = image.convert(dither=self.options['dither'],palette=pimage)
        imagep = imagep.quantize(colors=self.CCPalSize)
        imagep.save(self.namebase+'_data.BMP')#NOTE: despite this only using 16 colors, a full 256 color palette is stored. The 16 colors used are in the first 16 slots, then padded with zeros
        return imagep
    
    def getpalette(self):
        if self.options['palette']==0:
            self.CCDispProg[17]="""175 RGB:POKE 65496,0'RESET PALETTE, SLOW DOWN AND EXIT"""
            #These color palette values were found here at http://exstructus.com/blog/2017/coco3-colour-palette/
            R_CC = [0,0,0,0,85,85,85,85,0,0,0,0,85,85,85,85,0,0,0,0,85,85,85,85,0,85,0,0,85,85,85,85,170,170,170,170,255,255,255,255,170,170,170,170,255,255,255,255,170,170,170,170,255,255,255,255,170,170,170,170,255,255,255,255]
            G_CC = [0,0,85,85,0,0,85,85,0,0,85,85,0,0,85,85,170,170,255,255,170,170,255,255,170,255,255,255,170,170,255,255,0,0,85,85,0,0,85,85,0,0,85,85,0,0,85,85,170,170,255,255,170,170,255,255,170,170,255,255,170,170,255,255]
            B_CC = [0,85,0,85,0,85,0,85,170,255,170,255,170,255,170,255,0,85,0,85,0,85,0,85,170,255,170,255,170,255,170,255,0,85,0,85,0,85,0,85,170,255,170,255,170,255,170,255,0,85,0,85,0,85,0,85,170,255,170,255,170,255,170,255]
        elif self.options['palette']==1:
            self.CCDispProg[17]="""175 CMP:POKE 65496,0'RESET PALETTE, SLOW DOWN AND EXIT"""
            #These color palette values were found here at http://exstructus.com/blog/2017/coco3-colour-palette/
            R_CC = [0,14,12,21,51,86,108,118,113,92,61,21,1,5,12,13,50,29,49,86,119,158,179,192,186,165,133,94,23,16,23,25,116,74,102,142,179,219,243,252,251,230,198,155,81,61,52,57,253,137,161,189,215,240,253,253,251,237,214,183,134,121,116,255]
            G_CC = [0,78,69,53,33,4,1,1,12,24,31,35,37,51,67,77,50,149,141,123,103,77,55,39,35,43,53,63,100,119,137,148,116,212,204,186,164,137,114,97,88,89,96,109,156,179,199,211,253,230,221,207,192,174,158,148,143,144,150,162,196,212,225,255]
            B_CC = [0,20,18,14,10,10,12,19,76,135,178,196,148,97,29,20,50,38,36,32,28,25,24,78,143,207,248,249,228,174,99,46,116,58,52,48,44,41,68,132,202,250,250,250,251,243,163,99,254,104,83,77,82,105,142,188,237,251,251,251,252,240,183,255]
        self.CC_Colors = [i for i in zip(R_CC,G_CC,B_CC)]
        #Combined Palette, with full 256*3 palette used by PIL
        #flatten the 64 RGB triplets into a single list
        CCcomb =[]
        for i in self.CC_Colors:
            CCcomb.extend(i)
        #pad with zeros to the full 256*3 length
        CCcomb+= [0, ] * 192 * 3
        return CCcomb

    def findpalette(self):
        #This loop extracts the R,G,and B values from the BMP palette into separate lists, ignoring the zero byte for each entry
        i=0
        R=[]
        G=[]
        B=[]
        for num in self.Palette:
            if i%self.BytesPerPalette==0:
                B.append(num)
            elif (i-1)%self.BytesPerPalette==0:
                G.append(num)
            elif (i-2)%self.BytesPerPalette==0:
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
            for slot in self.CC_Colors: #go through each CoCo color
                dist=(color[0]-slot[0])**2+(color[1]-slot[1])**2+(color[2]-slot[2])**2 #find how far BMP color is from CoCo color
                if dist<mindist: #if it is closer than the current best, then it is the new best
                    bestslot = i #make the current color the best one
                    mindist = dist #set the current distance to the best distance
                i+=1
            CCPal.append(bestslot) #append the best color to the palette
        #truncate the Palette at the 16 non-dummy colors
        CCPalTrunc = CCPal[:self.CCPalSize]
        #convert the palette color numbers into a string that is usable for the BASIC program
        PalStr = str(CCPalTrunc)[1:-1]
        return PalStr

    def makebins(self):
        #These lines load the BMPfile into a string called fileContent, and then extract the header data into a tuple called data
        with open(self.namebase+'_data.BMP', mode='rb') as file: # b is important -> binary
            fileContent = file.read()
        L=len(fileContent)
        data=struct.unpack(self.BMPHeaderFormat+"B"*(L-self.LHead),fileContent)
        #This loads the important header data (DataStart=the byte where image data starts, W=image width in pixels, H=image height in pixels, and bpp=bits per pixel).
        Null,Null,Null,DataStart,Null,W,H,Null,bpp=data[:self.HeadVals]
        #Bpp is bytes per pixel representing the image. ImgRowWidth is the width in bytes of an image row, and LImage is the total length in bytes of the image data
        Bpp = 1.0*bpp/self.bitsPerByte
        ImgRowWidth = int(W*Bpp)
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
                rowData = b"".join([struct.pack('B',i) for i in B]) #store the new 0.5 Bpp row data as a string
            ImageContent = rowData+ImageContent #and put that row data at the top of the image
        ImageContent+=self.TailData #tack on the 2KB of zeros to complete the CoCo image data
        #This section creates the 4 CoCo .BIN files used that comprise the HSCREEN 2 image
        fileImages = []
        for i in range(4):
            fileImage=self.ImagefileHead+ImageContent[i*self.LImagefileMax:(i+1)*self.LImagefileMax]+self.ImagefileFoot #grab the appropriate 8KB chunk of image data, and tack the CoCo image file header and footer to that data
            fileImages.append(fileImage) #store that data in the list fileImages used for the image file data. This is not really needed, but could be used later for something...
            with open(self.truncname+" "+str(i+1)+".BIN",'wb') as outfile: #open the .BIN file
                outfile.write(fileImage) #and store the data there
        #These numbers are useful for finding the color vales for the CoCo Palette
        PaletteSize = 2**bpp #this is the palette size in the BMP, not the CoCo. Should be 256
        LPalette = self.BytesPerPalette*PaletteSize #This is the size in bytes of the BMP palette data
        PaletteStart = DataStart-LPalette-self.Offset #this is where the palette data starts in data
        self.Palette = data[PaletteStart:DataStart-self.Offset-1]#so this is the actual BMP palette

    def makeBAS(self):
        #Now that the name and palette data are found, assemble the basic program into a text file
        with open(self.name+".BAS",'w+') as outfile:
            for line in self.CCDispProg:
                if line=='30 A$="':
                    line+=self.truncname
                elif line=='180 DATA ':
                    line+=self.findpalette()+'\r'
                else:
                    line+='\r'
                outfile.write(line)

class GUI:
##The Base64 icon version as a string
    icon = """AAABAAEAICAQAAEABADoAgAAFgAAACgAAAAgAAAAQAAAAAEABAAAAAAAAAAAAGAAAABgAAAAEAAA
    AAAAAAD///8AAgICAPn5+QBzc3MAIyMjAN7e3wBAQEAAiYuIAFdXVwDJyMIAtbazAKSllACaeDAA
    PHsMABIhkQBze7sA//W3qbsgAAAAIAAAAAAAAJ7vvdrMoAAJlQmimatSkAAP7q3bvMICB6ezeTd6
    dXAABe733azJAgtbOqe3sHqCACD+6d27zCCoe4VzUzcztwIgXu/N2cyQWZVQVSVZVQkgAA/urdvM
    wgAAAAAAAAAAAAIlqlmpWZIiIiIiIiIiIiAAAAAAAAAAAAAAAAAAAAAAczMzMzMzMzMzMzMzMzMz
    O5ERGGZmZmRIQRhmZBaBERULEWiIh4N3dIOHM7QYcRGgIGEWREQUREFGZERBFkEYAiCRERERSGiI
    iIhmERERQgICCBEREUiDhxiHcxEREbAgAAUREREWRGQUZEQRERYCAAAgcREREREREREREREVAAAA
    ACQREREREREWERERcCAAAAIKERERERERgGERFgIAAAAAIGERERERFCBUERkCAAAAACBRERERERoC
    CREwIAAAAAACAxEREREwICB0IiAAAAAAAAJBEREUIgAAJQAAAAAiIiIgsRERGQIAAACjdQAAAAAA
    AiYRETAgAAADERRQAAAAAAIJERYiAAAgoRERYAAAAAAAIIEZAAAAIDERERUAAAAAAABRcCAAACCB
    EREVAgAAAAAACiAAAAAgMREREgAAAAAAAAAAAAAAAFERETAgAAAAAAACAAAAAAALQRggAAAAAAAA
    AAAAAAAAIFegAAAAH9//AB4gB4AKAAeACgBDQAQAAkAEEAngA///gAAAAf////8AAAAAAAAAAIAA
    AAFAAAACQAAAAqAAAAXgAAAL0AAAD/AAABfoABAv9AAQL/QAKF/6AFQf/gA8/wEAvw/+AX4H/oD0
    B/9D9AP/xfQC/+f0A////AX/7/4H///9Hw=="""

    def __init__(self,mainwin):
        icondata= base64.b64decode(self.icon)
        ## The temp file is icon_tmp.ico
        tempFile= "icon_tmp.ico"
        iconfile= open(tempFile,"wb")
        ## Extract the icon
        iconfile.write(icondata)
        iconfile.close()

        mainwin.title("Image2CoCo3")
        mainwin.wm_iconbitmap(tempFile)
        ## Delete the tempfile
        os.remove(tempFile)
        mainwin.lift()

        self.b_convert = ttk.Button(mainwin,text="Convert",command=self.convert)
        self.b_convert.grid(row=4,column=1,padx=5,pady=5)
        self.b_quit = ttk.Button(mainwin,text="Quit",command=self.Quit)
        self.b_quit.grid(row=4,column=2,padx=5,pady=5)
        
        self.lf_file = tk.LabelFrame(mainwin,text="Filename")
        self.lf_file.grid(row=0,column=0,columnspan=2,padx=5,pady=5,sticky=tk.W+tk.N+tk.S+tk.E)
        self.b_file=ttk.Button(self.lf_file,text=">>",width=3,command=self.getfile)
        self.b_file.pack(side=tk.LEFT,padx=3,pady=10)
        
        self.e_filename = tk.Entry(self.lf_file,width=21)
        self.e_filename.pack(side=tk.LEFT,padx=3,pady=10)
        self.e_filename.insert(0,"Pick a file")
        
        self.myimage = Img2CC3(self.e_filename.get())
        
        self.lf_preview = tk.LabelFrame(mainwin,text="CoCo Image Preview")
        self.lf_preview.grid(row=0,column=2,rowspan=2,columnspan=2,padx=5,pady=5,sticky=tk.W+tk.N+tk.E+tk.S)
        self.C_preview = tk.Canvas(self.lf_preview,width=self.myimage.prevW,height=self.myimage.prevH,bg=self.myimage.options['BackColor'])
        self.C_preview.pack(side=tk.BOTTOM)
        
        self.lf_palette = tk.LabelFrame(mainwin,text="Palette")
        self.lf_palette.grid(row=1,column=0,padx=5,pady=5,sticky=tk.W+tk.N+tk.S+tk.E)
        self.v_palette = tk.IntVar()
        self.v_palette.set(0)
        self.rb_palette_RGB = tk.Radiobutton(self.lf_palette,text="RGB",variable=self.v_palette,value=0,command=self.reposition)
        self.rb_palette_CMP = tk.Radiobutton(self.lf_palette,text="CMP",variable=self.v_palette,value=1,command=self.reposition)
        self.rb_palette_RGB.pack()
        self.rb_palette_CMP.pack()
        
        self.lf_dither = tk.LabelFrame(mainwin,text="Dither")
        self.lf_dither.grid(row=1,column=1,padx=5,pady=5,sticky=tk.W+tk.N+tk.S+tk.E)
        self.v_dither = tk.IntVar()
        self.cb_dither = tk.Checkbutton(self.lf_dither,text="Use dithering",variable=self.v_dither,onvalue=Image.FLOYDSTEINBERG,offvalue=Image.NONE,command=self.reposition)
        self.cb_dither.select()
        self.cb_dither.pack(side=tk.TOP)
        self.l_dither = tk.Label(self.lf_dither,text="(Floyd-Steinberg)")
        self.l_dither.pack(side=tk.BOTTOM,pady=2)
        
        self.lf_stretch = tk.LabelFrame(mainwin,text="Stretch Image")
        self.lf_stretch.grid(row=2,column=0,columnspan=2,padx=5,pady=2,sticky=tk.W+tk.N+tk.S+tk.E)
        self.v_stretch = tk.IntVar()
        self.cb_stretch = tk.Checkbutton(self.lf_stretch,text="Stretch image to full screen",variable=self.v_stretch,command=self.stretchtest)
        self.cb_stretch.pack()
        
        self.lf_backcolor = tk.LabelFrame(mainwin,text="Background Color")
        self.lf_backcolor.grid(row=3,column=0,columnspan=2,padx=5,pady=2,sticky=tk.W+tk.N+tk.S+tk.E)
        self.l_backcolor = tk.Label(self.lf_backcolor,text=self.myimage.options['BackColor'],width=20,font=("Courier", 10,'bold'),fg=self.ForeColor(self.myimage.options['BackColor']),bg=self.myimage.options['BackColor'])
        self.l_backcolor.bind("<Button-1>",self.getcolor)
        self.l_backcolor.pack(padx=2,pady=2)
        
        self.lf_pos = tk.LabelFrame(mainwin,text="Image Position")
        self.lf_pos.grid(row=2,column=2,rowspan=2,columnspan=2,padx=5,pady=2,sticky=tk.W+tk.N+tk.S+tk.E)
        self.v_posH = tk.IntVar()
        self.v_posH.set(1)
        self.v_posV = tk.IntVar()
        self.v_posV.set(1)
        self.rb_pos_left = tk.Radiobutton(self.lf_pos,text="Left",variable=self.v_posH,value=0,command=self.reposition)
        self.rb_pos_center = tk.Radiobutton(self.lf_pos,text="Cent",variable=self.v_posH,value=1,command=self.reposition)
        self.rb_pos_right = tk.Radiobutton(self.lf_pos,text="Right",variable=self.v_posH,value=2,command=self.reposition)
        self.rb_pos_top = tk.Radiobutton(self.lf_pos,text="Top",variable=self.v_posV,value=0,command=self.reposition)
        self.rb_pos_bot = tk.Radiobutton(self.lf_pos,text="Bot",variable=self.v_posV,value=2,command=self.reposition)
        self.rb_pos_left.grid(row=1,column=0,sticky=tk.W)
        self.rb_pos_center.grid(row=1,column=1,sticky=tk.W)
        self.rb_pos_right.grid(row=1,column=2,sticky=tk.W)
        self.rb_pos_top.grid(row=0,column=1,sticky=tk.W)
        self.rb_pos_bot.grid(row=2,column=1,sticky=tk.W)
        
        self.cb_stretch.config(state=tk.DISABLED)
        self.l_backcolor.config(state=tk.DISABLED)
        self.rb_pos_top.config(state=tk.DISABLED)
        self.rb_pos_bot.config(state=tk.DISABLED)
        self.rb_pos_center.config(state=tk.DISABLED)
        self.rb_pos_left.config(state=tk.DISABLED)
        self.rb_pos_right.config(state=tk.DISABLED)

    def getfile(self):
        fullname = askopenfilename(initialdir = ".",title = "Select file",filetypes = (("All image files","*.jpg"),("All image files","*.bmp"),("All image files","*.gif"),("All image files","*.png"),("All image files","*.tif"),("All image files","*.ico"),("All image files","*.eps"),("All image files","*.tga"),("Jpeg files","*.jpg"),("Bitmap files","*.bmp"),("GIF files","*.gif"),("PNG files","*.png"),("TIFF files","*.tif"),("Icon files","*.ico"),("Encapsulated Postscript files","*.eps"),("Targa files","*.tga"),("all files","*.*")))
        self.myimage.update(fullname=fullname)
        self.e_filename.delete(0,tk.END)
        self.e_filename.insert(0,self.myimage.options['fullname'])
        if not(self.myimage.ratio==self.myimage.CCRatio):
            self.cb_stretch.config(state=tk.NORMAL)
        else:
            self.cb_stretch.config(state=tk.DISABLED)
        self.stretchtest()
    
    def stretchtest(self):
        if self.v_stretch.get()==1 or self.myimage.ratio==self.myimage.CCRatio:
            self.l_backcolor.config(state=tk.DISABLED)
            self.rb_pos_top.config(state=tk.DISABLED)
            self.rb_pos_bot.config(state=tk.DISABLED)
            self.rb_pos_center.config(state=tk.DISABLED)
            self.rb_pos_left.config(state=tk.DISABLED)
            self.rb_pos_right.config(state=tk.DISABLED)
        else:
            self.l_backcolor.config(state=tk.NORMAL)
            if self.myimage.ratio<self.myimage.CCRatio:
                self.rb_pos_top.config(state=tk.NORMAL)
                self.rb_pos_bot.config(state=tk.NORMAL)
                self.rb_pos_center.config(state=tk.NORMAL,variable=self.v_posV)
                self.rb_pos_left.config(state=tk.DISABLED)
                self.rb_pos_right.config(state=tk.DISABLED)
            else:
                self.rb_pos_top.config(state=tk.DISABLED)
                self.rb_pos_bot.config(state=tk.DISABLED)
                self.rb_pos_center.config(state=tk.NORMAL,variable=self.v_posH)
                self.rb_pos_left.config(state=tk.NORMAL)
                self.rb_pos_right.config(state=tk.NORMAL)
        self.reposition()
        
    def getcolor(self,event):
        if self.l_backcolor['state']==tk.NORMAL:
            BackColor = askcolor()[1]
            self.l_backcolor.config(fg=self.ForeColor(BackColor),bg=BackColor,text=BackColor)
            self.C_preview.config(bg=BackColor)
            self.reposition()
    
    def reposition(self):
        if not(self.myimage.options['fullname']==self.myimage.fullname_init):
            self.myimage.update(BackColor=self.l_backcolor['text'],palette=self.v_palette.get(),dither=self.v_dither.get(),Stretch=self.v_stretch.get(),HPos=self.v_posH.get(),VPos=self.v_posV.get())
            self.C_preview.create_image(int(self.myimage.prevW/2)+1,int(self.myimage.prevH/2)+1,image=self.myimage.getprev(),anchor=tk.CENTER)
    
    def ForeColor(self,BackColor):
        return '#'+f"{~int('0x'+BackColor[1:],16)&int('0xffffff',16):0{6}x}"

    def convert(self):
        self.myimage.makebins()
        self.myimage.makeBAS()
        try:
            os.remove(self.myimage.namebase+'_data.BMP')
            os.remove(self.myimage.namebase+"_prev.gif")
        except:
            pass
        if not tkMB.askyesno("Image Converted!","Would you like to convert another image?"):
            self.Quit()
    
    def Quit(self):
        mainwin.destroy()
        exit()

mainwin = tk.Tk()
GUI(mainwin)
mainwin.mainloop()
