import subprocess
import re
import os
from pathlib import Path
import PyNomad
import numpy as np
from PIL import Image
from functions import *


x0=[1.0, 0.1, 0.5, 0.9, 0.6]

lb=[0.5, 0.1, 0.1, 0.1, 0.1]
ub=[2.0, 0.9, 0.9, 0.9, 0.9]

params = ["DIMENSION 5",
          "BB_OUTPUT_TYPE OBJ CSTR CSTR",
          "MAX_BB_EVAL 1000", 
          "BB_INPUT_TYPE (R R R R R)",
          "DISPLAY_ALL_EVAL true",
          "DISPLAY_STATS BBE ( sol ) OBJ", 
          'stats_file "Blackbox_result.txt" BBE ( sol ) OBJ',
          'DISPLAY_DEGREE 1']

PyNomad.optimize(energy, x0, lb, ub, params)

#penser à modifier le range(taille de x)
