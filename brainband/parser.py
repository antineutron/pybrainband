#!/usr/bin/python
 
# Copyright (c) 2011-2012 Andy Newton
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

# Parser for the Neurosky brain interface protocol (documented
# at http://wearcam.org/ece516/mindset_communications_protocol.pdf).
# Requires the python serial library to talk to the bluetooth serial port.

import serial
import array

class BrainBandParser:
    """
    BrainBand packet parser class.  Connects to a BrainBand
    via the bluetooth serial port and parses the resulting packet stream.

    """
    
    def __init__(self, serial_conn):
        """
        Constructor - requires a valid serial connection to read data from.  
        """

        # Serial connection opened to the BrainBand
        self.serial_conn = serial_conn

        # Zero out all initial data values

        # This is the raw brainwave data - presumably [related to]
        # the voltage across the sensors
        self.raw_data = 0

        # These are the various provessed brainwave values
        self.delta      = 0
        self.theta      = 0
        self.low_alpha  = 0
        self.high_alpha = 0
        self.low_beta   = 0
        self.high_beta  = 0
        self.low_gamma  = 0
        self.mid_gamma  = 0

        # These are the eSense values calculated by the Neurosky chip
        # Attention - higher means you're concentrating more - 0-100
        self.attention  = 0

        # Meditation - higher means you're more mentally relaxed - 0-100
        self.meditation = 0

        # Signal strength - the device reports a "poor signal value" 0-200,
        # where 200 is "not attached to head" and 0 is "everything's OK";
        # I simply invert this so it's a measure of signal strength,
        # 0 (bad) - 200 (good), which is what people would normally expect...
        self.signal_strength = 0


        ## Magic numbers used in packet parsing

        # Maximum packet length allowed by the spec
        self.MAX_PACKET_LEN = 169

        # Extension code magic value
        self.MAGIC_EXCODE = 0x55

        # SYNC bytes, the packet header...
        self.MAGIC_SYNC = 0xAA

        # Packet codes for single-byte values
        self.MAGIC_SIGNAL     = 0x02
        self.MAGIC_ATTENTION  = 0x04
        self.MAGIC_MEDITATION = 0x05
        self.MAGIC_BLINKSTR   = 0x16 # Not implemented

        # Packet codes for multi-byte values
        self.MAGIC_RAW        = 0x80
        self.MAGIC_EEG_DATA   = 0x83



    def readPacket(self):
        """
        Reads a single packet from the BrainBand.  Skips any extraneous shonk
        until it reads a valid packet header and validates the packet.

        See protocol spec at http://wearcam.org/ece516/mindset_communications_protocol.pdf
        """

        # This function is pretty straightforward - read one character at a time from the serial port
        # and as soon as we find a packet header, grab the relevant number of bytes and validate the checksum.
        # If it checks out, parse the packet data.  Handy things to know:
        # chr(some_integer)   => character with ASCII code some_integer
        # ord(some_character) => ASCII code of some_character
        # (chr/ord probably work with unicode too, but that's not relevant here)

        looping = True
        while(looping):

            # Wait until we hit a SYNC byte
            char = self.serial_conn.read()
            if(char != chr(self.MAGIC_SYNC)):
                continue
    
            # Read next char - make sure it's the second SYNC
            char = self.serial_conn.read()
            if(char != chr(self.MAGIC_SYNC)):
                continue

            # Now we've confirmed we have two SYNC bytes, it's vaguely
            # possible we have MORE than two - so read all of them until we run out
            while(char == chr(self.MAGIC_SYNC)):
                char = self.serial_conn.read()
    
            # The loop above should give us the length byte stored in char
            length = ord(char)

            # Longer than 169 bytes - INVALID as per spec - loop around again...
            if(length > self.MAX_PACKET_LEN):
                continue
    
            # Read the packet data and calculate simple checksum (see spec) - basically,
            # sum up all the data values, grab the lowest byte only, then complement it.
            cksumAcc = 0
            pktData = []
            for i in range(length):
                char = ord(self.serial_conn.read())
                cksumAcc += char
                pktData.append(char)
    
            # Final checksum calculation
            cksumAcc = (~cksumAcc) & 0xff
    
            # Read expected checksum
            cksum = ord(self.serial_conn.read())

            # Validate packet data
            if(cksumAcc != cksum):
                print "Invalid packet detected (checksum %x doesn't match expected %x)" % (cksumAcc, cksum)
                continue
    
            # Stop looping cos we've got a valid data packet
            looping = False
    
            # Parse packet data
            self.parsePacket(pktData)

    
    def parsePacket(self, packetRaw):
        """
        Given a valid packet payload, parse it into individual data values
        and update our internal state.
        """

        # Data structure: [excodes] [code] [data]
        # [code] determines the type of data
        # [excodes] - not currently implemented but would modify the meaning of each code

        # We'll keep popping bytes off the front of the packet data, so loop until it's all been read
        while(len(packetRaw) > 0):

            # Extended code values - the spec's a bit odd, basically there can be an
            # arbitrary number of 0x55 bytes at the start of the data value.  The number of
            # "extension codes" alters the meaning of the "real" code (nothing's actually implemented yet...)
            excodes = 0
            while(packetRaw[0] == self.MAGIC_EXCODE):
                excodes += 1
                packetRaw.pop(0)


            # Single-byte codes are between 0x00 and 0x7f, and have an implicit length of 1
            code = packetRaw.pop(0)
            if(code >= 0x00 and code <= 0x7f):
                length = 1
            # Multi-byte codes have the length as the next byte
            else:
                length = packetRaw.pop(0)
            

            # Build an array of the data values for this data row
            value = []
            while(length > 0):
                value.append(packetRaw.pop(0))
                length -= 1

            # Based on the code, set the appropriate internal state
            if(code == self.MAGIC_SIGNAL):

                # It's not actually signal strength, it's signal weakness;
                # but let's convert it to higher-value-is-better for sanity...
                self.signal_strength = 200 - value[0]
                #print "POOR_SIGNAL: %x (%d) (SSTR: %d)" % (value[0], value[0], self.signal_strength)

            elif(code == self.MAGIC_ATTENTION):
                self.attention = value[0]
                #print "ATTENTION: %x (%d)" % (value[0], value[0])

            elif(code == self.MAGIC_MEDITATION):
                self.meditation = value[0]
                #print "MEDITATION: %x (%d)" %(value[0], value[0])

            elif(code == self.MAGIC_BLINKSTR):
                self.blink_strength = value[0]
                #print "BLINK: %x (%d)" %(value[0], value[0])

            elif(code == self.MAGIC_RAW):
                # Two-byte raw brainwave data - shift/or to merge them into an int
                self.raw_data = value[0] << 8 | value[1]
                #print "WAVE: %02x%02x = %04x (%d)" % (value[0], value[1], self.raw_data, self.raw_data)

            elif(code == self.MAGIC_EEG_DATA):
                # 8 3-byte unsigned ints (hence the shifty-or-ification to munge the bytes together)
                # delta, theta, low-alpha, high-alpha,
                # low-beta, high-beta, low-gamma, mid-gamma
                self.delta      = value[0]  << 16 | value[1]  << 8 | value[2]
                self.theta      = value[3]  << 16 | value[4]  << 8 | value[5]
                self.low_alpha  = value[6]  << 16 | value[7]  << 8 | value[8]
                self.high_alpha = value[9]  << 16 | value[10] << 8 | value[11]
                self.low_beta   = value[12] << 16 | value[13] << 8 | value[14]
                self.high_beta  = value[15] << 16 | value[16] << 8 | value[17]
                self.low_gamma  = value[18] << 16 | value[19] << 8 | value[20]
                self.mid_gamma  = value[21] << 16 | value[22] << 8 | value[23]
                #print "ASIC_EEG_POWER: %d %d %d %d %d %d %d %d" % (
                #    self.delta, self.theta, self.low_alpha, self.high_alpha,
                #    self.low_beta, self.high_beta, self.low_gamma, self.mid_gamma
                #)
            #else:
            #    print "Unknown code %x" % (code)


    def getSignalStrength(self):
        return self.signal_strength
    
    def getAttention(self):
        return self.attention

    def getMeditation(self):
        return self.meditation

    def getBrainwaves(self):
        return [self.delta, self.theta, self.low_alpha, self.high_alpha, self.low_beta, self.high_beta, self.low_gamma, self.mid_gamma]

    def dump(self):
        print "Signal strength: %d Attention: %d Meditation: %d" % (self.signal_strength, self.attention, self.meditation)


# Example:
#
## Connect to the brainband serial port (this is what it shows up as on OSX)
# ser = serial.Serial('/dev/cu.BrainBand-DevB', 57600, timeout=1)
#
## Create a parser
# parser = BrainBandParser(ser)
#
## Keep reading data and printing the latest values
# while(True):
#    parser.readPacket()
#    parser.dump()
#
#ser.close()
