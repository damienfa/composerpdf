__author__ = 'mguillouet'

# inputs
#       -fichier conf cerfa (json)
#       -fichier data (json)
#       -cerfa file (pdf)


import os
import json
import uuid
import sys
from reportlab.pdfgen import canvas
import reportlab.lib.pagesizes  as formatPage
from pdfrw import PdfReader, PdfWriter, PageMerge


#######################################################################################"
############################ Classes

class ConfigCross(object):
    x=0
    y=0
    size=0

    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size

class ConfigString(object):
    x=0
    y=0
    font="Helvetica"
    fontSize=12

    def __init__(self, x, y):
        self.x = x
        self.y = y

class ConfigCase(object):
    x=0
    y=0
    width=0
    height=0
    spacing=0
    font="Helvetica"
    fontSize=10

    def __init__(self, x, y, width, height, spacing):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.spacing = spacing


class Drawer:
    can = {}

    def __init__(self):
        self.can = canvas.Canvas(temp, pagesize=formatPage.A4)
        self.can.translate(0, formatPage.A4[1]) 

    def drawbasicstring(self, string, config):
        self.can.setFont(config.font, config.fontSize)
        self.can.drawString(config.x, -config.y, string)

    def drawmulticase(self, string,config):
        self.can.setFont(config.font, config.fontSize)
        #check number max
        for iChar in range(0,len(string)):
            conf = ConfigString(config.x+iChar*(config.width+config.spacing),config.y)
            self.drawbasicstring(string[iChar],conf)

    def drawcross(self, x, y, size=10):
        x -= size*0.5;
        y += size*0.5;
        self.can.setLineWidth(2)
        self.can.line(x,-y,x+size,-y+size)
        self.can.line(x+size,-y,x,-y+size) 


#######################################################################################"
############################ Functions

def random_string(string_length=10):
    """Returns a random string of length string_length."""
    random = str(uuid.uuid4()) # Convert UUID format to a Python string.
    random = random.upper() # Make all characters uppercase.
    random = random.replace("-","") # Remove the UUID '-'.
    return random[0:string_length] # Return the random string.



def fillForm():
    # create a new PDF with Reportlab
    drawer = Drawer()
    can = drawer.can

    # Loop on the page
    for ii in range(1,nbPage+1):
        for iData in DataJS:
            value = DataJS[iData]
            if ConfCerfaJS[iData]["type"]=="text": # the input is some simple text
                conf = ConfigString(
                    ConfCerfaJS[iData]["position"]["x"],
                    ConfCerfaJS[iData]["position"]["y"]
                )
                width = ConfCerfaJS[iData]["size"]["width"]
                # check the font size | if not ok decrease fon size until ok
                if can.stringWidth(value,conf.font,conf.fontSize)>width:
                    while can.stringWidth(value,conf.font,conf.fontSize)>width:
                        conf.fontSize-=1

                drawer.drawbasicstring(value,conf)

            elif ConfCerfaJS[iData]["type"]=="multicase": # the input is some simple text
                conf = ConfigCase(ConfCerfaJS[iData]["position"]["x"],ConfCerfaJS[iData]["position"]["y"],ConfCerfaJS[iData]["size"]["width"],ConfCerfaJS[iData]["size"]["height"],ConfCerfaJS[iData]["size"]["spacing"])
                # check the font size
                width = ConfCerfaJS[iData]["size"]["width"]
                # check the font size | if not ok decrease fon size until ok
                if can.stringWidth(value,conf.font,conf.fontSize)>width:
                    while can.stringWidth(value[0].capitalize(),conf.font,conf.fontSize)>width:
                        conf.fontSize-=1

                drawer.drawmulticase(value,conf)

            elif ConfCerfaJS[iData]["type"]=="cross":
                if value==1:
                    drawer.drawcross(ConfCerfaJS[iData]["position"]["x"],ConfCerfaJS[iData]["position"]["y"],ConfCerfaJS[iData]["size"])

        can.showPage() # go on next page of the pdf
    can.save()
#end def fillform



WorkingFolder="./"
basePDF = "cerfa_1.pdf" #"cerfa_13750-05.pdf"
baseConf = "ConfCerfa.json";
cerfaFilled = "OutFilled.pdf"
fillDataFile = "data.json";


temp = os.path.join(WorkingFolder, "temp-%s.pdf" % random_string() )

# Lecture fichier conf des champs
with open(os.path.join(WorkingFolder,baseConf),'r') as f:
    ConfCerfaJS = json.loads( f.read() )
f.close()
#print(ConfCerfaJS)

# Count how many pages are filled in
nbPage = 0
for iconfig in ConfCerfaJS:
    if nbPage < ConfCerfaJS[iconfig]["position"]["page"]:
        nbPage = ConfCerfaJS[iconfig]["position"]["page"]


# Lecture data 
with open( WorkingFolder+fillDataFile,'r') as f:
    DataJS = json.loads(f.read())
f.close()


# Checking and Error Handling
for iData in DataJS:
    if not iData in  ConfCerfaJS:
        print("The field: " + iData + " has no defined configuration in the conf file")


###############################################
###############################################
# Remplissage Cerfa
fillForm()

#############################################################
####### Merge filled form and cerfa into one document #######
new_pdf = PdfReader(temp)

input = PdfReader( os.path.join(WorkingFolder,"cerfas",basePDF) )

tutu = PageMerge().add(new_pdf.pages[0]).xobj_box
#print(str(tutu))

wmark = PageMerge().add(new_pdf.pages[0])[0]
PageMerge(input.getPage(0)).add(wmark).render()

PdfWriter().write(os.path.join(WorkingFolder,cerfaFilled), input)

os.remove(temp);




