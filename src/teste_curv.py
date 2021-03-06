#!/usr/bin/python
import descritores as desc
import pylab
import numpy as np
import timeit

#start = timeit.default_timer()
l1 = desc.curvatura("../imagens/Acer_M_BIN_16.bmp",np.array([48.0]))
#l1 = desc.curvatura("../imagens/dude1.png",np.array([48.0]))
l2 = desc.curvatura("../imagens/dude1_big.png",np.array([48.0]))
l3 = desc.curvatura("../imagens/dude1_small.png",np.array([48.0]))

pylab.subplot(311)
pylab.plot(l1.curvs[0])
pylab.subplot(312)
pylab.plot(l2.curvs[0])
pylab.subplot(313)
pylab.plot(l3.curvs[0])

pylab.show()
