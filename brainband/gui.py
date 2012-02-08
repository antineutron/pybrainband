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

import wx
import os
from math import pi,sqrt

try:
    from agw import speedmeter
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.speedmeter as SM

try:
    from agw import peakmeter
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.peakmeter as PM

class BrainBandDialMeter(SM.SpeedMeter):

    def __init__(self, parent, title, min_val, max_val, colour=True):

        # Indicator for the signal strength value
        SM.SpeedMeter.__init__(self,
                               parent,
                               agwStyle=SM.SM_DRAW_HAND |
                               SM.SM_DRAW_SECTORS |
                               SM.SM_DRAW_MIDDLE_TEXT |
                               SM.SM_DRAW_SECONDARY_TICKS
                               )

        # Set angle range for the meter, in radians - we go from 0 to pi, so a semicircle
        self.SetAngleRange(0, pi)

        # Create The Intervals That Will Divide Our SpeedMeter In Sectors        
        intervals = range(min_val, max_val+1, (max_val-min_val)/10)
        self.SetIntervals(intervals)

        # Colours for the signal strength - red, orange, yellow, green
        if(colour):
            colours = ['#DB544D', '#DB993B', '#DB993B', '#DB993B', '#C3CC72', '#C3CC72','#C3CC72','#C3CC72', '#8BC480', '#8BC480']
        else:
            colours = ['#000000'] * 10

        self.SetIntervalColours(colours)

        # Assign The Ticks: Here They Are Simply The String Equivalent Of The Intervals
        ticks = [str(interval) for interval in intervals]
        self.SetTicks(ticks)
        # Set The Ticks/Tick Markers Colour
        self.SetTicksColour(wx.WHITE)
        # We Want To Draw 5 Secondary Ticks Between The Principal Ticks
        self.SetNumberOfSecondaryTicks(5)

        # Set The Font For The Ticks Markers
        self.SetTicksFont(wx.Font(7, wx.SWISS, wx.NORMAL, wx.NORMAL))

        # Centre text, with its font and colour
        self.SetMiddleText(title)
        if(colour):
            self.SetMiddleTextColour(wx.BLACK)
        else:
            self.SetMiddleTextColour(wx.WHITE)
        self.SetMiddleTextFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD))

        # Set The Colour For The Hand Indicator
        if(colour):
            self.SetHandColour(wx.BLACK)
        else:
            self.SetHandColour(wx.RED)

        # Don't draw a bounding arc round the outside (it looks crappy)
        self.DrawExternalArc(False)

        # Set starting value
        self.SetSpeedValue(0)

class BrainBandWaveMeter(PM.PeakMeterCtrl):
    def __init__(self, parent, min_val, max_val):
        PM.PeakMeterCtrl.__init__(self, parent, -1, style=wx.SIMPLE_BORDER, agwStyle=PM.PM_VERTICAL)
        self.SetMeterBands(8, 8)
        self.SetRangeValue(min_val, min_val+((max_val-min_val)/2), max_val)
        self.SetData([10,20,30,40,50,60,70,80], 0, 8)

