#!/usr/bin/env python
#
# Copyright (c) 2015 Serguei Glavatski ( verser  from cnc-club.ru )
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import hal                  # base hal class to react to hal signals
import os                   # needed to get the paths and directorys
import hal_glib             # needed to make our own hal pins
import gtk                  # base for pygtk widgets and constants
import gtk.glade
import sys                  # handle system calls
import linuxcnc             # to get our own error sytsem
import gobject              # needed to add the timer for periodic
import pygtk
import gladevcp
import pango
from linuxcnc import ini
import ConfigParser


CONFIGPATH1 = os.environ['CONFIG_DIR']


cp1 = ConfigParser.RawConfigParser
class ps_preferences(cp1):
    types = {
        bool: cp1.getboolean,
        float: cp1.getfloat,
        int: cp1.getint,
        str: cp1.get,
        repr: lambda self, section, option: eval(cp1.get(self, section, option)),
    }

    def __init__(self, path = None):
        cp1.__init__(self)
        if not path:
            path = "~/.toolch_preferences"
        self.fn = os.path.expanduser(path)
        self.read(self.fn)

    def getpref(self, option, default = False, type = bool):
        m = self.types.get(type)
        try:
            o = m(self, "DEFAULT", option)
        except Exception, detail:
            print detail
            self.set("DEFAULT", option, default)
            self.write(open(self.fn, "w"))
            if type in(bool, float, int):
                o = type(default)
            else:
                o = default
        return o

    def putpref(self, option, value, type = bool):
        self.set("DEFAULT", option, type(value))
        self.write(open(self.fn, "w"))


class ProbeScreenClass:
    
    def error_poll(self):
        error = self.e.poll()
        if error:
            kind, text = error
            if kind in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
                typus = "error"
                print typus, text
                return -1
            else:
                typus = "info"
                print typus, text
                return -1


    def get_preference_file_path(self):
        # we get the preference file, if there is none given in the INI
        # we use toolchange2.pref in the config dir
        temp = self.inifile.find("DISPLAY", "PREFERENCE_FILE_PATH")
        if not temp:
            machinename = self.inifile.find("EMC", "MACHINE")
            if not machinename:
                temp = os.path.join(CONFIGPATH1, "probe_screen.pref")
            else:
                machinename = machinename.replace(" ", "_")
                temp = os.path.join(CONFIGPATH1, "%s.pref" % machinename)
        print("****  probe_screen GETINIINFO **** \n Preference file path: %s" % temp)
        return temp

    # Spin buttons

    def on_spbtn1_search_vel_value_changed( self, gtkspinbutton, data = None ):
        self.halcomp["ps_searchvel"] = gtkspinbutton.get_value()
        self.prefs.putpref( "ps_searchvel", gtkspinbutton.get_value(), float )

    def on_spbtn1_probe_vel_value_changed( self, gtkspinbutton, data = None ):
        self.halcomp["ps_probevel"] = gtkspinbutton.get_value()
        self.prefs.putpref( "ps_probevel", gtkspinbutton.get_value(), float )

    def on_spbtn1_probe_max_value_changed( self, gtkspinbutton, data = None ):
        self.halcomp["ps_probe_max"] = gtkspinbutton.get_value()
        self.prefs.putpref( "ps_probe_max", gtkspinbutton.get_value(), float )

    def on_spbtn1_probe_latch_value_changed( self, gtkspinbutton, data = None ):
        self.halcomp["ps_probe_latch"] = gtkspinbutton.get_value()
        self.prefs.putpref( "ps_probe_latch", gtkspinbutton.get_value(), float )

    def on_spbtn1_probe_diam_value_changed( self, gtkspinbutton, data = None ):
        self.halcomp["ps_probe_diam"] = gtkspinbutton.get_value()
        self.prefs.putpref( "ps_probe_diam", gtkspinbutton.get_value(), float )

    def on_spbtn1_xy_clearance_value_changed( self, gtkspinbutton, data = None ):
        self.halcomp["ps_xy_clearance"] = gtkspinbutton.get_value()
        self.prefs.putpref( "ps_xy_clearance", gtkspinbutton.get_value(), float )

    def on_spbtn1_edge_lenght_value_changed( self, gtkspinbutton, data = None ):
        self.halcomp["ps_edge_lenght"] = gtkspinbutton.get_value()
        self.prefs.putpref( "ps_edge_lenght", gtkspinbutton.get_value(), float )

    def on_spbtn1_z_clearance_value_changed( self, gtkspinbutton, data = None ):
        self.halcomp["ps_z_clearance"] = gtkspinbutton.get_value()
        self.prefs.putpref( "ps_z_clearance", gtkspinbutton.get_value(), float )

    def gcode(self,s, data = None): 
        for l in s.split("\n"):
            self.command.mdi( l )
            self.command.wait_complete()
            if self.error_poll() == -1:
                return -1
        return 0

    def ocode(self,s, data = None):	
        self.command.mdi(s)
        self.stat.poll()
        while self.stat.exec_state == 7 or self.stat.exec_state == 3 :
            if self.error_poll() == -1:
                return -1
            self.command.wait_complete()
            self.stat.poll()
        self.command.wait_complete()
        if self.error_poll() == -1:
            return -1
        return 0

    def z_clearance_down(self, data = None):
        # move Z - z_clearance
        s="""G91
        G0 Z-%f
        G90""" % (self.spbtn1_z_clearance.get_value() )        
        if self.gcode(s) == -1:
            return -1
        return 0

    def z_clearance_up(self, data = None):
        # move Z + z_clearance
        s="""G91
        G0 Z%f
        G90""" % (self.spbtn1_z_clearance.get_value() )        
        if self.gcode(s) == -1:
            return -1
        return 0

    def lenght_x(self, data = None):
        if self.lb_probe_xm.get_text() == "" or self.lb_probe_xp.get_text() == "" :
            return
        xm = float(self.lb_probe_xm.get_text())
        xp = float(self.lb_probe_xp.get_text())
        if xm < xp :
            self.lb_probe_lx.set_text("%.4f" % (xp-xm))
        else:
            self.lb_probe_lx.set_text("%.4f" % (xm-xp))

    def lenght_y(self, data = None):
        if self.lb_probe_ym.get_text() == "" or self.lb_probe_yp.get_text() == "" :
            return
        ym = float(self.lb_probe_ym.get_text())
        yp = float(self.lb_probe_yp.get_text())
        if ym < yp :
            self.lb_probe_ly.set_text("%.4f" % (yp-ym))
        else:
            self.lb_probe_ly.set_text("%.4f" % (ym-yp))

    # Simulate
#    def on_simulate_pressed(self, data = None):
#        self.halcomp["ps_simulate"] = 0
#    def on_simulate_released(self, data = None):
#        self.halcomp["ps_simulate"] = 1

       
    # --------------  Command buttons -----------------
    #               Measurement outside
    # -------------------------------------------------
    # Down
    def on_down_released(self, data = None):
        self.command.mode( linuxcnc.MODE_MDI )
        self.command.wait_complete()
        # Start down.ngc
        if self.ocode ("O<down> call") == -1:
            return
        a=self.stat.probed_position
        self.lb_probe_z.set_text( "%.4f" % float(a[2]) )

    # X+
    def on_xp_released(self, data = None):
        self.command.mode( linuxcnc.MODE_MDI )
        self.command.wait_complete()
         # move X - xy_clearance
        s="""G91
        G0 X-%f
        G90""" % (self.spbtn1_xy_clearance.get_value() )        
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
       # Start xplus.ngc
        if self.ocode ("O<xplus> call") == -1:
            return
        a=self.stat.probed_position
        res=float(a[0])+0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_xp.set_text( "%.4f" % res )
        self.lenght_x()
        # move Z to start point up
        if self.z_clearance_up() == -1:
            return
        # move to finded  point
        self.command.mdi( "G0 X%f" % res)
        self.command.wait_complete()

    # Y+
    def on_yp_released(self, data = None):
        self.command.mode( linuxcnc.MODE_MDI )
        self.command.wait_complete()
         # move Y - xy_clearance
        s="""G91
        G0 Y-%f
        G90""" % (self.spbtn1_xy_clearance.get_value() )        
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start yplus.ngc
        if self.ocode ("O<yplus> call") == -1:
            return
        a=self.stat.probed_position
        res=float(a[1])+0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_yp.set_text( "%.4f" % res )
        self.lenght_y()
        # move Z to start point up
        if self.z_clearance_up() == -1:
            return
        # move to finded  point
        self.command.mdi( "G0 Y%f" % res)
        self.command.wait_complete()

    # X-
    def on_xm_released(self, data = None):
        self.command.mode( linuxcnc.MODE_MDI )
        self.command.wait_complete()
         # move X + xy_clearance
        s="""G91
        G0 X%f
        G90""" % (self.spbtn1_xy_clearance.get_value() )        
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start xminus.ngc
        if self.ocode ("O<xminus> call") == -1:
            return
        a=self.stat.probed_position
        res=float(a[0])-0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_xm.set_text( "%.4f" % res )
        self.lenght_x()
        # move Z to start point up
        if self.z_clearance_up() == -1:
            return
        # move to finded  point
        self.command.mdi( "G0 X%f" % res)
        self.command.wait_complete()

    # Y-
    def on_ym_released(self, data = None):
        self.command.mode( linuxcnc.MODE_MDI )
        self.command.wait_complete()
         # move Y + xy_clearance
        s="""G91
        G0 Y%f
        G90""" % (self.spbtn1_xy_clearance.get_value() )        
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start yminus.ngc
        if self.ocode ("O<yminus> call") == -1:
            return
        a=self.stat.probed_position
        res=float(a[1])-0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_ym.set_text( "%.4f" % res )
        self.lenght_y()
        # move Z to start point up
        if self.z_clearance_up() == -1:
            return
        # move to finded  point
        self.command.mdi( "G0 Y%f" % res)
        self.command.wait_complete()


    # Corners
    # Move Probe manual under corner 2-3 mm
    # X+Y+ 
    def on_xpyp_released(self, data = None):
        self.command.mode( linuxcnc.MODE_MDI )
        self.command.wait_complete()
        # move X - xy_clearance Y + edge_lenght
        s="""G91
        G0 X-%f Y%f
        G90""" % (self.spbtn1_xy_clearance.get_value(), self.spbtn1_edge_lenght.get_value() )        
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start xplus.ngc
        if self.ocode ("O<xplus> call") == -1:
            return
        # show X result
        a=self.stat.probed_position
        xres=float(a[0])+0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_xp.set_text( "%.4f" % xres )
        self.lenght_x()
        # move Z to start point up
        if self.z_clearance_up() == -1:
            return

        # move X + edge_lenght +xy_clearance,  Y - edge_lenght - xy_clearance
        a=self.spbtn1_edge_lenght.get_value()+self.spbtn1_xy_clearance.get_value()
        s="""G91
        X%f Y-%f
        G90""" % (a,a)        
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start yplus.ngc
        if self.ocode ("O<yplus> call") == -1:
            return
        # show Y result
        a=self.stat.probed_position
        yres=float(a[1])+0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_yp.set_text( "%.4f" % yres )
        self.lenght_y()
        # move Z to start point up
        if self.z_clearance_up() == -1:
            return
        # move to finded  point
        self.command.mdi( "G0 X%f Y%f" % (xres,yres))
        self.command.wait_complete()

    # X+Y-
    def on_xpym_released(self, data = None):
        self.command.mode( linuxcnc.MODE_MDI )
        self.command.wait_complete()
        # move X - xy_clearance Y + edge_lenght
        s="""G91
        G0 X-%f Y-%f
        G90""" % (self.spbtn1_xy_clearance.get_value(),self.spbtn1_edge_lenght.get_value() )        
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start xplus.ngc
        if self.ocode ("O<xplus> call") == -1:
            return
        # show X result
        a=self.stat.probed_position
        xres=float(a[0])+0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_xp.set_text( "%.4f" % xres )
        self.lenght_x()
        # move Z to start point up
        if self.z_clearance_up() == -1:
            return

        # move X + edge_lenght +xy_clearance,  Y + edge_lenght + xy_clearance
        a=self.spbtn1_edge_lenght.get_value()+self.spbtn1_xy_clearance.get_value()
        s="""G91
        X%f Y%f
        G90""" % (a,a)        
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start yminus.ngc
        if self.ocode ("O<yminus> call") == -1:
            return
        # show Y result
        a=self.stat.probed_position
        yres=float(a[1])-0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_ym.set_text( "%.4f" % yres )
        self.lenght_y()
        # move Z to start point up
        if self.z_clearance_up() == -1:
            return
        # move to finded  point
        self.command.mdi( "G0 X%f Y%f" % (xres,yres))
        self.command.wait_complete()

    # X-Y+
    def on_xmyp_released(self, data = None):
        self.command.mode( linuxcnc.MODE_MDI )
        self.command.wait_complete()
        # move X + xy_clearance Y + edge_lenght
        s="""G91
        G0 X%f Y%f
        G90""" % (self.spbtn1_xy_clearance.get_value(),self.spbtn1_edge_lenght.get_value() )        
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start xminus.ngc
        if self.ocode ("O<xminus> call") == -1:
            return
        # show X result
        a=self.stat.probed_position
        xres=float(a[0])-0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_xm.set_text( "%.4f" % xres )
        self.lenght_x()
        # move Z to start point up
        if self.z_clearance_up() == -1:
            return

        # move X - edge_lenght - xy_clearance,  Y - edge_lenght - xy_clearance
        a=self.spbtn1_edge_lenght.get_value()+self.spbtn1_xy_clearance.get_value()
        s="""G91
        X-%f Y-%f
        G90""" % (a,a)        
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start yplus.ngc
        if self.ocode ("O<yplus> call") == -1:
            return
        # show Y result
        a=self.stat.probed_position
        yres=float(a[1])+0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_yp.set_text( "%.4f" % yres )
        self.lenght_y()
        # move Z to start point up
        if self.z_clearance_up() == -1:
            return
        # move to finded  point
        self.command.mdi( "G0 X%f Y%f" % (xres,yres))
        self.command.wait_complete()

    # X-Y-
    def on_xmym_released(self, data = None):
        self.command.mode( linuxcnc.MODE_MDI )
        self.command.wait_complete()
        # move X + xy_clearance Y - edge_lenght
        s="""G91
        G0 X%f Y-%f
        G90""" % (self.spbtn1_xy_clearance.get_value(), self.spbtn1_edge_lenght.get_value() )        
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start xminus.ngc
        if self.ocode ("O<xminus> call") == -1:
            return
        # show X result
        a=self.stat.probed_position
        xres=float(a[0])-0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_xm.set_text( "%.4f" % xres )
        self.lenght_x()
        # move Z to start point up
        if self.z_clearance_up() == -1:
            return

        # move X - edge_lenght - xy_clearance,  Y + edge_lenght + xy_clearance
        a=self.spbtn1_edge_lenght.get_value()+self.spbtn1_xy_clearance.get_value()
        s="""G91
        X-%f Y%f
        G90""" % (a,a)        
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start yminus.ngc
        if self.ocode ("O<yminus> call") == -1:
            return
        # show Y result
        a=self.stat.probed_position
        yres=float(a[1])-0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_ym.set_text( "%.4f" % yres )
        self.lenght_y()
        # move Z to start point up
        if self.z_clearance_up() == -1:
            return
        # move to finded  point
        self.command.mdi( "G0 X%f Y%f" % (xres,yres))
        self.command.wait_complete()

    # Center X+ X- Y+ Y-
    def on_xy_center_released(self, data = None):
        self.command.mode( linuxcnc.MODE_MDI )
        self.command.wait_complete()
        # move X - edge_lenght- xy_clearance
        s="""G91
        X-%f
        G90""" % (self.spbtn1_edge_lenght.get_value() + self.spbtn1_xy_clearance.get_value() )        
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start xplus.ngc
        if self.ocode ("O<xplus> call") == -1:
            return
        # show X result
        a=self.stat.probed_position
        xres=float(a[0])+0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_xp.set_text( "%.4f" % xres )
        self.lenght_x()
        # move Z to start point up
        if self.z_clearance_up() == -1:
            return

        # move X + 2 edge_lenght + 2 xy_clearance
        aa=2*(self.spbtn1_edge_lenght.get_value()+self.spbtn1_xy_clearance.get_value())
        s="""G91
        X%f
        G90""" % (aa)        
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start xminus.ngc
        if self.ocode ("O<xminus> call") == -1:
            return
        # show X result
        a=self.stat.probed_position
        xres1=float(a[0])-0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_xm.set_text( "%.4f" % xres1 )
        self.lenght_x()
        cxres=0.5*(xres+xres1)
        self.lb_probe_xc.set_text( "%.4f" % cxres )
        self.stat.poll()
        back_x=self.stat.position[0]-cxres
        # move Z to start point up
        if self.z_clearance_up() == -1:
            return

        # move Y - edge_lenght- xy_clearance  X - edge_lenght - xy_clearance
        a=self.spbtn1_edge_lenght.get_value()+self.spbtn1_xy_clearance.get_value()
        s="""G91
        X-%f Y-%f
        G90""" % (a,a)        
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start yplus.ngc
        if self.ocode ("O<yplus> call") == -1:
            return
        # show Y result
        a=self.stat.probed_position
        yres=float(a[1])+0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_yp.set_text( "%.4f" % yres )
        self.lenght_y()
        # move Z to start point up
        if self.z_clearance_up() == -1:
            return

        # move Y + 2 edge_lenght + 2 xy_clearance
        aa=2*(self.spbtn1_edge_lenght.get_value()+self.spbtn1_xy_clearance.get_value())
        s="""G91
        Y%f
        G90""" % (aa)        
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start xminus.ngc
        if self.ocode ("O<yminus> call") == -1:
            return
        # show Y result
        a=self.stat.probed_position
        yres1=float(a[1])-0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_ym.set_text( "%.4f" % yres1 )
        self.lenght_y()
        # find, show and move to finded  point
        cyres=0.5*(yres+yres1)
        self.lb_probe_yc.set_text( "%.4f" % cyres )
        diam=0.5*((xres1-xres)+(yres1-yres))
        self.lb_probe_d.set_text( "%.4f" % diam )
        # move Z to start point up
        if self.z_clearance_up() == -1:
            return
        # move to finded  point
        self.command.mdi( "G0 X%f Y%f" % (cxres,cyres))
        self.command.wait_complete()

    # --------------  Command buttons -----------------
    #               Measurement inside
    # -------------------------------------------------

    # Corners
    # Move Probe manual under corner 2-3 mm
    # X+Y+ 
    def on_xpyp1_released(self, data = None):
        self.command.mode( linuxcnc.MODE_MDI )
        self.command.wait_complete()
        # move Y - edge_lenght X - xy_clearance
        s="""G91
        G0 X-%f Y-%f
        G90""" % (self.spbtn1_xy_clearance.get_value(),self.spbtn1_edge_lenght.get_value() )        
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start xplus.ngc
        if self.ocode ("O<xplus> call") == -1:
            return
        # show X result
        a=self.stat.probed_position
        xres=float(a[0])+0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_xm.set_text( "%.4f" % xres )
        self.lenght_x()

        # move X - edge_lenght Y - xy_clearance
        tmpxy=self.spbtn1_edge_lenght.get_value()-self.spbtn1_xy_clearance.get_value()
        s="""G91
        X-%f Y%f
        G90""" % (tmpxy,tmpxy)        
        if self.gcode(s) == -1:
            return
        # Start yplus.ngc
        if self.ocode ("O<yplus> call") == -1:
            return
        # show Y result
        a=self.stat.probed_position
        yres=float(a[1])+0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_yp.set_text( "%.4f" % yres )
        self.lenght_y()
        # move Z to start point
        if self.z_clearance_up() == -1:
            return
        # move to finded  point
        self.command.mdi( "G0 X%f Y%f" % (xres,yres))
        self.command.wait_complete()

    # X+Y-
    def on_xpym1_released(self, data = None):
        self.command.mode( linuxcnc.MODE_MDI )
        self.command.wait_complete()
        # move Y + edge_lenght X - xy_clearance
        s="""G91
        G0 X-%f Y%f
        G90""" % (self.spbtn1_xy_clearance.get_value(),self.spbtn1_edge_lenght.get_value() )        
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start xplus.ngc
        if self.ocode ("O<xplus> call") == -1:
            return
        # show X result
        a=self.stat.probed_position
        xres=float(a[0])+0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_xm.set_text( "%.4f" % xres )
        self.lenght_x()

        # move X - edge_lenght Y + xy_clearance
        tmpxy=self.spbtn1_edge_lenght.get_value()-self.spbtn1_xy_clearance.get_value()
        s="""G91
        X-%f Y-%f
        G90""" % (tmpxy,tmpxy)        
        if self.gcode(s) == -1:
            return
        # Start yminus.ngc
        if self.ocode ("O<yminus> call") == -1:
            return
        # show Y result
        a=self.stat.probed_position
        yres=float(a[1])-0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_yp.set_text( "%.4f" % yres )
        self.lenght_y()
        # move Z to start point
        if self.z_clearance_up() == -1:
            return
        # move to finded  point
        self.command.mdi( "G0 X%f Y%f" % (xres,yres))
        self.command.wait_complete()

    # X-Y+
    def on_xmyp1_released(self, data = None):
        self.command.mode( linuxcnc.MODE_MDI )
        self.command.wait_complete()
        # move Y - edge_lenght X + xy_clearance
        s="""G91
        G0 X%f Y-%f
        G90""" % (self.spbtn1_xy_clearance.get_value(),self.spbtn1_edge_lenght.get_value() )        
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start xminus.ngc
        if self.ocode ("O<xminus> call") == -1:
            return
        # show X result
        a=self.stat.probed_position
        xres=float(a[0])-0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_xm.set_text( "%.4f" % xres )
        self.lenght_x()

        # move X + edge_lenght Y - xy_clearance
        tmpxy=self.spbtn1_edge_lenght.get_value()-self.spbtn1_xy_clearance.get_value()
        s="""G91
        X%f Y%f
        G90""" % (tmpxy,tmpxy)        
        if self.gcode(s) == -1:
            return
        # Start yplus.ngc
        if self.ocode ("O<yplus> call") == -1:
            return

        # show Y result
        a=self.stat.probed_position
        yres=float(a[1])+0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_yp.set_text( "%.4f" % yres )
        self.lenght_y()
        # move Z to start point
        if self.z_clearance_up() == -1:
            return
        # move to finded  point
        self.command.mdi( "G0 X%f Y%f" % (xres,yres))
        self.command.wait_complete()

    # X-Y-
    def on_xmym1_released(self, data = None):
        self.command.mode( linuxcnc.MODE_MDI )
        self.command.wait_complete()
        # move Y + edge_lenght X + xy_clearance
        s="""G91
        G0 X%f Y%f
        G90""" % (self.spbtn1_xy_clearance.get_value(),self.spbtn1_edge_lenght.get_value() )        
        if self.gcode(s) == -1:
            return
        if self.z_clearance_down() == -1:
            return
        # Start xminus.ngc
        if self.ocode ("O<xminus> call") == -1:
            return
        # show X result
        a=self.stat.probed_position
        xres=float(a[0])-0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_xm.set_text( "%.4f" % xres )
        self.lenght_x()

        # move X + edge_lenght Y - xy_clearance
        tmpxy=self.spbtn1_edge_lenght.get_value()-self.spbtn1_xy_clearance.get_value()
        s="""G91
        X%f Y-%f
        G90""" % (tmpxy,tmpxy)        
        if self.gcode(s) == -1:
            return
        # Start yminus.ngc
        if self.ocode ("O<yminus> call") == -1:
            return
        # show Y result
        a=self.stat.probed_position
        yres=float(a[1])-0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_yp.set_text( "%.4f" % yres )
        self.lenght_y()
        # move Z to start point
        if self.z_clearance_up() == -1:
            return
        # move to finded  point
        self.command.mdi( "G0 X%f Y%f" % (xres,yres))
        self.command.wait_complete()

    # Hole Xin- Xin+ Yin- Yin+
    def on_xy_hole_released(self, data = None):
        self.command.mode( linuxcnc.MODE_MDI )
        self.command.wait_complete()
        if self.z_clearance_down() == -1:
            return
        # move X - edge_lenght Y + xy_clearance
        tmpx=self.spbtn1_edge_lenght.get_value()-self.spbtn1_xy_clearance.get_value()
        s="""G91
        X-%f
        G90""" % (tmpx)        
        if self.gcode(s) == -1:
            return
        # Start xminus.ngc
        if self.ocode ("O<xminus> call") == -1:
            return
        # show X result
        a=self.stat.probed_position
        xres=float(a[0])-0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_xm.set_text( "%.4f" % xres )
        self.lenght_x()

        # move X +2 edge_lenght - 2 xy_clearance
        tmpx=2*(self.spbtn1_edge_lenght.get_value()-self.spbtn1_xy_clearance.get_value())
        s="""G91
        X%f
        G90""" % (tmpx)        
        if self.gcode(s) == -1:
            return
        # Start xplus.ngc
        if self.ocode ("O<xplus> call") == -1:
            return
        # show X result
        a=self.stat.probed_position
        xres1=float(a[0])+0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_xp.set_text( "%.4f" % xres1 )
        self.lenght_x()
        cxres=0.5*(xres+xres1)
        self.lb_probe_xc.set_text( "%.4f" % cxres )

        # move X to new center
        s="""G0 X%f""" % (cxres)        
        if self.gcode(s) == -1:
            return

        # move Y - edge_lenght + xy_clearance
        tmpy=self.spbtn1_edge_lenght.get_value()-self.spbtn1_xy_clearance.get_value()
        s="""G91
        G0 Y-%f
        G90""" % (tmpy)        
        if self.gcode(s) == -1:
            return
        # Start yminus.ngc
        if self.ocode ("O<yminus> call") == -1:
            return
        # show Y result
        a=self.stat.probed_position
        yres=float(a[1])-0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_ym.set_text( "%.4f" % yres )
        self.lenght_y()

        # move Y +2 edge_lenght - 2 xy_clearance
        tmpy=2*(self.spbtn1_edge_lenght.get_value()-self.spbtn1_xy_clearance.get_value())
        s="""G91
        G0 Y%f
        G90""" % (tmpy)        
        if self.gcode(s) == -1:
            return
        # Start yplus.ngc
        if self.ocode ("O<yplus> call") == -1:
            return
        # show Y result
        a=self.stat.probed_position
        yres1=float(a[1])+0.5*self.spbtn1_probe_diam.get_value()
        self.lb_probe_yp.set_text( "%.4f" % yres1 )
        self.lenght_y()
        # find, show and move to finded  point
        cyres=0.5*(yres+yres1)
        self.lb_probe_yc.set_text( "%.4f" % cyres )
        diam=0.5*((xres1-xres)+(yres1-yres))
        self.lb_probe_d.set_text( "%.4f" % diam )
        # move to center
        self.command.mdi( "G0 Y%f" % cyres)
        self.command.wait_complete()
        # move Z to start point
        self.z_clearance_up()


    def __init__(self, halcomp,builder,useropts):
        inipath = os.environ["INI_FILE_NAME"]
        self.inifile = ini(inipath)
        if not self.inifile:
            print("**** probe_screen GETINIINFO **** \n Error, no INI File given !!")
            sys.exit()
        self.command = linuxcnc.command()
        self.stat = linuxcnc.stat()
        self.builder = builder
        self.prefs = ps_preferences( self.get_preference_file_path() )
        self.e = linuxcnc.error_channel()

        self.xpym = self.builder.get_object("xpym")
        self.ym = self.builder.get_object("ym")
        self.xmym = self.builder.get_object("xmym")
        self.xp = self.builder.get_object("xp")
        self.center = self.builder.get_object("center")
        self.xm = self.builder.get_object("xm")
        self.xpyp = self.builder.get_object("xpyp")
        self.yp = self.builder.get_object("yp")
        self.xmyp = self.builder.get_object("xmyp")
        self.down = self.builder.get_object("down")
        self.hole = self.builder.get_object("hole")
        self.angle = self.builder.get_object("angle")

        self.spbtn1_search_vel = self.builder.get_object("spbtn1_search_vel")
        self.spbtn1_probe_vel = self.builder.get_object("spbtn1_probe_vel")
        self.spbtn1_z_clearance = self.builder.get_object("spbtn1_z_clearance")
        self.spbtn1_probe_max = self.builder.get_object("spbtn1_probe_max")
        self.spbtn1_probe_latch = self.builder.get_object("spbtn1_probe_latch")
        self.spbtn1_probe_diam = self.builder.get_object("spbtn1_probe_diam")
        self.spbtn1_xy_clearance = self.builder.get_object("spbtn1_xy_clearance")
        self.spbtn1_edge_lenght = self.builder.get_object("spbtn1_edge_lenght")

        self.lb_probe_xp = self.builder.get_object("lb_probe_xp")
        self.lb_probe_yp = self.builder.get_object("lb_probe_yp")
        self.lb_probe_xm = self.builder.get_object("lb_probe_xm")
        self.lb_probe_ym = self.builder.get_object("lb_probe_ym")
        self.lb_probe_lx = self.builder.get_object("lb_probe_lx")
        self.lb_probe_ly = self.builder.get_object("lb_probe_ly")
        self.lb_probe_z = self.builder.get_object("lb_probe_z")
        self.lb_probe_d = self.builder.get_object("lb_probe_d")
        self.lb_probe_xc = self.builder.get_object("lb_probe_xc")
        self.lb_probe_yc = self.builder.get_object("lb_probe_yc")
        self.lb_probe_a = self.builder.get_object("lb_probe_a")


        self.halcomp = hal.component("probe")
        self.halcomp.newpin( "ps_searchvel", hal.HAL_FLOAT, hal.HAL_OUT )
        self.halcomp.newpin( "ps_probevel", hal.HAL_FLOAT, hal.HAL_OUT )
        self.halcomp.newpin( "ps_z_clearance", hal.HAL_FLOAT, hal.HAL_OUT )
        self.halcomp.newpin( "ps_probe_max", hal.HAL_FLOAT, hal.HAL_OUT )
        self.halcomp.newpin( "ps_probe_latch", hal.HAL_FLOAT, hal.HAL_OUT )
        self.halcomp.newpin( "ps_probe_diam", hal.HAL_FLOAT, hal.HAL_OUT )
        self.halcomp.newpin( "ps_xy_clearance", hal.HAL_FLOAT, hal.HAL_OUT )
        self.halcomp.newpin( "ps_edge_lenght", hal.HAL_FLOAT, hal.HAL_OUT )
#        self.halcomp.newpin( "ps_simulate", hal.HAL_BIT, hal.HAL_OUT )
        self.spbtn1_search_vel.set_value( self.prefs.getpref( "ps_searchvel", 75.0, float ) )
        self.spbtn1_probe_vel.set_value( self.prefs.getpref( "ps_probevel", 10.0, float ) )
        self.spbtn1_z_clearance.set_value( self.prefs.getpref( "ps_z_clearance", 100.0, float ) )
        self.spbtn1_probe_max.set_value( self.prefs.getpref( "ps_probe_max", 1.0, float ) )
        self.spbtn1_probe_latch.set_value( self.prefs.getpref( "ps_probe_latch", 0.5, float ) )
        self.spbtn1_probe_diam.set_value( self.prefs.getpref( "ps_probe_diam", 2.0, float ) )
        self.spbtn1_xy_clearance.set_value( self.prefs.getpref( "ps_xy_clearance", 5.0, float ) )
        self.spbtn1_edge_lenght.set_value( self.prefs.getpref( "ps_edge_lenght", 5.0, float ) )

        self.halcomp["ps_searchvel"] = self.spbtn1_search_vel.get_value()
        self.halcomp["ps_probevel"] = self.spbtn1_probe_vel.get_value()
        self.halcomp["ps_z_clearance"] = self.spbtn1_z_clearance.get_value()
        self.halcomp["ps_probe_max"] = self.spbtn1_probe_max.get_value()
        self.halcomp["ps_probe_latch"] = self.spbtn1_probe_latch.get_value()
        self.halcomp["ps_probe_diam"] = self.spbtn1_probe_diam.get_value()
        self.halcomp["ps_xy_clearance"] = self.spbtn1_xy_clearance.get_value()
        self.halcomp["ps_edge_lenght"] = self.spbtn1_edge_lenght.get_value()
#        self.halcomp["ps_simulate"] = 1



def get_handlers(halcomp,builder,useropts):
    return [ProbeScreenClass(halcomp,builder,useropts)]