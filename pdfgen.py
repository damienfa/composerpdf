__author__ = 'mattguillouet & damien.fa'

# inputs
#       -fichier conf cerfa (json)
#       -fichier data (json)
#       -cerfa file (pdf)


######################## Remaining
# input args
# integrate maxChar in the code
# chained fields: handle text (possible ???)

import os
import json
import uuid
import sys
import urllib.request
import reportlab.lib.pagesizes  as formatPage
import math
import re

#import reportlab.lib.utils
#import reportlab.pdfbase.pdfmetrics


from reportlab.pdfgen import canvas
from pdfrw import PdfReader, PdfWriter, PageMerge
from collections import OrderedDict

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
    font="Courier"
    fontSize=12
    fontSizeMin=6

    def __init__(self, x, y):
        self.x = x
        self.y = y

class ConfigCase(object):
    x=0
    y=0
    width=0
    height=0
    spacing=0
    nbMax=0
    font="Courier"
    fontSize=13
    fontSizeMin=6

    def __init__(self, x, y, width, height, spacing, nbMax):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.spacing = spacing
        self.nbMax = nbMax


class Drawer:
    can = {}

    def __init__(self, sizeCanvas):
        self.can = canvas.Canvas(temp, pagesize=sizeCanvas)
        self.can.translate(0, sizeCanvas[1])

    def routage(self, confEntry, val, which):
        if which=="text":
            conf = ConfigString(
                confEntry["position"]["x"],
                confEntry["position"]["y"])
            width = confEntry["size"]["width"]

            # optimalFontSize and minimalFontSize
            if "optimalFontSize" in confEntry:
                conf.fontSize = confEntry["optimalFontSize"]

            if "minimalFontSize" in confEntry:
                conf.fontSizeMin = confEntry["minimalFontSize"]

            # check the font size | if not ok decrease font size until ok
            while self.can.stringWidth(val,conf.font,conf.fontSize)>width and conf.fontSizeMin<conf.fontSize:
                conf.fontSize-=1
            self.draw_basicString(val,conf)

        elif which=="multiCase":
            conf = ConfigCase(confEntry["position"]["x"],confEntry["position"]["y"],
                                            confEntry["size"]["width"],confEntry["size"]["height"],
                                                confEntry["size"]["spacing"],confEntry["size"]["nbMax"])
            # check the font size
            width = confEntry["size"]["width"]
            # height = confEntry["size"]["height"]

            # check the font size | if not ok decrease font size until ok
            while self.can.stringWidth(val[0].upper(),conf.font,conf.fontSize)>width and conf.fontSizeMin<conf.fontSize:
                conf.fontSize-=1
            self.draw_multiCase(val,conf)

        elif which=="cross":
            if val==1:
                self.draw_cross(confEntry["position"]["x"],confEntry["position"]["y"],confEntry["size"])


    def draw_basicString(self, string, config):
        self.can.setFont(config.font, config.fontSize)
        self.can.drawString(config.x, -config.y, string)

    def draw_multiCase(self, string, config):
        #check number max
        for iChar in range(0,min(config.nbMax,len(string))):
            conf = ConfigString(config.x+iChar*(config.width+config.spacing),config.y)
            conf.font = config.font
            conf.fontSize = config.fontSize
            self.draw_basicString(string[iChar], conf)

    def draw_cross(self, x, y, size=10):
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


def download_cerfa(urlCerfa, basepdf):
    response = urllib.request.urlopen(urlCerfa)
    with open(basepdf, 'wb') as g:
	    g.write(response.read())
	    g.close()


def fillForm():
    # create a new PDF with Reportlab
    drawer = Drawer(sizeCerfa)
    can = drawer.can

    # Loop on the page
    for ii in range(1,nbPage+1):
        for iData in dataJS:
            if confCerfaJS[iData]["position"]["page"]==ii: # check if it is on this page
                value = dataJS[iData]
                if confCerfaJS[iData]["type"]=="text": # Simple text
                    drawer.routage(confCerfaJS[iData],value,"text")

                elif confCerfaJS[iData]["type"]=="multiCase": #  Multicase text
                    drawer.routage(confCerfaJS[iData],value,"multiCase")

                elif confCerfaJS[iData]["type"]=="cross": # Cross
                    drawer.routage(confCerfaJS[iData],value,"cross")

                elif confCerfaJS[iData]["type"]=="multiLine": # Multi-line text
                    conf = ConfigString(0,0) #initialisation conf string
                    widthCase = confCerfaJS[iData]["size"]["width"] # case width
                    nbLineMax = confCerfaJS[iData]["size"]["nbLineMax"] # number max of line

                    sizeFullString = can.stringWidth(value,conf.font,conf.fontSize)
                    nbLineNeeded = math.floor(sizeFullString/widthCase) + 1
                    while nbLineNeeded > nbLineMax and conf.fontSize > conf.fontSizeMin:
                        conf.fontSize -= 1
                        sizeFullString = can.stringWidth(value,conf.font,conf.fontSize)
                        nbLineNeeded = math.floor(sizeFullString/widthCase) + 1

                    beginLine = 0
                    nbLine = 0
                    previousWord = 0
                    for w in re.finditer(" ",value):
                        if can.stringWidth(value[beginLine:w.start()],conf.font,conf.fontSize) > widthCase:
                            conf.x = confCerfaJS[iData]["position"]["x"]
                            conf.y = confCerfaJS[iData]["position"]["y"] + nbLine*confCerfaJS[iData]["size"]["deltaLine"]
                            drawer.draw_basicString(value[beginLine:previousWord],conf)
                            nbLine += 1
                            beginLine = previousWord + 1
                        previousWord = w.start()

                    conf.x = confCerfaJS[iData]["position"]["x"]
                    conf.y = confCerfaJS[iData]["position"]["y"] + nbLine*confCerfaJS[iData]["size"]["deltaLine"]
                    drawer.draw_basicString(value[beginLine:],conf)


                    # reportlab.lib.utils.simpleSplit() test this function to split the lines


                elif confCerfaJS[iData]["type"]=="chainedFields": # Chained fields
                    iVal = 0
                    x0 = confCerfaJS[iData]["position"]["x"]
                    y0 = confCerfaJS[iData]["position"]["y"]

                    for iChain in confCerfaJS[iData]["fields"].keys():
                        chain = confCerfaJS[iData]["fields"][iChain]
                        if chain["type"]=="multiCase":
                            confCerfaJS[iData]["position"]["x"] = x0 + chain["delta"]["x"]
                            confCerfaJS[iData]["position"]["y"] = y0 + chain["delta"]["y"]
                            confCerfaJS[iData]["size"] = chain["size"]
                            drawer.routage(confCerfaJS[iData], value[iVal:iVal+chain["nbChar"]],"multiCase")
                            iVal += chain["nbChar"]


        can.showPage() # go on next page of the pdf
    can.save()
#end def fillform

#########################################################################
##################### Main

WorkingFolder="./"
#basePDF = "cerfa_1.pdf" #"cerfa_13750-05.pdf"
baseConf = "ConfCerfa.json"
cerfaFilled = "OutFilled.pdf"
fillDataFile = "data.json"


urlCerfa = "https://www.formulaires.modernisation.gouv.fr/gf/cerfa_13750.do"

fileName = os.path.split(urlCerfa)[1] + "-" + random_string() + ".pdf"
basePDF = os.path.join(WorkingFolder,fileName)

print("Downloading cerfa from: " + urlCerfa)
download_cerfa(urlCerfa, basePDF)

temp = os.path.join(WorkingFolder, "temp-%s.pdf" % random_string() )

print("Reading configuration and data files")
# Lecture fichier conf des champs
with open(os.path.join(WorkingFolder,baseConf),'r') as f:
    confCerfaJS = json.loads(f.read(), object_pairs_hook=OrderedDict) # import the json Conf as an ordered dictionary
f.close()

# Lecture data
with open( WorkingFolder+fillDataFile,'r') as f:
    dataJS = json.loads(f.read(), object_pairs_hook=OrderedDict) # import the json data as an ordered dictionary
f.close()

# Checking that entries correspond
for iData in dataJS:
    if not iData in  confCerfaJS:
        print("The field: " + iData + " has no defined configuration in the conf file")
        dataJS.pop(iData) # delete this entry


###############################################
###############################################
# Get the document size, we assume that all the pages have the same size
PdfIn = PdfReader(basePDF)
sizePdf = PdfIn.Root.Pages.Kids[0].MediaBox
sizeCerfa = (float(sizePdf[2]),float(sizePdf[3]))

###############################################
###############################################
# Remplissage Cerfa

# Count how many pages are filled in
nbPage = 0
for iconfig in confCerfaJS:
    if nbPage < confCerfaJS[iconfig]["position"]["page"]:
        nbPage = confCerfaJS[iconfig]["position"]["page"]

print("Building the filled cerfa")
fillForm()

#############################################################
####### Merge filled form and cerfa into one document #######
layersPdf = PdfReader(temp)

for iPage in range(0,nbPage):
    cerfaLayer = PageMerge().add(layersPdf.pages[iPage])[0]
    PageMerge(PdfIn.getPage(iPage)).add(cerfaLayer).render()

print("Writing filled cerfa")
PdfWriter().write(os.path.join(WorkingFolder,cerfaFilled), PdfIn)

##### Delete temp files
os.remove(temp)
os.remove(basePDF)



