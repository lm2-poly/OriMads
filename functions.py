import subprocess
import re
from pathlib import Path
from PIL import Image


def run( cmd):
    completed = subprocess.run(["powershell", "-Command", cmd], capture_output=True)
    return completed

def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))

def getImage(longueur):
    im = Image.open('./images/Deployed'+str(int(longueur))+'.png')
    im_new = crop_center(im, 1050, 634)
    im_new.save('./images/Deployed'+str(int(longueur))+'.png', quality=95)
    im = Image.open('./images/Folded'+str(int(longueur))+'.png')
    im_new = crop_center(im, 1050, 634)
    im_new.save('./images/Folded'+str(int(longueur))+'.png', quality=95)
    im = Image.open('./images/Base'+str(int(longueur))+'.png')
    im_new = crop_center(im, 1050, 634)
    im_new.save('./images/Base'+str(int(longueur))+'.png', quality=95)

def Launch(x, compute_type):
    print("x="+str(x)+", analysis="+compute_type[1])
    with open("Launch.py", "w") as f:
        f.write("from "+compute_type[0]+"waterbomb_function import *\n")    
        f.write("from Post_process import *\n")
        f.write("rel_depth="+str(x[0])+"\n")
        f.write("t1="+str(x[1])+"\n")
        f.write("t2="+str(x[2])+"\n")
        f.write("t3="+str(x[3])+"\n")
        f.write("disp="+str(x[4])+"\n")
        f.write(compute_type[1]+"(rel_depth,t1,t2,t3,disp)\n")
        f.write("post_process(rel_depth,t1,t2,t3,disp)\n")
        f.close()
        
def Report(result):
    with open("Report.txt", "r") as file:
        last_line = file.readlines()[-1]
        file.close()
        last_line = last_line.split()
    if result.group(1) == "" and last_line[-1] != '-inf':
        energy = -float(last_line[-1])
        constraint = float(last_line[-3])
        Umax = float(last_line[-2])
        with open('Report.txt', 'r') as fp:
            longueur=len(fp.readlines())
    else:
        energy=float('inf')
        constraint = float(last_line[-2])
        Umax = float(last_line[-3])
    return energy, constraint, Umax

def energy(x):
    x1=[]
    for i in range(5):
        x1.append(x.get_coord(i))   
    #enleve les anciens fichiers
    for filename in Path(".").glob("waterbomb.*") and Path(".").glob("abaqus*")  :
        filename.unlink()
    #modifie le script global
    Launch(x1, ["","model"])
    
    #lance le script
    command = "abaqus cae nogui=Launch.py"
    cmd_output = run(command)
    result = re.search("stdout=b'(.*)', stderr", str(cmd_output))    
    
    ##ligne de retour utile en cas de problème
    #print(result.group(1)+"point:"+str(x1))
    
    #on récupère le résultat dans le fichier report
    energy, constraint, Umax = Report(result)
    
    print("result:"+str(-energy), "constraint:"+str(constraint), "Umax:"+str(Umax))
    rawBBO = str(energy) + " " + str(constraint-100.0) + " " + str(36.7-Umax)
    x.setBBO(str(rawBBO).encode("UTF-8"))
    return 1

def surrogate(x):
    x1=[]
    for i in range(6):
        x1.append(x.get_coord(i))   
    #enleve les anciens fichiers
    for filename in Path(".").glob("waterbomb.*") and Path(".").glob("abaqus*")  :
        filename.unlink()
    #modifie le script global
    Launch(x1, ["surrogate_","surrogate"])
    
    #lance le script
    command = "abaqus cae nogui=Launch.py"
    cmd_output = run(command)
    result = re.search("stdout=b'(.*)', stderr", str(cmd_output))    
    
    ##ligne de retour utile en cas de problème
    #print(result.group(1)+"point:"+str(x1))
    
    #on récupère le résultat dans le fichier report
    energy=Report(result)  
    
    print("result:"+str(-energy))    
    x.setBBO(str(energy).encode("UTF-8"))
    return 1