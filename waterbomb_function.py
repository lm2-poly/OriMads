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


import math
import numpy as np

def model(rel_depth,t1,t2,t3,disp):

    project='waterbomb'
    project_flat = 'waterbomb_flat'
    model_flat = project+'_model'
    model = project + '_model'
    cae_file_flat   = project_flat+'.cae'
    cae_file = project + '.cae'
    odbname=project+'.odb'
    odbname_flat = project_flat + '.odb'

    #--------------------------------------------------------------------
    #Parametres de l'etoile 
    #(n=symetrie, radius=cercle sans matiere au centre, 
    #exte=longueur branche, inte=longueur interieur, depth=epaisseur de l'etoile, width=largeur de la crease)
    #--------------------------------------------------------------------
        
    n=4
    #depth=0.1
    #t1=0.1
    #t2=0.5
    #t3=0.9
    r_ext=60
    r_int=6
    size=1.5
    size2=0.5
    thickness=1

    quadratique=False
    hyperelastic=False
        
    hard_mat=2600
    soft_mat=120
    c_coeff=0.015
        
    m=mdb.Model(modelType=STANDARD_EXPLICIT, name=model_flat)
        
    #--------------------------------------------------------------------
    #part 1 - base faces
    #--------------------------------------------------------------------

    s=m.ConstrainedSketch(name='base', sheetSize=200.0)
    s.ArcByCenterEnds(center=(0.0, 0.0), direction=COUNTERCLOCKWISE, point1=(r_int, 0.0), point2=(r_int*cos(pi/n), r_int*sin(pi/n)))
    s.ArcByCenterEnds(center=(0.0, 0.0), direction=COUNTERCLOCKWISE, point1=(r_ext, 0.0), point2=(r_ext*cos(pi/n), r_ext*sin(pi/n)))
    s.Line(point1=(r_int, 0.0), point2=(r_ext, 0.0))
    s.Line(point1=(r_int*cos(pi/n), r_int*sin(pi/n)), point2=(r_ext*cos(pi/n), r_ext*sin(pi/n)))

    p=m.Part(dimensionality=THREE_D, name='base', type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)

    p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)

    s1=m.ConstrainedSketch(gridSpacing=1.0, name='__profile__', sheetSize=100.0, transform=p.MakeSketchTransform(
        sketchPlane=p.faces[0], 
        sketchPlaneSide=SIDE1, 
        sketchUpEdge=p.datums[2], 
        sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0)))

    s1.Line(point1=(r_ext*cos(t1*pi/n),r_ext*sin(t1*pi/n)),
            point2=(r_int*cos(t2*pi/n),r_int*sin(t2*pi/n)))
    s1.Line(point1=(r_int*cos(t2*pi/n),r_int*sin(t2*pi/n)),
            point2=(r_ext*cos(t3*pi/n),r_ext*sin(t3*pi/n)))

    s1.ConstructionLine(point1=(0.0, 0.0), point2=(cos(pi/n), sin(pi/n)))
    #s1.copyMirror(mirrorLine=s1.geometry[4], 
    #    objectList=(s1.geometry[2], s1.geometry[3]))
    #s1.radialPattern(centerPoint=(0.0, 0.0), geomList=(s1.geometry[2], s1.geometry[3], s1.geometry[5], s1.geometry[6]), number=n, totalAngle=360.0, vertexList=())
    p.PartitionFaceBySketch(faces=p.faces[0], sketch=s1, 
            sketchUpEdge=p.datums[2])


    p.Set(faces=(p.faces[0:2]), name='soft')
    p.Set(faces=(p.faces[:]), name='all')
    p.Set(faces=(p.faces[2:3]), name='hard')
    p.Set(vertices=(p.vertices[0:1]), name='block')
    p.Set(vertices=(p.vertices[1:2]), name='force_initial')
    p.Set(vertices=(p.vertices[4:5]), name='force')
    p.Set(edges=(p.edges[3:4],p.edges[5:6]), name='int')
    p.Set(edges=(p.edges[1:2],p.edges[7:8]), name='ext')
    p.Set(edges=(p.edges[2:3],p.edges[6:7]), name='sym')

    #--------------------------------------------------------------------
    #assembly
    #--------------------------------------------------------------------
        
    a=m.rootAssembly
    a.Instance(dependent=ON, name='base', part=p)

    CSYS=a.DatumCsysByThreePoints(coordSysType=CYLINDRICAL, 
            name='Cylindrique', 
            origin=(0.0,0.0,0.0), 
            point1=(1.0,0.0,0.0), 
            point2=(0.0,1.0,0.0))

    #--------------------------------------------------------------------
    #materiau
    #--------------------------------------------------------------------
        
    m.Material(name='hard')
    m.materials['hard'].Density(
        table=((1.04e-09, ), ))
    m.materials['hard'].Elastic(
        table=((hard_mat, 0.35), ))
        
    m.Material(name='soft')
    m.materials['soft'].Density(
        table=((1.2e-09, ), ))
    if hyperelastic==False:
        m.materials['soft'].Elastic(
            table=((soft_mat, 0.45), ))
    elif hyperelastic==True:
        m.materials['soft'].Hyperelastic(materialType=ISOTROPIC, table=((c_coeff, 0.0), ), testData=OFF, type=
            NEO_HOOKE, volumetricResponse=VOLUMETRIC_DATA)
        
    #--------------------------------------------------------------------
    #Section
    #--------------------------------------------------------------------

    m.HomogeneousShellSection(idealization=NO_IDEALIZATION, 
        integrationRule=SIMPSON, 
        material='hard', 
        name='hard', 
        nodalThicknessField='', 
        numIntPts=5, 
        poissonDefinition=DEFAULT, 
        preIntegrate=OFF, 
        temperature=GRADIENT, 
        thickness=thickness, 
        thicknessField='', 
        thicknessModulus=None, 
        thicknessType=UNIFORM, 
        useDensity=OFF)

    m.HomogeneousShellSection(idealization=NO_IDEALIZATION, 
        integrationRule=SIMPSON, 
        material='soft', 
        name='soft', 
        nodalThicknessField='', 
        numIntPts=5, 
        poissonDefinition=DEFAULT, 
        preIntegrate=OFF, 
        temperature=GRADIENT, 
        thickness=thickness*rel_depth, 
        thicknessField='', 
        thicknessModulus=None, 
        thicknessType=UNIFORM, 
        useDensity=OFF)
        
    p.SectionAssignment(offset=0.0, offsetField='', offsetType=MIDDLE_SURFACE, region=
        p.sets['hard'], sectionName='hard', thicknessAssignment=FROM_SECTION)

    p.SectionAssignment(offset=0.0, offsetField='', offsetType=MIDDLE_SURFACE, region=
        p.sets['soft'], sectionName='soft', thicknessAssignment=FROM_SECTION)


    #--------------------------------------------------------------------
    #step - Pour l'instant seul l'explicit fonctionne, j'ai inclus tous les autres types d'analyses que j'ai essaye mais qui n'ont pas fonctionnees
    #--------------------------------------------------------------------

    #m.ExplicitDynamicsStep(improvedDtMethod=ON, maxIncrement=0.1, name='Analysis', previous='Initial')
    m.ImplicitDynamicsStep(alpha=DEFAULT, amplitude=RAMP, application=QUASI_STATIC, initialConditions=OFF, initialInc=0.001, minInc=5e-5, maxInc=0.01, maxNumInc=10000, name='Analysis', nlgeom=ON, nohaf=OFF, previous= 'Initial')
    m.historyOutputRequests['H-Output-1'].setValues(frequency=1)
    m.fieldOutputRequests['F-Output-1'].setValues(frequency=1)
    #m.StaticStep(initialInc=0.001, maxInc=0.01, maxNumInc=10000, minInc=1e-20, name='Analysis', nlgeom=ON, previous='Initial', timePeriod=2.0)
    #m.StaticRiksStep(initialArcInc=0.01, maxArcInc=0.1, maxLPF=1.0, maxNumInc=10000, name='Analysis', nlgeom=ON, previous='Initial')
        
    #--------------------------------------------------------------------
    #Mesh
    #--------------------------------------------------------------------
        

    p.seedPart(deviationFactor=0.1, minSizeFactor=0.1, size=size)
    p.seedEdgeBySize(constraint=FINER, deviationFactor=0.1, edges=p.sets['int'].edges, minSizeFactor=0.1, size=size2)
    p.seedEdgeBySize(constraint=FINER, deviationFactor=0.1, edges=p.sets['ext'].edges, minSizeFactor=0.1, size=size2)
    p.setMeshControls(elemShape=QUAD, regions=p.faces[:], technique=STRUCTURED)
    if (quadratique==True):
        p.setElementType(elemTypes=(ElemType(elemCode=S8R, elemLibrary=STANDARD), ElemType(
            elemCode=STRI65, elemLibrary=STANDARD)), regions=p.sets['all'])
    elif (quadratique==False):
        p.setElementType(elemTypes=(ElemType(elemCode=S4, elemLibrary=STANDARD), ElemType(
            elemCode=S3, elemLibrary=STANDARD, secondOrderAccuracy=OFF)), regions=p.sets['all'])

    p.generateMesh()
    a.regenerate()

    #--------------------------------------------------------------------
    #Conditions aux limites et chargements
    #--------------------------------------------------------------------


    m.DisplacementBC(amplitude=UNSET,
        createStepName='Analysis',
        distributionType=UNIFORM,
        fieldName='',
        localCsys=None,
        name='Displacement',
        region=a.instances['base'].sets['force_initial']
        , u1=UNSET, u2=UNSET, u3=-disp*r_ext, ur1=UNSET, ur2=UNSET, ur3=UNSET)
        
    m.DisplacementBC(amplitude=UNSET, 
        createStepName='Analysis', 
        distributionType=UNIFORM, 
        fieldName='', 
        localCsys=None, 
        name='Lock', 
        region=a.instances['base'].sets['block']
        , u1=UNSET, u2=UNSET, u3=SET, ur1=UNSET, ur2=UNSET, ur3=SET)

    m.DisplacementBC(amplitude=UNSET, 
        createStepName='Analysis', 
        distributionType=UNIFORM, 
        fieldName='', 
        localCsys=a.datums[CSYS.id], 
        name='Sym', 
        region=a.instances['base'].sets['sym']
        , u1=UNSET, u2=SET, u3=UNSET, ur1=SET, ur2=UNSET, ur3=SET)

    a.regenerate()

    #--------------------------------------------------------------------
    #job
    #--------------------------------------------------------------------
        
    j=mdb.Job(atTime=None, contactPrint=OFF, description='', echoPrint=OFF, 
        explicitPrecision=SINGLE, getMemoryFromAnalysis=True, historyPrint=OFF, 
        memory=90, memoryUnits=PERCENTAGE, model=model, modelPrint=OFF, 
        multiprocessingMode=DEFAULT, name=project_flat, nodalOutputPrecision=SINGLE,
        numCpus=6, numDomains=6, numGPUs=1, numThreadsPerMpiProcess=1, queue=None, 
        resultsFormat=ODB, scratch='', type=ANALYSIS, userSubroutine='', waitHours=
        0, waitMinutes=0)

    mdb.saveAs(cae_file_flat)
    j.submit()
    j.waitForCompletion()
    mdb.saveAs(cae_file_flat)

    odb = session.openOdb(name=odbname_flat)
    data= session.XYDataFromHistory(name='data', odb=odb, steps=('Analysis',), outputVariableName='Strain energy: ALLSE for Whole Model')


    #--------------------------------------------------------------------
    #Deformed shape
    #--------------------------------------------------------------------

    m2=mdb.Model(modelType=STANDARD_EXPLICIT, name=model)
    p3=m2.PartFromOdb(frame=len(data)-1, instance='BASE', name='Deformed', odb=session.openOdb(odbname_flat), shape=DEFORMED, step=0)

    #--------------------------------------------------------------------
    #assembly
    #--------------------------------------------------------------------
        
    a=m2.rootAssembly
    a.Instance(dependent=ON, name='Deformed', part=p3)
    CSYS=a.DatumCsysByThreePoints(coordSysType=CYLINDRICAL, 
            name='Cylindrique', 
            origin=(0.0,0.0,0.0), 
            point1=(1.0,0.0,0.0), 
            point2=(0.0,1.0,0.0))
    #--------------------------------------------------------------------
    #materiau
    #--------------------------------------------------------------------
        
    m2.Material(name='hard')
    m2.materials['hard'].Density(
        table=((1.04e-09, ), ))
    m2.materials['hard'].Elastic(
        table=((hard_mat, 0.35), ))
        
    m2.Material(name='soft')
    m2.materials['soft'].Density(
        table=((1.2e-09, ), ))
    if hyperelastic==False:
        m2.materials['soft'].Elastic(
            table=((soft_mat, 0.45), ))
    elif hyperelastic==True:
        m2.materials['soft'].Hyperelastic(materialType=ISOTROPIC, table=((c_coeff, 0.0), ), testData=OFF, type=
            NEO_HOOKE, volumetricResponse=VOLUMETRIC_DATA)
        
    #--------------------------------------------------------------------
    #Section
    #--------------------------------------------------------------------

    m2.HomogeneousShellSection(idealization=NO_IDEALIZATION, 
        integrationRule=SIMPSON, 
        material='hard', 
        name='hard', 
        nodalThicknessField='', 
        numIntPts=5, 
        poissonDefinition=DEFAULT, 
        preIntegrate=OFF, 
        temperature=GRADIENT, 
        thickness=thickness, 
        thicknessField='', 
        thicknessModulus=None, 
        thicknessType=UNIFORM, 
        useDensity=OFF)

    m2.HomogeneousShellSection(idealization=NO_IDEALIZATION, 
        integrationRule=SIMPSON, 
        material='soft', 
        name='soft', 
        nodalThicknessField='', 
        numIntPts=5, 
        poissonDefinition=DEFAULT, 
        preIntegrate=OFF, 
        temperature=GRADIENT, 
        thickness=thickness*rel_depth, 
        thicknessField='', 
        thicknessModulus=None, 
        thicknessType=UNIFORM, 
        useDensity=OFF)
        
    p3.SectionAssignment(offset=0.0, offsetField='', offsetType=MIDDLE_SURFACE, region=
        p3.sets['HARD'], sectionName='hard', thicknessAssignment=FROM_SECTION)

    p3.SectionAssignment(offset=0.0, offsetField='', offsetType=MIDDLE_SURFACE, region=
        p3.sets['SOFT'], sectionName='soft', thicknessAssignment=FROM_SECTION)

    #--------------------------------------------------------------------
    #step - Pour l'instant seul l'explicit fonctionne, j'ai inclus tous les autres types d'analyses que j'ai essaye mais qui n'ont pas fonctionnees
    #--------------------------------------------------------------------

    #m.ExplicitDynamicsStep(improvedDtMethod=ON, maxIncrement=0.1, name='Analysis', previous='Initial')
    m2.ImplicitDynamicsStep(alpha=DEFAULT, amplitude=RAMP, application=QUASI_STATIC, initialConditions=OFF, initialInc=0.001, minInc=5e-5, maxInc=0.01, maxNumInc=10000, name='Analysis', nlgeom=ON, nohaf=OFF, previous= 'Initial')
    m2.historyOutputRequests['H-Output-1'].setValues(frequency=1)
    m2.fieldOutputRequests['F-Output-1'].setValues(frequency=1)
    #m.StaticStep(initialInc=0.001, maxInc=0.01, maxNumInc=10000, minInc=1e-20, name='Analysis', nlgeom=ON, previous='Initial', timePeriod=2.0)
    #m.StaticRiksStep(initialArcInc=0.01, maxArcInc=0.1, maxLPF=1.0, maxNumInc=10000, name='Analysis', nlgeom=ON, previous='Initial')
        



    #--------------------------------------------------------------------
    #Conditions aux limites et chargements
    #--------------------------------------------------------------------


    m2.DisplacementBC(amplitude=UNSET, 
        createStepName='Analysis', 
        distributionType=UNIFORM, 
        fieldName='', 
        localCsys=a.datums[CSYS.id],
        name='Displacement', 
        region=a.instances['Deformed'].sets['FORCE_INITIAL']
        , u1=UNSET, u2=UNSET, u3=SET, ur1=UNSET, ur2=UNSET, ur3=UNSET)


    m2.DisplacementBC(amplitude=UNSET, 
        createStepName='Analysis', 
        distributionType=UNIFORM, 
        fieldName='', 
        localCsys=a.datums[CSYS.id], 
        name='Sym', 
        region=a.instances['Deformed'].sets['SYM']
        , u1=UNSET, u2=SET, u3=UNSET, ur1=SET, ur2=UNSET, ur3=SET)

    m2.DisplacementBC(amplitude=UNSET,
                      createStepName='Analysis',
                      distributionType=UNIFORM,
                      fieldName='',
                      localCsys=a.datums[CSYS.id],
                      name='int',
                      region=a.instances['Deformed'].sets['INT']
                      , u1=UNSET, u2=UNSET, u3=-2 * disp * r_ext, ur1=UNSET, ur2=UNSET, ur3=SET)

    a.regenerate()

    #--------------------------------------------------------------------
    #job
    #--------------------------------------------------------------------

    j=mdb.Job(atTime=None, contactPrint=OFF, description='', echoPrint=OFF, 
        explicitPrecision=SINGLE, getMemoryFromAnalysis=True, historyPrint=OFF, 
        memory=90, memoryUnits=PERCENTAGE, model=model, modelPrint=OFF, 
        multiprocessingMode=DEFAULT, name=project, nodalOutputPrecision=SINGLE, 
        numCpus=6, numDomains=6, numGPUs=1, numThreadsPerMpiProcess=1, queue=None, 
        resultsFormat=ODB, scratch='', type=ANALYSIS, userSubroutine='', waitHours=
        0, waitMinutes=0)

    mdb.saveAs(cae_file)
    j.submit()
    j.waitForCompletion()
    mdb.saveAs(cae_file)