# this script was created by Tim castelijn
# 26 november 2015
# www.timcastelijn.nl
# it will only work in xyz space and is especially designed for fablabBreda milling machine


import rhinoscriptsyntax as rs
import math
import os
import Rhino

# save offset from the workpiece
Z_OFFSET = 2 #[mm]
   
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
        
    #get the script file dir
    # dir = os.getcwd()
    # f = open(dir + '/config.ini')
    
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
    file.write("G00 X%0.4f"%pt.X+" Y%0.4f"%pt.Y+" Z%0.4f"%Z_OFFSET+"\n")

def writePlungeToCurveStart(curve):
    # fast move to path start
    pt = rs.CurveStartPoint(curve)
    file.write("G01 X%0.4f"%pt.X+" Y%0.4f"%pt.Y+" Z%0.4f"%pt.Z+"\n")        
        
def writePlungeRetract(curve):
    # fast move to path start
    pt = rs.CurveEndPoint(curve)
    file.write("G00 X%0.4f"%pt.X+" Y%0.4f"%pt.Y+" Z%0.4f"%Z_OFFSET+"\n")          
        
def writeSpindleEnable():
    file.write("M03\n") # spindle on clockwise

def writeSpindleDisable():
    file.write("M05\n") # spindle on clockwise

def writeReturnToHomingPos():
    file.write("G00 X0.0000 Y0.0000 F1000\n")        

def writeHeader(file, par):

    sfeed           = par['feedrate_cut']
    sspindle        = par['intensity_cut']
    
    # write header
    file.write("G90\n") # absolute positioning
    file.write("G21\n") # use milimeters
    file.write("F"+str(sfeed)+"\n") # initialize feed rate
    file.write("S"+str(sspindle)+"\n") # initialize spindle speed
    file.write("M08\n") # coolant on     
     
def writePolyline(curve):  
    points = rs.CurvePoints(curve)
    for pt in points:
        file.write("G01 X%0.4f"%pt.X+" Y%0.4f"%pt.Y+" Z%0.4f"%pt.Z+"\n")
     
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
        file.write("G01 X%0.4f"%pt.X+" Y%0.4f"%pt.Y+" Z%0.4f"%pt.Z+"\n")
    
    # remove objects after use
    rs.DeleteObjects(polyLine)

def writeG(selection, par):

    global sfeed, efeed, sspindle, e_intensity, tolerance, a_tolerance
    
    # get variables
    sfeed           = par['feedrate_cut']
    efeed           = par['feedrate_engrave']
    sspindle        = par['intensity_cut']
    e_intensity     = par['intensity_engrave']
    tolerance       = par['curve_tolerance']
    a_tolerance     = par['curve_angle_tolerance']
    
    print("new")
    
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