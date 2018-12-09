#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Wei Shuai"
__copyright__ = "Copyright 2018 Wei Shuai <cpuwolf@gmail.com>"
__version__ = "1.0"
__email__ = "cpuwolf@gmail.com"
"""
Created on Dec 2018
@author: Wei Shuai <cpuwolf@gmail.com>


"""

import os
import shutil, errno
import sys
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import QThread
from PyQt4.QtGui import QFileDialog
import ConfigParser
import logging
import tempfile
from appdirs import *


def findwholeline(data,keyword,startidx):
    idx=data[startidx:].find(keyword)
    if idx != -1:
        #print idx
        idxtmpstart = startidx+idx
        idxtmpend=data[idxtmpstart:].find("\n")
        idxend = idxtmpstart +idxtmpend
        #print idxend
        if idxtmpend != -1:
            lines=data[:idxend].splitlines()
            #print lines[-1]
            idxstart=data[startidx:].find(lines[-1])
            if idxstart != -1:
                #print idxstart,idxend
                return [startidx+idxstart,idxend]
        else:
            #file end without '\n'
            lines=data.splitlines()
            #print lines[-1]
            idxstart=data[startidx:].find(lines[-1])
            if idxstart != -1:
                #print idxstart,idxend
                return [startidx+idxstart,len(data)]
    return [-1,-1]


def findsectionstartend(data,keywordstart,keywordend):
    searchidx=0
    result=[]
    while searchidx <= len(data):
        [idxstart,idxend]=findwholeline(data,keywordstart,searchidx)
        if (idxstart != -1) and (idxend != -1):
            [idxsecstart,idxsecend]=findwholeline(data,keywordend,idxend)
            if (idxsecstart != -1) and (idxsecend != -1):
                searchidx=idxsecend
                result.append([idxstart,idxsecend,data[idxstart:idxend]])
            else:
                print "error"
                break
        else:
            break
    return result

def findsection(data,keyword):
    searchidx=0
    result=[]
    while searchidx <= len(data):
        [idxstart,idxend]=findwholeline(data,keyword,searchidx)
        if (idxstart != -1) and (idxend != -1):
            searchidx=idxend
            result.append([idxstart,idxend,data[idxstart:idxend]])
        else:
            break
    return result   
def getsectionstarteng(seclines):
    if len(seclines) > 0:
        return [seclines[0][0],seclines[-1][1]]
    else:
        return [0,0]

class objidx():
    def __init__(self, bidx=0):
        self.idxs=[]
        self.baseidx=bidx
        self.start =0
        self.end=0
    def processsection_dx(self,seclines):
        for line in seclines:
            str = line[2]
            cols=str.split()
            self.idxs.append(self.baseidx+int(cols[1]))
        [s, e]=getsectionstarteng(seclines)
        if self.end == self.start:
            self.start = s
        if e > self.end:
            self.end=e
    def processsection_dx10(self,seclines):
        for line in seclines:
            str = line[2]
            cols=str.split()
            num = len(cols)
            if  num >= 11:
                for i in range(1,10):
                    self.idxs.append(self.baseidx+int(cols[i]))
        [self.start, self.end]=getsectionstarteng(seclines)
    def getsectionstarteng(self):
        return [self.start, self.end]

        
class xpobj():
    def __init__(self):
        self.oidx = objidx()
    def processxpobj(self,filepath):
        with open(filepath,"rU") as f:
            self.data = f.read()
            self.pc=findsection(self.data,"POINT_COUNTS")
            [self.pc_start,self.pc_end]= getsectionstarteng(self.pc)
            [self.pc_tris,self.pc_lines,self.pc_lites,self.pc_indices]=self.processsection_pc()
            

            self.vt=findsection(self.data,"VT")
            #print vt
            [self.vt_start,self.vt_end]= getsectionstarteng(self.vt)
            print "vt section ",[self.vt_start,self.vt_end]
            self.dx10=findsection(self.data,"DX10")
            #print dx10
            self.oidx.processsection_dx10(self.dx10)
            self.dx=findsection(self.data,"DX")
            #print dx
            self.oidx.processsection_dx(self.dx)

            if self.pc_tris == len(self.vt):
                print "vt max=", len(self.vt)
            else:
                print "error tris number"
            if self.pc_indices == len(self.oidx.idxs):
                print "idx max=", len(self.oidx.idxs)
            else:
                print "error indices number"
            
            [self.idx_start,self.idx_end]= self.oidx.getsectionstarteng()
            print "idx section ",[self.idx_start,self.idx_end]
                   
        #shutil.copy(filepath, filepath+".orig.obj")
            
        
        return True
    def processsection_pc(self):
        if len(self.pc) != 1:
            print "error: processsection_pc"
        for line in self.pc:
            str = line[2]
            cols=str.split()
            return [int(cols[1]),int(cols[2]),int(cols[3]),int(cols[4])]


def xpobjmerge(filepath1, filepath2):
    newdata=[]
    mainobj=xpobj()
    mainobj.processxpobj(filepath1)
    secobj=xpobj()
    secobj.processxpobj(filepath2)
    #use main header
    newdata=mainobj.data[:mainobj.pc_start]
    tris = mainobj.pc_tris + secobj.pc_tris
    indices = mainobj.pc_indices + secobj.pc_indices
    newdata+="POINT_COUNTS\t"+str(tris)+"\t"+str(mainobj.pc_lines)+"\t"+str(mainobj.pc_lites)+"\t"+str(indices)
    newdata+=mainobj.data[mainobj.pc_end:mainobj.idx_start]
    newdata+=secobj.data[secobj.vt_start:secobj.vt_end]

    with open(filepath1+".merge.obj","w") as fw:
            fw.write(newdata)

def loadinputfile(filetxt):
    cookies = []
    wewant = []
    try:
        with open(filetxt,"rU") as f:
            data = f.read()
            sections=findsection(data,"ANIM_rotate_begin ","ANIM_rotate_end")
            index=1
            while index < len(sections):
                if sections[index][0]-sections[index-1][1] == 1:
                    cookies.append([sections[index-1][0],sections[index][1],sections[index-1][2]])
                    tmpidx=index
                    tmpidx+=2
                    if tmpidx < len(sections):
                        index+=2
                    else:
                        index+=1
                else:
                    cookies.append(sections[index])
                    index+=1
            #print cookies
            for cookie in cookies:
                sp=cookie[2].split(' ')
                wewant.append([sp[-1],data[cookie[0]:cookie[1]]])
                #wewant.append([cookie[2],data[cookie[0]:cookie[1]]])
            print wewant, len(wewant)
    except IOError:
        return wewant
    return wewant
    

def user_path(relative_path):
    base_path = user_data_dir("xpobjmerge","cpuwolf")
    if not os.path.exists(base_path):
        os.makedirs(base_path, 0o777)
    mpath = os.path.join(base_path, relative_path)
    return mpath


    
def resource_path(relative_path): # needed for bundling
    mpath = user_path(relative_path)
    if os.path.exists(mpath):
        return mpath
                                                                                                                     
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def myreadconfig():
    config = ConfigParser.RawConfigParser()
    config.read(resource_path('xpobjmerge.cfg'))
    return [config.get('basic', 'inputfile'),config.get('basic', 'outputfolder')]

        
def mywriteconfig(ifile,ofolder):
    config = ConfigParser.RawConfigParser()
    config.add_section('basic')
    config.set('basic', 'inputfile', ifile)
    config.set('basic', 'outputfolder', ofolder)
    with open(user_path('xpobjmerge.cfg'), 'wb') as configfile:
        config.write(configfile)

class MyThread(QThread):
    set_text = QtCore.pyqtSignal('QString')
    set_done = QtCore.pyqtSignal()
    def __init__(self):
        QThread.__init__(self)
        self.text_valuepath = None
        self.text_folderpath = None
    def __del__(self):
        self.wait()
    def run(self):
        self.set_text.emit("<h1>please wait...</h1>")
        xpobjmerge(self.text_valuepath, self.text_folderpath)
        self.set_text.emit("<h1>done</h1>")
        self.set_done.emit()

#debug_logger = logging.getLogger('wingflex')
#debug_logger.write = debug_logger.debug    #consider all prints as debug information
#debug_logger.flush = lambda: None   # this may be called when printing
#sys.stdout = debug_logger

qtCreatorFile = "main.ui" # Enter file here.

Ui_MainWindow, QtBaseClass = uic.loadUiType(resource_path(qtCreatorFile))

class MyApp(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.pushButtonfix.clicked.connect(self.GoCrazy)
        self.pushButtonValue.clicked.connect(self.getfile)
        self.pushButton777.clicked.connect(self.getfolder)
        a=myreadconfig()
        self.lineEditvalue.setText(a[0])
        self.lineEdit777.setText(a[1])
    
    def GoCrazy(self):
        print "start"
        self.myThread = MyThread()
        self.myThread.text_valuepath = self.lineEditvalue.text()
        self.myThread.text_folderpath = unicode(self.lineEdit777.text())
        self.myThread.set_text.connect(self.on_set_text)
        self.myThread.set_done.connect(self.on_set_done)
        self.pushButtonfix.setEnabled(False)
        self.myThread.start()

    def on_set_done(self):
        self.pushButtonfix.setEnabled(True)

    def on_set_text(self, generated_str):
        #print("on_set_text:", generated_str)
        self.label_st.setText(generated_str)
    
    def upconfig(self):
        mywriteconfig(self.lineEditvalue.text(), self.lineEdit777.text())
        
    def getfile(self):
        self.lineEditvalue.setText(QFileDialog.getOpenFileName(self, 'Open X-Plane obj file', self.lineEditvalue.text(),"X-Plane obj file(*.obj *.*)"))
        self.upconfig()
    
    def getfolder(self):
        self.lineEdit777.setText(QFileDialog.getOpenFileName(self, 'Open X-Plane obj file', self.lineEdit777.text(),"X-Plane obj file(*.obj *.*)"))
        self.upconfig()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    app.exec_()
print "all done!"