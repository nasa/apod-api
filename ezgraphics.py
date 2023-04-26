## @package ezgraphics.py
#
# This module is part of the Python Graphics and GUI Toolkit which is an
# ongoing open source project designed to provide simple Python GUI tools 
# for use in the classroom. This module provides classes for creating 
# top-level GUI windows that can be used for creating and displaying simple 
# geometric shapes and color digital images.
#
# (c) 2017 by Rance Necaise 
# http://ezgraphics.org 
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions: 
#  
# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software. 
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Version: 2.1
#

# CHANGES since v2.0
# ------------------
# 10/2/2017 - Fixed a problem with the initialization of the Tk system within
# some IDE environments that only load the module once per session instead
# of everytime the program is executed.


try: 
  import tkinter as tk
except ImportError :
  import Tkinter as tk
  import Tkinter.tkSimpleDialog as tkdlg
  
## This class defines a basic top level window that can be opened on the 
#  desktop and used to produce simple graphical drawings. It contains a
#  canvas on which geometric shapes can be drawn and manipulated. It also 
#  allows for an optional menu bar displayed at the top of the window and
#  a status bar displayed at the bottom of the window. Mouse and keyboard
#  events can be captured and handled using a callback function or 
#  methods.
#
class GraphicsWindow :
    
  # Class variable used to identify the first toplevel window created,
  # which serves as the main window. 
  
  _MainWindow = None
  
  ## Creates a new graphics window with an empty canvas.
  #  @param width The horizontal size of the canvas in pixels.
  #  @param height The vertical size of the canvas in pixels.
  #
  def __init__(self, width = 400, height = 400) :    

    global _rootWin
  
     # The window is initially visible, unless both arguments are None.
    visible = True
    if width is None and height is None :
      width = 400
      height = 400
      visible = False
      
     # If this is the first toplevel window, then tkinter has to be initialized
     # with the creation of a root window. We also need to remember this as the 
     # main window so we know when to terminate the event loop.
    if GraphicsWindow._MainWindow is None :
      _rootWin = tk.Tk()
      _rootWin.withdraw()  
      _rootWin.update_idletasks()
      GraphicsWindow._MainWindow = self      
      
    self._tkwin = tk.Toplevel(_rootWin, padx=0, pady=0, bd=0)      
    self._tkwin.protocol("WM_DELETE_WINDOW", self.close)
    self._tkwin.title("")    
      
     # A menu bar is created, but not used by default. To use a menu bar, 
     # the user must call showMenu() and configure it by accessing the 
     # menu via the menu() method.
    self._menubar = GraphicsMenu(self)    

     # Create a canvas inside the top-level window that is used 
     # for drawing the graphical shapes and text.
    self._canvas = GraphicsCanvas(self, width, height) 

     # Create a status bar that can be used at the bottom of the window.
    self._tkstatus = tk.Label(self._tkwin, text="",
                               anchor="w", relief=tk.SUNKEN)

     # Used to implement the local event loops for getMouse(), getKey()
     # and pause().
    self._waitVar = tk.IntVar()
    self._waitVar.set(0)
    self._waitValue = None
    
     # References to the callback function or class when the _onXYZ 
     # methods are not used.
    self._cbRoutine = None
    self._cbObject = None

     # A timer can be set that does not stop or pause the event loop. When
     # the timer is set, we must save it's id number.
    self._tktimer = None

     # Keep track of the id number of an image displayed over the entire
     # canvas.
    self._imgId = None
    
     # If the window is initially visible, then bring the window to the 
     # front of all other windows and force an update.
    if visible :
      self._tkwin.lift()     
      self._tkwin.resizable(0, 0)    
      self._tkwin.update_idletasks()
    else :
      self._tkwin.withdraw()
      
     # Is the window open and valid?
    self._valid = True

  ## Closes and destroys the window. A closed window can not be used.
  #
  def close(self) :
     # We can not close a window that was previously closed.    
    if not self._valid : return
    
     # If this is the main window being closed, then the mainloop and 
     # the GUI app has to be terminated.
    if self is GraphicsWindow._MainWindow :
       self.quit() #self._tkwin.quit()

     # Destroy the window and force an update so it will close when  
     # used in IDLE or the Wing IDE.
    else :
      self._tkwin.destroy()
      self._tkwin.update_idletasks()
      
     # Indicate that the window has been closed.
    self._valid = False
      
  ## Terminates the event loop causing the program to continue execution 
  #  immediately after the call to the wait() method.
  #
  def quit(self) :
  
    global _rootWin
    
    if GraphicsWindow._MainWindow._valid :
      GraphicsWindow._MainWindow._tkwin.update_idletasks()
      
       # If we are in a local event loop (getMouse, getKey, pause), 
       # then we must terminate those before destroying the windows.
      if self._waitVar.get() == 1 :
        self._waitVar.set(0)
        
       # Destroy the main and root windows to terminate the mainloop.
      GraphicsWindow._MainWindow._tkwin.destroy()
      GraphicsWindow._MainWindow = None
      _rootWin.destroy()  
      _rootWin = None
            
  ## Starts the event loop which handles various window events. This causes
  #  the sequential execution of the program to stop and wait for the user 
  #  to click the close button on the main window or to call the quit method
  #  on any window. This method should only be called on the main window.
  #  
  def wait(self):
    if self._valid and self == GraphicsWindow._MainWindow : 
      self._tkwin.mainloop()
    
  def getMouse(self) :
    def _onMouse(event) :
      self._waitVar.set(0)
      self._waitValue = (event.x, event.y)

    if self._valid :  
      self._tkwin.update()
      self._waitVar.set(1)      
      self._canvas._tkcanvas.bind("<ButtonRelease>", _onMouse)
      self._tkwin.wait_variable(self._waitVar)
      self._canvas._tkcanvas.unbind("<ButtonRelease>")
      return self._waitValue
    else :
      return (-1, -1)
    
  def getKey(self) :     
    def _onKey(event) :
      self._waitVar.set(0)
      if len(event.char) == 0 :
        self._waitValue = event.keysym
      else :
        num = ord(event.char)
        if num == 8 or num == 9 or num == 13 or num == 27 or num == 127:
          self._waitValue = event.keysym
        else :
          self._waitValue = event.char 
      
    if self._valid :
      self._tkwin.update()      
      self._waitVar.set(1)
      self._tkwin.bind("<KeyRelease>", _onKey)
      self._tkwin.wait_variable(self._waitVar)
      self._tkwin.unbind("<KeyRelease>")
      return self._waitValue
    else :
      return ""
        
  def pause(self, msTime) :
    def _onPause() :
      self._waitVar.set(0)  

    if self._tkwin.winfo_exists() :
      self._tkwin.update()      
      self._waitVar.set(1)
      self._tkwin.after(msTime, _onPause)
      self._tkwin.wait_variable(self._waitVar)
    
  ## Returns a reference to the canvas contained within the window. 
  #  The canvas can be used to draw and manipulate geometric shapes
  #  and text.
  #  @return A reference to the GraphicsCanvas contained in the window.
  #
  def canvas(self) :
    return self._canvas
                  
  ## Sets the title of the window. 
  #  By default, the window has no title.
  #  @param title A text string to which the title of the window is set. 
  #               To remove the title, use pass an empty string to the 
  #               method.
  #
  def setTitle(self, title):
    self._tkwin.title(title)
    
  ## Returns a Boolean indicating whether the window exists or was 
  #  previously closed. 
  #  Window operations can not be performed on a closed window.
  #  @return True if the window is closed and False otherwise.
  #
  def isValid(self):
    return self._valid
    
  ## Hides or iconifies the top level window. 
  #  The window is not destroyed, it's simply hidden from view and 
  #  can be displayed again using the show() method. 
  #
  def hide(self):    
    self._tkwin.withdraw()
    self._tkwin.update()
      
  ## Shows or deiconifies a previously hidden window.
  #
  def show(self):
    self._tkwin.deiconify()
    self._tkwin.update()
       
  ## Returns a reference to the menu bar associated with the window.  
  #  A menu bar will be displayed after this method is called the first 
  #  time and the menu has been configured.
  #  @return a reference to a GraphicsMenu object.
  #
  def menu(self) :
    return self._menubar

  ## Displays the menu bar at the top of the window. 
  #  The menu() method is used to access the menu for configuration.
  #
  def showMenu(self) :
    self._tkwin.config(menu=self._menubar._tkmenu)
  
  ## Hides the menu bar and removes it from the window. 
  #  The menu still exists and can be displayed again and/or configured
  #  further. 
  #
  def hideMenu(self) :
    self._tkwin.config(menu="")
        
  ## Displays a status bar at the bottom of the window that can be  
  #  used to display text messages.
  #
  def showStatus(self) :
    self._tkstatus.pack(side=tk.BOTTOM, fill=tk.X)
   
  ## Hides the status bar by removing it from the bottom of the window. 
  #  Hiding the bar does not destroy it or remove the text contained in
  #  the bar.
  #
  def hideStatus(self) :
    self._tkstatus.pack_forget()
  
  ## Sets the text message displayed in the message bar. 
  #  By default, the message is aligned to the left side of the bar.
  #  @param text The text string to be displayed in the status bar.
  #
  def setStatus(self, text="") :
    self._tkstatus.config(text=text)
  
  ## Modifies one or more configuration options of the status bar. 
  #  The options and settings are specified as keyword parameters. 
  #  @param options One or more named parameters. The options that can
  #                 be configured include the following:
  #
  #          fg: the text color specified as a string.
  #          bg: the background color specified as a string.
  #          anchor: a string command that specifies how the text is aligned 
  #                  within the status bar. The valid values are:
  #                  "n", "s", "e", "w", "center", "nw", "ne", "sw", "se"
  #          font: a tuple indicating the font used to draw the text message.
  #          justify: a string command that specifies how multiple lines of 
  #                  text should be aligned. The valid values are: 
  #                  "left", "center", "right" 
  #          padx: extra horizontal padding added around the text.
  #          pady: extra veritcal padding added around the text.
  #
  def configStatus(self, **options) :
    self._tkstatus.config(options)

  ## Enables one or more action events on the window.
  #     w.setEvent(event1, event2, ...)
  #
  #  @param events 
  #
  def enableEvents(self, *events) : 
    for eventType in events :
      eventType = eventType.lower()
      if eventType == "keypress" :
        self._tkwin.bind("<Key>", self._handleEvents)
      elif eventType == "mousemove" :
        self._canvas._tkcanvas.bind("<Motion>", self._handleEvents)
      elif eventType == "mousedown" :
        self._canvas._tkcanvas.bind("<ButtonPress>", self._handleEvents)
      elif eventType == "mouseup" :
        self._canvas._tkcanvas.bind("<ButtonRelease>", self._handleEvents)

  ## Clears or deactivates one or more window events that were set using 
  #  the enableEvents() method.
  #  @param events 
  #
  def clearEvents(self, *events) :
    for eventType in events :
      eventType = eventType.lower()      
      if eventType == "keypress" :
        self._tkwin.unbind("<Key>")
      elif eventType == "mousemove" :
        self._canvas._tkcanvas.unbind("<Motion>")
      elif eventType == "mousedown" :
        self._canvas._tkcanvas.unbind("<ButtonPress>")
      elif eventType == "mouseup" :
        self._canvas._tkcanvas.unbind("<ButtonRelease>")
     
  ## Sets the event handler to a user defined function or object instead
  #  of using the onXYZ callback methods.
  #
  def setEventHandler(self, handler) :
    if hasattr(handler, "__call__") :
      self._cbRoutine = handler
      self._cbObject = None
    else :
      self._cbObject = handler
      self._cbRoutine = None
    
  ## Sets a timer that triggers an alarm after it expires. The time is
  #  given in milliseconds.
  #
  def setTimer(self, msTime) :
    event = tk.Event()
    event.type = "Alarm"
    theCommand = lambda: self.onAlarm(event)
    self._tktimer = self._tkwin.after(msTime, theCommand)
  
  ## Clears the timer before it expires.
  #
  def clearTimer(self) :
    if self._tktimer is not None :
      self._tkwin.after_cancel(self._tktimer)
      self._tktimer = None
  
#--- Call back routines that can be overridden in a derived class in 
#    order to handle various events. These methods are documented in the
#    documentation.py file. They should not be called directly.
  def onMenuSelect(self, event) :
    if self._cbObject :
      self._cbObject.onMenuSelect(self, event)
    elif self._cbRoutine :
      self._cbRoutine(self, event)
    
  def onMouseMove(self, event) :
    if self._cbObject :
      self._cbObject.onMouseMove(self, event)
    elif self._cbRoutine :
      self._cbRoutine(self, event)
    
  def onMouseDrag(self, event) :
    if self._cbObject :
      self._cbObject.onMouseDrag(self, event)
    elif self._cbRoutine :
      self._cbRoutine(self, event)
  
  def onMouseDown(self, event):
    if self._cbObject :
      self._cbObject.onMouseDown(self, event)
    elif self._cbRoutine :
      self._cbRoutine(self, event)
 
  def onMouseUp(self, event):
    if self._cbObject :
      self._cbObject.onMouseUp(self, event)
    elif self._cbRoutine :
      self._cbRoutine(self, event)
  
  def onKeyPress(self, event) :
    if self._cbObject :
      self._cbObject.onKeyPress(self, event)
    elif self._cbRoutine :
      self._cbRoutine(self, event)
  
  def onAlarm(self, event) :
    if self._cbObject :
      self._cbObject.onAlarm(self, event)
    elif self._cbRoutine :
      self._cbRoutine(self, event)
      
  ## Helper method that handles the tkevents.
  #
  def _handleEvents(self, event) :
    if event.type == "2" :
      event.type = "KeyPress"
      self.onKeyPress(event)
      
    elif event.type == "4" :
      event.type = "MouseDown"
      event.button = int(event.num)
      self.onMouseDown(event)
      
    elif event.type == "5" :
      event.type = "MouseUp"
      event.button = int(event.num)
      self.onMouseUp(event)
      
    elif event.type == "6" :      
       # If one of the mouse buttons were pressed, this is a mouse drag.    
      if event.state & 0xF00 :
        if event.state & 0x100 != 0 :
          event.button = 1
        elif event.state & 0x200 != 0 :
          event.button = 2
        elif event.state & 0x400 != 0 :
          event.button = 3
        else :
          event.button = 0
        event.type = "MouseDrag"
        self.onMouseDrag(event)
      
       # Otherwise, it's a mouse move.
      else :
        event.button = 0
        event.type = "MouseMove"
        self.onMouseMove(event)      
              
      
## This class defines a canvas on which geometric shapes and text can be 
#  drawn. The canvas uses discrete Cartesian coordinates >= 0 with (0,0) 
#  being in the upper-left corner of the window. Unlike a canvas that a 
#  painter might use, shapes drawn on a graphics canvas are stored as 
#  objects that can later be reconfigured without having to redraw them. 
#  A collection of shape properties are also maintained as part of the 
#  canvas. These properties, which can be changed by calling specific 
#  methods, are used in drawing the various shapes and text. All shapes 
#  and text are drawn using the current context or the property settings 
#  at the time the shape is first drawn. 
#
class GraphicsCanvas :
  ## Creates a new empty graphics canvas. A graphics canvas is 
  #  automatically created as part of a GraphicsWindow. Thus, there should 
  #  be no need for the user of this module to explicitly create one.
  #  @param win, A reference to the GraphicsWindow in which the canvas 
  #          is used.
  #  @param width, (int) The width of the canvas in pixels.
  #  @param height, (int) The height of the canvas in pixels.
  #
  def __init__( self, win, width, height ):
   
    # The GraphicsWindow that contains the canvas.
   self._win = win
   
    # Keep track of the size of the canvas.
   self._width = width
   self._height = height
       
    # Maintain the options used for drawing objects and text.
   self._polyOpts = {"outline" : "black", "width" : 1, "dash" : None, "fill" : ""}
   self._arcStyle = "pieslice"
   self._textOpts = {"text" : "", "justify" : tk.LEFT, "anchor" : tk.NW,
                      "fill" : "black",
                      "font" : ("helvetica", 10, "normal")}

    # Tk requires the application to maintain a reference to the images
    # that are drawn on the canvas. For convenience, we maintain a 
    # dictionary of the image references.
   self._images = {}
   
    # Create the tk canvas inside the given window.
   self._tkcanvas = tk.Canvas(self._win._tkwin, highlightthickness = 0,
                         width = width, height = height, bg = "white" )
   self._tkcanvas.pack()   
                       
  ## Changes the height of the canvas. 
  #  The window is resized to fit the size of the canvas.
  #  @param size (int) The new height of the canvas in number of pixels.
  #                       
  def setHeight(self, size):
    if type(size) != int or size <= 0 :
      raise GraphicsParamError( "The window height must be >= 1." )
    self._tkcanvas.config( height=size )
    self._height = size
    self._tkcanvas.update_idletasks()

  ## Changes the width of the canvas. 
  #  The window is resized to fit the size of the canvas.
  #  @param size (int) The new width of the canvas in number of pixels.
  #
  def setWidth(self, size):    
    if type(size) != int or size <= 0 :
      raise GraphicsParamError("The window width must be >= 1.")
    self._tkcanvas.config(width=size)
    self._width = size
    self._tkcanvas.update_idletasks()
    
  ## Returns the height of the canvas.
  #  @return The canvas height in number of pixels.
  #
  def height(self):
    return self._height
  
  ## Returns the width of the canvas.
  #  @return The canva width in number of pixels.
  #
  def width(self):
    return self._width
     
  ## Clears the canvas by removing all items previously drawn on it. 
  #  The canvas acts as a container for the shapes and text. Thus, when a
  #  geometric shape or text is drawn on the canvas, the item is 
  #  maintained internally as an object until cleared.
  #
  def clear(self):
    self._tkcanvas.delete(tk.ALL)
    self._images = {}
    self._tkcanvas.update_idletasks()
    self._win._imgId = None

   
  ## Sets the current background color of the canvas. 
  #  The color can either be specified as a string that names a color or 
  #  as three integer values in the range [0..255].
  #
  #     c.setBackground(colorname)
  #     c.setBackground(red, green, blue)
  #   
  def setBackground(self, red, green = None, blue = None) :
    if type(red) == int :
      color = "#%02X%02X%02X" % (red, green, blue) 
    elif type(red) != str :
      raise GraphicsParamError("Invalid color.")
    else :
      color = red
    self._tkcanvas.config(bg = color)
    self._tkcanvas.update_idletasks()

  ## Sets the fill color used when drawing new polygon shapes. 
  #  The color can be specified either as a string that names the color 
  #  or as three integer values in the range [0..255]. If no argument is 
  #  provided, it clears the fill color and the shapes will be drawn in 
  #  outline form only.
  #
  #     c.setFill()
  #     c.setFill(colorname)
  #     c.setFill(red, green, blue)
  #    
  def setFill(self, red = None, green = None, blue = None) :
    if red is None :
      color = ""
    elif type(red) == int :
      color = "#%02X%02X%02X" % (red, green, blue)       
    elif type(red) != str :
      raise GraphicsParamError("Invalid color.")
    else :
      color = red
    self._polyOpts["fill"] = color
        
  ## Sets the outline color used when drawing new polygon shapes and the
  #  color used to draw lines, pixels, and text. 
  #  The color can be specified either as a string that names the color 
  #  or as three integer values in the range [0..255]. If no argument is 
  #  provided, it clears the outline color. A cleared outline color is 
  #  only meant for drawing polygon type shapes that are only filled, 
  #  without an outline.
  #
  #     c.setOutline()
  #     c.setOutline(colorname)
  #     c.setOutline(red, green, blue)
  #
  def setOutline(self, red = None, green = None, blue = None) :
    if red is None :
      color = ""
    elif type(red) == int :
      color = "#%02X%02X%02X" % (red, green, blue)  
    elif type(red) != str :
      raise GraphicsParamError("Invalid color.")
    else :
      color = red
    self._polyOpts["outline"] = color
    self._textOpts["fill"] = color
     
  ## Sets both the fill and outline colors used when drawing shapes and text
  #  on the canvas. 
  #  The color can be specified either as a string that names the color 
  #  or as three integer values in the range [0..255]. 
  #
  #     c.setColor(colorname)
  #     c.setColor(red, green, blue)
  #
  def setColor(self, red, green = None, blue = None) :
    if type(red) == int :
       color = "#%02X%02X%02X" % (red, green, blue)
    elif type(red) != str :
       raise GraphicsParamError("Invalid color.")
    else :
       color = red
    self._polyOpts["outline"] = color
    self._polyOpts["fill"] = color
    self._textOpts["fill"] = color     
    
  ## Sets the width of lines drawn on the canvas. 
  #  This includes the line and vector shapes and the outlines of polygons.
  #  @param size (int) The new line width in number of pixels.
  #
  def setLineWidth(self, size):
    if type(size) != int or size <= 0 :
      raise GraphicsParamError("Invalid line width.")
    self._polyOpts["width"] = size
    if self._polyOpts["dash"] :
      self._polyOpts["dash"] = (4 * size, 4 * size)

  ## Sets the style used to drawn lines on the canvas. 
  #  This includes the line and vector shapes and the outlines of polygons. 
  #  @param style (str) The style to use for new lines. It can be either 
  #               "solid" or "dashed".
  #
  def setLineStyle(self, style):
    if style == "dashed" :
      width = self._polyOpts["width"]
      self._polyOpts["dash"] = (4 * width, 4 * width)
    else :
      self._polyOpts["dash"] = None


  ## Sets the style used when drawing an arc on the canvas. 
  #  @param style, The style of the arc. It can be one of the strings: 
  #             "pieslice", "chord", or "arc". The default is "pieslice".
  #
  def setArcStyle(self, style) :
    if style not in ("pieslice", "chord", "arc") :
      raise GraphicsParamError("Invalid arc style.")
    self._arcStyle = "pieslice"
  
  ## Sets the font used to draw text on the canvas. 
  #  @param family (str) The font family. It can be one of: 
  #               "arial", "courier", "times", "helvetica".
  #  @param size (int) The point size of the font.
  #  @param style (string) The font style. It can be one of:
  #               "normal", "bold", "italic", or "bold italic".
  #  
  def setTextFont(self, family = None, style = None, size = None ):
    origFamily, origSize, origStyle = self._textOpts["font"]
    if family is None :
      family = origFamily    
    elif (family is not None and 
       family not in ('helvetica', 'arial', 'courier', 'times', 'times roman')) :
      raise GraphicsParamError("Invalid font family.")
      
    if style is None :
      style = origStyle    
    elif (style is not None and 
       style not in ('bold', 'normal', 'italic', 'bold italic')) :
      raise GraphicsParamError( "Invalid font style." )

    if size is None :
       size = origSize    
    elif size is not None and (type(size) != int or size <= 0) :
      raise GraphicsParamError( "Invalid font size." )
       
    self._textOpts["font"] = (family, size, style)     

  ## Sets the position that text is drawn in relation to a bounding box. 
  #  The (x, y) coordinate provided with drawText() is anchored to a spot on
  #  the bounding box that surrounds the text and the text is positioned 
  #  relative to the anchor. 
  #  @param position A string indicating the anchor position on the 
  #                  bounding box. It can be one of:
  #                  "n", "s", "e", "w", "center", "nw", "ne", "sw", "se".
  #
  def setTextAnchor(self, position):
    if position not in ('n', 's', 'e', 'w', 'nw', 'ne', 'sw', 'se', 'center') :
      raise GraphicsParamError( "Invalid anchor position." )       
    self._textOpts["anchor"] = position
     
     
  ## Sets the justification used to draw new multiline text on the canvas.
  #  @param style A string specifying the justification. It can be one of:
  #               "left", "center", or "right".
  #
  def setTextJustify(self, style):
    if style in ("left", "center", "right") :
      self._textOpts["justify"] = style
    else :
      raise GraphicsParamError("Invalid justification value.")
    
 #--- The object drawing methods.

  ## Draws or plots a single point (pixel) on the canvas.
  #  @param x, y  Integers indicating the (x, y) pixel coordinates at which
  #               the point is drawn.
  #  @return An integer that uniquely identifies the new canvas item.
  #
  def drawPoint(self, x, y):
    obj = self._tkcanvas.create_line(x, y, x+1, y,
                                    fill=self._polyOpts["outline"], 
                                    width=self._polyOpts["width"])
    self._tkcanvas.update_idletasks()
    return obj    

  ## Draws a line segment on the canvas. 
  #  The line is drawn between two discrete end points.
  #  @param x1, y1 The coordinates of the starting point.
  #  @param x2, y2 The coordinates of the ending point.
  #  @return An integer that uniquely identifies the new canvas item.
  #
  def drawLine(self, x1, y1, x2, y2):
    obj = self._tkcanvas.create_line(x1, y1,
                                     x2, y2,
                                     fill=self._polyOpts["outline"], 
                                     width=self._polyOpts["width"],
                                     dash=self._polyOpts["dash"])
    self._tkcanvas.update_idletasks()
    return obj
  
  ## Draws an arrow or vector on the canvas. 
  #  The same as a line segment, except an arrow head is drawn at the 
  #  end of the segment.
  #  @returns An integer that uniquely identifies the new canvas item.
  #
  def drawArrow(self, x1, y1, x2, y2):
    obj = self._tkcanvas.create_line(x1, y1, x2, y2, 
                                     fill=self._polyOpts["outline"], 
                                     width=self._polyOpts["width"],
                                     dash=self._polyOpts["dash"],
                                     arrow=tk.LAST)
    self._tkcanvas.update_idletasks()
    return obj
    
  ## Draws a rectangle on the canvas. 
  #  The rectangle is defined by the coordinates of the upper left corner of
  #  the rectangle and its width and height. 
  #  @param x, y The coordinates of the upper-left corner of the rectangle.
  #  @param width, height The dimensions of the rectangle.
  #  @returns An integer that uniquely identifies the new canvas item.
  #
  def drawRect(self, x, y, width, height) :
    obj = self._tkcanvas.create_rectangle(x, y, x + width, y + height, self._polyOpts)
    self._tkcanvas.update_idletasks()
    return obj
  
  ## The same as drawRect(). 
  #
  def drawRectangle(self, x, y, width, height) :
    return self.drawRect(x, y, width, height)
    
  ## Draws a polygon on the canvas. The polygon is defined by three or more vertices
  #  specified in counter-clockwise order. There are four forms of the method: 
  #  
  #     c.drawPoly(x1, y1, x2, y2, ..., xN, yN)
  #     c.drawPoly(sequence of ints)
  #     c.drawPoly((x1, y1), (x2, y2), ..., (xN, yN))
  #     c.drawPoly(sequence of 2-tuples)
  #     
  #  @returns An integer that uniquely identifies the new canvas item.
  #  
  def drawPoly(self, *coords):
    minCoords = 6
    
     # Unwrap the cooridinates which allows the method to accept individual 
     # vertices or a list of vertices.
    if len(coords) == 1 and (type(coords[0]) == list or type(coords[0]) == tuple) :
       expCoords = tuple(*coords)
    else :
       expCoords = coords
       
    if type(expCoords[0]) == list or type(expCoords[0]) == tuple :
      minCoords = 3
       
    if len(expCoords) < minCoords :
      raise GraphicsParamError("At least 3 vertices must be provided.")
    obj = self._tkcanvas.create_polygon( expCoords, self._polyOpts )
    self._tkcanvas.update_idletasks()
    return obj
  
  ## The same as drawPoly().
  #
  def drawPolygon(self, *coords) :
    return self.drawPoly(*coords)
      
  ## Draws an oval on the canvas. 
  #  The oval is defined by a bounding rectangle that is specified by 
  #  the coordinates of its upper-left corner and its dimensions. 
  #  @param x, y The upper-left coordinates of the bounding rectangle.
  #  @param width, height The dimensions of the bounding rectangle.
  #  @returns An integer that uniquely identifies the new canvas item.
  #
  def drawOval(self, x, y, width, height):
    obj = self._tkcanvas.create_oval(x, y, x + width, y + height, self._polyOpts)
    self._tkcanvas.update_idletasks()
    return obj    
            
  ## Draws an arc or part of a circle on the canvas. 
  #  The arc is defined by a bounding square and two angles. The angles 
  #  are specified in degrees with zero degrees corresponding to the x-axis.
  #  @param x, y The upper-left coordinates of the bounding square.
  #  @param diameter The dimensions of the bounding rectangle.
  #  @param startAngle The angle in degrees at which the arc begins. 
  #  @param extent The extent of the arc given as an angle in degrees. 
  #  @returns An integer that uniquely identifies the new canvas item.
  #       
  def drawArc(self, x, y, diameter, startAngle, extent) :
    obj = self._tkcanvas.create_arc(x, y, x + diameter, y + diameter, 
                          self._polyOpts, style=self._arcStyle,
                          start=startAngle, extent=extent) 
    self._tkcanvas.update_idletasks()
    return obj
  
  ## Draws text on the canvas. 
  #  The text is drawn such that an anchor point on a
  #  bounding box is positioned at a given point on the canvas. The default 
  #  position of the anchor is in the upper-left (northwest) corner of the
  #  bounding box. The anchor position can be changed using the setTextAnchor()
  #  method. The text is drawn using the default font family, size, and style.
  #  The setTextFont() method can be used to change those characteristics. The 
  #  text to be drawn can consists of multiple lines, each separated by a
  #  newline character. The justification of the text can be set when drawing
  #  multiple lines of text.
  #  @param x, y The position on the canvas at which the anchor point of the 
  #              bounding box is positioned.
  #  @param text A string containing the text to be drawn on the canvas.
  #  
  def drawText(self, x, y, text):
    self._textOpts["text"] = text
    obj = self._tkcanvas.create_text(x, y, self._textOpts)
    self._tkcanvas.update_idletasks()
    return obj
         
  ## Draws an image onto the canvas.
  #
  def drawImage(self, x, y = None, image = None) :
    if type(x) == GraphicsImage :
      image = x
      self.setWidth(image.width())
      self.setHeight(image.height())
      obj = self._tkcanvas.create_image(0, 0, anchor="nw", image=image._tkimage)
    else :
      obj = self._tkcanvas.create_image(x, y, anchor="nw", image=image._tkimage)
      
    self._images[obj] = image
    self._tkcanvas.update_idletasks()      
    return obj
    
 #--- Methods that can be used to manipulate the items previously drawn 
 #--- on the canvas. Each canvas drawing method returns a unique id number
 #--- used to identify the resulting object.
 
  ## Shifts an item on the canvas.
  #  The item to be shifted is indicated by its id number, which was
  #  returned when the item was drawn. The item is shifted by a given 
  #  amount in both the horizontal and vertical directions.
  #  @param itemId The id number of the item to be shifted. 
  #  @param dx The amount to shift the item in the horizontal direction. 
  #  @param dy The amount to shift the item in the vertical direction. 
  #
  def shiftItem(self, itemId, dx, dy) :
    self._tkcanvas.move(itemId, dx, dy)    
    self._tkcanvas.update_idletasks()
  
  ## Scales or resizes a geometric shape on the canvas.
  #  The coordinates that define the given geometric shape are modified
  #  by a given scale factor. 
  #  @param itemId The id number of the item to be resized.
  #  @param xScale, yScale - the horizontal and vertical scale factor.
  #  @param xOffset, yOffset - the horizontal and vertical offset.
  #
  def scaleItem(self, itemId, xScale, yScale, xOffset = None, yOffset = None) :
    if xOffset is None and yOffset is None :
      bbox = self._tkcanvas.bbox(itemId)
      xOffset = (bbox[2] - bbox[0]) // 2 + bbox[0]
      yOffset = (bbox[3] - bbox[1]) // 2 + bbox[1]
    self._tkcanvas.scale(itemId, xOffset, yOffset, xScale, yScale)
    self._tkcanvas.update_idletasks()
     
  ## Removes an item from the canvas. 
  #  The item to be removed is indicated
  #  by its id number, which was returned when the item was drawn. 
  #  @param itemId The id number of the item to be removed.
  #
  def removeItem(self, itemId) :
    self._tkcanvas.delete(itemId)
    if itemId in self._images :
      self._images.pop(itemId)
    self._tkcanvas.update_idletasks()
    
  ## Shows or unhides an item that was previously hidden. 
  #  The item to unhide is indicated by its id number, which was returned
  #  when the item was drawn.
  #  @param itemId The id number of the item to be shown. 
  #
  def showItem(self, itemId) :
    self._tkcanvas.itemconfig(itemId, state = "normal")
    self._tkcanvas.update_idletasks()
    
  ## Hides an item on the canvas. 
  #  The item is still part of the canvas, but it is hidden from view. 
  #  The item to be removed is indicated by its id
  #  number, which was returned when the item was drawn.  
  #  @param itemId The id number of the item to be hidden. 
  #
  def hideItem(self, itemId) :
    self._tkcanvas.itemconfig(itemId, state = "hidden")
    self._tkcanvas.update_idletasks()
   
  ## Raises an item to the top of the canvas stack or above another item.
  #  @param itemId The id number of the item to be raised.
  #  @param aboveId If provided, the id number of the item above which an
  #                item is raised, otherwise, the item is raised to the 
  #                top of the stack.
  #
  def raiseItem(self, itemId, aboveId = None) :    
    if aboveId is None :
      self._tkcanvas.tag_raise(itemId)
    else :
      self._tkcanvas.tag_raise(itemId, aboveId)      
    self._tkcanvas.update_idletasks()
  
  ## Lowers an item to the bottom of the canvas stack or below another item.
  #  @param itemId The id number of the item to be lowered.
  #  @param belowId If provided, the id number of the item below which an
  #                item is lowered. Otherwise, the item is lowered to the 
  #                bottom of the stack.
  #
  def lowerItem(self, itemId, belowId = None) :
    if belowId is None :
      self._tkcanvas.tag_lower(itemId)
    else :
      self._tkcanvas.tag_lower(itemId, belowId)    
    self._tkcanvas.update_idletasks()
 
  ## Determines if an id number is valid. For an id number to be valid, it
  #  must be associated with an item currently on the canvas. Once an item is
  #  removed, the id number is no longer valid.  
  #  @returns True if the id number if valid and False otherwise.
  #
  def __contains__(self, itemId):
    if self._tkcanvas.winfo_ismapped() :
      return len(self._tkcanvas.find_withtag(itemId)) > 0
    else :
      return False

  ##
  #
  #def itemCoords(self, itemId) :
  #  return self._tkcanvas.itemconfig(itemId)
  #  return self._tkcanvas.coords(itemId)
    
  ## Returns the type of item associated with the given id number.
  #  @returns  A string indicating the type of item associated with the
  #            given id number. The value will be one of the following: 
  #            "arc", "line" (note that a pixel is drawn as a line), 
  #            "oval", "polygon", "rectangle", "text".		
  #
  def itemType(self, itemId) :
    return self._tkcanvas.type(itemId)
   
  ## Returns a list containing the id numbers of all items on the canvas,
  #  whether visible or not. 
  #  @returns A list of integers that correspond to the id numbers of the
  #           shapes and text on the canvas 
  #
  def items(self) :
    return self._tkcanvas.find_all()
    self._tkcanvas.update_idletasks()
  
  ## Returns the id number of the item that is just above the given target
  #  item on the canvas stack.
  #  @param itemId the id number of the target item.
  #  @returns the id number of the item that is just above the target item.
  #           If the target item is at the top of the stack, 0 is returned.
  #
  def itemAbove(self, itemId) :
    idList = self._tkcanvas.find_above(itemId)
    if len(idList) == 0 :
      return 0
    else :
      return idList[0]
      
  ## Returns the id number of the item that is just below the given target
  #  item on the canvas stack.
  #  @param itemId the id number of the target item.
  #  @returns the id number of the item that is just below the target item.
  #           If the target item is at the bottom of the stack, 0 is returned.
  #
  def itemBelow(self, itemId) :
    idList = self._tkcanvas.find_below(itemId)
    if len(idList) == 0 :
      return 0
    else :
      return idList[0]            
        
## This class defines a basic top level window that can display a
#  digital GraphicsImage.
#
class ImageWindow(GraphicsWindow) :
  
  ## Creates a new window for displaying images. This provides a quick
  #  way to display images without having to access and draw on the 
  #  canvas of a graphics window.
  #         
  def __init__(self) :
    super().__init__(None, None)
    self._imgId = None
    
  ## Displays an image in the window. The window is resized to fit tightly
  #  around the image.
  #  @param image  The GraphicsImage object containing the image to 
  #                be displayed.
  #
  def display(self, image = None) :
    if self._imgId is not None :
      self._canvas._tkcanvas.delete(self._imgId) 
      self._imgId = None
    if image is None : return
    
    width = image.width()
    height = image.height()
    self._canvas._tkcanvas.config(width=width, height=height)
    self._canvas._width = width
    self._canvas._height = height

    self._tkwin.deiconify()    
    self._imgId = self._canvas._tkcanvas.create_image(
                         0, 0, anchor="nw", image=image._tkimage)
    self._canvas._tkcanvas.update_idletasks()
    self._tkwin.update()
         
 
## This class defines an RGB digital image that is contained within an
#  ImageWindow.
#
class GraphicsImage :
  
  ## Creates a new graphics image. 
  #
  def __init__(self, width = None, height = None) :
     # Create the photo image.
    if height is None and type(width) == str :
      filename = width
      self._tkimage = tk.PhotoImage(file = filename)
    else :
      self._tkimage = tk.PhotoImage(width = width, height = height)
  
  ## Gets the width of the image in pixels.
  #  @return The width of the image.
  #
  def width(self) :
    return self._tkimage.width()

  ## Gets the height of the image in pixels.
  #  @return The width of the image.
  #
  def height(self) :
    return self._tkimage.height()

  ## Sets a pixel to a given RGB color.
  #  There are two forms of the method:
  # 
  #      win.setPixel(row, col, red, green, blue)
  #      win.setPixel(row, col, hexColor)
  #      win.setPixel(row, col, pixel)
  #
  #  @param row, col (int) The pixel coordinates.
  #  @param red, green, blue (int) The discrete RGB color components in 
  #                        the range [0..255].
  #  @param hexColor  The RGB color components specified as a hex string.
  #  @param pixel The RGB color components specified as a 3-tuple.
  #
  def setPixel(self, row, col, *rgbColor) :
    if len(rgbColor) == 1 :
      if type(rgbColor[0]) == str :
        color = rgbColor[0]
      else :
        rgbColor = tuple(*rgbColor)
        color = "{#%02x%02x%02x}" % rgbColor      
    else :
      color = "{#%02x%02x%02x}" % rgbColor      
    self._tkimage.put(color, (col, row))
  
  ## Returns a 3-tuple containing the RGB color of a given pixel.
  #  @param row, col (int) The pixel coordinates.
  #  @return An RGB color as a 3-tuple.
  #
  def getPixel(self, row, col) :
    result = self._tkimage.get(col, row)
    if type(result) == str :
      parts = result.split()
      return (int(parts[0]), int(parts[1]), int(parts[2]))
    else :
      return result

  ## Returns the red component of the RGB color of a given pixel.
  #  @param row, col (int) The pixel coordinates.
  #  @return The value of the red component of the given pixel. 
  def getRed(self, row, col) :
    pixel = self.getPixel(row, col)
    return pixel[0]
    
  ## Returns the green component of the RGB color of a given pixel.
  #  @param row, col (int) The pixel coordinates.
  #  @return The green component of the given pixel. 
  def getGreen(self, row, col) :
    pixel = self.getPixel(row, col)
    return pixel[1]
    
  ## Returns the blue component of the RGB color of a given pixel.
  #  @param row, col (int) The pixel coordinates.
  #  @return The blue component of the given pixel. 
  def getBlue(self, row, col) :
    pixel = self.getPixel(row, col)
    return pixel[2]
    
  ## Clears the image and removes all of the pixels but the size of the 
  #  image remains the same.
  #
  def clear(self) :
    self._tkimage.blank()
    
  ## Creates a duplicate copy of the image.
  #
  def copy(self) :
    image = GraphicsImage(1, 1)
    image._tkimage = self._tkimage.copy()
    return image
  
  ## Saves the digital image to a file in either the gif or ppm format.
  #  @param filename, The full name of a gif or ppm image file.
  #  @param format, The format in which to save the image. It can be either
  #          "gif" or "ppm". The default is "gif".
  #
  def save(self, filename, format="gif") :
    if format not in ("gif", "ppm") :
      raise GraphicsParamError( "Invalid image format.")
    self._tkimage.write(filename, format=format)


## This class defines a menu container into which menu options can be added.
#  Each option can be associated with a command code or a pull-down menu.
#  When an option with a command code is selected, the menu callback routine
#  is called with the given code.
#
class GraphicsMenu :
  def __init__(self, win, menu = None) :
    self._win = win
    self._menu = menu
    if menu :
      self._tkmenu = tk.Menu(menu._tkmenu, tearoff=0)
    else :
      self._tkmenu = tk.Menu(win._tkwin, tearoff=0)
    
  def addSubMenu(self, label) :
    submenu = GraphicsMenu(self._win, self)
    self._tkmenu.add_cascade(label=label, menu=submenu._tkmenu)
    return submenu
    
  def addOption(self, label, cmdCode) :
    if hasattr(cmdCode, "__call__") :
      theCommand = cmdCode
    else :
      event = tk.Event()
      event.type = "MenuSelect"
      event.menutype = "item"
      event.cmdcode = cmdCode
      theCommand = lambda: self._win.onMenuSelect(event)
    self._tkmenu.add_command(label=label, command=theCommand)
  
  def addSeparator(self) :
    self._tkmenu.add_separator()

  def addCheckButton(self, label, cmdCode, checked = False) :    
    boolVar = tk.BooleanVar()
    boolVar.set(checked)
    if hasattr(cmdCode, "__call__") :
      theCommand = cmdCode
    else :
      event = tk.Event()
      event.type = "MenuSelect"
      event.menutype = "check"
      event.cmdcode = cmdCode
      event.var = boolVar
      theCommand = lambda: self._win.onMenuSelect(event)

    self._tkmenu.add_checkbutton(label=label, variable=boolVar, 
                        onvalue=1, offvalue=0, command=theCommand)
    return boolVar

  ## Adds a group of radio buttons to a menu. 
  #  The entries for the radio button group are passed as a sequence of
  #  strings. The entries are added to the menu in the order that they
  #  occur within the sequence. The currently selected entry is indicated
  #  by its position within the group, with the first entry at position 1.
  #  The radio button that is initially selected can be specified, 
  #  otherwise, the first entry in the sequence is used.    
  #  @param buttonLabels A sequence of string that serve as the labels
  #                for the radio buttons in the group. 
  #  @param cmdCode The code associated with the group of radios buttons 
  #                that will be passed to the callback routine when a radio
  #                button is selected.
  #  @returns A reference to a special IntVar object that contains the 
  #           value of the currently selected radio button. This value 
  #           can be accessed using the objects get() method.
  #
  def addRadioButtons(self, buttonLabels, cmdCode, initValue=None) :
    intVar = tk.IntVar()
    if initValue is None :
      intVar.set(1)
    else :
      intVar.set(initValue)
      
    if hasattr(cmdCode, "__call__") :
      theCommand = cmdCode
    else :
      event = tk.Event()
      event.type = "MenuSelect"
      event.menutype = "radio"
      event.cmdcode = cmdCode
      event.var = intVar
      theCommand = lambda: self._win.onMenuSelect(event)

    num = 1
    for entry in buttonLabels :
      self._tkmenu.add_radiobutton(label=entry, variable=intVar, 
                        value=num, command=theCommand)
      num = num + 1
    return intVar
        
# --- Defines special graphics exceptions that are raised when an error
# --- occurs in a GraphicsWindow method.

class GraphicsError(Exception) :
  def __init__( self, message ):
    super(GraphicsError, self).__init__( message )

class GraphicsObjError(GraphicsError) :
  def __init__( self ):
    super(GraphicsError, self).__init__( "Invalid object id." )

class GraphicsWinError(GraphicsError) :
  def __init__( self ):
    super(GraphicsWinError, self).__init__(
              "Operation can not be performed on a closed window." )

class GraphicsParamError(GraphicsError) :
  def __init__( self, message ):
    super(GraphicsParamError, self).__init__( message )
  

# --- Initialize a system wide variable that holds Tk's root window.
_rootWin = None

