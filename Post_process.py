from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from optimization import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *
from abaqus import *
from abaqusConstants import *
import __main__

import math
import numpy as np

def post_process(rel_depth,t1,t2,t3,disp):

    project='waterbomb'
    project_flat = 'waterbomb_flat'
    report_address='Report.txt'
    model      = project+'_model'
    cae_file   = project+'.cae'
    
    
    odbname=project+'.odb'
    odb = session.openOdb(name=odbname)
    data= session.XYDataFromHistory(name='data', odb=odb, steps=('Analysis',), outputVariableName='Strain energy: ALLSE for Whole Model')
    energy=np.array(data)[:,1]
    displacement=np.array([odb.steps['Analysis'].frames[i].frameValue for i in range(len(energy))])
    derivative=np.array([(energy[i+1]-energy[i])/(displacement[i+1]-displacement[i]) for i in range(len(energy)-2)])

    odbname_flat = project_flat + '.odb'
    odb_flat = session.openOdb(name=odbname_flat)
    displacement_flat = odb_flat.steps['Analysis'].frames[-1].frameValue

    if len(derivative[derivative<0])!=0:
        end=derivative.tolist().index(derivative[derivative<0][-1])
        start=end-1
        iteration=derivative[start]
        while iteration<0:
        	start-=1
        	iteration=derivative[start]
        
        if (len(derivative[derivative<0])>0) and (float(start)/len(derivative)>0.25):
            delta=(energy[start+2]-energy[end+1])/energy[start+2]
            Umax=energy[start+2]
        else:
            delta=-float('inf')
            Umax=-float('inf')
    else:
        delta=-float('inf')
        Umax = -float('inf')
        end=len(derivative)-1
        
    session.viewports['Viewport: 1'].setValues(displayedObject=odb)
    session.viewports['Viewport: 1'].odbDisplay.setFrame(step=0, frame=1)
    odbName=session.viewports[session.currentViewportName].odbDisplay.name
    session.odbData[odbName].setValues(activeFrames=(('Analysis', ('0:'+str(end), )), ))
    session.fieldReportOptions.setValues(printXYData=OFF, printTotal=OFF,
        numberFormat=NumberFormat(numDigits=5, precision=0, format=ENGINEERING))
    session.writeFieldReport(fileName='abaqus.rpt', append=OFF,
        sortItem='S.Mises', odb=odb, step=0, frame=end,
        outputPosition=INTEGRATION_POINT, variable=(('S', INTEGRATION_POINT, ((
        INVARIANT, 'Mises'), )), ), stepFrame=ALL)
    stress=[]
    with open("abaqus.rpt", 'r') as file:
        content = file.readlines()
        for i in range(len(content)-30):
            if content[i] == "   Step: Analysis\n":
                stress.append(max(float(content[i+32].split()[1]),float(content[i+32].split()[2])))
        file.close()
    if displacement[-1] != 1.0 or displacement_flat != 1.0:
        delta=-float('inf')
    with open(report_address, 'a') as fp:
    	fp.write(str(rel_depth)+"\t"+
    		str(t1)+"\t"+
    		str(t2)+"\t"+
    		str(t3)+"\t"+
            str(disp)+"\t"+
            str(np.argmax(stress))+"\t"+
            str(max(stress))+"\t"+
            str(Umax) + "\t"+
    		str(delta)+"\n")
    odb.close()
    return 