#!/usr/bin/python

# Copyright (c) 2011-2017 Paul Kulyk, Paul Olszynski
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pygtk
pygtk.require( "2.0" )
import gtk
import sys
import gobject
import os
import subprocess
import pickle
import glob
from omxplayer.player import OMXPlayer
from pathlib import Path
import serial
import logging

class Main:

  # Gobal Variable to store RFID reader strings and bools
  dataString =""
  addRfidTag = False


  #Set debug logging parameters level = logging.DEBUG/ERROR/WARNING
  logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

 
  #Define serialport and parameters - aotumate later or add to setings
  try:
          ultrasoundProbe = serial.Serial(
          port = '/dev/ttyUSB0',
          baudrate = 115200,
          parity=serial.PARITY_NONE,
          stopbits = serial.STOPBITS_ONE,
          bytesize = serial.EIGHTBITS)
  except Exception as e:
    logging.debug(e)
  #Add send command to device
  # To do

  # After the combo boxes have been initialized we set them to have the same selected value
  # as during the last run
  def load_settings(self, filename):
    try:
      pickle_file = open(filename,'rb')
      list_import = pickle.load(pickle_file)
      self.list_store1.clear()
      for i in  range(len(list_import)):
        logging.debug("item " + str(list_import[i]))
        self.list_store1.append(list_import[i])
      pickle_file.close()
    except Exception as e:
      logging.debug(e)      

  # Pickle the settings data for use in the next run
  def save_settings( self, filename ):
    pickle_file = open(filename,'wb')
    list_iter = self.list_store1.get_iter_root()
    list_dump = []
    while(list_iter):
      tup = self.list_store1.get(list_iter,0,1,2)
      list_dump.append(list(tup))
      list_iter = self.list_store1.iter_next(list_iter)
    pickle.dump(list_dump,pickle_file)
    pickle_file.close()

  def gtk_main_quit( self, window ):
    self.save_settings(sys.path[0] + "/settings.p")
    gtk.main_quit()

  def cb_quit(self, window, event):
    self.save_settings(sys.path[0] + "/settings.p")
    gtk.main_quit()

  def cb_about_press( self, window ):
    response = self.about_dialog.run()
    self.about_dialog.hide()
    return response != 1

  def cb_settings_press( self, window ):
    self.set_add_rfid_tag_active(True)
    response = self.settings_dialog.run()
    self.settings_dialog.hide()
    if response == gtk.RESPONSE_DELETE_EVENT:
      self.set_add_rfid_tag_active(False)
      logging.debug("close event on settings press")
    return response != 1

  def cb_add_scan_press( self, window ):
    response        = self.add_scan_dialog.run()
    self.add_scan_dialog.hide()
    return response != 1
  
  def settings_cancel_clicked(self, window ):
    self.set_add_rfid_tag_active(False)
    logging.debug("Set tag false on settings exit")

  def cb_add_scan_apply_clicked( self, window ):
    new_name          = self.name_entry.get_text()
    new_rfid              = self.rfid_entry.get_text()
    new_filename     = self.filechooser.get_filename()
    self.list_store1.append([new_name, new_rfid, new_filename])
    return True

  # Callback to run when load settings button is pressed
  # Will open a window, prompt for files and update the filename variable
  def cb_load_settings_press(self, window):
    response        = self.load_settings_filechooserdialog.run()
    self.load_settings_filechooserdialog.hide()
    if response == 1:
      self.load_settings(self.load_settings_filechooserdialog.get_filename())
    return response != 1

  # Callback to run when save settings button is pressed
  # Will open a window, prompt for files and update the filename variable
  def cb_save_settings_press(self, window):
    response        = self.save_settings_filechooserdialog.run()
    self.save_settings_filechooserdialog.hide()
    if response == 1:
      self.save_settings(self.save_settings_filechooserdialog.get_filename())
    return response != 1

  # Opting to add a whole directory full of videos at once.
  def cb_quick_add_press( self, window ):
    response        = self.quick_add_dialog.run()
    self.quick_add_dialog.hide()
    return response != 1

  def cb_quick_add_ok_press( self, window ):
    # Get a list of all files in the directory
    quick_add_dir   = self.filechooser_quick.get_filename()
    quick_add_files = os.listdir(quick_add_dir)
    # For each of the files in the directory we will try to add a scan
    for filename in quick_add_files:
      new_filename    = quick_add_dir + '/' + filename
      new_name        = filename
      self.quick_add_cur_filename.set_text(filename)
      # Need to grab the focus back into the text ectry box so every scan will end by prompting fo rthe next scan
      self.rfid_quick_entry.grab_focus()
      response = self.quick_add_item.run()
      # If OK was clicked (or the scan triggered the default action)
      if response == 1:
        new_rfid        = self.rfid_quick_entry.get_text()
        self.list_store1.append([new_name, new_rfid, new_filename])
      # The button was clicked, the default action is then to skip this file and read the next one
      elif response == 2:
        break
      # Blank the text entry box and get ready for new text
      self.rfid_quick_entry.set_text('')
    # The scan is done so hide the directory
    self.quick_add_item.hide()
    return True

  def cb_remove_scan_press( self, button ):
    # Obtain selection
    sel = self.tree.get_selection()

    # If nothing is selected, return.
    if sel.count_selected_rows == 0:
      return

    # Get selected path
    (model, rows) = sel.get_selected_rows()
    for row in reversed(rows):
      iter1 = model.get_iter( row )
      model.remove(iter1)
    return

  #Messenger dialog box
  def message_dialog_show( self, message):
      self.message_dialog.set_property("text",message)
      response = self.message_dialog.run()
      self.message_dialog.hide()
    
  def on_key_press_event(self, widget, event):
   try:
    keyname = gtk.gdk.keyval_name(event.keyval)
    # Grab the letter q to stop the current movie
    if keyname == 'q' or keyname == 'Q':
      if(self.check_active_player()):
         self.player.quit()
    #Pause on spacebar
    if keyname == 'space':
      self.player.play_pause()
    #Strings from the reader end with a new line... so we take in all characters and process the last 10 on a newline
    if keyname == 'Return':
      rfid_string_scanned = self.dataString[-10::]
      self.dataString = '';
   except Exception as e: print(e)


  # Play video
  def play_video( self, filename):
         if self.check_active_player():
            self.player.quit()
         print "Playing " + filename
         VIDEO_PATH = Path("" + filename + "")
         self.player = OMXPlayer(VIDEO_PATH,args=['-b'])
         
           

   # Catch exception if process is not running when checking activity
  def check_active_player(self):
    try:
         playerStatus = self.player.playback_status()
         if playerStatus == 'Playing' or playerStatus =='Paused':
            return True          
    except:
         return False
         print "Exception thrown on inactive player"

  # Callback for radio button
  def toggle_fs(self,widget,data=None):
    logging.debug("Fullscreen %s" % (("OFF", "ON")[widget.get_active()]))
    if widget.get_active():
      self.mainWindow.fullscreen()
    else:
      self.mainWindow.unfullscreen()

  def listen_serial(self):
    try:
         if(self.ultrasoundProbe.inWaiting() > 0):
            s =''
            s += self.ultrasoundProbe.read(16)
            self.ultrasoundProbe.flushInput()
            self.dataString = s
            if(self.addRfidTag):
               self.handle_rfid_tag_text()
               return True
            else:
               self.handle_video_playing()
               logging.debug(self.dataString )
               return True
         else:
            if self.check_active_player():
               self.player.quit()
            logging.debug("No Tag in Range")
            return True
    except Exception as e:
         logging.debug(e)
         self.message_dialog_show(e)


  # Serial rfid tag to gui
  def handle_rfid_tag_text(self):
            rfid_string_scanned = self.dataString.strip()
            logging.debug(rfid_string_scanned)
            #Setting both add quick and add normal RFID fields to current read tag
            self.rfid_entry.set_text(rfid_string_scanned)
            self.rfid_quick_entry.set_text(rfid_string_scanned)
            self.dataString = ''
            
  # Continuously read rfid tags
  def handle_video_playing(self):
            logging.debug("read rfid for video playing")
            rfid_string_scanned = self.dataString.strip()
            logging.debug(rfid_string_scanned)
            self.dataString = ''

            # This code aims to check if the file is already playing so we don't continually start
            # the movie over if we are on the border of one of the tags
            # Need to check this sometimes, so always call it

            if self.check_active_player():              
              current_file = str(self.player.get_filename())
            else:
              current_file = None
            #Search for the matching rfid string and play the associated file
            # Get the tree to iterate over
            list_iter = self.list_store1.get_iter_root()
            while(list_iter):
              rfid_entry  = self.list_store1.get_value(list_iter, 1)
              rfid_entry = rfid_entry.strip()
              if rfid_entry == rfid_string_scanned:
                filename  = self.list_store1.get_value(list_iter, 2)
                # If we are not playing a video start the one requested
                if current_file == None:
                  self.play_video(filename)
                  return filename
                # If this filename doesn't match the current playing one, fire it up
                elif filename.find(current_file) == -1:
                  self.play_video(filename)
                  return filename
                else:
                  logging.debug("Not playing %s because it is already playing" % filename)
                  return True
              list_iter   = self.list_store1.iter_next(list_iter)
            logging.debug("Tag not stored in settings file yet!!")
           # return True

  #Flag for scanning to play video or read tag into gui textbox    
  def set_add_rfid_tag_active(self,flag = False):    
    self.addRfidTag = flag
    logging.debug("add rfid status flag " + str(self.addRfidTag))
      

  def __init__( self ):    

    #Glade compomnents intialise
    self.builder = gtk.Builder()
    self.builder.add_from_file(sys.path[0] + "/EDUS2.glade")
    #Interval timer to loop listen_serial while return is true
    self.timer = gtk.timeout_add(200, self.listen_serial)

    self.window           = self.builder.get_object( "window1" )
    self.settings_dialog  = self.builder.get_object( "settings_dialog" )
    self.add_scan_dialog  = self.builder.get_object( "add_scan_dialog" )
    self.quick_add_dialog  = self.builder.get_object( "quick_add_dialog" )
    self.quick_add_item  = self.builder.get_object( "quick_add_item" )
    self.about_dialog     = self.builder.get_object( "aboutdialog1")
    self.tree             = self.builder.get_object( "treeview2" )
    self.list_store1      = self.builder.get_object( "treeview" )
    self.rfid_entry       = self.builder.get_object( "rfid_entry" )
    self.rfid_quick_entry       = self.builder.get_object( "rfid_quick_entry" )
    self.name_entry       = self.builder.get_object( "name_entry" )
    self.quick_add_cur_filename       = self.builder.get_object( "quick_add_cur_filename" )
    self.filechooser      = self.builder.get_object( "filechooserbutton1" )
    self.filechooser_quick      = self.builder.get_object( "filechooserbutton_quick" )
    self.load_settings_filechooserdialog = self.builder.get_object("load_settings_filechooserdialog")
    self.save_settings_filechooserdialog = self.builder.get_object("save_settings_filechooserdialog")
    self.message_dialog = self.builder.get_object("message_dialog")

    self.load_settings(sys.path[0] + "/settings.p")
    self.builder.connect_signals( self )

    # Set up treeView to allow multiple item selection for better delete
    self.tree.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

    self.mainWindow = self.builder.get_object("window1")

    self.mainWindow.connect("key-press-event",self.on_key_press_event)
    self.window.show_all()
    self.mainWindow.fullscreen()



if __name__ == "__main__":
  win = Main()
  win.window.show_all()

  gtk.main()


