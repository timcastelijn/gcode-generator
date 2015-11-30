# this script was created by Tim castelijn
# 26 november 2015
# www.timcastelijn.nl
# it will only work in xyz space and is especially designed for fablabBreda milling machine


import rhinoscriptsyntax as rs
import math
import os
import Rhino

# save offset from the workpiece
PRECISION = 4
SPACING = ""
Z_OFFSET = 2 #[mm]
LINE_INDEX = True #type None for no
line_index = 0

def write(command, x=None, y=None, z=None, f=None, comment = None):

    global line_index, LINE_INDEX, SPACING


    line = ""
    if LINE_INDEX:
        line = line + "N%d0"%line_index + SPACING
        line_index+=1
        
    line = line + command + SPACING
    
    if not x == None:
        line = line + "X%0.4f"%x + SPACING
    if not y == None:
        line = line + "Y%0.4f"%y + SPACING
    if not z == None:
        line = line + "Z%0.4f"%z + SPACING
    if not f == None:
        line = line + "F%0.4f"%f + SPACING
    if not comment == None:
        line = line + ";" + comment
    
    file.write(line+"\n")
    
    

   
def OpenFileName(title=None, filter=None, folder=None, filename=None, extension=None):
    fd = Rhino.UI.OpenFileDialog()
    if title: fd.Title = title
    if filter: fd.Filter = filter
    if folder: fd.InitialDirectory = folder
    if filename: fd.FileName = filename
    if extension: fd.DefaultExt = extension
    if fd.ShowDialog(): return fd.FileName
    
# read a configfile in the specified directory
def readConfig():
    
    filename = OpenFileName("Save", "Toolpath Files (*.ini)|*.ini||", os.getcwd())

    # retrun function if no filename was specified
    if not filename: return
    
    f = open(filename)
    
    lines = f.readlines()
    f.close()
    par ={}
    for line in lines:
        name, val = line.split("=")
        par[name] = float(val)
    return par
    
def SaveFileName(title=None, filter=None, folder=None, filename=None, extension=None):
    fd = Rhino.UI.SaveFileDialog()
    if title: fd.Title = title
    if filter: fd.Filter = filter
    if folder: fd.InitialDirectory = folder
    if filename: fd.FileName = filename
    if extension: fd.DefaultExt = extension
    if fd.ShowDialog(): return fd.FileName

def writeFastMoveToCurveStart(curve):
    # fast move to path start
    pt = rs.CurveStartPoint(curve)
    write("G00", pt.X, pt.Y, 0 + Z_OFFSET )
    
def writePlungeToCurveStart(curve):
    # fast move to path start
    pt = rs.CurveStartPoint(curve)
    write("G01", pt.X, pt.Y, pt.Z )
        
def writePlungeRetract(curve):
    # fast move to path end
    pt = rs.CurveEndPoint(curve)
    write("G00", pt.X, pt.Y, 0 + Z_OFFSET )
        
def writeSpindleEnable():
    write("M03")

def writeSpindleDisable():
    write("M05")
    
def writeReturnToHomingPos():
    write("G00", z = 2, comment = "retract from workpiece" )    
    write("G00", x=0 , y=0, comment = "return to 0" )

def writeHeader(file, par):

    sfeed           = par['feedrate']
    sspindle        = par['spindle_speed']
    
    # write header
    write("G21", comment = "metric units")
    write("G17", comment = "select xy-plane")
    write("G90", comment = "absolute distance mode")
    write("G40", comment = "cutter radius compensation off")
    write("G49", comment = "no tool length offset")
    write("G80", comment = "cancel current motor movement")
    
    write("T1M06", comment = "tool change to tool 1")
    write("G43Z5.000H1", comment = "set tool length offset for tool 1 t0 5")
    write("G94", comment = "units per minute")
    
    write("F" + str(sfeed), comment = "set feedrate" )
    write("S" + str(sspindle), comment = "set spindle speed" ) 
    write("M08")   
     
def writePolyline(curve):  
    points = rs.CurvePoints(curve)
    for pt in points:
        write("G01", pt.X, pt.Y, pt.Z )
     
def writeArc(curve):
            
    normal = rs.CurveTangent(curve, 0)
            
    # get curvepoints
    startpt     = rs.CurveStartPoint(curve)
    endpt       = rs.CurveEndPoint(curve)
    midpt       = rs.ArcCenterPoint(curve)
            
    # calc G2/G3 parameters
    x   = endpt.X
    y   = endpt.Y
    i   = -startpt.X + midpt.X
    j   = -startpt.Y + midpt.Y
        
    # make a distinction between positive and negative direction
    if ((normal[1] > 0) and (startpt.X > midpt.X)) or ((normal[1] < 0) and (startpt.X < midpt.X) or (normal[1]==0 and (normal[0]==1 or normal[0] ==-1) and startpt.X == midpt.X)):
        file.write("G03 X%0.4f"%x+" Y%0.4f"%y+" I%0.4f"%i+" J%0.4f"%j +"\n")
    else:
        file.write("G02 X%0.4f"%x+" Y%0.4f"%y+" I%0.4f"%i+" J%0.4f"%j +"\n")    

def writeCurve(curve):
                        
    polyLine    = rs.ConvertCurveToPolyline(curve, a_tolerance, tolerance)
    points      = rs.CurvePoints(polyLine)
            
    # insert division points as line
    for pt in points:
        write("G01", pt.X, pt.Y, pt.Z )
    
    # remove objects after use
    rs.DeleteObjects(polyLine)

def writeG(selection, par):
    
    # get filename frm dialog
    filename = SaveFileName ("Save", "Toolpath Files (*.nc)|*.nc||")
        
    # retrun function if no filename was specified
    if not filename: return

    global file 
    file = open(filename, 'w')
    
    writeHeader(file, par)
    writeSpindleEnable()
    
    for curve in selection:

        #move to start of the curve at height 0+offset
        writeFastMoveToCurveStart(curve)
        writePlungeToCurveStart(curve)

        # detect type of curve for different G-codes
        if (rs.IsPolyline(curve)) or rs.IsLine(curve):
            writePolyline(curve)
        
        # elif rs.IsArc(curve):
        #     writeArc(curve)
 
        else:
            writeCurve(curve)
        
        # return to offset at end of the curve
        writePlungeRetract(curve)

    # return to homing position and turn of the spindle
    writeReturnToHomingPos()
    writeSpindleDisable()  
    
    file.close()


# Check to see if this file is being executed as the "main" python
# script instead of being used as a module by some other python script
# This allows us to use the module which ever way we want.
if( __name__ == "__main__" ):
    
    par = readConfig()
        
    if not par: 
        print "no config file selected"
    else:    
    
        selection = rs.GetObjects("Select Curves/polylines/arcs/circles", rs.filter.curve, True, True)
        writeG(selection, par)