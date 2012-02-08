#!/usr/bin/env python

# Copyright (c) 2012 Andy Newton
#
# This file is part of pybrainband.
#
# pybrainband is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pybrainband is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pybrainband.  If not, see <http://www.gnu.org/licenses/>.



# Highly shonky demo code which reads from a brainband and displays the
# various readings on some WXWidgets meters.  Really rather rough and ready!

import wx
import serial
import threading
from brainband.gui import BrainBandDialMeter, BrainBandWaveMeter
from brainband.parser import BrainBandParser

# Thread for grabbing brainial data
class BrainThread(threading.Thread):
    def __init__(self, serial, gui):
        threading.Thread.__init__(self)
        self.gui = gui
        self.parser = BrainBandParser(serial)

    def run(self):
        counter = 0
        while(True):
            # Read a packet of data
            self.parser.readPacket()
            counter += 1
            if(counter > 100):
                counter = 0
                self.gui.updateMeters(self.parser)


    def state_updated(self, data):
        # Create a BrainEvent for the WX gui shonk to handle
        evt = BrainEvent(BrainEventType, -1, data)
        wx.PostEvent(self.gui, evt)

class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        self.dirname=''

        # A "-1" in the size parameter instructs wxWidgets to use the default size.
        # In this case, we select 200px width and the default height.
        wx.Frame.__init__(self, parent, title=title, size=(200,-1))
        #self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.CreateStatusBar() # A Statusbar in the bottom of the window

        # Setting up the menu.
        filemenu= wx.Menu()
        menuExit = filemenu.Append(wx.ID_EXIT,"E&xit"," Close the program")

        # Creating the menubar.
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.

        # Events.
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)


        # We want to nest a couple of horizontal layouts inside a vertical layout...
        sizerTop    = wx.BoxSizer(wx.HORIZONTAL)
        sizerBottom = wx.BoxSizer(wx.HORIZONTAL)
        sizerColumn = wx.BoxSizer(wx.VERTICAL)
        sizerColumn.Add(sizerTop, 1, wx.EXPAND)
        sizerColumn.Add(sizerBottom, 1, wx.EXPAND)

        # Indicator for the signal strength value
        self.meter_sigstr = BrainBandDialMeter(self, 'Signal strength', 0, 200, True)

        # Peak level meter thingy for the various brainwaves
        self.meter_brainwaves = BrainBandWaveMeter(self, 1, 0xffff)

        # Indicators for the Attention and Meditation values
        self.meter_attention  = BrainBandDialMeter(self, 'Attention', 0, 100, False)
        self.meter_meditation = BrainBandDialMeter(self, 'Meditation', 0, 100, False)

        # Stick the top panels in - signal strength and the brainwave meter
        sizerTop.Add(self.meter_sigstr, 1, wx.EXPAND)
        sizerTop.Add(self.meter_brainwaves, 1, wx.EXPAND)
        # Stick the bottom panels in - attention and meditation indicators
        sizerBottom.Add(self.meter_attention, 1, wx.EXPAND)
        sizerBottom.Add(self.meter_meditation, 1, wx.EXPAND)

        #self.buttons = []
        #self.buttons2 = []
        #for i in range(0, 6):
        #    self.buttons.append(wx.Button(self, -1, "Button &"+str(i)))
        #    self.buttons2.append(wx.Button(self, -1, "Button &"+str(i+6)))
        #    sizerTop.Add(self.buttons[i], 1, wx.EXPAND)
        #    sizerBottom.Add(self.buttons2[i], 1, wx.EXPAND)

        #Layout sizers
        self.SetSizer(sizerColumn)
        self.SetAutoLayout(1)
        sizerColumn.Fit(self)
        self.Show()



    def OnExit(self,e):
        self.Close(True)

    def updateMeters(self, data):
        
        self.meter_brainwaves.SetData(data.getBrainwaves(), 0, 8)
        self.meter_sigstr.SetSpeedValue(data.getSignalStrength())
        self.meter_attention.SetSpeedValue(data.getAttention())
        self.meter_meditation.SetSpeedValue(data.getMeditation())

ser = serial.Serial('/dev/cu.BrainBand-DevB', 57600, timeout=1)

app = wx.App(False)
frame = MainWindow(None, "BrainBand status")
#frame.meter_brainwaves.Start(50)

parser = BrainBandParser(ser)

thread = BrainThread(ser, frame)
thread.start()

app.MainLoop()
