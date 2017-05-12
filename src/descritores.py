# -*- coding: iso-8859-1 -*-
# descritores : m�dulo que implementa o c�lculo de assinaturas e descritores de imagens

import numpy as np
#import cv
from skimage import measure,io,img_as_float
from scipy.interpolate import interp1d 
from scipy.spatial.distance import pdist,squareform
from math import sqrt,acos

class contour_base:
 '''Represents an binary image contour as a complex discrete signal. 
   Some calculation methods are provided to compute contour 1st derivative, 2nd derivatives and perimeter.
   The signal variable (self.c) is represented as a single dimensional ndarray of complex.  
   This class is interable and callable so, interation over objects results in sequential access to each signal variable element. Furthermore, calling the object as a function yields as return value te signal variable.
 
 '''

 def __init__(self,fn):

  self.__i = 0
  if type(fn) is str:
   im = img_as_float(io.imread(fn, as_grey = True))
   s = measure.find_contours(im,.5)[0]
   self.c = np.array([complex(i[1],i[0]) for i in s])
  elif type(fn) is np.ndarray:
   self.c = fn
  #if type(fn) is str:
   #im = cv.LoadImage(fn,cv.CV_LOAD_IMAGE_GRAYSCALE)
   #s = cv.FindContours(im,cv.CreateMemStorage(),cv.CV_RETR_LIST,cv.CV_CHAIN_APPROX_NONE) 
   #self.c = np.array([complex(i[1],i[0]) for i in s])
  #elif (type(fn) is np.ndarray):
    #self.c = fn
  #elif (type(fn) is cv.iplimage):
    #s = cv.FindContours(fn,cv.CreateMemStorage(),cv.CV_RETR_LIST,cv.CV_CHAIN_APPROX_NONE) 
    #self.c = np.array([complex(i[1],i[0]) for i in s])
  N = self.c.size
  self.freq = np.fft.fftfreq(N,1./float(N))

  self.ftc = np.fft.fft(self.c)

  if isinstance(self,contour_base):
   self.calc_derivatives()
 
 def calc_derivatives(self):
   ftcd = np.complex(0,1) * 2 * np.pi * self.freq * self.ftc
   ftcdd = - (2 * np.pi * self.freq)**2 * self.ftc 
   self.cd = np.fft.ifft(ftcd)
   self.cdd = np.fft.ifft(ftcdd)

 def first_deriv(self): 
  '''Return the contour signal 1st derivative'''
  return self.cd

 def second_deriv(self): 
  '''Return the contour signal 2nd derivative'''
  return self.cdd

 def perimeter(self): 
  '''Calculate and return the contour perimeter'''
  return (2*np.pi*np.sum(np.abs(self.cd))/float(self.cd.size))

 def __iter__(self): return self

 def next(self):

  if self.__i > self.c.size-1:
   self.__i = 0
   raise StopIteration
  else:
   self.__i += 1
   return self.c[self.__i-1]
 
 def __call__(self): return self.c

class contour(contour_base):
  '''Like contour_base except that, prior to derive a complex signal representation, smooths the image contour using a Gaussian kernel. The kernel parameter (gaussian standard deviation) is the second constructor parameter. See also contour_base.'''

  # Gaussian smoothing function 
  def __G(self,s):
    return (1/(s*(2*np.pi)**0.5))*np.exp(-self.freq**2/(2*s**2))
  
  def __init__(self,fn,sigma=None):
   contour_base.__init__(self,fn)
   if sigma is not None:
    E = np.sum(self.ftc * self.ftc.conjugate())
    self.ftc = self.ftc * self.__G(sigma)
    Eg  = np.sum(self.ftc * self.ftc.conjugate())
    k = sqrt(abs(E/Eg))
    self.c = np.fft.ifft(self.ftc)*k
    self.calc_derivatives()
    self.cd = self.cd * k
    self.cdd = self.cdd * k
     

# classe curvatura : calcula a curvatura de um contorno para v�rios n�veis de suaviza��o
# Par�metros do Construtor:   def __init__(self,fn = None,sigma_range = np.linspace(2,30,10)) 
#  fn : Pode ser o nome de um arquivo de imagem (string) que contenha uma forma bin�ria ou um vetor (ndarray) de valores das
# coordenadas do contorno de uma forma (representa��o complexa x+j.y). 
# No primeiro caso os contornos s�o extra�dos atrav�s da fun��o cv.FindContours() da biblioteca Opencv
#  sigma_range :  vetor (ndarray) que cont�m os valores que ser�o utilizados como desvio padr�o para o FPB Gaussiana. 
# que filtra os contorno antes do c�lculo da curvatura.
 #  when zero no filtering is applied to contour

class curvatura:
  '''For a given binary image calculates and yields a family of curvature signals represented in a two dimensional ndarray structure; each row corresponds to the curvature signal derived from the smoothed contour for a certain smooth level.'''

  def __Calcula_Curvograma(self,fn):
   z = contour(fn)
   caux = [contour(z(),s) for s in self.sigmas]
   caux.append(z)
   self.contours = np.array(caux)
   self.t = np.linspace(0,1,z().size)
   self.curvs = np.ndarray((self.sigmas.size+1,self.t.size),dtype = "float")
  
   for c,i in zip(self.contours,np.arange(self.contours.size)):
    # Calcula curvatura para varias escalas de suaviza��o do contorno da forma
     curv = c.first_deriv() * np.conjugate(c.second_deriv())
     curv = - curv.imag
     curv = curv/(np.abs(c.first_deriv())**3)
     # Array bidimensional curvs = Curvature Function k(sigma,t) 
     self.curvs[i] = np.tanh(curv)*c.perimeter() 
 
  # Contructor 
  def __init__(self,fn = None,sigma_range = np.linspace(2,30,20)):
   # Extrai contorno da imagem
   self.sigmas = sigma_range
   self.__Calcula_Curvograma(fn)

 # Function to compute curvature
 # It is called into class constructor
  def __call__(self,idx = 0,t= None):
    if t is None:
     __curv = self.curvs[idx]
    elif (type(t) is np.ndarray):
     __curv = interp1d(self.t,y = self.curvs[idx],kind='quadratic')
     return(__curv(t))
    else:
      __curv = self.curvs[idx]

    return(__curv)
   
class bendenergy:
 ''' For a given binary image, computes the multiscale contour curvature bend energy descriptor'''
 
 def __init__(self,fn,scale):
  self.__i = 0
  k = curvatura(fn,scale[::-1])
  # p = perimetro do contorno nao suavisado
  p = k.contours[-1].perimeter() 
  self.phi  = np.array([(p**2)*np.mean(k(i)**2) for i in np.arange(0,scale.size)])

 def __call__(self): return self.phi
 
 def __iter__(self): return self

 def next(self):

   if self.__i > self.phi.size-1:
    self.__i = 0
    raise StopIteration
   else:
    self.__i += 1
    return self.phi[self.__i-1]

class areaintegralinvariant:

 def __init__(self,fn,raio,sigma,n):
  self.r = raio
  t = np.linspace(0,1,n)
  k = curvatura(fn,np.linspace(sigma,sigma,1))
  self.ir = np.ndarray((t.size),dtype="double")
  self.ir = 2*self.r**2*np.arccos(self.r*k(0,t)/2)
 
 def __call__(self): return (self.ir)

def dii(fn,raio):
  r = raio
  c = contour_base(fn)
  aux = np.vstack([c.c.real,c.c.imag]).T
  d = squareform(pdist(aux))
  return np.array([x[np.nonzero(x <= r)].sum() for x in d])
 
def cd(fn,sigma=27.0):
  if (sigma != 0):
   img_c = contour(fn,sigma)
  else:
   img_c = contour_base(fn)
  # Calcula dist�ncia ao centr�ide
  dc = np.abs((img_c()-img_c().mean()))
  dc = dc/np.max(dc)
  # m = maior distancia do contorno ao centroide
  #m = np.max(dc)
  #m = np.nonzero(dc == m)[0][0]
  # rearranja vetor a partir da maior distancia 
  # e normaliza valores
  #dc = np.r_[dc[m:],dc[0:m-1]]/float(dc[m])
  return dc

# Angle sequence shape signature
class angle_seq_signature:

 def __init__(self,fn,raio,sigma=27.0):
  #self.r = raio
  if (sigma != 0):
   self.cont = contour(fn,sigma).c
  else:
   self.cont = contour_base(fn).c
   
  self.N = self.cont.shape[0] 
  
  if raio != 0.:   
   self.sig = self.angle_seq(int(round(raio*self.N)))
  else: 
   aux = np.zeros((self.N,))
   for i in range(1,round(self.N/8),4):
    aux = aux + self.angle_seq(i);
    self.sig = aux/len(range(1,round(self.N/8),4))
  
  self.sig = self.sig/self.sig.max()
  
 def angle_seq(self,r):
  low = self.cont[0:r].copy()
  high = self.cont[self.N-r:self.N].copy()
  cont = np.hstack((high,self.cont,low))
  a = []
  for i in np.arange(r,self.N+r):
   v1 = cont[i] - cont[i-r]
   v2 = cont[i+r] - cont[i]
   cc = (v1*v2).real/float(abs(v1)*abs(v2))
   if cc > 1.0:
    cc = 1.0
   if cc < -1.0:
    cc = -1.0
   angle = acos(cc)
   a.append(angle)
   
  return np.array(a)

# Triangle area signature
class TAS:
 def TAN(self,c,ts):
  low = c[0:ts].copy()
  high = c[self.N-ts:self.N].copy()
  c = np.hstack((high,c,low))
  
  ta = []
  for i in np.arange(ts,self.N+ts):
   a = 0.5*(c[i].real*(c[i+ts]-c[i-ts]).imag + c[i+ts].real*(c[i-ts]-c[i]).imag + c[i-ts].real*(c[i]-c[i+ts]).imag)
   ta.append(a)
  ta = np.array(ta)
  ta = ta/np.abs(ta).max()
  return ta

 def __init__(self,fn):
  cont = contour_base(fn).c
  self.N = cont.shape[0]
  print(fn,self.N)
  Ts = int(np.floor((self.N-1)/2))
  t = []
  for ts in np.arange(1,Ts):
   t.append(self.TAN(cont,ts))
  
  acum = t[0] 
  for a in t[1:]:
   acum = acum + a
  self.sig = np.array(acum)/float(Ts)
