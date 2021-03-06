import os, sys
from osgeo import gdal, ogr
from osgeo.gdalconst import *

def betweenstring(string,a,b):
    list = []
    stringsplit = string.split(a)
    if stringsplit != []:
        for item in stringsplit[1:]:
            nr = item.find(b)
            if nr != -1:
                list.append(item.split(b)[0])
    return list

gdal.AllRegister()

text = '''
For each CRISM .img data in listfile create .js (JSON) in metadata folder containing metadata. These are used by the PlanetServer webclient.

  createcrismstats.py /path/list.txt <region>
'''

if len(sys.argv) == 1:
    print text
    sys.exit()
else:
    filecoll = []
    listfile = sys.argv[1]
    try:
        region = sys.argv[2]
    except:
        region = ""

outputfolder = os.path.join(os.getcwd(),'metadata')
if not os.path.exists(outputfolder):
    os.makedirs(outputfolder)
    
f = open(listfile,"r")
for line in f:
    line = line.strip().split(",")
    filename = line[0]
    collname = line[1]
    header = "".join(open(filename + ".hdr", "r").readlines()).replace("\n","")

    wavelength = betweenstring(header, "wavelength = {", "}")[0].replace(" ","").split(",")
    fwhm = betweenstring(header, "fwhm = {", "}")[0].replace(" ","").split(",")
    bbl = betweenstring(header, "bbl = {", "}")[0].replace(" ","").split(",")

    inDs = gdal.Open(filename, GA_ReadOnly)
    bands = inDs.RasterCount
    transform = inDs.GetGeoTransform()
    xres = transform[1]
    yres = transform[5]
    xmin = transform[0]
    ymax = transform[3]
    width = inDs.RasterXSize
    height = inDs.RasterYSize
    xmax = xmin + (xres * width)
    ymin = ymax - (abs(yres) * height)

    xmlfile = filename + ".aux.xml"
    if not os.path.exists(xmlfile):
        print "Creating metadata XML file"
        os.system("gdalinfo -stats " + filename + ">/dev/null")
    try:
        xmldata = "".join(open(xmlfile, "r").readlines()).replace("\n","")
        succesbands = betweenstring(xmldata,'band="','"')
        minimum = betweenstring(xmldata,'<MDI key="STATISTICS_MINIMUM">','</MDI>')
        maximum = betweenstring(xmldata,'<MDI key="STATISTICS_MAXIMUM">','</MDI>')
        mean = betweenstring(xmldata,'<MDI key="STATISTICS_MEAN">','</MDI>')
        stddev = betweenstring(xmldata,'<MDI key="STATISTICS_STDDEV">','</MDI>')
    except:
        print "XML stats not created!"
        sys.exit()
    
    print "Writing " + collname + ".js"
    o = open(os.path.join(outputfolder,collname + ".js"),"w")
    out = "{\"region\": \"" + str(region) + "\", \"xmin\": " + str(xmin) + ", \"xmax\": " + str(xmax) + ", \"ymin\": " + str(ymin) + ", \"ymax\": " + str(ymax) + ", \"width\": " + str(width) + ", \"height\": " + str(height) + ", \"bands\": " + str(bands) + ","
    gdallist = ["minimum","maximum","mean","stddev"]
    for item in gdallist:
        i = 0
        out = out + "\"" + item + "\": ["
        exec("temp = " + item)
        for value in temp:
            if str(i+1) in succesbands:
                out = out + temp[i] + ","
            else:
                out = out + "0,"
            i += 1
        out = out[:-1] + "],"
    hdrlist = ["wavelength","fwhm","bbl"]
    for item in hdrlist:
        i = 0
        out = out + "\"" + item + "\": ["
        exec("temp = " + item)
        for value in temp:
            out = out + temp[i] + ","
            i += 1
        out = out[:-1] + "],"
    out = out[:-1] + "}"
    o.write(out)
    o.close()

f.close()
