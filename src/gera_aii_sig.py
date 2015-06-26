#!/usr/bin/python

import sys
import cPickle
import numpy as np
import aii

diretorio = sys.argv[1]
#diretorio = ".\\1400_mpeg7\\"
raio = 0.35

f = open(diretorio+"classes.txt","r")
cl = cPickle.load(f)
f.close()

db = {}

for im_file in cl.keys():
   tmp = aii.AreaIntegralInvariant2(diretorio+im_file,0.35,0)
   h = np.histogram(tmp,bins = 30,range = (0.05,0.9))
   h = h[0].astype(float)/float(h[0].sum())
   print im_file,h
   db[im_file] = np.hstack((cl[im_file],h))
#   print im_file,db[im_file]
   
cPickle.dump(db,open(sys.argv[2],"w"))