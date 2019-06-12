'''Basic QuBit Characterizations'''

from os.path import basename as bs
mdlname = bs(__file__).split('.')[0] # instrument-module's name e.g. ENA, PSG, YOKO

from flask import request
from numpy import linspace, sin, pi
from pyqum.instrument.benchtop import ENA
from pyqum.instrument.logger import settings, clocker
from pyqum.instrument.analyzer import curve
from pyqum.instrument.toolbox import cdatasearch, gotocdata, waveform

@settings()
def TESTC(corders={'C1':[0,0,0], 'C2':[0,0,0], 'C3':[0,0,0], 'C4':[0,0,0], 'C5':[0,0,0]}, comment='', dayindex='', taskentry=0, resumepoint=0):
    '''Serve as a template for other real tasks to come
        dayindex: {string:access data, -1:new data 0-:manage data}
    '''
    x = 0
    C1 = waveform('%s to %s * %s'%tuple(corders['C1']))
    C2 = waveform('%s to %s * %s'%tuple(corders['C2']))
    C3 = waveform('%s to %s * %s'%tuple(corders['C3']))
    C4 = waveform('%s to %s * %s'%tuple(corders['C4']))
    C5 = waveform('%s to %s * %s'%tuple(corders['C5']))
    datasize = C1.count*C2.count*C3.count*C4.count*C5.count
    # setting how often the data is logged along the way:
    buffersize = C5.count
    yield corders, comment, dayindex, taskentry, buffersize, resumepoint
    
    # running measurement:
    data = []
    for i in range(resumepoint,datasize):
        # print("%s of %s"%(i+1,datasize))
        caddress = cdatasearch(i, [C1.count,C2.count,C3.count,C4.count,C5.count])
        # Use Cj.data[caddress[j]] for parameters' value here
        x += 1
        # x = C1.data[caddress[0]] + C5.data[caddress[4]]*C2.data[caddress[1]]*sin(pi/2*C3.data[caddress[2]]) + C4.data[caddress[3]]
        data.append(x)
        # saving chunck by chunck improves speed a lot!
        if not (i+1)%buffersize: #multiples of buffersize
            yield data
            data = []

@settings()
def Network_Analyzer(amp, powr, freq, ifb, iq, comment=''):
    '''Testing Room Temperature Amplifier
        iq: [0,1,2] <I:0;Q:1> '''
    bench = ENA.Initiate()
    ENA.setrace(bench, Mparam=['S12'], window='D1')
    ENA.dataform(bench, action=['Set', 'REAL32'])
    ENA.sweep(bench, action=['Set', 'ON', freq[2]])
    fstart, fstop = freq[0], freq[1]
    ENA.linfreq(bench, action=['Set', fstart, fstop]) #F-sweep

    # Iteration part
    for ifb in linspace(ifb[0],ifb[1],ifb[2]):
        ENA.ifbw(bench, action=['Set', ifb])
        for p in linspace(powr[0],powr[1],powr[2]):
            ENA.power(bench, action=['Set', p])
            #start sweeping
            stat = ENA.sweep(bench)
            print("Time-taken would be: %s (%spts)" %(stat[1]['TIME'], stat[1]['POINTS']))
            print("Ready: %s" %ENA.measure(bench)[1])
            ENA.autoscal(bench)
            ENA.selectrace(bench, action=['Set', 'para 1 calc 1'])
            data = ENA.sdata(bench)
            for d in data:
                yield d

    ENA.rfports(bench, action=['Set', 'OFF'])
    ENA.close(bench)


def test():
    points = 70
    C = eval('[1,70,%s]' %points)
    # access-only mode:
    M = TESTC()
    k = M.whichday()
    if k < 0:
        stage, prev = clocker(0) # Marking starting point of time
        i = prev
        # Creating New Data:
        M = TESTC({'C1':[0,0,0], 'C2':[0.1,0.1,0], 'C3':[1,1,0], 'C4':[0,12,3], 'C5':C},'',-1)
        print("For %s points:" %points)
        stage, prev = clocker(stage, prev) # Marking time lapsed
        print("Hence this pc can write %ss per point" %((prev - i) / points))
    else:
        M.selectday(k)
        M.listime()
        m = M.whichmoment()
        # reading Data
        print("Before compensating:\n")
        M.accesstructure()
        M.loadata()
        M.buildata()
        print(M.datacontainer)
        # Manage Data
        M = TESTC(dayindex=k,taskentry=m)
        # reading Data
        print("After compensating:\n")
        M.buildata()
        print(M.datacontainer)
   

# test()

