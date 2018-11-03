#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  headertestgtk.py
#  
#  Copyright 2018 youcef sourani <youssef.m.sourani@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
import gi
import subprocess
import os
import sys
import time
gi.require_version('Gst' , '1.0')
gi.require_version('Gtk' , '3.0')
gi.require_version('Wnck', '3.0')
from gi.repository import Gst, Gtk,Gdk,GLib,Wnck,Gio,GdkPixbuf

Gst.init(None)


MENU_XML="""
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <menu id="app-menu">
    <section>
      <item>
        <attribute name="action">app.about</attribute>
        <attribute name="label" translatable="yes">_About</attribute>
      </item>
      <item>
        <attribute name="action">app.quit</attribute>
        <attribute name="label" translatable="yes">_Quit</attribute>
        <attribute name="accel">&lt;Primary&gt;q</attribute>
    </item>
    </section>
  </menu>
</interface>
"""

css = b"""
#AreaChooser {
    background-color: rgba(255, 255, 255, 0);
    border: 1px solid red;
}
"""

class Yes_Or_No(Gtk.MessageDialog):
    def __init__(self,msg,parent):
        Gtk.MessageDialog.__init__(self,buttons = Gtk.ButtonsType.OK_CANCEL)
        self.props.message_type = Gtk.MessageType.QUESTION
        self.props.text         = msg
        self.p=parent
        if self.p != None:
            self.parent=self.p
            self.set_transient_for(self.p)
            self.set_modal(True)
            self.p.set_sensitive(False)
        else:
            self.set_position(Gtk.WindowPosition.CENTER)
            
    def check(self):
        rrun = self.run()
        if rrun == Gtk.ResponseType.OK:
            self.destroy()
            if self.p != None:
                self.p.set_sensitive(True)
            return True
        else:
            if self.p != None:
                self.p.set_sensitive(True)
            self.destroy()
            return False


class NInfo(Gtk.MessageDialog):
    def __init__(self,message,parent=None):
        Gtk.MessageDialog.__init__(self,buttons = Gtk.ButtonsType.OK)
        self.props.message_type = Gtk.MessageType.INFO
        self.props.text         = message
        self.p=parent
        if self.p != None:
            self.parent=self.p
            self.set_transient_for(self.p)
            self.set_modal(True)
            self.p.set_sensitive(False)
        else:
            self.set_position(Gtk.WindowPosition.CENTER)
        self.run() 
        if self.p != None:
            self.p.set_sensitive(True)
        self.destroy()

def gnome_shell_version():
    try:
        bus          = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        __proxy      = Gio.DBusProxy.new_sync(bus, 
                               Gio.DBusProxyFlags.NONE,
                               None,
                               'org.gnome.Shell',
                               '/org/gnome/Shell',
                               'org.freedesktop.DBus.Properties', 
                               None)

        return __proxy.call_sync('Get',GLib.Variant("(ss)",("org.gnome.Shell","ShellVersion")), Gio.DBusCallFlags.NO_AUTO_START,500,None)[0]
    except :
        return False
    return True


def is_gnome_shell():
    if gnome_shell_version():
        return True
    return False


def is_gnome_on_xorg():
    if gnome_shell_version():
        if "xorg" in GLib.environ_getenv(GLib.get_environ(),"XDG_SESSION_DESKTOP"):
            return True
        else:
            return False
    return True

def run_appinfo(location):
    try:
        Gio.AppInfo.launch_default_for_uri((location),None)
    except Exception as e:
        print(e)
    
def old_alsa_get_audio_sources():
    result = dict()
    count = 0
    p = subprocess.Popen("aplay -l",shell=True,stdout=subprocess.PIPE).communicate()[0].decode("utf-8").split("\n")
    for line in p:
        line = line.strip()
        if line.startswith("card "):
            hw ,name = line.split(":",1)
            result.setdefault(name.strip(),str(count))
            count+=1
    return result
    
def alsa_get_audio_sources(raw=False):
    result = {}
    p = subprocess.Popen("aplay -l",shell=True,stdout=subprocess.PIPE).communicate()[0].decode("utf-8").split("\n")
    for i in p:
        if i.startswith("card "):
            pp = i.split(":")
            for j in pp:
                jj = j.strip()
                if jj.startswith("card "):
                    card = jj[-1]
                elif jj[:-1].endswith("device "):
                    device = jj[-1]
                    info   = jj[:-9]
                    info   = info + pp[pp.index(j)+1]
            if not raw:
                result.setdefault("Alsa "+info,"alsasrc device=\"hw:{},{}\"".format(card,device))
            else:
                result.setdefault("Alsa "+info,"hw:{},{}".format(card,device))
    return result


def pulse_get_audio_source(raw=False):
    result = {}
    p=subprocess.Popen("pactl list | grep -A3 'Source #'",shell=True,stdout=subprocess.PIPE).communicate()[0].decode("utf-8").strip().split("\n")
    for i in p:
        ii=i.strip()
        if ii.startswith("Name:"):
            if not raw:
                result.setdefault("Pulse "+p[p.index(i)+1].split(":",1)[-1].strip(),"pulsesrc device=\"{}\"".format(ii.split(":",1)[-1].strip()))
            else:
                result.setdefault("Pulse "+p[p.index(i)+1].split(":",1)[-1].strip(),ii.split(":",1)[-1].strip())
    
    return result



def get_all_window_xid():
    result = []
    try:
        screen = Wnck.Screen.get_default()
        screen.force_update()
        wins = screen.get_windows()
        for w in wins:
            buf         = w.get_icon()
            app         = w.get_application().get_name()
            title       = w.get_name()
            id_         = w.get_xid()
            
            image       = Gtk.Image.new_from_pixbuf(buf)
            app_label   = Gtk.Label.new(app)
            title_label = Gtk.Label.new(title)
            result.append([id_,app,title,image,app_label,title_label])
    except:
        return []
    
    return result

def get_first_window_xid():
    try:
        screen = Wnck.Screen.get_default()
        screen.force_update()
        w      = screen.get_windows_stacked()[-1]
        buf         = w.get_icon()
        app         = w.get_application().get_name()
        title       = w.get_name()
        id_         = w.get_xid()
            
        image       = Gtk.Image.new_from_pixbuf(buf)
        app_label   = Gtk.Label.new(app)
        title_label = Gtk.Label.new(title)
        return [id_,app,title,image,app_label,title_label]
    except:
        return []
    return []


class MonitorInfo(object):
    def __init__(self):
        display        = Gdk.Display().get_default()
        self.monitor   = display.get_monitor(0)
        self.x         = self.monitor.get_geometry().x
        self.y         = self.monitor.get_geometry().y
        self.width     = self.monitor.get_geometry().width
        self.height    = self.monitor.get_geometry().height
        self.geometry  = self.monitor.get_geometry()
        self.info      = {"monitor":self.monitor,"x":self.x,"y":self.y,"width":self.width,"height":self.height}
        

class GstScreenCast(object):
    def __init__(self,filelocation,
                      status,
                      pipeline,
                      xid,
                      startx,
                      starty,
                      endx,
                      endy,
                      show_pointer,
                      use_damage,
                      parent,
                      iconify,
                      start_button,
                      stop_button,
                      framerate,
                      time_label,
                      selectarea,
                      open_location,
                      play):
                          
        self.filelocation  = filelocation
        self.start_button  = start_button
        self.stop_button   = stop_button
        self.time_label    = time_label
        self.pipeline      = pipeline
        self.startx        = startx
        self.starty        = starty
        self.endx          = endx
        self.endy          = endy
        self.xid           = xid
        self.show_pointer  = show_pointer
        self.use_damage    = use_damage
        self.status        = status
        self.parent        = parent
        self.iconify       = iconify
        self.framerate     = framerate
        self.selectarea    = selectarea
        self.open_location = open_location
        self.play          = play
        if self.xid != 0:
            self.use_damage = "false"
        if self.xid != 0 or  self.selectarea:
            self.pipe         = Gst.parse_launch("ximagesrc startx={} \
                                             starty={} \
                                             endx={} \
                                             endy={} \
                                             show-pointer={} \
                                             xid = {} \
                                             use-damage={} !  \
                                             {} \
                                             ! filesink \
                                             location={}".format(self.startx,
                                                                 self.starty,
                                                                 self.endx,
                                                                 self.endy,
                                                                 self.show_pointer,
                                                                 self.xid,
                                                                 self.use_damage,
                                                                 self.pipeline,
                                                                 self.filelocation[7:]))
        else:
            self.pipe         = Gst.parse_launch("ximagesrc startx={} \
                                             starty={} \
                                             endx={} \
                                             endy={} \
                                             show-pointer={} \
                                             xid = {} \
                                             use-damage={} !  \
                                             video/x-raw,framerate={}/2,width={},height={} !  \
                                             {} \
                                             ! filesink \
                                             location={}".format(self.startx,
                                                                 self.starty,
                                                                 self.endx,
                                                                 self.endy,
                                                                 self.show_pointer,
                                                                 self.xid,
                                                                 self.use_damage,
                                                                 self.framerate,
                                                                 self.endx,
                                                                 self.endy,
                                                                 self.pipeline,
                                                                 self.filelocation[7:]))
        
        bus = self.pipe.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.__on_message)

        self.is_start      = False

    def set_timeout_to_label(self,old_time):
        t = time.gmtime(time.time()-old_time)
        t = time.strftime("%H:%M:%S",t)
        self.time_label.props.label = "<span font_weight=\"bold\" foreground=\"red\">{}</span>".format(t)
        if not self.is_start:
            self.time_label.props.label = "<span font_weight=\"bold\" foreground=\"red\">""</span>"
        return self.is_start
        
    def start(self):
        self.status[0] =  self.pipe.set_state(Gst.State.PLAYING)
        if self.status[0]:
            self.start_button.set_sensitive(False)
            self.stop_button.set_sensitive(True)
            self.is_start = True
            old_time = time.time()
            GLib.timeout_add(1000, self.set_timeout_to_label,old_time)
        else:
            self.start_button.set_sensitive(True)
            self.stop_button.set_sensitive(False)
            self.is_start = False
            NInfo("Start Recorging Failed.",self.parent)
        if self.status[0] and self.parent and self.iconify:
            self.parent.iconify()
        return self.status[0]
        
    def stop(self):
        self.status[0] = self.pipe.set_state(Gst.State.NULL)
        if self.status[0]:
            self.start_button.set_sensitive(True)
            self.stop_button.set_sensitive(False)
            self.is_start = False
            if self.open_location:
                run_appinfo(os.path.dirname(self.filelocation))
            if self.play:
                run_appinfo(self.filelocation)
                
        else:
            self.start_button.set_sensitive(False)
            self.stop_button.set_sensitive(True)
            self.is_start = True
            NInfo("Stop Recording Failed",self.parent)
        return self.status[0]

    def __on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.pipe.set_state(Gst.State.NULL)
            self.is_start = False
            
        elif t == Gst.MessageType.ERROR:
            self.pipe.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print("Eror : {} {}".format(err, debug))
            NInfo("Eror : {} {}".format(err, debug),self.parent)
            self.start_button.set_sensitive(True)
            self.stop_button.set_sensitive(False)
            self.is_start = False
            return
        self.status[0] = t


class GnomeScreenCast(object):
    def __init__(self,filelocation,
                      status,
                      pipeline,
                      startx,
                      starty,
                      endx,
                      endy,
                      show_pointer,
                      framerate,
                      parent,
                      iconify,
                      start_button,
                      stop_button,
                      time_label,
                      open_location,
                      play):

        self.filelocation  = filelocation
        self.start_button  = start_button
        self.stop_button   = stop_button
        self.time_label    = time_label
        self.pipeline      = pipeline
        self.startx        = startx
        self.starty        = starty
        self.endx          = endx
        self.endy          = endy
        self.show_pointer  = show_pointer
        self.framerate     = framerate
        self.status        = status
        self.parent        = parent
        self.iconify       = iconify
        self.open_location = open_location
        self.play          = play
        self.bus           = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.__proxy       = Gio.DBusProxy.new_sync(self.bus, 
                               Gio.DBusProxyFlags.NONE,
                               None,
                               'org.gnome.Shell.Screencast',
                               '/org/gnome/Shell/Screencast',
                               'org.gnome.Shell.Screencast', 
                               None)
        
        self.is_start      = False

    def set_timeout_to_label(self,old_time):
        self.time_label.props.label = "<span font_weight=\"bold\" foreground=\"red\">{}</span>".format(int(time.time()-old_time))
        if not self.is_start:
            self.time_label.props.label = "<span font_weight=\"bold\" foreground=\"red\">""</span>"
        return self.is_start
        
        
    def start(self):
        show_pointer = True if self.show_pointer=="true" else False
        options    =  {"draw-cursor":GLib.Variant("b",show_pointer),"framerate":GLib.Variant("i",int(self.framerate)),"pipeline":GLib.Variant("s",self.pipeline)}
        parameters =  GLib.Variant("(iiiisa{sv})",(self.startx,
                      self.starty,
                      self.endx,
                      self.endy,
                      self.filelocation[7:],
                      options))

        self.status[0] =  self.__proxy.call_sync('ScreencastArea',parameters , Gio.DBusCallFlags.NO_AUTO_START,-1,None)
        if self.status[0] and self.parent and self.iconify:
            self.parent.iconify()

        if self.status[0][0]:
            self.start_button.set_sensitive(False)
            self.stop_button.set_sensitive(True)
            self.is_start = True
            old_time = time.time()
            GLib.timeout_add(1000, self.set_timeout_to_label,old_time)
        else:
            self.start_button.set_sensitive(True)
            self.stop_button.set_sensitive(False)
            self.is_start = False
            NInfo("Recored Failed.",self.parent)
        return self.status[0]
        
    def stop(self):
        self.status[0] = self.__proxy.call_sync('StopScreencast', None , Gio.DBusCallFlags.NO_AUTO_START,-1,None)
        if self.status[0][0]:
            self.start_button.set_sensitive(True)
            self.stop_button.set_sensitive(False)
            self.is_start = False
            if self.open_location:
                run_appinfo(os.path.dirname(self.filelocation))
            if self.play:
                run_appinfo(self.filelocation)
        else:
            self.start_button.set_sensitive(False)
            self.stop_button.set_sensitive(True)
            NInfo("Stop Recored Failed.",self.parent)
            self.is_start = True
        return self.status[0]
        
        





class ScreenCast(object):
    def __init__(self,filelocation,
                      pipeline="queue  ! videoconvert  ! vp8enc min_quantizer=13 max_quantizer=13 cpu-used=5 deadline=1000000 threads=2 ! mux. alsasrc !  queue ! audioconvert ! audioresample ! vorbisenc ! webmmux name=mux",
                      xid=0,
                      startx=0,
                      starty=0,
                      endx=0,
                      endy=0,
                      show_pointer="true",
                      use_damage="true",
                      framerate="30",
                      selectarea=False,
                      iconify=False,
                      parent=None,
                      force_use_window_area=False,
                      start_button=None,
                      stop_button=None,
                      time_label=None,
                      open_location=False,
                      play=False):
                          

        self.parent       = parent

        
        self.filelocation  = filelocation
        self.start_button  = start_button
        self.stop_button   = stop_button
        self.time_label    = time_label
        self.pipeline      = pipeline
        self.startx        = startx
        self.starty        = starty
        self.endx          = endx
        self.endy          = endy
        self.show_pointer  = show_pointer
        self.framerate     = framerate
        self.xid           = xid
        self.show_pointer  = show_pointer
        self.use_damage    = use_damage
        self.status        = [None]
        self.selectarea    = selectarea
        self.iconify       = iconify
        self.open_location = open_location
        self.play          = play
        self.force_use_window_area = force_use_window_area
        if self.xid != 0 and self.selectarea:
            self.selectarea = False
        

    def on_delete_areachooser(self,window,p):
        self.window.destroy()
        if self.parent:
            self.parent.show()

    def on_apply_areachooser(self,button):
        monitor      = MonitorInfo()
        width,height = self.window.get_size()
        x, y         = self.window.get_position()
        x           %= monitor.width
        y           %= monitor.height
        self.window.destroy()
        if is_gnome_on_xorg():
            self.player = GstScreenCast(self.filelocation,status=self.status,
                                        pipeline=self.pipeline,
                                        show_pointer=self.show_pointer,
                                        startx=x,starty=y,use_damage=self.use_damage,
                                        endx=width,endy=height,xid=self.xid,iconify=self.iconify,parent=self.parent,
                                        start_button=self.start_button,
                                        stop_button=self.stop_button,framerate=self.framerate,time_label=self.time_label,selectarea=self.selectarea,
                                        open_location=self.open_location,play=self.play)
        else:
            self.player = GnomeScreenCast(self.filelocation,startx=x,starty=y,
                                     endx=width,endy=height,
                                     pipeline=self.pipeline,
                                     show_pointer=self.show_pointer,
                                     framerate=self.framerate,
                                     status=self.status,iconify=self.iconify,parent=self.parent,
                                     start_button=self.start_button,
                                     stop_button=self.stop_button,time_label=self.time_label,open_location=self.open_location,play=self.play)
        if self.parent:
            self.parent.show()
        self.player.start()
                                     
    def start(self):
        if self.selectarea:
            if not is_gnome_shell() or  self.force_use_window_area:
                style_provider = Gtk.CssProvider()
                style_provider.load_from_data(css)
                Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
                self.window = Gtk.Window()
                hb=Gtk.HeaderBar()
                #hb.set_show_close_button(True)
                hb.props.title = "AreaChooser"
                
                self.window.props.title = "AreaChooser"
                self.window.props.window_position = Gtk.WindowPosition.CENTER
                self.window.props.gravity = Gdk.Gravity.SOUTH
                self.window.set_titlebar(hb)
                self.window.set_name('AreaChooser')
                self.window.connect("delete-event", self.on_delete_areachooser)
                
                box = Gtk.Box()
                box.props.orientation = Gtk.Orientation.HORIZONTAL
                Gtk.StyleContext.add_class(box.get_style_context(), "linked")
                
                button = Gtk.Button()
                button.connect("clicked",self.on_apply_areachooser)
                arrow = Gtk.Arrow()
                arrow.props.arrow_type  = Gtk.ArrowType.LEFT
                arrow.props.shadow_type = Gtk.ShadowType.NONE
                button.add(arrow)
                
                box.add(button)
                hb.pack_start(box)
                if self.parent:
                    self.parent.hide()
                self.window.show_all()
            else:
                bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
                __proxy = Gio.DBusProxy.new_sync(bus, 
                               Gio.DBusProxyFlags.NONE,
                               None,
                               'org.gnome.Shell.Screenshot',
                               '/org/gnome/Shell/Screenshot',
                               'org.gnome.Shell.Screenshot', 
                               None)
                x,y,width,height = __proxy.call_sync('SelectArea',None, Gio.DBusCallFlags.NO_AUTO_START,-1,None)
                if is_gnome_on_xorg():
                    self.player = GstScreenCast(self.filelocation,status=self.status,
                                                pipeline=self.pipeline,
                                                show_pointer=self.show_pointer,
                                                startx=x,starty=y,use_damage=self.use_damage,
                                                endx=width,endy=height,xid=self.xid,iconify=self.iconify,
                                                parent=self.parent,
                                                start_button=self.start_button,
                                                stop_button=self.stop_button,framerate=self.framerate,time_label=self.time_label,selectarea=self.selectarea,
                                                open_location=self.open_location,play=self.play)
                else:
                    self.player = GnomeScreenCast(self.filelocation,startx=x,starty=y,
                                             endx=width,endy=height,
                                             pipeline=self.pipeline,
                                             show_pointer=self.show_pointer,
                                             framerate=self.framerate,
                                             status=self.status,iconify=self.iconify,parent=self.parent,
                                             start_button=self.start_button,
                                             stop_button=self.stop_button,time_label=self.time_label,
                                             open_location=self.open_location,play=self.play)
                return self.player.start()
        
        else:
            if is_gnome_on_xorg():
                self.player = GstScreenCast(self.filelocation,status=self.status,
                                            pipeline=self.pipeline,
                                            show_pointer=self.show_pointer,
                                            startx=self.startx,starty=self.starty,use_damage=self.use_damage,
                                            endx=self.endx,endy=self.endy,xid=self.xid,iconify=self.iconify,parent=self.parent,
                                            start_button=self.start_button,
                                            stop_button=self.stop_button,framerate=self.framerate,time_label=self.time_label,selectarea=self.selectarea,
                                            open_location=self.open_location,play=self.play)
            else:
                self.player = GnomeScreenCast(self.filelocation,startx=self.startx,starty=self.starty,
                                         endx=self.endx,endy=self.endy,
                                         pipeline=self.pipeline,
                                         show_pointer=self.show_pointer,
                                         framerate=self.framerate,
                                         status=self.status,iconify=self.iconify,parent=self.parent,
                                         start_button=self.start_button,
                                         stop_button=self.stop_button,time_label=self.time_label,
                                         open_location=self.open_location,play=self.play)
            return self.player.start()

    def stop(self):
        return self.player.stop()

    def get_status(self):
        return self.__status[0]





class AppWindow(Gtk.ApplicationWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connect("delete-event",self.on_delete_event)
        self.set_border_width(10)
        self.set_size_request(500, 300)
        self.set_resizable(False)
        
        self.mainvbox             = Gtk.VBox()
        self.mainvbox.props.spacing = 30
        
        self.mainhbox_label_combo = Gtk.HBox()
        self.mainhbox_label_combo.props.spacing = 10
        
        
        self.mainvbox_label       = Gtk.VBox()
        self.mainvbox_combo       = Gtk.VBox()
        self.mainvbox_label.props.homogeneous = True
        self.mainvbox_combo.props.homogeneous = True
        
        
        self.mainvbox.pack_start(self.mainhbox_label_combo,False,False,0)
        self.mainhbox_label_combo.pack_start(self.mainvbox_label,False,False,0)
        self.mainhbox_label_combo.pack_start(self.mainvbox_combo,False,False,0)
        

        ########################################################################
        self.audio_source_combo       = Gtk.ComboBoxText()
        self.audio_source_combo_label = Gtk.Label()
        self.audio_source_combo_label.props.label = "Audio Source"
        
        all_audio_sources = pulse_get_audio_source()
        alsa_audio_source = alsa_get_audio_sources()
        all_audio_sources.update(alsa_audio_source)
        for k,v in all_audio_sources.items():
            self.audio_source_combo.append(v,k)
        self.audio_source_combo.set_active(0)

        self.mainvbox_label.pack_start(self.audio_source_combo_label,False,True,0)
        self.mainvbox_combo.pack_start(self.audio_source_combo,True,True,0)
        ##########################################################################
        
        
        ##########################################################################
        self.video_source_combo       = Gtk.ComboBoxText()
        self.video_source_combo_label = Gtk.Label()
        self.video_source_combo_label.props.label = "Video Source"
        


        self.video_source_combo.append("0","Current Monitor")
        self.video_source_combo.append("-1","Select Area")
        for i in get_all_window_xid():
            self.video_source_combo.append("{}".format(i[0]),i[1]+" "+i[2][:50])
        self.video_source_combo.set_active(0)

        self.mainvbox_label.pack_start(self.video_source_combo_label,False,True,0)
        self.mainvbox_combo.pack_start(self.video_source_combo,True,True,0)
        ##########################################################################
        
        
        self.mainhbox_label_button = Gtk.HBox()
        self.mainhbox_label_button.props.spacing = 10
        
        
        self.mainvbox_label       = Gtk.VBox()
        self.mainvbox_button      = Gtk.VBox()
        self.mainvbox_label.props.homogeneous = True
        self.mainvbox_button.props.homogeneous = True
        
        
        self.mainvbox.pack_start(self.mainhbox_label_button,False,False,0)
        self.mainhbox_label_button.pack_start(self.mainvbox_label,False,False,0)
        self.mainhbox_label_button.pack_start(self.mainvbox_button,False,False,0)
        ##########################################################################
        
        
        
        ##########################################################################
        self.frame_label = Gtk.Label()
        self.frame_label.props.label = "Framerate"
        adjustment = Gtk.Adjustment(value=30,lower=10,upper=61,page_size=1,step_increment=1, page_increment=0)
        self.frame = Gtk.SpinButton(max_width_chars=2,value=30,adjustment=adjustment)

        self.mainvbox_label.pack_start(self.frame_label,True,False,0)
        self.mainvbox_button.pack_start(self.frame,False,False,0)
        ##########################################################################
        
        
        
        
        ##########################################################################
        self.audio_label = Gtk.Label()
        self.audio_label.props.label = "Record Audio"
        self.audiocheckbutton = Gtk.CheckButton()
        self.audiocheckbutton.set_active(True)

        self.mainvbox_label.pack_start(self.audio_label,True,False,0)
        self.mainvbox_button.pack_start(self.audiocheckbutton,False,False,0)



        
        ##########################################################################
        
        

        ##########################################################################
        self.mouse_label = Gtk.Label()
        self.mouse_label.props.label = "Show Mouse"
        self.mousecheckbutton = Gtk.CheckButton()
        self.mousecheckbutton.set_active(True)
        
        self.mainvbox_label.pack_start(self.mouse_label,True,False,0)
        self.mainvbox_button.pack_start(self.mousecheckbutton,False,False,0)
        ##########################################################################
        
        
        ##########################################################################
        self.minimize_label = Gtk.Label()
        self.minimize_label.props.label = "Minimize Before Record"
        self.minimizecheckbutton = Gtk.CheckButton()
        self.minimizecheckbutton.set_active(False)
        self.mainvbox_label.pack_start(self.minimize_label,True,False,0)
        self.mainvbox_button.pack_start(self.minimizecheckbutton,False,False,0)
        #########################################################################
        
        ##########################################################################
        self.open_location_label = Gtk.Label()
        self.open_location_label.props.label = "Open Location After Stop"
        self.openlocationecheckbutton = Gtk.CheckButton()
        self.openlocationecheckbutton.set_active(True)
        self.mainvbox_label.pack_start(self.open_location_label,True,False,0)
        self.mainvbox_button.pack_start(self.openlocationecheckbutton,False,False,0)
        #########################################################################
        
        
        ##########################################################################
        self.play_label = Gtk.Label()
        self.play_label.props.label = "Play Video After Stop"
        self.playcheckbutton = Gtk.CheckButton()
        self.playcheckbutton.set_active(False)
        self.mainvbox_label.pack_start(self.play_label,True,False,0)
        self.mainvbox_button.pack_start(self.playcheckbutton,False,False,0)
        #########################################################################
        
        #########################################################################
        
        self.filevbox = Gtk.VBox()
        self.filevbox.props.spacing = 10
        self.mainvbox.pack_start(self.filevbox,False,False,0)
        self.filenameentry = Gtk.Entry()
        self.filenameentry.set_placeholder_text("Enter File Name...")
        self.filenameentry.set_max_length(20)


        self.folder = "file://"+GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_VIDEOS)
        self.choicefolder = Gtk.FileChooserButton()
        self.choicefolder.props.action = Gtk.FileChooserAction(2)
        self.choicefolder.set_uri(self.folder)
        
        self.filevbox.pack_start(self.filenameentry,False,False,0)
        self.filevbox.pack_start(self.choicefolder,False,False,0)
        ############################################################################
        
        
        
        
        ############################################################################
        
        self.time_label = Gtk.Label()
        self.time_label.props.use_markup = True


        self.mainvbox.pack_start(self.time_label,False,False,0)
        #############################################################################
        
        

        ############################################################################
        self.is_record_active = False
        self.play_image = Gtk.Image.new_from_icon_name(
                "gtk-media-play",
                Gtk.IconSize.MENU
            )
        self.pause_image = Gtk.Image.new_from_icon_name(
                "gtk-media-pause",
                Gtk.IconSize.MENU
            )
        self.stop_image = Gtk.Image.new_from_icon_name(
                "gtk-media-stop",
                Gtk.IconSize.MENU
            )
        self.start_stop_hbox = Gtk.HBox()
        self.mainvbox.pack_start(self.start_stop_hbox,False,False,0)
        self.start_button = Gtk.Button()
        self.stop_button  = Gtk.Button()
        self.start_button.set_image(self.play_image)
        self.stop_button.set_image(self.stop_image)
        self.stop_button.set_sensitive(False)
        
        self.start_stop_hbox.pack_start(self.start_button,True,True,0)
        self.start_stop_hbox.pack_start(self.stop_button,True,True,0)
        
        self.start_button.connect("clicked",self.on_start_clicked)
        self.stop_button.connect("clicked",self.on_stop_clicked)
        
        ###############################################################################
        self.add(self.mainvbox)
        self.show_all()

    def on_start_clicked(self,button):
        text = self.filenameentry.get_text()
        if  text:
            file_name = text+".webm"
        else:
            file_name = "SGvrecord"+str(int(time.time()))+".webm"
        location = self.choicefolder.get_uri()
        location = os.path.join(location,file_name)

        if os.path.exists(location[7:]):
            if not os.path.isfile(location[7:]):
                msg = "Cant Replace  \"{}\"!\nAn older unknown location type with same name already exists".format(location[7:])
                NInfo(msg,self)
                return
            msg = "Replace file \"{}\"?\nAn older file with same name already exists".format(location[7:])
            yn = Yes_Or_No(msg,self)
            if not yn.check():
                return
        monitor=MonitorInfo()
        
        if self.audiocheckbutton.get_active():
            pipe = "queue  ! videoconvert  ! vp8enc min_quantizer=13 max_quantizer=13 cpu-used=5 deadline=1000000 threads=2 ! mux. {} !  queue ! audioconvert ! audioresample ! vorbisenc ! webmmux name=mux".format(self.get_audio_source())
        else:
            pipe = "queue  ! videoconvert  ! vp8enc min_quantizer=13 max_quantizer=13 cpu-used=5 deadline=1000000 threads=2 ! queue ! webmmux "

        xid = self.get_video_source()

        if int(xid)==-1:
            selectarea = True
            xid = 0
        else:
            selectarea = False
            xid = int(xid)
            
        if self.mousecheckbutton.get_active():
            show_pointer = "true"
        else:
            show_pointer = "false"
        
        frame = str(self.frame.get_value_as_int())
        
        if self.minimizecheckbutton.get_active():
            iconify = True
        else:
            iconify = False

        if is_gnome_on_xorg():
            self.player = ScreenCast(location,
                                     pipeline=pipe,
                                     xid=xid,
                                     startx=monitor.x,
                                     starty=monitor.y,
                                     endx=monitor.width,
                                     endy=monitor.height,
                                     show_pointer=show_pointer,
                                     use_damage="true",
                                     framerate=frame,
                                     selectarea=selectarea,
                                     iconify=iconify,
                                     parent=self,
                                     force_use_window_area=False,
                                     stop_button=self.stop_button,
                                     start_button=self.start_button,
                                     time_label=self.time_label,
                                     open_location=self.openlocationecheckbutton.get_active(),
                                     play=self.playcheckbutton.get_active())
        else:
            self.player = ScreenCast(location,
                                     pipeline=pipe,
                                     xid=xid,
                                     startx=monitor.x,
                                     starty=monitor.y,
                                     endx=monitor.width,
                                     endy=monitor.height,
                                     show_pointer=show_pointer,
                                     use_damage="true",
                                     framerate=frame,
                                     selectarea=selectarea,
                                     iconify=iconify,
                                     parent=self,
                                     force_use_window_area=False,
                                     stop_button=self.stop_button,
                                     start_button=self.start_button,
                                     time_label=self.time_label,
                                     open_location=self.openlocationecheckbutton.get_active(),
                                     play=self.playcheckbutton.get_active())
                                     
        self.player.start()

        
    def on_stop_clicked(self,button):
        self.player.stop()

        
    def get_audio_source(self):
        iter_     = self.audio_source_combo.get_active_iter()
        if iter_ != None:
            return self.audio_source_combo.get_model()[iter_][1]
        return ""
        
    def get_video_source(self):
        iter_     = self.video_source_combo.get_active_iter()
        if iter_ != None:
            return self.video_source_combo.get_model()[iter_][1]
        return ""
        
    def on_delete_event(self,window,event):
        try:
            if not window.start_button.get_sensitive():
                y = Yes_Or_No("Record Is Running ,Exit?",window)
                if not y.check():
                    return True
                else:
                    self.player.stop()
        except Exception as e:
            print(e)
            pass

        
class Application(Gtk.Application):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="com.github.yucefsourani.SGVrecord",
                         flags=Gio.ApplicationFlags.FLAGS_NONE,
                         **kwargs)
        self.icon = "com.github.yucefsourani.sgvrecord.png" if os.path.isfile("com.github.yucefsourani.sgvrecord.png") else "/usr/share/pixmaps/com.github.yucefsourani.sgvrecord.png"
        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)
        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.on_about)
        self.add_action(action)
        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.on_quit)
        self.add_action(action)
        builder = Gtk.Builder.new_from_string(MENU_XML, -1)
        self.set_app_menu(builder.get_object("app-menu"))

    def do_activate(self):
        if not self.window:
            self.window = AppWindow(application=self, title="SGVrecord")

        self.window.present()
    def on_quit(self, action, param):
        try:
            if not self.window.start_button.get_sensitive():
                y = Yes_Or_No("Record Is Running ,Exit?",self.window)
                if not y.check():
                    return True
                else:
                    self.window.player.stop()
                    self.quit()
        except Exception as e:
            print(e)
            pass
        self.quit()

    def on_about(self,a,p):
        authors = ["Youssef Sourani <youssef.m.sourani@gmail.com>"]
        about = Gtk.AboutDialog(parent=self.window,transient_for=self.window, modal=True)
        about.set_program_name("SGvrecord")
        about.set_version("1.0")
        about.set_copyright("Copyright © 2018 Youssef Sourani")
        about.set_comments("Simple Tool To Record Screen")
        about.set_website("https://github.com/yucefsourani/sgvrecord")
        about.set_logo(GdkPixbuf.Pixbuf.new_from_file(self.icon))
        about.set_authors(authors)
        about.set_license_type(Gtk.License.GPL_3_0)
        translators = ("translator-credit")
        if translators != "translator-credits":
            about.set_translator_credits(translators)
        about.run()
        about.destroy()


if __name__ == "__main__":
    app = Application()
    app.run(sys.argv)



# add delay
