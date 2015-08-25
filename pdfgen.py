__author__ = 'mattguillouet & damien.fa'

# inputs
#       -fichier conf cerfa (json)
#       -fichier data (json)
#       -cerfa file (pdf)


######################## remaining
# champs multi-line
# chained-fields
# arguments input
# add some comments in the console


import os
import json
import uuid
import sys
import urllib.request
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
    font="Helvetica"
    fontSize=12
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

    def drawbasicstring(self, string, config):
        self.can.setFont(config.font, config.fontSize)
        self.can.drawString(config.x, -config.y, string)

    def drawmulticase(self, string, config):
        self.can.setFont(config.font, config.fontSize)
        #check number max
        for iChar in range(0,config.nbMax):
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


def download_cerfa(urlCerfa, basepdf):

	Response = urllib.request.urlopen(urlCerfa)
	with open(basepdf, 'wb') as g:
		g.write(Response.read())
		g.close()


def fillForm():
    # create a new PDF with Reportlab
    drawer = Drawer(sizeCerfa)
    can = drawer.can

    # Loop on the page
    for ii in range(1,nbPage+1):
        for iData in dataJS:
            if ConfCerfaJS[iData]["position"]["page"]==ii: #check if it is on this page
                value = dataJS[iData]
                if ConfCerfaJS[iData]["type"]=="text": # the input is some simple text
                    conf = ConfigString(
                        ConfCerfaJS[iData]["position"]["x"],
                        ConfCerfaJS[iData]["position"]["y"]
                    )
                    width = ConfCerfaJS[iData]["size"]["width"]
                    # check the font size | if not ok decrease fon size until ok
                    if can.stringWidth(value,conf.font,conf.fontSize)>width:
                        while can.stringWidth(value,conf.font,conf.fontSize)>width and conf.fontSizeMin<conf.fontSize:
                            conf.fontSize-=1

                    drawer.drawbasicstring(value,conf)

                elif ConfCerfaJS[iData]["type"]=="multicase": # the input is some simple text
                    conf = ConfigCase(ConfCerfaJS[iData]["position"]["x"],ConfCerfaJS[iData]["position"]["y"],
                                            ConfCerfaJS[iData]["size"]["width"],ConfCerfaJS[iData]["size"]["height"],
                                                ConfCerfaJS[iData]["size"]["spacing"],ConfCerfaJS[iData]["size"]["nbmax"])
                    # check the font size
                    width = ConfCerfaJS[iData]["size"]["width"]
                    # check the font size | if not ok decrease fon size until ok
                    if can.stringWidth(value,conf.font,conf.fontSize)>width:
                        while can.stringWidth(value[0].capitalize(),conf.font,conf.fontSize)>width and conf.fontSizeMin<conf.fontSize:
                            conf.fontSize-=1

                    drawer.drawmulticase(value,conf)

                elif ConfCerfaJS[iData]["type"]=="cross":
                    if value==1:
                        drawer.drawcross(ConfCerfaJS[iData]["position"]["x"],ConfCerfaJS[iData]["position"]["y"],ConfCerfaJS[iData]["size"])

        can.showPage() # go on next page of the pdf
    can.save()
#end def fillform

#########################################################################
##################### Main

WorkingFolder=""
#basePDF = "cerfa_1.pdf" #"cerfa_13750-05.pdf"
baseConf = "ConfCerfa.json"
cerfaFilled = "OutFilled.pdf"
fillDataFile = "data.json"


urlCerfa = "https://www.formulaires.modernisation.gouv.fr/gf/cerfa_13750.do"

fileName = urlCerfa.split('/')[-1]
fileName = fileName.split('.')[0]
fileName += "-" + random_string() + ".pdf"
basePDF = os.path.join(WorkingFolder,fileName)

download_cerfa(urlCerfa, basePDF)

temp = os.path.join(WorkingFolder, "temp-%s.pdf" % random_string() )


# Lecture fichier conf des champs
with open(os.path.join(WorkingFolder,baseConf),'r') as f:
    ConfCerfaJS = json.loads(f.read())
f.close()
#print(ConfCerfaJS)

# Count how many pages are filled in
nbPage = 0
for iconfig in ConfCerfaJS:
    if nbPage < ConfCerfaJS[iconfig]["position"]["page"]:
        nbPage = ConfCerfaJS[iconfig]["position"]["page"]


# Lecture data
with open( WorkingFolder+fillDataFile,'r') as f:
    dataJS = json.loads(f.read())
f.close()


# Checking and Error Handling
for iData in dataJS:
    if not iData in  ConfCerfaJS:
        print("The field: " + iData + " has no defined configuration in the conf file")
        # delete this entry if not bug

###############################################
###############################################
# Open base cerfa to get the document size, we assume that all the pages have the same size
PdfIn = PdfReader(basePDF)
ok = PdfIn.Root.Pages.Kids[0].MediaBox
sizeCerfa = (float(ok[2]),float(ok[3]))

###############################################
###############################################
# Remplissage Cerfa
fillForm()

#############################################################
####### Merge filled form and cerfa into one document #######
new_pdf = PdfReader(temp)

for iPage in range(0,nbPage):
    wmark = PageMerge().add(new_pdf.pages[iPage])[0]
    PageMerge(PdfIn.getPage(iPage)).add(wmark).render()

PdfWriter().write(os.path.join(WorkingFolder,cerfaFilled), PdfIn)


##### Delete temp files
os.remove(temp)
os.remove(basePDF)



