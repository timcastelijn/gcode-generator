# this script was created by Tim castelijn
# 26 november 2015
# www.timcastelijn.nl
# it will only work in xyz space and is especially designed for fablabBreda milling machine


import rhinoscriptsyntax as rs
import math
import sys
import Rhino


def getDirectory():
    myDir = ""
    for item in sys.path:
        myDir = myDir + item
    return myDIr

def read_config():
        
    dir = '/Users/timcastelijn/Library/Application Support/McNeel/Rhinoceros/scripts/'
    # dir = getDirectory()
    
    f = open(dir + 'config.ini')
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

def write_G(path, par):
    #
    # G code output
    #
    

    
    # get variables
    sfeed           = par['feedrate_cut']
    efeed           = par['feedrate_engrave']
    sspindle        = par['intensity_cut']
    e_intensity     = par['intensity_engrave']
    tolerance       = par['curve_tolerance']
    a_tolerance     = par['curve_angle_tolerance']
    
    print("new")
    
    filename = SaveFileName ("Save", "Toolpath Files (*.nc)|*.nc||")
        
    
    if not filename: return
    
        
    file = open(filename, 'w')
    
    
    # write header
    file.write("G90\n") # absolute positioning
    file.write("F"+str(sfeed)+"\n") # feed rate
    file.write("S"+str(sspindle)+"\n") # spindle speed
    file.write("M08\n") # coolant on
    for curve in path:
        
        # fast move to path start
        pt = rs.CurveStartPoint(curve)
        file.write("G00 X%0.4f"%pt.X+" Y%0.4f"%pt.Y+"\n")
        file.write("M03\n") # spindle on clockwise
        
        # change feedrate for engraving
        if (rs.ObjectLayer(curve) == "engrave"):
            file.write("F%0.1f"%efeed + "\n")
            file.write("S%0.1f"%e_intensity + "\n")
        else:
            file.write("F%0.1f"%sfeed + "\n")
            file.write("S%0.1f"%sspindle + "\n")
        
        # detect type of curve for different G-codes
        if (rs.IsPolyline(curve)) or rs.IsLine(curve):

            points = rs.CurvePoints(curve)
            for pt in points:
                file.write("G01 X%0.4f"%pt.X+" Y%0.4f"%pt.Y+"\n")
        
        elif rs.IsArc(curve):
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
#                file.write(";positive ARC ccw \n")
                file.write("G03 X%0.4f"%x+" Y%0.4f"%y+" I%0.4f"%i+" J%0.4f"%j +"\n")
            else:
#                file.write(";negative ARC cw \n")
                file.write("G02 X%0.4f"%x+" Y%0.4f"%y+" I%0.4f"%i+" J%0.4f"%j +"\n")
 
        else:
            print "curve detected, subdiv needed"
            
            #rs.ConvertCurveToPolyline(segment,angle_tolerance=5.0, tolerance=0.01, delete_input=False)
            polyLine    = rs.ConvertCurveToPolyline(curve, a_tolerance, tolerance)
            points      = rs.CurvePoints(polyLine)
            
            # insert division points as line
            for pt in points:
                file.write("G01 X%0.4f"%pt.X+" Y%0.4f"%pt.Y+"\n")
            # remove objects after use
            rs.DeleteObjects(polyLine)
                
        file.write("M05\n") # spindle stop
    
    file.write("G00 X0.0000 Y0.0000 F1000\n")
    # file.write("M09\n") # coolant off
    # file.write("M30\n") # program end and reset
    file.close()

    # rs.MessageBox("file succesfully saved to: " + filename + ", with the following parameters:\n"+
    #               "cut feedrate: %0.1f"%sfeed+"\n"+
    #               "cut intensity: %0.1f"%sspindle+"\n"+
    #               "engrave feedrate: %0.1f"%efeed+"\n"+
    #               "engrave intensity: %0.1f"%e_intensity+"\n"
    #               )


# Check to see if this file is being executed as the "main" python
# script instead of being used as a module by some other python script
# This allows us to use the module which ever way we want.
if( __name__ == "__main__" ):
    
    par = read_config()
    
    path = rs.GetObjects("Select Curves/polylines/arcs/circles", rs.filter.curve, True, True)
    
    write_G(path, par)