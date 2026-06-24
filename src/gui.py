#######################################################################################
# gui.py       Version 4.0     22-Jun-2026
#
# Taj Ballinger, Trevor Ritchie, Dana Hughes, and Bill Manaris
#
#######################################################################################
#
# This file is part of PythonMusic.
#
# PythonMusic is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PythonMusic is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PythonMusic.  If not, see <https://www.gnu.org/licenses/>.
#
# PythonMusic derives from JythonMusic (https://jythonmusic.me),
# Copyright (C) 2011-2023 Bill Manaris, John-Anthony Thevos, Marge Marshall,
# Chris Benson, and Kenneth Hanson.
# Modifications Copyright (C) 2025 Dr. Bill Manaris and the PythonMusic contributors.
#
#######################################################################################
#
# REVISIONS:
#
# 4.0   22-Jun-2026 (tb)   Ported from JythonMusic to PythonMusic.
#      - Replaced Java AWT/Swing backend with Qt (PySide6)
#      - Qt event loop runs in child process (GuiRenderer) via GuiHandler, never blocks user code
#         - Qt process is solely for rendering; calculations and canonical state
#           is handled in PythonMusic process
#      - Rebuilt widget hierarchy natively, was Swing subclasses plus Java listener classes:
#         - Interactable base for Display and Drawable
#         - Drawable/Graphics shapes: Rectangle, Oval, Circle, Arc, Polyline, Line, Polygon, Icon, Label
#         - Control widgets: Button, CheckBox, Slider, DropDownList, TextField, TextArea
#         - MusicControl group: HFader, VFader, Rotary, Push, Toggle, XYPad
#      - Added native Color and Font classes, were java.awt
#      - Major Drawable updates:
#         - Added Groups to move, rotate, and resize shapes as a unit
#         - Drawables are internally affine transform matrices
#         - Added rotation and visibility properties
#         - Added get/set size/width/height functions
#         - Added get/set center functions
#         - Added getEndpoints and getBoundingBox
#         - Added get/set length to Line
#         - Added Polyline class
#         - Added alpha channel to Icon get/set pixel functions
#      - Display draw methods now stamp to canvas, instead of creating interactive object
#      - colorGradient -> Color.gradient; uses OKLab transition
#      - Added full Google-style docstrings throughout
#
# TODO:
#    - Can we rotate Controls in Qt? (QWidgets)
#
#######################################################################################

from utilities import *    # mapValue, etc.
import numpy as np
from PythonMusic.GuiHandler import _createHandler

#######################################################################################
# GuiHandler singleton and object ID allocator
#######################################################################################
# gui.py's display rendering, hit testing, and event handling is powered by Qt(PySide6).
# However, Qt's event loop blocks the python intepreter while its running.  Since Qt
# requires its event loop to be in the main thread, we offload it to a child process,
# which is managed by GuiHandler.  As a result, PythonMusic's user libraries never
# need to touch Qt.
# 
# NOTE: GuiHandler's components have mirrored versions of PythonMusic's visual
# objects to help with converting to Qt.  Future changes to gui's API may require
# updating those mirrored objects as well.

_GUI_HANDLER = None   # lazily created on first Display
def _handler():
   """"""
   global _GUI_HANDLER
   if _GUI_HANDLER is None:
      _GUI_HANDLER = _createHandler()
   return _GUI_HANDLER

_OBJECT_ID_COUNTER = 0

def _nextObjectId():
   """"""
   global _OBJECT_ID_COUNTER
   _OBJECT_ID_COUNTER += 1
   return _OBJECT_ID_COUNTER

#######################################################################################
# Virtual Key Constants
#######################################################################################
# Java 8 Virtual Keys -> Qt Virtual Key Codes
VK_A = 65
VK_B = 66
VK_C = 67
VK_D = 68
VK_E = 69
VK_F = 70
VK_G = 71
VK_H = 72
VK_I = 73
VK_J = 74
VK_K = 75
VK_L = 76
VK_M = 77
VK_N = 78
VK_O = 79
VK_P = 80
VK_Q = 81
VK_R = 82
VK_S = 83
VK_T = 84
VK_U = 85
VK_V = 86
VK_W = 87
VK_X = 88
VK_Y = 89
VK_Z = 90

VK_0 = 48
VK_1 = 49
VK_2 = 50
VK_3 = 51
VK_4 = 52
VK_5 = 53
VK_6 = 54
VK_7 = 55
VK_8 = 56
VK_9 = 57

VK_NUMPAD0 = 48
VK_NUMPAD1 = 49
VK_NUMPAD2 = 50
VK_NUMPAD3 = 51
VK_NUMPAD4 = 52
VK_NUMPAD5 = 53
VK_NUMPAD6 = 54
VK_NUMPAD7 = 55
VK_NUMPAD8 = 56
VK_NUMPAD9 = 57

VK_F1            = 16777264
VK_F2            = 16777265
VK_F3            = 16777266
VK_F4            = 16777267
VK_F5            = 16777268
VK_F6            = 16777269
VK_F7            = 16777270
VK_F8            = 16777271
VK_F9            = 16777272
VK_F10           = 16777273
VK_F11           = 16777274
VK_F12           = 16777275

VK_ESCAPE        = 16777216
VK_TAB           = 16777217
VK_CAPS_LOCK     = 16777252
VK_SHIFT         = 16777248
VK_CONTROL       = 16777249
VK_ALT           = 16777251
VK_SPACE         = 32
VK_ENTER         = 16777220
VK_BACK_SPACE    = 16777219
VK_DELETE        = 16777223
VK_HOME          = 16777232
VK_END           = 16777233
VK_PAGE_UP       = 16777238
VK_PAGE_DOWN     = 16777239
VK_UP            = 16777235
VK_DOWN          = 16777237
VK_LEFT          = 16777234
VK_RIGHT         = 16777236
VK_INSERT        = 16777222
VK_PAUSE         = 16777224
VK_PRINTSCREEN   = 16777225
VK_SCROLL_LOCK   = 16777254
VK_NUM_LOCK      = 16777253
VK_SEMICOLON     = 59
VK_EQUALS        = 61
VK_COMMA         = 44
VK_MINUS         = 45
VK_PERIOD        = 46
VK_SLASH         = 47
VK_BACK_SLASH    = 92
VK_OPEN_BRACKET  = 91
VK_CLOSE_BRACKET = 93
VK_QUOTE         = 39
VK_BACK_QUOTE    = 96

# Arc Constants (in degrees)
PI      = 180
HALF_PI = 90
TWO_PI  = 360

# Arc Style Constants
PIE   = 0
OPEN  = 1
CHORD = 2

# Label Alignment Constants
LEFT   = 1
CENTER = 132
RIGHT  = 2

# Widget Orientation Constants
HORIZONTAL = 1
VERTICAL   = 2


#######################################################################################
# Color
#######################################################################################
class Color:
   """Represent a color as red, green, and blue components, with optional transparency.

   Pass red, green, and blue to build a color directly. Leave any of the three out
   and a color-selection dialog opens for you to pick one instead. Ready-made
   constants are also available: Color.BLACK, Color.BLUE, Color.CYAN, Color.DARK_GRAY,
   Color.GRAY, Color.GREEN, Color.LIGHT_GRAY, Color.MAGENTA, Color.ORANGE, Color.PINK,
   Color.PURPLE, Color.RED, Color.WHITE, Color.YELLOW, and Color.CLEAR.

   Args:
       red (int, optional): The red component, from 0 to 255. If omitted, a color-selection dialog opens.
       green (int, optional): The green component, from 0 to 255. If omitted, a color-selection dialog opens.
       blue (int, optional): The blue component, from 0 to 255. If omitted, a color-selection dialog opens.
       alpha (int, optional): The opacity, from 0 (fully transparent) to 255 (fully opaque).
   """

   def __init__(self, red=None, green=None, blue=None, alpha=255):
      """"""

      if None in (red, green, blue):
         # at least one necessary color was missing, so bring up color selection.
         red   = red   if red   is not None else 255  # replace None values with 255
         green = green if green is not None else 255
         blue  = blue  if blue  is not None else 255
         
         red, green, blue = Color.select(red, green, blue)  # get a usable color

      # store color values as 0-255 integers
      self.red   = int(red)
      self.green = int(green)
      self.blue  = int(blue)
      self.alpha = int(alpha)

   def __str__(self):
      return f'Color(red = {self.getRed()}, green = {self.getGreen()}, blue = {self.getBlue()}, alpha = {self.getAlpha()})'

   def __repr__(self):
      return str(self)

   def getRed(self):
      """Return the red component of the color.

      Returns:
          red (int): The red component, from 0 to 255.
      """
      red = self.red
      return red

   def setRed(self, red):
      """Set the red component of the color.

      Args:
          red (int): The new red component, from 0 to 255.
      """
      self.red = int(red)

   def getGreen(self):
      """Return the green component of the color.

      Returns:
          green (int): The green component, from 0 to 255.
      """
      green = self.green
      return green

   def setGreen(self, green):
      """Set the green component of the color.

      Args:
          green (int): The new green component, from 0 to 255.
      """
      self.green = int(green)

   def getBlue(self):
      """Return the blue component of the color.

      Returns:
          blue (int): The blue component, from 0 to 255.
      """
      blue = self.blue
      return blue

   def setBlue(self, blue):
      """Set the blue component of the color.

      Args:
          blue (int): The new blue component, from 0 to 255.
      """
      self.blue = int(blue)

   def getAlpha(self):
      """Return the alpha (transparency) component of the color.

      Returns:
          alpha (int): The opacity, from 0 (fully transparent) to 255 (fully opaque).
      """
      alpha = self.alpha
      return alpha

   def setAlpha(self, alpha):
      """Set the alpha (transparency) component of the color.

      Args:
          alpha (int): The new opacity, from 0 (fully transparent) to 255 (fully opaque).
      """
      self.alpha = int(alpha)

   def getRGB(self):
      """Return the color's red, green, and blue components together.

      Returns:
          red (int): The red component, from 0 to 255.
          green (int): The green component, from 0 to 255.
          blue (int): The blue component, from 0 to 255.
      """
      red, green, blue = self.red, self.green, self.blue
      return red, green, blue

   def getRGBA(self):
      """Return the color's red, green, blue, and alpha components together.

      Returns:
          red (int): The red component, from 0 to 255.
          green (int): The green component, from 0 to 255.
          blue (int): The blue component, from 0 to 255.
          alpha (int): The opacity, from 0 (fully transparent) to 255 (fully opaque).
      """
      red, green, blue, alpha = self.red, self.green, self.blue, self.alpha
      return red, green, blue, alpha

   def brighter(self):
      """Return a brighter version of the color.

      The original color is left unchanged.

      Returns:
          brighterColor (Color): A new color, brighter than this one.
      """
      brighterRed   = min(255, int(self.red * 1.1))
      brighterGreen = min(255, int(self.green * 1.1))
      brighterBlue  = min(255, int(self.blue * 1.1))
      brighterAlpha = self.alpha
      brighterColor = Color(brighterRed, brighterGreen, brighterBlue, brighterAlpha)
      return brighterColor

   def darker(self):
      """Return a darker version of the color.

      The original color is left unchanged.

      Returns:
          darkerColor (Color): A new color, darker than this one.
      """
      darkerRed   = min(255, int(self.red * 0.9))
      darkerGreen = min(255, int(self.green * 0.9))
      darkerBlue  = min(255, int(self.blue * 0.9))
      darkerAlpha = self.alpha
      darkerColor = Color(darkerRed, darkerGreen, darkerBlue, darkerAlpha)
      return darkerColor

   @staticmethod
   def select(red=255, green=255, blue=255):
      """Open a color-selection dialog and return the color the user picks.

      Color.select is a static utility. Call it on the class itself, for example
      Color.select().

      Args:
          red (int, optional): The red component the dialog starts on, from 0 to 255.
          green (int, optional): The green component the dialog starts on, from 0 to 255.
          blue (int, optional): The blue component the dialog starts on, from 0 to 255.

      Returns:
          red (int): The chosen red component, from 0 to 255.
          green (int): The chosen green component, from 0 to 255.
          blue (int): The chosen blue component, from 0 to 255.
      """
      red, green, blue = _handler().sendQuery('colorDialog', None, {'initial': [red, green, blue, 255]})
      return red, green, blue

   @staticmethod
   def HSBtoRGB(hue, saturation, brightness):
      """Convert a color from HSB (hue, saturation, brightness) to RGB.

      Color.HSBtoRGB is a static utility. Call it on the class itself, for example
      Color.HSBtoRGB(). Values outside 0.0 to 1.0 are clamped to that range.

      Args:
          hue (float): The hue, from 0.0 to 1.0.
          saturation (float): The saturation, from 0.0 to 1.0.
          brightness (float): The brightness, from 0.0 to 1.0.

      Returns:
          red (int): The red component, from 0 to 255.
          green (int): The green component, from 0 to 255.
          blue (int): The blue component, from 0 to 255.
      """
      import colorsys
      
      # clamp HSB to 0.0 - 1.0
      hue        = max(0.0, min(1.0, hue))
      saturation = max(0.0, min(1.0, saturation))
      brightness = max(0.0, min(1.0, brightness))
      
      # convert HSB to RGB
      red, green, blue = colorsys.hsv_to_rgb(hue, saturation, brightness)
      
      # convert RGB to 0 - 255
      red   = int(red * 255)
      green = int(green * 255)
      blue  = int(blue * 255)
      
      return red, green, blue

   @staticmethod
   def RGBtoHSB(red, green, blue):
      """Convert a color from RGB to HSB (hue, saturation, brightness).

      Color.RGBtoHSB is a static utility. Call it on the class itself, for example
      Color.RGBtoHSB().

      Args:
          red (int): The red component, from 0 to 255.
          green (int): The green component, from 0 to 255.
          blue (int): The blue component, from 0 to 255.

      Returns:
          hue (float): The hue, from 0.0 to 1.0.
          saturation (float): The saturation, from 0.0 to 1.0.
          brightness (float): The brightness, from 0.0 to 1.0.
      """
      import colorsys

      # convert RGB to 0.0 - 1.0
      red   = red / 255
      green = green / 255
      blue  = blue / 255

      # convert RGB to HSV
      hue, saturation, brightness = colorsys.rgb_to_hsv(red, green, blue)

      return hue, saturation, brightness

   @staticmethod
   def getHSBColor(hue, saturation, brightness):
      """Create a Color from HSB (hue, saturation, brightness) values.

      Color.getHSBColor is a static utility. Call it on the class itself, for example
      Color.getHSBColor().

      Args:
          hue (float): The hue, from 0.0 to 1.0.
          saturation (float): The saturation, from 0.0 to 1.0.
          brightness (float): The brightness, from 0.0 to 1.0.

      Returns:
          hsbColor (Color): The matching color.
      """
      red, green, blue = Color.HSBtoRGB(hue, saturation, brightness)
      hsbColor = Color(red, green, blue)
      return hsbColor

   @staticmethod
   def HextoRGB(hex):
      """Convert a hex color string to RGB.

      Color.HextoRGB is a static utility. Call it on the class itself, for example
      Color.HextoRGB(). The leading "#" is optional.

      Args:
          hex (str): A hex color string, for example "#ff8800".

      Returns:
          red (int): The red component, from 0 to 255.
          green (int): The green component, from 0 to 255.
          blue (int): The blue component, from 0 to 255.
      """
      hexCode = hex.lstrip('#')
      color   = []

      for i in [0, 2, 4]:
         # convert to base 10 integer
         hexValue = hexCode[i:i+2]
         rgbValue = int(hexValue, 16)
         color.append(rgbValue)

      red   = color[0]
      green = color[1]
      blue  = color[2]

      return red, green, blue

   @staticmethod
   def RGBtoHex(red, green, blue):
      """Convert red, green, and blue values to a hex color string.

      Color.RGBtoHex is a static utility. Call it on the class itself, for example
      Color.RGBtoHex().

      Args:
          red (int): The red component, from 0 to 255.
          green (int): The green component, from 0 to 255.
          blue (int): The blue component, from 0 to 255.

      Returns:
          hexCode (str): A hex color string, for example "#ff8800".
      """

      hexCode = "#"

      for color in [red, green, blue]:
         # convert to a two-digit base-16 string and append it
         hexCode += f"{color:02x}"

      return hexCode

   @staticmethod
   def getHexColor(hex):
      """Create a Color from a hex color string.

      Color.getHexColor is a static utility. Call it on the class itself, for example
      Color.getHexColor(). The leading "#" is optional.

      Args:
          hex (str): A hex color string, for example "#ff8800".

      Returns:
          hexColor (Color): The matching color.
      """
      red, green, blue = Color.HextoRGB(hex)
      hexColor = Color(red, green, blue)
      return hexColor

###### OKLab Gradient Interpolation
# Our color gradient logic is repurposed from David Koch's CITA / CSCI 284 code.
# His explanation of the program is preserved below:
#
# Notes:   \\\\\DAVID EXPLANATION/////
#        
#          WE WILL NOT HAVE GRAY IN BETWEEN YELLOW AND BLUE
#          this happens because Yellow is (225, 225, 0) and
#          Blue is (0, 0, 255) so in the middle they are gray (122, 122, 122)
#          (The above comment is describing a Standard RGB method (SRGB)
#          That is not how humans percieve light
#
#          What we want is a smooth brightness level
#          We have to convert SRBG to OKLab values then back to our traditional SRGB.
#
#          Convert RGB to Linear RGB (how light sort of works in real life/better for monitors)
#          to OKLab (the perceptual space) then blend and then
#          finally back to our RGB (which JythonMusic can read) for our number of columns.
#
#          The t variable later is used to smooth interpolation using a cosine curve.
#          (That specific calculation is recommended for any gradient calculation,
#          OKLab is just an extra step for a good digital gradient)
#          (AKA: Start and end smoothly)
#
#          What is LMS? The long, medium, and short cones in our eyes
#          OKLab simulates/needs it
#
#          TLDR:
#          We are going from SRGB to LRGB to LMS to OKLab and back
#          Each of them need the values from the previous
#
#          SRGB       - bad
#          Linear RGB - better
#          LMS        - human perception of color (gamma/brightness)
#          OKLab      - calculations to make it smooth for digital display
#
#
#          I did not come up with the calculations in documentation
#          I only brought them for my own program's "color correction"
#          I already have experience in OKLab before this assignment
#          through Gneiss Name's OKLab Minecraft world and personal projects
#          along with gamma correction calculations from 3D programs to photoshop
#
#          An amazing explanation of this digital problem by Gneiss Name:
#          https://youtu.be/nJlZT5AE9zY?si=Sr_JxHg9bcaFhtJu
#
#
#          \\\\\DOCUMENTATION/////
#
#          SRGB introduction:
#          https://en.wikipedia.org/wiki/SRGB#From_sRGB_to_CIE_XYZ
#
#          OKLab reference, taken from the author of OKLab, Björn Ottosson, 
#          and general calculations of smoothing taken from these two, public domain:
#          -------------------------------------------------
#          Björn Ottosson's code for computing linear values: 
#          https://bottosson.github.io/posts/colorwrong/#what-can-we-do%3F
#
#          Björn Ottosson's code for converting linear sRGB to OKLab
#          https://bottosson.github.io/posts/oklab/


   @staticmethod
   def _sRGBtoLinear(channel):
      """"""
      c = channel / 255.0

      if c <= 0.04045:       # is our color very dark?
         linear = c / 12.92  # yes, we don't need to modify it much -- it is close to linear light already
      else:                  # other colors need gamma correction          
         linear = ((c + 0.055) / 1.055) ** 2.4

      return linear

   @staticmethod
   def _linearToSRGB(linear):
      """"""
      if linear <= 0.0031308:  # is our color very dark?
         c = 12.92 * linear    # yes, we don't need to modify it much -- it is close to linear light already
      else:                    # other colors need gamma correction   
         c = 1.055 * (linear ** (1 / 2.4)) - 0.055

      # make sure color is within sRGB range
      channel = max(0.0, min(255.0, c * 255.0))

      return channel

   @staticmethod
   def _RGBtoOKLab(red, green, blue):
      """"""
      # convert RGB to linear light
      # linear blending looks more natural to our eyes
      r = Color._sRGBtoLinear(red)
      g = Color._sRGBtoLinear(green)
      b = Color._sRGBtoLinear(blue)

      # linear RGB -> LMS (long/medium/short cone response)
      # accounts for our percieved brightness of colors
      l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
      m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
      s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b

      # eyes perceive brightness non-linearly — cube root models that
      l = l ** (1/3)
      m = m ** (1/3)
      s = s ** (1/3)

      # LMS -> OKLab
      L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s  # lightness
      A = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s  # green/red
      B = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s  # blue/yellow

      return [L, A, B]

   @staticmethod
   def _OKLabtoRGB(L, A, B):
      """"""
      # OKLab -> LMS
      l = L + 0.3963377774 * A + 0.2158037573 * B
      m = L - 0.1055613458 * A - 0.0638541728 * B
      s = L - 0.0894841775 * A - 1.2914855480 * B

      # reverse the cube root
      l = l ** 3
      m = m ** 3
      s = s ** 3

      # LMS -> linear RGB
      r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
      g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
      b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s

      return [int(Color._linearToSRGB(r)),
              int(Color._linearToSRGB(g)),
              int(Color._linearToSRGB(b))]

   @staticmethod
   def gradient(startColor, endColor, steps):
      """Create a smooth run of colors blending from one color to another.

      The blend is computed in a perceptual color space, so the steps look evenly
      spaced to the eye. Color.gradient is a static utility. Call it on the class
      itself, for example Color.gradient(). Also available as colorGradient().

      Args:
          startColor (Color or list[int]): The starting color, as a Color or an [red, green, blue] list.
          endColor (Color or list[int]): The ending color, as a Color or an [red, green, blue] list.
          steps (int): How many colors to produce.

      Returns:
          gradientList (list[Color] or list[list[int]]): The blended colors. These are Color objects if you passed Color objects, otherwise [red, green, blue] lists.
      """
      from math import cos, pi

      # extract colors to RGB values
      if isinstance(startColor, Color):
         red1, green1, blue1 = startColor.getRGB()
      elif isinstance(startColor, (list, tuple)):
         red1, green1, blue1 = startColor
      else:
         raise ValueError(f"colorGradient(): startColor should be a Color object or [r,g,b] list (it was a {str(type(startColor))})")

      if isinstance(endColor, Color):
         red2, green2, blue2 = endColor.getRGB()
      elif isinstance(endColor, (list, tuple)):
         red2, green2, blue2 = endColor
      else:
         raise ValueError(f"colorGradient(): endColor should be a Color object or [r,g,b] list (it was a {str(type(endColor))})")

      # convert endpoints to OKLab
      L1, A1, B1 = Color._RGBtoOKLab(red1, green1, blue1)
      L2, A2, B2 = Color._RGBtoOKLab(red2, green2, blue2)

      # interpolate by steps
      gradientList = []
      for i in range(steps):
         # cosine smoothing — eases in/out at the endpoints
         t = i / steps
         t = (1 - cos(t * pi)) / 2

         L = L1 + (L2 - L1) * t
         A = A1 + (A2 - A1) * t
         B = B1 + (B2 - B1) * t

         gradientList.append(Color._OKLabtoRGB(L, A, B))

      # if input was Color objects (e.g., Color.RED), return Color objects
      # otherwise, keep as RGB lists (e.g., [255, 0, 0])
      if isinstance(startColor, Color):
         gradientList = [Color(rgb[0], rgb[1], rgb[2]) for rgb in gradientList]

      return gradientList

# alias colorGradient for backwards compatibility
colorGradient = Color.gradient

# Color constants, for convenience
Color.BLACK      = Color(  0,   0,   0)
Color.BLUE       = Color(  0,   0, 255)
Color.CYAN       = Color(  0, 255, 255)
Color.DARK_GRAY  = Color( 44,  44,  44)
Color.GRAY       = Color(128, 128, 128)
Color.GREEN      = Color(  0, 255,   0)
Color.LIGHT_GRAY = Color(211, 211, 211)
Color.MAGENTA    = Color(255,   0, 255)
Color.ORANGE     = Color(255, 165,   0)
Color.PINK       = Color(255, 192, 203)
Color.PURPLE     = Color(128,   0, 128)
Color.RED        = Color(255,   0,   0)
Color.WHITE      = Color(255, 255, 255)
Color.YELLOW     = Color(255, 255,   0)
Color.CLEAR      = Color(  0,   0,   0,   0)


########################################################################################
# Font
########################################################################################
class Font:
   """Represent a text font: a name, a style, and a size.

   Use a Font to set how text looks on a Label, Button, TextField, TextArea, or a
   drawn label, for example Font("Serif", Font.ITALIC, 16). The style is one of the
   constants Font.PLAIN, Font.BOLD, Font.ITALIC, or Font.BOLDITALIC.

   Args:
       name (str): The font name, for example "Serif", "Dialog", or "TimesRoman".
       style (tuple, optional): The text style, one of Font.PLAIN, Font.BOLD, Font.ITALIC, or Font.BOLDITALIC.
       size (int, optional): The point size. If left as the default, the standard size is used.
   """
   PLAIN      = (400, False)  # (Weight, Italic)
   BOLD       = (700, False)  # Weight values are from QtGui.QFont.Weight
   ITALIC     = (400, True)
   BOLDITALIC = (700, True)

   def __init__(self, name, style=PLAIN, size=-1):
      """"""
      self.name  = name
      self.style = style
      self.size  = size

   def __str__(self):
      return f'Font(name = "{self.getName()}", style = {self.getStyle()}, size = {self.getSize()}")'

   def __repr__(self):
      return str(self)

   def getName(self):
      """Return the font's name.

      Returns:
          name (str): The font name, for example "Serif".
      """
      name = self.name
      return name

   def setName(self, name):
      """Set the font's name.

      Args:
          name (str): The new font name, for example "Serif", "Dialog", or "TimesRoman".
      """
      self.name = name

   def getStyle(self):
      """Return the font's style.

      Returns:
          style (tuple): The text style, one of Font.PLAIN, Font.BOLD, Font.ITALIC, or Font.BOLDITALIC.
      """
      style = self.style
      return style

   def setStyle(self, style):
      """Set the font's style.

      Args:
          style (tuple): The new text style, one of Font.PLAIN, Font.BOLD, Font.ITALIC, or Font.BOLDITALIC.
      """
      self.style = style

   def getSize(self):
      """Return the font's point size.

      Returns:
          size (int): The point size.
      """
      size = self.size
      return size

   def setSize(self, size):
      """Set the font's point size.

      Args:
          size (int): The new point size.
      """
      self.size = size


#######################################################################################
# Interactable - items that can trigger events
#######################################################################################
class Interactable:
   """Provide the mouse and keyboard event handling shared by displays and drawable objects.

   Interactable is a base class. You do not create one yourself. A Display and every
   drawable object inherit its on… methods, which let you respond to the mouse and
   keyboard. Each on… method takes a function (a callback) that the system calls when
   that event happens; mouse callbacks receive the mouse position in display
   coordinates, where x increases to the right and y increases downward.
   """
   def __init__(self):
      self._objectId = _nextObjectId()
      self._actionList = {}

   def _registerCallback(self, eventType, action):
      """"""
      alreadyRegistered = eventType in self._actionList
      self._actionList[eventType] = action
      if not alreadyRegistered:
         _handler().registerEvent(self._objectId, eventType, action)

   def onMouseClick(self, action):
      """Set up a function to call when the mouse is clicked on this object.

      Args:
          action (Callable): The function to call; it receives two parameters, x and y, giving the mouse position in display coordinates.
      """
      self._registerCallback('mouseClick', action)

   def onMouseDown(self, action):
      """Set up a function to call when the mouse button is pressed on this object.

      Args:
          action (Callable): The function to call; it receives two parameters, x and y, giving the mouse position in display coordinates.
      """
      self._registerCallback('mouseDown', action)

   def onMouseUp(self, action):
      """Set up a function to call when the mouse button is released over this object.

      Args:
          action (Callable): The function to call; it receives two parameters, x and y, giving the mouse position in display coordinates.
      """
      self._registerCallback('mouseUp', action)

   def onMouseMove(self, action):
      """Set up a function to call when the mouse moves over this object.

      Args:
          action (Callable): The function to call; it receives two parameters, x and y, giving the mouse position in display coordinates.
      """
      self._registerCallback('mouseMove', action)

   def onMouseDrag(self, action):
      """Set up a function to call when the mouse is dragged over this object.

      A drag is moving the mouse while a button is held down.

      Args:
          action (Callable): The function to call; it receives two parameters, x and y, giving the mouse position in display coordinates.
      """
      self._registerCallback('mouseDrag', action)

   def onMouseEnter(self, action):
      """Set up a function to call when the mouse moves onto this object.

      Args:
          action (Callable): The function to call; it receives two parameters, x and y, giving the mouse position in display coordinates.
      """
      self._registerCallback('mouseEnter', action)

   def onMouseExit(self, action):
      """Set up a function to call when the mouse moves off this object.

      Args:
          action (Callable): The function to call; it receives two parameters, x and y, giving the mouse position in display coordinates.
      """
      self._registerCallback('mouseExit', action)

   def onKeyType(self, action):
      """Set up a function to call when a key is typed (pressed and released).

      Args:
          action (Callable): The function to call; it receives one parameter, the key typed as a string, for example "a", "A", "1", or "/". Upper and lower case are distinguished.
      """
      self._registerCallback('keyType', action)

   def onKeyDown(self, action):
      """Set up a function to call when a key is pressed down.

      Holding a key down may call the function repeatedly, at the keyboard's repeat rate.

      Args:
          action (Callable): The function to call; it receives one parameter, the virtual key code as an int, for example VK_SHIFT or VK_A.
      """
      self._registerCallback('keyDown', action)

   def onKeyUp(self, action):
      """Set up a function to call when a key is released.

      Args:
          action (Callable): The function to call; it receives one parameter, the virtual key code as an int, for example VK_SHIFT or VK_A.
      """
      self._registerCallback('keyUp', action)

#######################################################################################
class Display(Interactable):
   """Create a window to hold widgets and drawings.

   A Display is the window your GUI objects appear in. Build a GUI by adding shapes,
   images, text, and controls to it with add(). The window opens as soon as you create
   it. Inside the display the origin (0, 0) is the top-left corner; x increases to the
   right and y increases downward.

   Args:
       title (str, optional): The window title.
       width (int or float, optional): The window width, in pixels.
       height (int or float, optional): The window height, in pixels.
       x (int or float, optional): The horizontal position of the window's top-left corner on the screen, in pixels.
       y (int or float, optional): The vertical position of the window's top-left corner on the screen, in pixels.
       color (Color, optional): The background color.
   """

   def __init__(self, title='', width=600, height=400, x=0, y=50, color=Color.WHITE):
      """"""
      Interactable.__init__(self)

      # initialize internal properties
      self._itemList        = []     # list of items in this display (front=top)
      self._toolTipText     = None   # tooltip text for this display
      self._showCoordinates = False  # show mouse coordinates in tooltip?
      self._title           = title
      self._width           = width
      self._height          = height
      self._color           = color.getRGBA()

      # create display in the renderer child process
      _handler().sendCommand('create', self._objectId, {
         'type':   'Display',
         'title':  title,
         'width':  width,
         'height': height,
         'x':      x,
         'y':      y,
         'color':  color.getRGBA(),
      })

   def __str__(self):
      r, g, b, a = self._color
      return f'Display(title = "{self._title}", width = {self._width}, height = {self._height}, color = Color({r}, {g}, {b}, {a}))'

   def show(self):
      """Show the display.

      This happens automatically when a display is created, so you only need it after
      hide().
      """
      _handler().sendCommand('show', self._objectId)

   def hide(self):
      """Hide the display.

      Use show() to bring it back.
      """
      _handler().sendCommand('hide', self._objectId)

   def close(self):
      """Close the display.

      Before closing, calls the function set with onClose(), if any.
      """
      if 'onClose' in self._actionList:
         action = self._actionList['onClose']
         if callable(action):
            action()

      _handler().sendCommand('close', self._objectId)
      self.removeAll()

   def add(self, item, x=None, y=None):
      """Add a GUI object to the display at the given position.

      Aligns the object's top-left corner (for a Circle, its center) with (x, y), where
      (0, 0) is the display's top-left corner. An object can be on only one display at a
      time. Adding it here removes it from any display it was on. If x and y are left
      out, the object's current position is used.

      Args:
          item (Drawable): The GUI object to add.
          x (int or float, optional): The horizontal position, in pixels. Defaults to the object's current position.
          y (int or float, optional): The vertical position, in pixels. Defaults to the object's current position.
      """
      self.addOrder(item, 0, x, y)  # use logic from addOrder()

   def addOrder(self, item, order, x=None, y=None):
      """Add a GUI object to the display at the given position and layer.

      Same as add(), but also sets the object's layer. Layers run from smallest to
      largest, where 0 is closest to the front. If the object is already on another
      display, it is removed from there first.

      Args:
          item (Drawable): The GUI object to add.
          order (int): The layer to place the object on; 0 is closest to the front.
          x (int or float, optional): The horizontal position, in pixels. Defaults to the object's current position.
          y (int or float, optional): The vertical position, in pixels. Defaults to the object's current position.
      """
      if not isinstance(item, Drawable):
         raise TypeError(f'{type(self).__name__}.addOrder(): item should be a Drawable object (it was {type(item).__name__})')

      # remember where the item appears now, so it keeps its rotation, scale, and
      # position on screen as it moves onto this Display
      itemOnScreen = item._getSceneMatrix()
      # take the item out of whatever Group or Display currently holds it
      currentParent = item.getGroup()
      if currentParent is None:
         currentParent = item.getDisplay()
      if currentParent is not None:
         currentParent.remove(item)
      item._parent = self
      item._bakeReparent(itemOnScreen, np.identity(3))   # a Display anchors the chain

      # place the item at the requested drawing order
      order = max(0, min(len(self._itemList), order))
      self._itemList.insert(order, item)

      # mirror the addition in the renderer (its placement is sent separately)
      _handler().sendCommand('addOrder', self._objectId, {
         'itemId': item._objectId,
         'order':  order,
      })

      # if the caller gave an explicit position, it replaces the remembered one
      if x is not None or y is not None:
         currentX, currentY = item.getPosition()
         item.setPosition(x if x is not None else currentX, y if y is not None else currentY)

   def remove(self, item):
      """Remove a GUI object from the display.

      Args:
          item (Drawable): The GUI object to remove.
      """
      if item in self._itemList:
         item._parent = None
         self._itemList.remove(item)
         _handler().sendCommand('remove', self._objectId, {
            'itemId': item._objectId,
         })

   def removeAll(self):
      """Remove every GUI object from the display.

      A quick way to clear the display.
      """
      for item in list(self._itemList):
         item._parent = None
      self._itemList.clear()
      _handler().sendCommand('removeAll', self._objectId)

   def move(self, item, x, y):
      """Move a GUI object to a new position on the display.

      Args:
          item (Drawable): The GUI object to move.
          x (int or float): The new horizontal position, in pixels.
          y (int or float): The new vertical position, in pixels.
      """
      if item in self._itemList:  # skip if item not on Display
         item.setPosition(x, y)   # move item

   def getOrder(self, item):
      """Return the layer a GUI object sits on.

      Args:
          item (Drawable): The GUI object to look up.

      Returns:
          order (int): The object's layer, where 0 is closest to the front; None if the object is not on the display.
      """
      order = None
      if item in self._itemList:  # skip if item not on Display
         order = self._itemList.index(item)
      return order

   def setOrder(self, item, order):
      """Move a GUI object to a different layer.

      Layers run from smallest to largest, where 0 is closest to the front. Does nothing
      if the object is not on the display.

      Args:
          item (Drawable): The GUI object to re-layer.
          order (int): The layer to move it to; 0 is closest to the front.
      """
      if item in self._itemList:  # skip if item not on Display
         self.addOrder(item, order)  # remove and re-add item at desired order

   def setToolTipText(self, text=None):
      """Set the hover text shown over the display.

      Args:
          text (str, optional): The tooltip text. If omitted, the tooltip is cleared.
      """
      self._toolTipText = text
      _handler().sendCommand('setToolTipText', self._objectId, {'text': text})

   def showMouseCoordinates(self):
      """Show the mouse position in the display's tooltip as the mouse moves.

      Handy while building a GUI, for finding the coordinates to place widgets at.
      """
      self._showCoordinates = True
      _handler().sendCommand('showMouseCoordinates', self._objectId)

   def hideMouseCoordinates(self):
      """Stop showing the mouse position in the display's tooltip.

      Restores any tooltip behavior that was in place before showMouseCoordinates().
      """
      self._showCoordinates = False
      _handler().sendCommand('hideMouseCoordinates', self._objectId)

   def getColor(self):
      """Return the display's background color.

      Returns:
          color (Color): The current background color.
      """
      color = Color(*self._color)
      return color

   def setColor(self, color=None):
      """Set the display's background color.

      Args:
          color (Color, optional): The new background color, for example Color.RED. If omitted, a color-selection dialog opens.
      """
      if color is None:
         r, g, b = Color.select()
         color = Color(r, g, b)

      if isinstance(color, Color):
         r, g, b, a = color.getRGBA()
      else:
         raise TypeError(f'{type(self).__name__}.setColor(): color should be a Color object (it was {type(color).__name__})')

      self._color = [r, g, b, a]
      _handler().sendCommand('setColor', self._objectId, {'color': [r, g, b, a]})

   def getTitle(self):
      """Return the display's title.

      Returns:
          title (str): The window title.
      """
      title = self._title
      return title

   def setTitle(self, title):
      """Set the display's title.

      Args:
          title (str): The new window title.
      """
      self._title = title
      _handler().sendCommand('setTitle', self._objectId, {'title': title})

   def getWidth(self):
      """Return the display's width.

      Returns:
          width (int or float): The width, in pixels.
      """
      width, _ = self.getSize()
      return width

   def setWidth(self, width):
      """Set the display's width.

      Args:
          width (int or float): The new width, in pixels.
      """
      self.setSize(width, self.getHeight())

   def getHeight(self):
      """Return the display's height.

      Returns:
          height (int or float): The height, in pixels.
      """
      _, height = self.getSize()
      return height

   def setHeight(self, height):
      """Set the display's height.

      Args:
          height (int or float): The new height, in pixels.
      """
      self.setSize(self.getWidth(), height)

   def getSize(self):
      """Return the display's width and height.

      Returns:
          width (int or float): The width, in pixels.
          height (int or float): The height, in pixels.
      """
      width  = self._width
      height = self._height
      return width, height

   def setSize(self, width, height):
      """Set the display's width and height.

      Args:
          width (int or float): The new width, in pixels.
          height (int or float): The new height, in pixels.
      """
      if (width <= 0) or (height <= 0):
         print(f"{type(self).__name__}.setSize(): width and height should be positive, non-zero integers (they were {width} and {height}).")
      else:
         self._width  = width
         self._height = height
         _handler().sendCommand('setSize', self._objectId, {'width': width, 'height': height})

   def _setScrollable(self, sceneWidth, sceneHeight):
      """"""
      _handler().sendCommand('setScrollable', self._objectId,
                             {'sceneWidth': sceneWidth, 'sceneHeight': sceneHeight})

   def getPosition(self):
      """Return the display's position on the screen.

      Returns:
          x (int or float): The horizontal position of the window's top-left corner, in pixels.
          y (int or float): The vertical position of the window's top-left corner, in pixels.
      """
      result = _handler().sendQuery('getPosition', self._objectId)
      x, y = result
      return x, y

   def setPosition(self, x, y):
      """Set the display's position on the screen.

      The screen origin (0, 0) is at the top-left.

      Args:
          x (int or float): The new horizontal position of the window's top-left corner, in pixels.
          y (int or float): The new vertical position of the window's top-left corner, in pixels.
      """
      _handler().sendCommand('setPosition', self._objectId, {'x': int(x), 'y': int(y)})

   def getX(self):
      """Return the display's horizontal position on the screen.

      Returns:
          x (int or float): The horizontal position of the window's top-left corner, in pixels.
      """
      # updates to getPosition() automatically update how this method works
      x, _ = self.getPosition()
      return x

   def setX(self, x):
      """Set the display's horizontal position on the screen.

      Args:
          x (int or float): The new horizontal position of the window's top-left corner, in pixels.
      """
      # updates to setPosition() automatically update how this method works
      self.setPosition(x, self.getY())

   def getY(self):
      """Return the display's vertical position on the screen.

      Returns:
          y (int or float): The vertical position of the window's top-left corner, in pixels.
      """
      # updates to getPosition() automatically update how this method works
      _, y = self.getPosition()
      return y

   def setY(self, y):
      """Set the display's vertical position on the screen.

      Args:
          y (int or float): The new vertical position of the window's top-left corner, in pixels.
      """
      # updates to setPosition() automatically update how this method works
      self.setPosition(self.getX(), y)

   def getCenter(self):
      """Return the center point of the display's canvas.

      The center is the canvas width divided by two and the canvas height divided by two,
      measured from the top-left corner (0, 0).

      Returns:
          centerX (int or float): The horizontal position of the canvas center, in pixels.
          centerY (int or float): The vertical position of the canvas center, in pixels.
      """
      width, height = self.getSize()
      centerX = width / 2
      centerY = height / 2
      return centerX, centerY

   def getCenterX(self):
      """Return the horizontal center of the display's canvas.

      Returns:
          x (int or float): The horizontal position of the canvas center, in pixels.
      """
      # updates to getCenter() automatically update how this method works
      x, _ = self.getCenter()
      return x

   def getCenterY(self):
      """Return the vertical center of the display's canvas.

      Returns:
          y (int or float): The vertical position of the canvas center, in pixels.
      """
      # updates to getCenter() automatically update how this method works
      _, y = self.getCenter()
      return y

   def getItems(self):
      """Return the GUI objects currently on the display.

      Returns:
          itemList (list[Drawable]): A copy of the list of objects on the display.
      """
      itemList = list(self._itemList)  # make a second list, but keeps the same items
      return itemList

   def addMenu(self, menu):
      """Add a menu to the display's menu bar.

      Menus appear left to right along the top of the display, for example "File" then
      "Edit".

      Args:
          menu (Menu): The menu to add.
      """
      if not isinstance(menu, Menu):
         raise TypeError(f'{type(self).__name__}.addMenu(): menu should be a Menu object (it was {type(menu).__name__})')
      _handler().sendCommand('addMenu', self._objectId, {'menuId': menu._objectId})

   def addPopupMenu(self, menu):
      """Add a pop-up (right-click) menu to the display.

      Args:
          menu (Menu): The menu to show when the user right-clicks the display.
      """
      if not isinstance(menu, Menu):
         raise TypeError(f'{type(self).__name__}.addPopupMenu(): menu should be a Menu object (it was {type(menu).__name__})')
      _handler().sendCommand('addPopupMenu', self._objectId, {'menuId': menu._objectId})

   def save(self, filename, width=None, height=None):
      """Save a picture of the display to an image file.

      Args:
          filename (str): The file to write, ending in ".jpg" or ".png".
          width (int or float, optional): The width of the saved image, in pixels. Defaults to the display's width.
          height (int or float, optional): The height of the saved image, in pixels. Defaults to the display's height.
      """
      result = _handler().sendQuery('write', self._objectId, {'filename': filename, 'width': width, 'height': height})
      success, resolvedPath = result[0], result[1]
      if success:
         print(f'{type(self).__name__}.save(): saved canvas to "{resolvedPath}"')
      else:
         print(f'{type(self).__name__}.save(): failed to save to "{resolvedPath}"')

   def onClose(self, action):
      """Set up a function to call right before the display closes.

      Called whether the display is closed with the mouse, the keyboard, or close(). Use
      it to clean up, play a sound, update other displays, and so on.

      Args:
          action (Callable): The function to call; it receives no parameters.
      """
      self._actionList['displayClose'] = action

   # ── Draw Methods ────────────────────────────────────────────────────────────────
   # These methods draw a shape directly to the canvas without returning an object.
   # Since there's no object to manage, these methods are very fast to render, and are
   # ideal for drawing shapes that you don't intend on altering later.

   def clearDrawing(self):
      """Erase everything drawn with the draw… methods.

      This clears the shapes drawn by drawRectangle(), drawLine(), and the other draw…
      methods. GUI objects added with add() are not affected.
      """
      _handler().sendCommand('clearDrawing', self._objectId)

   def drawRectangle(self, x1, y1, x2, y2, color=Color.BLACK, fill=False, thickness=1, rotation=0, visibility=100):
      """Draw a rectangle straight onto the display.

      This draws to the canvas and returns nothing, which is fast and best for shapes you
      will not change later. To keep a handle you can move or delete, create a Rectangle
      and add() it instead. Erase these drawings with clearDrawing().

      Args:
          x1 (int or float): The horizontal position of the top-left corner, in pixels.
          y1 (int or float): The vertical position of the top-left corner, in pixels.
          x2 (int or float): The horizontal position of the bottom-right corner, in pixels.
          y2 (int or float): The vertical position of the bottom-right corner, in pixels.
          color (Color, optional): The color.
          fill (bool, optional): Whether the rectangle is filled in (True) or just an outline (False).
          thickness (int, optional): The outline thickness, in pixels.
          rotation (int or float, optional): How far to turn the rectangle, in degrees, counter-clockwise.
          visibility (int, optional): How visible the rectangle is, from 0 (invisible) to 100 (fully visible).
      """
      _handler().sendCommand('draw', self._objectId, {
         'shape':      'rectangle',
         'x':          min(x1, x2),
         'y':          min(y1, y2),
         'width':      abs(x1 - x2),
         'height':     abs(y1 - y2),
         'color':      color.getRGBA(),
         'fill':       bool(fill),
         'thickness':  int(thickness),
         'rotation':   rotation,
         'visibility': visibility,
      })

   def drawOval(self, x1, y1, x2, y2, color=Color.BLACK, fill=False, thickness=1, rotation=0, visibility=100):
      """Draw an oval straight onto the display.

      The oval fills the box with corners (x1, y1) and (x2, y2). This draws to the canvas
      and returns nothing, which is fast and best for shapes you will not change later. To
      keep a handle you can move or delete, create an Oval and add() it instead. Erase
      these drawings with clearDrawing().

      Args:
          x1 (int or float): The horizontal position of the box's top-left corner, in pixels.
          y1 (int or float): The vertical position of the box's top-left corner, in pixels.
          x2 (int or float): The horizontal position of the box's bottom-right corner, in pixels.
          y2 (int or float): The vertical position of the box's bottom-right corner, in pixels.
          color (Color, optional): The color.
          fill (bool, optional): Whether the oval is filled in (True) or just an outline (False).
          thickness (int, optional): The outline thickness, in pixels.
          rotation (int or float, optional): How far to turn the oval, in degrees, counter-clockwise.
          visibility (int, optional): How visible the oval is, from 0 (invisible) to 100 (fully visible).
      """
      _handler().sendCommand('draw', self._objectId, {
         'shape':      'oval',
         'x':          min(x1, x2),
         'y':          min(y1, y2),
         'width':      abs(x1 - x2),
         'height':     abs(y1 - y2),
         'color':      color.getRGBA(),
         'fill':       bool(fill),
         'thickness':  int(thickness),
         'rotation':   rotation,
         'visibility': visibility,
      })

   def drawCircle(self, x, y, radius, color=Color.BLACK, fill=False, thickness=1, visibility=100):
      """Draw a circle straight onto the display.

      This draws to the canvas and returns nothing, which is fast and best for shapes you
      will not change later. To keep a handle you can move or delete, create a Circle and
      add() it instead. Erase these drawings with clearDrawing().

      Args:
          x (int or float): The horizontal position of the center, in pixels.
          y (int or float): The vertical position of the center, in pixels.
          radius (int or float): The radius, in pixels.
          color (Color, optional): The color.
          fill (bool, optional): Whether the circle is filled in (True) or just an outline (False).
          thickness (int, optional): The outline thickness, in pixels.
          visibility (int, optional): How visible the circle is, from 0 (invisible) to 100 (fully visible).
      """
      diameter = radius * 2
      _handler().sendCommand('draw', self._objectId, {
         'shape':      'circle',
         'x':          x - radius,
         'y':          y - radius,
         'width':      diameter,
         'height':     diameter,
         'color':      color.getRGBA(),
         'fill':       bool(fill),
         'thickness':  int(thickness),
         'rotation':   0,
         'visibility': visibility,
      })

   def drawPoint(self, x, y, color=Color.BLACK, visibility=100):
      """Draw a single point straight onto the display.

      This draws to the canvas and returns nothing, which is fast and best for shapes you
      will not change later. To keep a handle you can move or delete, create a Point and
      add() it instead. Erase these drawings with clearDrawing().

      Args:
          x (int or float): The horizontal position, in pixels.
          y (int or float): The vertical position, in pixels.
          color (Color, optional): The color.
          visibility (int, optional): How visible the point is, from 0 (invisible) to 100 (fully visible).
      """
      _handler().sendCommand('draw', self._objectId, {
         'shape':      'point',
         'x':          x - 1,
         'y':          y - 1,
         'width':      2,
         'height':     2,
         'color':      color.getRGBA(),
         'fill':       True,
         'thickness':  1,
         'rotation':   0,
         'visibility': visibility,
      })

   def drawArc(self, x1, y1, x2, y2, startAngle=PI, endAngle=TWO_PI, style=OPEN, color=Color.BLACK, fill=False, thickness=1, rotation=0, visibility=100):
      """Draw an arc straight onto the display.

      The arc is part of the oval that fills the box with corners (x1, y1) and (x2, y2).
      Angles are in degrees, with 0 at the three o'clock position; a positive angle goes
      counter-clockwise, a negative one clockwise. The constants HALF_PI, PI, and TWO_PI
      may be used for the angles. This draws to the canvas and returns nothing, which is fast and best for shapes you will not change later. To keep a handle you can move
      or delete, create an Arc and add() it instead. Erase these drawings with
      clearDrawing().

      Args:
          x1 (int or float): The horizontal position of the box's top-left corner, in pixels.
          y1 (int or float): The vertical position of the box's top-left corner, in pixels.
          x2 (int or float): The horizontal position of the box's bottom-right corner, in pixels.
          y2 (int or float): The vertical position of the box's bottom-right corner, in pixels.
          startAngle (int or float, optional): The starting angle, in degrees.
          endAngle (int or float, optional): The ending angle, in degrees.
          style (int, optional): The arc style, one of OPEN (an open arc), CHORD (closed with a straight line between the ends), or PIE (closed with two lines to the center).
          color (Color, optional): The color.
          fill (bool, optional): Whether the arc is filled in (True) or just an outline (False).
          thickness (int, optional): The outline thickness, in pixels.
          rotation (int or float, optional): How far to turn the arc, in degrees, counter-clockwise.
          visibility (int, optional): How visible the arc is, from 0 (invisible) to 100 (fully visible).
      """
      _handler().sendCommand('draw', self._objectId, {
         'shape':      'arc',
         'x':          min(x1, x2),
         'y':          min(y1, y2),
         'width':      abs(x1 - x2),
         'height':     abs(y1 - y2),
         'startAngle': startAngle,
         'endAngle':   endAngle,
         'style':      style,
         'color':      color.getRGBA(),
         'fill':       bool(fill),
         'thickness':  int(thickness),
         'rotation':   rotation,
         'visibility': visibility,
      })

   def drawArcCircle(self, x, y, radius, startAngle=PI, endAngle=TWO_PI, style=OPEN, color=Color.BLACK, fill=False, thickness=1, rotation=0, visibility=100):
      """Draw a circular arc straight onto the display.

      Like drawArc(), but the arc is part of a circle given by its center and radius.
      Angles are in degrees, with 0 at the three o'clock position; a positive angle goes
      counter-clockwise, a negative one clockwise. The constants HALF_PI, PI, and TWO_PI
      may be used for the angles. This draws to the canvas and returns nothing, which is fast and best for shapes you will not change later. To keep a handle you can move
      or delete, create an ArcCircle and add() it instead. Erase these drawings with
      clearDrawing().

      Args:
          x (int or float): The horizontal position of the center, in pixels.
          y (int or float): The vertical position of the center, in pixels.
          radius (int or float): The radius, in pixels.
          startAngle (int or float, optional): The starting angle, in degrees.
          endAngle (int or float, optional): The ending angle, in degrees.
          style (int, optional): The arc style, one of OPEN (an open arc), CHORD (closed with a straight line between the ends), or PIE (closed with two lines to the center).
          color (Color, optional): The color.
          fill (bool, optional): Whether the arc is filled in (True) or just an outline (False).
          thickness (int, optional): The outline thickness, in pixels.
          rotation (int or float, optional): How far to turn the arc, in degrees, counter-clockwise.
          visibility (int, optional): How visible the arc is, from 0 (invisible) to 100 (fully visible).
      """
      diameter = radius * 2
      _handler().sendCommand('draw', self._objectId, {
         'shape':      'arc',
         'x':          x - radius,
         'y':          y - radius,
         'width':      diameter,
         'height':     diameter,
         'startAngle': startAngle,
         'endAngle':   endAngle,
         'style':      style,
         'color':      color.getRGBA(),
         'fill':       bool(fill),
         'thickness':  int(thickness),
         'rotation':   rotation,
         'visibility': visibility,
      })

   def drawPolyline(self, xPoints, yPoints, color=Color.BLACK, thickness=1, rotation=0, visibility=100):
      """Draw a connected series of line segments straight onto the display.

      The xPoints and yPoints lists are parallel: the first corner is (xPoints[0],
      yPoints[0]), the next is (xPoints[1], yPoints[1]), and so on. This draws to the
      canvas and returns nothing, which is fast and best for shapes you will not change
      later. To keep a handle you can move or delete, create a Polyline and add() it
      instead. Erase these drawings with clearDrawing().

      Args:
          xPoints (list[int or float]): The horizontal positions of the corners, in pixels.
          yPoints (list[int or float]): The vertical positions of the corners, in pixels.
          color (Color, optional): The color.
          thickness (int, optional): The line thickness, in pixels.
          rotation (int or float, optional): How far to turn the shape, in degrees, counter-clockwise.
          visibility (int, optional): How visible the shape is, from 0 (invisible) to 100 (fully visible).
      """
      _handler().sendCommand('draw', self._objectId, {
         'shape':      'polyline',
         'xPoints':    list(xPoints),
         'yPoints':    list(yPoints),
         'color':      color.getRGBA(),
         'thickness':  int(thickness),
         'rotation':   rotation,
         'visibility': visibility,
      })

   def drawLine(self, x1, y1, x2, y2, color=Color.BLACK, thickness=1, rotation=0, visibility=100):
      """Draw a line straight onto the display.

      This draws to the canvas and returns nothing, which is fast and best for shapes you
      will not change later. To keep a handle you can move or delete, create a Line and
      add() it instead. Erase these drawings with clearDrawing().

      Args:
          x1 (int or float): The horizontal position of one end, in pixels.
          y1 (int or float): The vertical position of one end, in pixels.
          x2 (int or float): The horizontal position of the other end, in pixels.
          y2 (int or float): The vertical position of the other end, in pixels.
          color (Color, optional): The color.
          thickness (int, optional): The line thickness, in pixels.
          rotation (int or float, optional): How far to turn the line, in degrees, counter-clockwise.
          visibility (int, optional): How visible the line is, from 0 (invisible) to 100 (fully visible).
      """
      _handler().sendCommand('draw', self._objectId, {
         'shape':      'line',
         'x1':         x1,
         'y1':         y1,
         'x2':         x2,
         'y2':         y2,
         'color':      color.getRGBA(),
         'thickness':  int(thickness),
         'rotation':   rotation,
         'visibility': visibility,
      })

   def drawPolygon(self, xPoints, yPoints, color=Color.BLACK, fill=False, thickness=1, rotation=0, visibility=100):
      """Draw a polygon straight onto the display.

      The xPoints and yPoints lists are parallel: the first corner is (xPoints[0],
      yPoints[0]), the next is (xPoints[1], yPoints[1]), and so on. This draws to the
      canvas and returns nothing, which is fast and best for shapes you will not change
      later. To keep a handle you can move or delete, create a Polygon and add() it
      instead. Erase these drawings with clearDrawing().

      Args:
          xPoints (list[int or float]): The horizontal positions of the corners, in pixels.
          yPoints (list[int or float]): The vertical positions of the corners, in pixels.
          color (Color, optional): The color.
          fill (bool, optional): Whether the polygon is filled in (True) or just an outline (False).
          thickness (int, optional): The outline thickness, in pixels.
          rotation (int or float, optional): How far to turn the polygon, in degrees, counter-clockwise.
          visibility (int, optional): How visible the polygon is, from 0 (invisible) to 100 (fully visible).
      """
      _handler().sendCommand('draw', self._objectId, {
         'shape':      'polygon',
         'xPoints':    list(xPoints),
         'yPoints':    list(yPoints),
         'color':      color.getRGBA(),
         'fill':       bool(fill),
         'thickness':  int(thickness),
         'rotation':   rotation,
         'visibility': visibility,
      })

   def drawIcon(self, filename, x, y, width=None, height=None, rotation=0, visibility=100):
      """Draw an image straight onto the display.

      This draws to the canvas and returns nothing, which is fast and best for images you
      will not change later. To keep a handle you can move or delete, create an Icon and
      add() it instead. Erase these drawings with clearDrawing().

      Args:
          filename (str): The image file to load, ending in ".jpg" or ".png".
          x (int or float): The horizontal position of the top-left corner, in pixels.
          y (int or float): The vertical position of the top-left corner, in pixels.
          width (int or float, optional): The width to scale the image to, in pixels. Defaults to the image's own width.
          height (int or float, optional): The height to scale the image to, in pixels. Defaults to the image's own height.
          rotation (int or float, optional): How far to turn the image, in degrees, counter-clockwise.
          visibility (int, optional): How visible the image is, from 0 (invisible) to 100 (fully visible).
      """
      _handler().sendCommand('draw', self._objectId, {
         'shape':      'icon',
         'filename':   filename,
         'x':          x,
         'y':          y,
         'width':      width,
         'height':     height,
         'rotation':   rotation,
         'visibility': visibility,
      })

   def drawLabel(self, text, x, y, color=Color.BLACK, font=None, visibility=100):
      """Draw a line of text straight onto the display.

      This draws to the canvas and returns nothing, which is fast and best for text you
      will not change later. To keep a handle you can move or delete, create a Label and
      add() it instead. Erase these drawings with clearDrawing().

      Args:
          text (str): The text to draw.
          x (int or float): The horizontal position of the top-left corner, in pixels.
          y (int or float): The vertical position of the top-left corner, in pixels.
          color (Color, optional): The text color.
          font (Font, optional): The font, for example Font("Serif", Font.ITALIC, 16). If omitted, the default font is used.
          visibility (int, optional): How visible the text is, from 0 (invisible) to 100 (fully visible).
      """
      fontData = None
      if isinstance(font, Font):
         fontData = [font.getName(), font.getStyle(), font.getSize()]

      _handler().sendCommand('draw', self._objectId, {
         'shape':      'label',
         'text':       str(text),
         'x':          x,
         'y':          y,
         'color':      color.getRGBA(),
         'font':       fontData,
         'visibility': visibility,
      })

   # ── Compatibility Aliases ─────────────────────────────────────────────────────────

   def drawText(self, text, x, y, color=Color.BLACK, font=None, visibility=100):
      """Draw a line of text straight onto the display.

      Same as drawLabel().

      Args:
          text (str): The text to draw.
          x (int or float): The horizontal position of the top-left corner, in pixels.
          y (int or float): The vertical position of the top-left corner, in pixels.
          color (Color, optional): The text color.
          font (Font, optional): The font, for example Font("Serif", Font.ITALIC, 16). If omitted, the default font is used.
          visibility (int, optional): How visible the text is, from 0 (invisible) to 100 (fully visible).
      """
      self.drawLabel(text, x, y, color, font, visibility)


#######################################################################################
# Drawable - items that can be added to a Display
#######################################################################################
# Coordinate spaces and the scene graph
#######################################################################################
# Drawables are positioned in scene coordinates - where they sit on the Display the
# user can see.  Internally, though, each Drawable only remembers its placement
# relative to its parent (a Group, or the Display itself).  This keeps grouped items
# simple: moving or turning a Group just changes the Group's own placement and its
# children follow along, instead of every child having to be rewritten.
#
# To turn a parent-relative placement into a final on-screen placement, we combine each
# placement with its parent's, all the way up to the Display.  The helper functions
# below carry out that combining math so the rest of the file can work in terms of
# whole placements rather than the arithmetic behind them.
#
# ──────────────────────────────────────────────────────────────────────────────────
# TECHNICAL NOTE - affine transforms (for maintainers extending this math)
#
# A placement is stored as a 3x3 affine matrix that maps a local point to a point in
# the parent's space:
#
#       | a  b  tx |   | x |
#       | c  d  ty | . | y |
#       | 0  0   1 |   | 1 |
#
# The (tx, ty) column is the translation (the item's center); the (a b / c d) block is
# the combined rotation and scale.  Two placements combine by multiplying their
# matrices, so an item's on-screen placement is the product of every placement from the
# item up to the Display.  Our angles are CCW-positive in a y-down space - the opposite
# sense from the matrix's natural direction - so an angle is negated when it goes into a
# matrix and negated again when it is read back out.
# ──────────────────────────────────────────────────────────────────────────────────

def _affineMatrix(centerX, centerY, rotationDegrees, scaleX, scaleY):
   """"""
   # negate the angle so a positive (CCW) rotation comes out correctly in y-down space
   radians = np.radians(-rotationDegrees)
   cosine  = np.cos(radians)
   sine    = np.sin(radians)
   matrix  = np.array([
      [cosine * scaleX, -sine * scaleY, centerX],
      [sine   * scaleX,  cosine * scaleY, centerY],
      [              0,                0,        1],
   ], dtype=float)
   return matrix

def _matrixRotation(matrix):
   """"""
   # the matrix's first column is where the item's local x-axis points once placed; the
   # angle of that direction is the rotation, negated back into our convention
   mappedAxisX = matrix[0, 0]
   mappedAxisY = matrix[1, 0]
   rotationDegrees = np.degrees(np.arctan2(-mappedAxisY, mappedAxisX))
   return float(rotationDegrees)

def _decomposeAffine(matrix):
   """"""
   # matrix entries, named by their position; see the technical note above
   topLeft     = matrix[0, 0]
   topRight    = matrix[0, 1]
   bottomLeft  = matrix[1, 0]
   bottomRight = matrix[1, 1]

   centerX = float(matrix[0, 2])
   centerY = float(matrix[1, 2])
   rotationDegrees = _matrixRotation(matrix)

   # each scale is the length of its column in the rotation-and-scale block
   scaleX = float(np.hypot(topLeft, bottomLeft))
   scaleY = float(np.hypot(topRight, bottomRight))

   # a negative determinant means the placement mirrors the item, so carry that mirror
   # through on one axis
   determinant = topLeft * bottomRight - topRight * bottomLeft
   if determinant < 0:
      scaleY = -scaleY

   return centerX, centerY, rotationDegrees, scaleX, scaleY

# ──────────────────────────────────────────────────────────────────────────────────
# TECHNICAL NOTE - testing whether outlines contain a point or overlap
#
# A point is inside a convex outline when it stays on the same side of every edge,
# walking the edges in order.  "Side" is the sign of the 2D cross product of an edge
# with the line from the edge's start to the point.
#
# Two convex outlines overlap unless some line can be drawn between them.  It is enough
# to test the directions square-on to each outline's edges: if the two outlines, cast
# down onto any one of those directions, leave a gap, they cannot be touching.
# ──────────────────────────────────────────────────────────────────────────────────

def _pointInConvexPolygon(pointX, pointY, xPoints, yPoints):
   """"""
   isInside     = True   # holds only while the point is on the same side of every edge
   requiredSide = 0      # the side the first edge put the point on; 0 until that is known
   cornerCount  = len(xPoints)

   for index in range(cornerCount):
      nextIndex = (index + 1) % cornerCount
      startX = xPoints[index]
      startY = yPoints[index]
      endX   = xPoints[nextIndex]
      endY   = yPoints[nextIndex]

      # which side of this edge the point falls on (positive, negative, or right on it)
      edgeCross = (endX - startX) * (pointY - startY) - (endY - startY) * (pointX - startX)

      if edgeCross != 0:
         pointSide = 1 if edgeCross > 0 else -1
         if requiredSide == 0:
            requiredSide = pointSide        # the first edge fixes the side the rest must share
         elif pointSide != requiredSide:
            isInside = False                # a different side means the point is outside

   return isInside

def _projectionRange(axisX, axisY, xPoints, yPoints):
   """"""
   smallest = None
   largest  = None
   for index in range(len(xPoints)):
      distance = axisX * xPoints[index] + axisY * yPoints[index]
      if smallest is None or distance < smallest:
         smallest = distance
      if largest is None or distance > largest:
         largest = distance
   return smallest, largest

def _convexPolygonsIntersect(firstXPoints, firstYPoints, secondXPoints, secondYPoints):
   """"""
   overlaps = True   # holds unless we find a direction along which the outlines are apart

   # the directions worth testing are the ones square-on to each outline's edges
   bothOutlines = ((firstXPoints, firstYPoints), (secondXPoints, secondYPoints))
   for edgeXPoints, edgeYPoints in bothOutlines:
      cornerCount = len(edgeXPoints)
      for index in range(cornerCount):
         nextIndex = (index + 1) % cornerCount
         # a direction square-on to this edge (the edge turned a quarter turn)
         axisX = -(edgeYPoints[nextIndex] - edgeYPoints[index])
         axisY =  (edgeXPoints[nextIndex] - edgeXPoints[index])

         firstSmallest,  firstLargest  = _projectionRange(axisX, axisY, firstXPoints, firstYPoints)
         secondSmallest, secondLargest = _projectionRange(axisX, axisY, secondXPoints, secondYPoints)

         # a gap along this direction means the outlines cannot be touching
         if firstLargest < secondSmallest or secondLargest < firstSmallest:
            overlaps = False

   return overlaps

# ──────────────────────────────────────────────────────────────────────────────────
# TECHNICAL NOTE - testing a point against a non-convex or open shape
#
# A point is inside a polygon of any shape when a ray drawn from it crosses the
# polygon's edges an odd number of times (the even-odd rule).  This handles shapes that
# curve back on themselves, such as a pie slice, where the simpler convex test above
# does not.
#
# An open shape - a curve with no inside, such as an unfilled arc - is counted as hit
# when the point lands within a small distance of the line itself, checked one segment
# at a time.
# ──────────────────────────────────────────────────────────────────────────────────

def _pointInPolygon(pointX, pointY, xPoints, yPoints):
   """"""
   isInside      = False
   cornerCount   = len(xPoints)
   previousIndex = cornerCount - 1
   for index in range(cornerCount):
      startX = xPoints[previousIndex]
      startY = yPoints[previousIndex]
      endX   = xPoints[index]
      endY   = yPoints[index]
      # a rightward ray from the point crosses this edge when the edge straddles the
      # point's height; each crossing flips whether we are inside
      edgeStraddlesPoint = (startY > pointY) != (endY > pointY)
      if edgeStraddlesPoint:
         edgeFraction = (pointY - startY) / (endY - startY)
         crossingX    = startX + edgeFraction * (endX - startX)
         if pointX < crossingX:
            isInside = not isInside
      previousIndex = index
   return isInside

def _distancePointToSegment(pointX, pointY, startX, startY, endX, endY):
   """"""
   segmentX = endX - startX
   segmentY = endY - startY
   segmentLengthSquared = segmentX * segmentX + segmentY * segmentY
   if segmentLengthSquared == 0:
      nearestX = startX        # the segment is really just a single point
      nearestY = startY
   else:
      # how far along the segment the closest point lies, kept within the segment's ends
      alongSegment = ((pointX - startX) * segmentX + (pointY - startY) * segmentY) / segmentLengthSquared
      clampedAlong = max(0.0, min(1.0, alongSegment))
      nearestX = startX + clampedAlong * segmentX
      nearestY = startY + clampedAlong * segmentY
   offsetX = pointX - nearestX
   offsetY = pointY - nearestY
   return float(np.hypot(offsetX, offsetY))

def _pointNearPath(pointX, pointY, xPoints, yPoints, nearnessAllowed):
   """"""
   isNear       = False
   segmentCount = len(xPoints) - 1
   for index in range(segmentCount):
      startX = xPoints[index]
      startY = yPoints[index]
      endX   = xPoints[index + 1]
      endY   = yPoints[index + 1]
      distanceToSegment = _distancePointToSegment(pointX, pointY, startX, startY, endX, endY)
      if distanceToSegment <= nearnessAllowed:
         isNear = True
   return isNear

#######################################################################################
class Drawable(Interactable):
   """Provide the shared behavior of every object you can place on a display.

   Drawable is a base class. You do not create one yourself. Shapes, images, text
   labels, and groups all inherit its methods for positioning, sizing, rotating, and
   testing overlap. Positions and sizes are in display coordinates and pixels, where x
   increases to the right and y increases downward; rotation is measured in degrees,
   counter-clockwise.
   """

   def __init__(self):
      Interactable.__init__(self)

      self._parent = None   # the Group or Display this item belongs to (None until added)

      # the item's placement relative to its parent.  Where the item actually appears on
      # the Display is worked out by combining this with each parent's placement, so a
      # level item inside a turned Group still ends up turned on screen.
      self._centerX  = 0.0
      self._centerY  = 0.0
      self._rotation = 0.0   # degrees, CCW, about the center
      self._scaleX   = 1.0   # a negative scale mirrors the item left-to-right
      self._scaleY   = 1.0   # a negative scale mirrors the item top-to-bottom

      # the item's own size before any rotation or scaling.  A plain shape keeps this
      # directly; a Group or a shape made from points works it out from its contents.
      self._baseWidth  = 0.0
      self._baseHeight = 0.0

      self._visible     = True   # whether the item is drawn at all
      self._visibility  = 100    # how opaque the item is, from 0 (clear) to 100 (solid)
      self._toolTipText = None   # hover text shown over the item, or None for none

      self._sceneMatrix = None   # remembered on-screen placement; cleared when it changes

   # ── Helpers ──────────────────────────────────────────────────────────

   def _asNumber(self, value):
      """
      Convert numbers from numpy data types to int/float, as appropriate.
      """
      rounded = round(float(value), 6)  # coerce numpy scalars to float and reduce floating-point values
      if rounded == int(rounded):       # does the value have no fractional part?
         number = int(rounded)
      else:
         number = rounded
      return number

   def _pushTransform(self):
      """
      Send this item's parent-relative transform to the renderer.
      We never send the final, on-screen position.
      """
      _handler().sendCommand('setTransform', self._objectId, {
         'cx':       self._centerX,
         'cy':       self._centerY,
         'rotation': self._rotation,
         'sx':       self._scaleX,
         'sy':       self._scaleY,
      })

   def _pushExtent(self):
      """
      Send this item's extent (base) size to the renderer.
      We never send the final, on-screen size; that's calculated from the transform.
      """
      _handler().sendCommand('setExtent', self._objectId, {
         'width':  self._baseWidth,
         'height': self._baseHeight,
      })

   # ── Scene placement ──────────────────────────────────────────────────────────
   # These small hooks help Groups and point-defined shapes vary what their box is and
   # what children they hold, while the geometry further down works the same for every
   # kind of drawable.

   def _baseExtent(self):
      """"""
      return (self._baseWidth, self._baseHeight)

   def _children(self):
      """"""
      return ()

   def _localMatrix(self):
      """"""
      return _affineMatrix(self._centerX, self._centerY, self._rotation, self._scaleX, self._scaleY)

   def _parentSceneMatrix(self):
      """"""
      if isinstance(self._parent, Drawable):
         parentMatrix = self._parent._getSceneMatrix()
      else:
         parentMatrix = np.identity(3)
      return parentMatrix

   def _getSceneMatrix(self):
      """"""
      if self._sceneMatrix is None:
         parentMatrix = self._parentSceneMatrix()
         localMatrix  = self._localMatrix()
         self._sceneMatrix = parentMatrix @ localMatrix
      return self._sceneMatrix

   def _invalidateSceneMatrix(self):
      """"""
      self._sceneMatrix = None
      for child in self._children():
         child._invalidateSceneMatrix()

   def _markParentExtentDirty(self):
      """"""
      if isinstance(self._parent, Group):
         self._parent._markDirty()

   def _localCorners(self):
      """"""
      width, height = self._baseExtent()
      halfWidth  = width / 2.0
      halfHeight = height / 2.0
      # the corners sit around the center; with y increasing downward, the top corners
      # take the smaller y.  The row of 1s lets the placement matrix shift the corners
      # as well as turn and scale them.
      corners = np.array([
         [-halfWidth, -halfWidth, halfWidth,  halfWidth],
         [-halfHeight, halfHeight, halfHeight, -halfHeight],
         [          1,          1,         1,           1],
      ], dtype=float)
      return corners

   def _localHitOutline(self):
      """"""
      return self._localCorners()

   # ── Meta Information ─────────────────────────────────────────────────
   # Bounding box, scene endpoints, parent Group/Display, tooltips

   def _sceneEndpoints(self):
      """"""
      sceneMatrix   = self._getSceneMatrix()
      localCorners  = self._localCorners()
      placedCorners = sceneMatrix @ localCorners
      xPoints = placedCorners[0]
      yPoints = placedCorners[1]
      return xPoints, yPoints

   def _visibleUnrotatedOutline(self):
      """"""
      # the object's outline (its corners, or its actual points for point-defined shapes)
      # in display coordinates, scaled as it currently appears but with its visible
      # rotation taken out about its center.  __str__ methods use this so the size and
      # positions they report are global and post-scale, while rotation is reported on its
      # own via getRotation().
      centerX, centerY, rotation, scaleX, scaleY = _decomposeAffine(self._getSceneMatrix())
      unrotatedPlacement = _affineMatrix(centerX, centerY, 0, scaleX, scaleY)
      placedOutline = unrotatedPlacement @ self._localHitOutline()
      xPoints = [self._asNumber(value) for value in placedOutline[0]]
      yPoints = [self._asNumber(value) for value in placedOutline[1]]
      return xPoints, yPoints

   def getEndpoints(self):
      """Return the object's four corners.

      The corners turn with the object, so a rotated object's endpoints are its actual
      tilted corners. For the upright box around the object instead, use getBoundingBox().

      Returns:
          xPoints (list[int or float]): The horizontal positions of the four corners, in pixels.
          yPoints (list[int or float]): The vertical positions of the four corners, in pixels.
      """
      coordinates = self._sceneEndpoints()
      xPoints = [self._asNumber(value) for value in coordinates[0]]
      yPoints = [self._asNumber(value) for value in coordinates[1]]
      return xPoints, yPoints

   def getBoundingBox(self):
      """Return the smallest upright box that surrounds the object.

      The box's own corners are never tilted, so it grows as the object rotates. For the
      object's actual (possibly tilted) corners instead, use getEndpoints().

      Returns:
          xPoints (list[int or float]): The horizontal positions of the box's four corners, in pixels.
          yPoints (list[int or float]): The vertical positions of the box's four corners, in pixels.
      """
      xPoints, yPoints = self._sceneEndpoints()
      leftX   = self._asNumber(xPoints.min())
      rightX  = self._asNumber(xPoints.max())
      topY    = self._asNumber(yPoints.min())
      bottomY = self._asNumber(yPoints.max())
      xPoints = [leftX, leftX, rightX, rightX]
      yPoints = [topY, bottomY, bottomY, topY]
      return xPoints, yPoints

   def getGroup(self):
      """Return the Group this object belongs to.

      Returns:
          group (Group): The group holding this object, or None if it is not in a group.
      """
      if isinstance(self._parent, Group):
         group = self._parent
      else:
         group = None

      return group

   def getDisplay(self):
      """Return the Display this object is on.

      Returns:
          display (Display): The display showing this object, or None if it is not on a display.
      """
      parent = self._parent
      
      if isinstance(parent, Display):
         display = parent
      elif isinstance(parent, Group):
         # our group's display is our display
         display = parent.getDisplay()
      else:
         display = None

      return display

   def setToolTipText(self, text=None):
      """Set the hover text shown over the object.

      Args:
          text (str, optional): The tooltip text. If omitted, the tooltip is cleared.
      """
      self._toolTipText = text
      _handler().sendCommand('setToolTipText', self._objectId, {'text': text})


   # ── Position ───────────────────────────────────────────────────────────────

   def _sceneCenter(self):
      """"""
      sceneMatrix = self._getSceneMatrix()
      # the center is where the item's local origin lands, which the placement matrix
      # records as its translation
      centerX = sceneMatrix[0, 2]
      centerY = sceneMatrix[1, 2]
      return centerX, centerY

   def _bakeReparent(self, oldSceneMatrix, newParentSceneMatrix):
      """"""
      # find the parent-relative placement that reproduces the old on-screen placement
      inverseNewParent     = np.linalg.inv(newParentSceneMatrix)
      placementInNewParent = inverseNewParent @ oldSceneMatrix
      (self._centerX, self._centerY, self._rotation,
       self._scaleX, self._scaleY) = _decomposeAffine(placementInNewParent)
      self._invalidateSceneMatrix()
      self._markParentExtentDirty()
      self._pushTransform()

   def getPosition(self):
      """Return the object's position, the top-left corner of its bounding box.

      Returns:
          x (int or float): The horizontal position of the top-left corner, in pixels.
          y (int or float): The vertical position of the top-left corner, in pixels.
      """
      coordinates = self._sceneEndpoints()
      x = self._asNumber(coordinates[0].min())
      y = self._asNumber(coordinates[1].min())
      return x, y

   def setPosition(self, x, y):
      """Move the object so the top-left corner of its bounding box sits at the given point.

      Args:
          x (int or float): The new horizontal position, in pixels.
          y (int or float): The new vertical position, in pixels.
      """
      # shift the center by however far the bounding-box corner needs to move; exact
      # values are used here so repeated moves do not slowly drift
      xPoints, yPoints = self._sceneEndpoints()
      currentLeft = xPoints.min()
      currentTop  = yPoints.min()
      centerX, centerY = self._sceneCenter()
      self.setCenter(centerX + (x - currentLeft), centerY + (y - currentTop))

   def getX(self):
      """Return the object's horizontal position.

      Returns:
          x (int or float): The horizontal position of the top-left corner, in pixels.
      """
      # updates to getPosition() automatically update how this method works
      x, _ = self.getPosition()
      return x

   def setX(self, x):
      """Set the object's horizontal position.

      Args:
          x (int or float): The new horizontal position, in pixels.
      """
      # updates to setPosition() automatically update how this method works
      self.setPosition(x, self.getY())

   def getY(self):
      """Return the object's vertical position.

      Returns:
          y (int or float): The vertical position of the top-left corner, in pixels.
      """
      # updates to getPosition() automatically update how this method works
      _, y = self.getPosition()
      return y

   def setY(self, y):
      """Set the object's vertical position.

      Args:
          y (int or float): The new vertical position, in pixels.
      """
      # updates to setPosition() automatically update how this method works
      self.setPosition(self.getX(), y)

   def move(self, x, y):
      """Move the object to a new position.

      Same as setPosition().

      Args:
          x (int or float): The new horizontal position, in pixels.
          y (int or float): The new vertical position, in pixels.
      """
      self.setPosition(x, y)

   def getCenter(self):
      """Return the object's center point.

      Returns:
          centerX (int or float): The horizontal position of the center, in pixels.
          centerY (int or float): The vertical position of the center, in pixels.
      """
      centerPosition = self._sceneCenter()
      centerX = self._asNumber(centerPosition[0])
      centerY = self._asNumber(centerPosition[1])
      return centerX, centerY

   def setCenter(self, x, y):
      """Move the object so its center sits at the given point.

      Args:
          x (int or float): The new horizontal position of the center, in pixels.
          y (int or float): The new vertical position of the center, in pixels.
      """
      # the target is given on the Display, so undo the parent's placement to get the
      # parent-relative center we actually store
      inverseParent    = np.linalg.inv(self._parentSceneMatrix())
      targetScenePoint = np.array([x, y, 1.0])
      localCenter      = inverseParent @ targetScenePoint
      self._centerX = float(localCenter[0])
      self._centerY = float(localCenter[1])
      self._invalidateSceneMatrix()
      self._markParentExtentDirty()
      self._pushTransform()

   def getCenterX(self):
      """Return the object's horizontal center.

      Returns:
          x (int or float): The horizontal center, in pixels.
      """
      # updates to getCenter() automatically update how this method works
      x, _ = self.getCenter()
      return x

   def setCenterX(self, x):
      """Set the object's horizontal center.

      Args:
          x (int or float): The new horizontal center, in pixels.
      """
      # updates to setCenter() automatically update how this method works
      self.setCenter(x, self.getCenterY())
   
   def getCenterY(self):
      """Return the object's vertical center.

      Returns:
          y (int or float): The vertical center, in pixels.
      """
      # updates to getCenter() automatically update how this method works
      _, y = self.getCenter()
      return y

   def setCenterY(self, y):
      """Set the object's vertical center.

      Args:
          y (int or float): The new vertical center, in pixels.
      """
      # updates to setCenter() automatically update how this method works
      self.setCenter(self.getCenterX(), y)

   # ── Size ───────────────────────────────────────────────────────────────────

   def _resize(self, targetWidth, targetHeight, currentWidth, currentHeight):
      """"""
      self._baseWidth  = (self._baseWidth  * targetWidth  / currentWidth)  if currentWidth  else targetWidth
      self._baseHeight = (self._baseHeight * targetHeight / currentHeight) if currentHeight else targetHeight
      self._markParentExtentDirty()
      self._pushExtent()

   def _anchorsTopLeftOnResize(self):
      """
      When a shape is resized, this decides which point stays put.
      While True, a shape grows from its top-left corner.
      While False, a shape grows from its center.
      Circular shapes (Circle, ArcCircle) always grow from their center.
      """
      return True

   def getSize(self):
      """Return the object's width and height.

      These are the size of its upright bounding box, so they grow as the object rotates.

      Returns:
          width (int or float): The width, in pixels.
          height (int or float): The height, in pixels.
      """
      xPoints, yPoints = self._sceneEndpoints()
      width  = self._asNumber(xPoints.max() - xPoints.min())
      height = self._asNumber(yPoints.max() - yPoints.min())
      return width, height

   def setSize(self, width, height):
      """Set the object's width and height.

      Args:
          width (int or float): The new width, in pixels.
          height (int or float): The new height, in pixels.
      """
      # measure the current size from exact values, then hand the target and current
      # sizes to _resize so each kind of shape can fit itself to the target
      xPoints, yPoints = self._sceneEndpoints()
      currentWidth  = xPoints.max() - xPoints.min()
      currentHeight = yPoints.max() - yPoints.min()

      targetWidth  = width  if width  is not None else currentWidth
      targetHeight = height if height is not None else currentHeight

      if targetWidth != currentWidth or targetHeight != currentHeight:
         # _resize keeps the center fixed; if this shape resizes from its top-left
         # corner instead, remember that corner and move back to it afterward
         topLeftX, topLeftY = self.getPosition()
         self._resize(targetWidth, targetHeight, currentWidth, currentHeight)
         if self._anchorsTopLeftOnResize():
            self.setPosition(topLeftX, topLeftY)

   def getWidth(self):
      """Return the object's width.

      Returns:
          width (int or float): The width, in pixels.
      """
      # updates to getSize() automatically update how this method works
      width, _ = self.getSize()
      return width

   def setWidth(self, width):
      """Set the object's width.

      Args:
          width (int or float): The new width, in pixels.
      """
      # updates to setSize() automatically update how this method works
      self.setSize(width, None)

   def getHeight(self):
      """Return the object's height.

      Returns:
          height (int or float): The height, in pixels.
      """
      # updates to getSize() automatically update how this method works
      _, height = self.getSize()
      return height

   def setHeight(self, height):
      """Set the object's height.

      Args:
          height (int or float): The new height, in pixels.
      """
      # updates to setSize() automatically update how this method works
      self.setSize(None, height)

   # ── Rotation ───────────────────────────────────────────────────────────────

   def getRotation(self):
      """Return how far the object is turned.

      Returns:
          rotation (int or float): The rotation, in degrees from 0 to 360, measured counter-clockwise.
      """
      sceneMatrix = self._getSceneMatrix()
      onScreenRotation = _matrixRotation(sceneMatrix)
      # report the angle in the usual 0-to-360 range
      rotation = self._asNumber(onScreenRotation % 360.0)
      return rotation

   def setRotation(self, rotation, anchorX=None, anchorY=None):
      """Turn the object to a given angle.

      By default the object turns about its own center. Give an anchor point to turn it
      about that point instead.

      Args:
          rotation (int or float): The angle to turn to, in degrees, counter-clockwise.
          anchorX (int or float, optional): The horizontal position of the point to turn about, in pixels. Defaults to the object's center.
          anchorY (int or float, optional): The vertical position of the point to turn about, in pixels. Defaults to the object's center.
      """
      rotation = float(rotation)

      if anchorX is not None and anchorY is not None:
         # turning about an anchor also swings the center around that anchor, by however
         # much the on-screen angle is changing
         centerX, centerY = self._sceneCenter()
         angleChange = rotation - self.getRotation()
         radians = np.radians(-angleChange)   # negated for our CCW, y-down angles
         cosine  = np.cos(radians)
         sine    = np.sin(radians)
         offsetX = centerX - anchorX
         offsetY = centerY - anchorY
         swungCenterX = anchorX + (cosine * offsetX - sine * offsetY)
         swungCenterY = anchorY + (sine * offsetX + cosine * offsetY)
         # store that swung center as a parent-relative center
         inverseParent = np.linalg.inv(self._parentSceneMatrix())
         localCenter   = inverseParent @ np.array([swungCenterX, swungCenterY, 1.0])
         self._centerX = float(localCenter[0])
         self._centerY = float(localCenter[1])

      # store the parent-relative angle that produces the requested on-screen angle
      parentRotation = _matrixRotation(self._parentSceneMatrix())
      self._rotation = rotation - parentRotation
      self._invalidateSceneMatrix()
      self._markParentExtentDirty()
      self._pushTransform()

   def rotate(self, angle):
      """Turn the object by an additional angle.

      The angle is added to the object's current rotation.

      Args:
          angle (int or float): How far to turn, in degrees, counter-clockwise.
      """
      currentRotation = self.getRotation()
      self.setRotation(currentRotation + angle)

   # ── Hit Testing ────────────────────────────────────────────────────────────

   def _sceneHitOutline(self):
      """"""
      sceneMatrix   = self._getSceneMatrix()
      localOutline  = self._localHitOutline()
      placedOutline = sceneMatrix @ localOutline
      return placedOutline[0], placedOutline[1]

   def contains(self, x, y):
      """Report whether a point lies inside the object.

      Args:
          x (int or float): The horizontal position to test, in pixels.
          y (int or float): The vertical position to test, in pixels.

      Returns:
          contains (bool): True if the point is inside the object, False otherwise.
      """
      xPoints, yPoints = self._sceneHitOutline()
      contains = _pointInConvexPolygon(x, y, xPoints, yPoints)
      return contains

   def intersects(self, other):
      """Report whether this object overlaps another.

      Args:
          other (Drawable): The other object to test against.

      Returns:
          otherIsIntersecting (bool): True if the two objects overlap, False otherwise.
      """
      if not isinstance(other, Drawable):
         raise TypeError(f'{type(self).__name__}.intersects(): other should be a Drawable object (it was {type(other).__name__})')
      ownXPoints, ownYPoints = self._sceneHitOutline()
      otherXPoints, otherYPoints = other._sceneHitOutline()
      otherIsIntersecting = _convexPolygonsIntersect(ownXPoints, ownYPoints, otherXPoints, otherYPoints)
      return otherIsIntersecting

   def encloses(self, other):
      """Report whether this object completely contains another.

      Args:
          other (Drawable): The other object to test against.

      Returns:
          otherIsInside (bool): True if the other object lies entirely inside this one, False otherwise.
      """
      if not isinstance(other, Drawable):
         raise TypeError(f'{type(self).__name__}.encloses(): other should be a Drawable object (it was {type(other).__name__})')
      ownXPoints, ownYPoints = self._sceneHitOutline()
      otherXPoints, otherYPoints = other._sceneHitOutline()
      # the other item is enclosed only when every one of its corners is inside ours
      otherIsInside = True
      for cornerX, cornerY in zip(otherXPoints, otherYPoints):
         if not _pointInConvexPolygon(cornerX, cornerY, ownXPoints, ownYPoints):
            otherIsInside = False
      return otherIsInside

   # ── Visibility ─────────────────────────────────────────────────────────────

   def _show(self):
      """"""
      self._visible = True
      _handler().sendCommand('show', self._objectId)

   def _hide(self):
      """"""
      self._visible = False
      _handler().sendCommand('hide', self._objectId)

   def getVisibility(self):
      """Return how visible the object is.

      Returns:
          visibility (int): How visible the object is, from 0 (invisible) to 100 (fully visible).
      """
      visibility = self._visibility
      return visibility

   def setVisibility(self, visibility):
      """Set how visible the object is.

      Args:
          visibility (int): How visible to make the object, from 0 (invisible) to 100 (fully visible). Values outside this range are clamped.
      """
      self._visibility = max(0, min(100, int(visibility)))
      _handler().sendCommand('setVisibility', self._objectId, {'visibility': self._visibility})


#######################################################################################
# Graphics - simple geometric shapes, icons, and text labels
#######################################################################################
class Graphics(Drawable):
   """Provide the shared look (color, fill, and outline thickness) of the simple shapes.

   Graphics is a base class. You do not create one yourself. The shapes (Rectangle,
   Oval, Circle, Point, Arc, ArcCircle, Line, Polyline, and Polygon) inherit from it,
   along with its color, fill, and thickness methods.

   Args:
       color (Color, optional): The color.
       fill (bool, optional): Whether the shape is filled in (True) or just an outline (False).
       thickness (int, optional): The outline thickness, in pixels.
   """
   def __init__(self, color=Color.BLACK, fill=False, thickness=1):
      Drawable.__init__(self)

      self._color     = color.getRGBA()  # color unpacked as rgba values
      self._fill      = bool(fill)       # is this shape filled in?
      self._thickness = int(thickness)   # outline width

   # ── Color ────────────────────────────────────────────────────────────────

   def getColor(self):
      """Return the shape's color.

      Returns:
          color (Color): The current color.
      """
      color = Color(*self._color)
      return color

   def setColor(self, color=None):
      """Set the shape's color.

      Args:
          color (Color, optional): The new color. If omitted, a color-selection dialog opens.
      """
      if color is None:
         color = Color()  # default color brings up color select dialog

      if isinstance(color, Color):
         r, g, b, a = color.getRGBA()
      else:
         raise TypeError(f'{type(self).__name__}.setColor(): color should be a Color object (it was {type(color).__name__})')

      self._color = [r, g, b, a]
      _handler().sendCommand('setColor', self._objectId, {'color': [r, g, b, a]})

   # ── Fill ────────────────────────────────────────────────────────────────

   def getFill(self):
      """Report whether the shape is filled in.

      Returns:
          isFilled (bool): True if the shape is filled in, False if it is just an outline.
      """
      isFilled = self._fill
      return isFilled

   def setFill(self, fill):
      """Set whether the shape is filled in.

      Args:
          fill (bool): True to fill the shape in, False for just an outline.
      """
      self._fill = bool(fill)
      _handler().sendCommand('setFill', self._objectId, {'fill': self._fill})

   # ── Thickness ────────────────────────────────────────────────────────────────

   def getThickness(self):
      """Return the shape's outline thickness.

      Returns:
          thickness (int): The outline thickness, in pixels.
      """
      thickness = self._thickness
      return thickness

   def setThickness(self, thickness):
      """Set the shape's outline thickness.

      Args:
          thickness (int): The new outline thickness, in pixels.
      """
      self._thickness = int(thickness)
      _handler().sendCommand('setThickness', self._objectId, {'thickness': self._thickness})

#######################################################################################

class Rectangle(Graphics):
   """Create a rectangle, given two opposite corners.

   Args:
       x1 (int or float): The horizontal position of the top-left corner, in pixels.
       y1 (int or float): The vertical position of the top-left corner, in pixels.
       x2 (int or float): The horizontal position of the bottom-right corner, in pixels.
       y2 (int or float): The vertical position of the bottom-right corner, in pixels.
       color (Color, optional): The color.
       fill (bool, optional): Whether the rectangle is filled in (True) or just an outline (False).
       thickness (int, optional): The outline thickness, in pixels.
       rotation (int or float, optional): How far to turn the rectangle, in degrees, counter-clockwise.
       visibility (int, optional): How visible the rectangle is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, x1, y1, x2, y2, color=Color.BLACK, fill=False, thickness=1, rotation=0, visibility=100):
      """"""
      Graphics.__init__(self, color, fill, thickness)

      # the two corners give the rectangle's size and where its center sits.  A brand
      # new item has no parent, so this center is already in scene coordinates.
      self._baseWidth  = abs(x2 - x1)
      self._baseHeight = abs(y2 - y1)
      self._centerX    = (x1 + x2) / 2.0
      self._centerY    = (y1 + y2) / 2.0
      self._rotation   = float(rotation)
      self._visibility = max(0, min(100, int(visibility)))

      _handler().sendCommand('create', self._objectId, {
         'type':       'Rectangle',
         'cx':         self._centerX,
         'cy':         self._centerY,
         'width':      self._baseWidth,
         'height':     self._baseHeight,
         'rotation':   self._rotation,
         'sx':         self._scaleX,
         'sy':         self._scaleY,
         'color':      self._color,
         'fill':       self._fill,
         'thickness':  self._thickness,
         'visibility': self._visibility,
      })

   def __str__(self):
      # describe the rectangle the way it was created: the two corners of its upright
      # (unrotated) shape, at the size and place it now appears
      xPoints, yPoints = self._visibleUnrotatedOutline()
      x1 = int(round(min(xPoints)))
      y1 = int(round(min(yPoints)))
      x2 = int(round(max(xPoints)))
      y2 = int(round(max(yPoints)))
      return (f'Rectangle(x1 = {x1}, y1 = {y1}, x2 = {x2}, y2 = {y2}, '
              f'color = {self.getColor()}, fill = {self.getFill()}, '
              f'thickness = {self.getThickness()}, rotation = {self.getRotation()}, '
              f'visibility = {self.getVisibility()})')

class Oval(Graphics):
   """Create an oval that fills the box given by two opposite corners.

   Args:
       x1 (int or float): The horizontal position of the box's top-left corner, in pixels.
       y1 (int or float): The vertical position of the box's top-left corner, in pixels.
       x2 (int or float): The horizontal position of the box's bottom-right corner, in pixels.
       y2 (int or float): The vertical position of the box's bottom-right corner, in pixels.
       color (Color, optional): The color.
       fill (bool, optional): Whether the oval is filled in (True) or just an outline (False).
       thickness (int, optional): The outline thickness, in pixels.
       rotation (int or float, optional): How far to turn the oval, in degrees, counter-clockwise.
       visibility (int, optional): How visible the oval is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, x1, y1, x2, y2, color=Color.BLACK, fill=False, thickness=1, rotation=0, visibility=100):
      """"""
      Graphics.__init__(self, color, fill, thickness)

      # the two corners give the oval's size and where its center sits.  A brand new
      # item has no parent, so this center is already in scene coordinates.
      self._baseWidth  = abs(x2 - x1)
      self._baseHeight = abs(y2 - y1)
      self._centerX    = (x1 + x2) / 2.0
      self._centerY    = (y1 + y2) / 2.0
      self._rotation   = float(rotation)
      self._visibility = max(0, min(100, int(visibility)))

      _handler().sendCommand('create', self._objectId, {
         'type':       'Oval',
         'cx':         self._centerX,
         'cy':         self._centerY,
         'width':      self._baseWidth,
         'height':     self._baseHeight,
         'rotation':   self._rotation,
         'sx':         self._scaleX,
         'sy':         self._scaleY,
         'color':      self._color,
         'fill':       self._fill,
         'thickness':  self._thickness,
         'visibility': self._visibility,
      })

   def __str__(self):
      # describe the oval the way it was created: the two corners of its upright
      # (unrotated) box, at the size and place it now appears
      xPoints, yPoints = self._visibleUnrotatedOutline()
      x1 = int(round(min(xPoints)))
      y1 = int(round(min(yPoints)))
      x2 = int(round(max(xPoints)))
      y2 = int(round(max(yPoints)))
      return (f'Oval(x1 = {x1}, y1 = {y1}, x2 = {x2}, y2 = {y2}, '
              f'color = {self.getColor()}, fill = {self.getFill()}, '
              f'thickness = {self.getThickness()}, rotation = {self.getRotation()}, '
              f'visibility = {self.getVisibility()})')

   # ── Hit Testing ───────────────────────────────────────────────────────────────

   def _localHitOutline(self):
      """"""
      pointCount = 32   # enough segments to follow the curve closely
      halfWidth  = self._baseWidth / 2.0
      halfHeight = self._baseHeight / 2.0
      xRow = []
      yRow = []
      for index in range(pointCount):
         angleAround = 2.0 * np.pi * index / pointCount
         xRow.append(halfWidth * np.cos(angleAround))
         yRow.append(halfHeight * np.sin(angleAround))
      onesRow = [1.0] * pointCount
      return np.array([xRow, yRow, onesRow], dtype=float)


class Circle(Oval):
   """Create a circle, given its center and radius.

   Args:
       x (int or float): The horizontal position of the center, in pixels.
       y (int or float): The vertical position of the center, in pixels.
       radius (int or float): The radius, in pixels.
       color (Color, optional): The color.
       fill (bool, optional): Whether the circle is filled in (True) or just an outline (False).
       thickness (int, optional): The outline thickness, in pixels.
       visibility (int, optional): How visible the circle is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, x, y, radius, color=Color.BLACK, fill=False, thickness=1, visibility=100):
      """"""
      x1 = x - radius
      y1 = y - radius
      x2 = x + radius
      y2 = y + radius

      Oval.__init__(self, x1, y1, x2, y2, color, fill, thickness, 0, visibility)

   def __str__(self):
      x, y      = self.getCenter()
      # radius from the un-rotated outline, so it stays the circle's true radius even if
      # the circle has been scaled or turned
      xPoints   = self._visibleUnrotatedOutline()[0]
      radius    = self._asNumber((max(xPoints) - min(xPoints)) / 2.0)
      color     = self.getColor()
      fill      = self.getFill()
      thickness = self.getThickness()

      return f'Circle(x = {x}, y = {y}, radius = {radius}, color = {color}, fill = {fill}, thickness = {thickness}, visibility = {self.getVisibility()})'

   # ── Size ────────────────────────────────────────────────────────────────

   def _anchorsTopLeftOnResize(self):
      return False   # a circle always grows from its center

   def setSize(self, width, height):
      """Set the circle's size.

      A circle's width and height are always the same; if they differ, the width is used
      for both.

      Args:
          width (int or float): The new diameter, in pixels.
          height (int or float): The new diameter, in pixels (should match the width).
      """
      if width != height:
         print(f"{type(self).__name__}.setSize(): the width and height of a {type(self).__name__} should be the same (they were '{width}' and '{height}').  Using the width.")

      Oval.setSize(self, width, width)

   def setWidth(self, width):
      """Set the circle's diameter.

      Sets both the width and the height, keeping the circle round.

      Args:
          width (int or float): The new diameter, in pixels.
      """
      self.setSize(width, width)

   def setHeight(self, height):
      """Set the circle's diameter.

      Sets both the height and the width, keeping the circle round.

      Args:
          height (int or float): The new diameter, in pixels.
      """
      self.setSize(height, height)

   # ── Radius ────────────────────────────────────────────────────────────────

   def getRadius(self):
      """Return the circle's radius.

      Returns:
          radius (int or float): The radius, in pixels.
      """
      radius = self.getWidth() / 2
      radius = self._asNumber(radius)
      return radius

   def setRadius(self, radius):
      """Set the circle's radius.

      Args:
          radius (int or float): The new radius, in pixels.
      """
      diameter = radius * 2
      self.setWidth(diameter)

   # ── Hit testing ────────────────────────────────────────────────────────────

   def intersects(self, other):
      """Report whether this circle overlaps another object.

      Args:
          other (Drawable): The other object to test against.

      Returns:
          otherIsIntersecting (bool): True if the two objects overlap, False otherwise.
      """
      if isinstance(other, Circle):
         selfCenterX, selfCenterY   = self._sceneCenter()
         otherCenterX, otherCenterY = other._sceneCenter()
         # a circle's radius on screen is half the width of its bounding box
         radiiSum = (self.getWidth() + other.getWidth()) / 2.0
         offsetX = selfCenterX - otherCenterX
         offsetY = selfCenterY - otherCenterY
         centerDistanceSquared = offsetX * offsetX + offsetY * offsetY
         otherIsIntersecting = centerDistanceSquared <= radiiSum * radiiSum
      else:
         otherIsIntersecting = Drawable.intersects(self, other)
      return otherIsIntersecting


class Point(Circle):
   """Create a single point.

   Args:
       x (int or float): The horizontal position, in pixels.
       y (int or float): The vertical position, in pixels.
       color (Color, optional): The color.
       visibility (int, optional): How visible the point is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, x, y, color=Color.BLACK, visibility=100):
      """"""
      Circle.__init__(self, x, y, 1, color, True, 1, visibility)

   def __str__(self):
      x, y  = self.getCenter()
      color = self.getColor()
      return f'Point(x = {x}, y = {y}, color = {color}, visibility = {self.getVisibility()})'

   def getEndpoints(self):
      """Return the point's location.

      A point has just the one corner, its own position.

      Returns:
          centerX (list[int or float]): The horizontal position, in pixels, as a one-item list.
          centerY (list[int or float]): The vertical position, in pixels, as a one-item list.
      """
      centerX, centerY = self.getCenter()
      return [centerX], [centerY]


class Arc(Graphics):
   """Create an arc, part of the oval that fills the box given by two opposite corners.

   Angles are in degrees, with 0 at the three o'clock position; a positive angle goes
   counter-clockwise, a negative one clockwise. The constants HALF_PI, PI, and TWO_PI
   may be used for the angles.

   Args:
       x1 (int or float): The horizontal position of the box's top-left corner, in pixels.
       y1 (int or float): The vertical position of the box's top-left corner, in pixels.
       x2 (int or float): The horizontal position of the box's bottom-right corner, in pixels.
       y2 (int or float): The vertical position of the box's bottom-right corner, in pixels.
       startAngle (int or float, optional): The starting angle, in degrees.
       endAngle (int or float, optional): The ending angle, in degrees.
       style (int, optional): The arc style, one of OPEN (an open arc), CHORD (closed with a straight line between the ends), or PIE (closed with two lines to the center).
       color (Color, optional): The color.
       fill (bool, optional): Whether the arc is filled in (True) or just an outline (False).
       thickness (int, optional): The outline thickness, in pixels.
       rotation (int or float, optional): How far to turn the arc, in degrees, counter-clockwise.
       visibility (int, optional): How visible the arc is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, x1, y1, x2, y2, startAngle=PI, endAngle=TWO_PI, style=OPEN, color=Color.BLACK, fill=False, thickness=1, rotation=0, visibility=100):
      """"""
      Graphics.__init__(self, color, fill, thickness)

      # the two corners give the arc's size and where its center sits.  A brand new
      # item has no parent, so this center is already in scene coordinates.
      self._baseWidth  = abs(x2 - x1)
      self._baseHeight = abs(y2 - y1)
      self._centerX    = (x1 + x2) / 2.0
      self._centerY    = (y1 + y2) / 2.0
      self._rotation   = float(rotation)
      self._visibility = max(0, min(100, int(visibility)))

      self._startAngle = startAngle
      self._endAngle   = endAngle
      self._style      = style

      _handler().sendCommand('create', self._objectId, {
         'type':       'Arc',
         'cx':         self._centerX,
         'cy':         self._centerY,
         'width':      self._baseWidth,
         'height':     self._baseHeight,
         'startAngle': self._startAngle,
         'endAngle':   self._endAngle,
         'style':      self._style,
         'rotation':   self._rotation,
         'sx':         self._scaleX,
         'sy':         self._scaleY,
         'color':      self._color,
         'fill':       self._fill,
         'thickness':  self._thickness,
         'visibility': self._visibility,
      })

   def __str__(self):
      # describe the arc the way it was created: the two corners of its upright
      # (unrotated) box, at the size and place it now appears
      xPoints, yPoints = self._visibleUnrotatedOutline()
      x1 = int(round(min(xPoints)))
      y1 = int(round(min(yPoints)))
      x2 = int(round(max(xPoints)))
      y2 = int(round(max(yPoints)))
      return (f'Arc(x1 = {x1}, y1 = {y1}, x2 = {x2}, y2 = {y2}, '
              f'startAngle = {self._startAngle}, endAngle = {self._endAngle}, '
              f'style = {self._style}, color = {self.getColor()}, fill = {self.getFill()}, '
              f'thickness = {self.getThickness()}, rotation = {self.getRotation()}, '
              f'visibility = {self.getVisibility()})')

   # ── Hit Testing ───────────────────────────────────────────────────────────────

   def _localHitOutline(self):
      """"""
      pointCount   = 32   # enough segments to follow the curve closely
      halfWidth    = self._baseWidth / 2.0
      halfHeight   = self._baseHeight / 2.0
      startRadians = np.radians(self._startAngle)
      # the renderer sweeps the opposite way from our angle convention, so match it
      sweepRadians = np.radians(-(self._endAngle - self._startAngle))

      xRow = []
      yRow = []
      if self._style == PIE:        # a pie slice begins at the center
         xRow.append(0.0)
         yRow.append(0.0)
      for index in range(pointCount + 1):
         angleAlongArc = startRadians + sweepRadians * index / pointCount
         xRow.append(halfWidth * np.cos(angleAlongArc))
         yRow.append(-halfHeight * np.sin(angleAlongArc))

      onesRow = [1.0] * len(xRow)
      return np.array([xRow, yRow, onesRow], dtype=float)

   def contains(self, x, y):
      """Report whether a point lies on (or inside) the arc.

      For an OPEN arc this tests whether the point is on the arc line; for a CHORD or PIE
      arc it tests whether the point is inside the closed shape.

      Args:
          x (int or float): The horizontal position to test, in pixels.
          y (int or float): The vertical position to test, in pixels.

      Returns:
          contains (bool): True if the point is on or inside the arc, False otherwise.
      """
      xPoints, yPoints = self._sceneHitOutline()
      if self._style == OPEN:
         nearnessAllowed = max(self._thickness, 1) / 2.0
         contains = _pointNearPath(x, y, xPoints, yPoints, nearnessAllowed)
      else:
         contains = _pointInPolygon(x, y, xPoints, yPoints)
      return contains

   # ── Arc width ────────────────────────────────────────────────────────────────

   def _setArcWidth(self, arcWidth):
      """
      Rotaries need this to update their arcWidth.
      NOTE: Should we consider making this a public part of the API?
      """
      _handler().sendCommand('setArcWidth', self._objectId, {'arcWidth': -arcWidth})


class ArcCircle(Arc):
   """Create a circular arc, given its center and radius.

   Like an Arc, but shaped from a circle instead of a box. Angles are in degrees, with
   0 at the three o'clock position; a positive angle goes counter-clockwise, a negative
   one clockwise. The constants HALF_PI, PI, and TWO_PI may be used for the angles.

   Args:
       x (int or float): The horizontal position of the center, in pixels.
       y (int or float): The vertical position of the center, in pixels.
       radius (int or float): The radius, in pixels.
       startAngle (int or float, optional): The starting angle, in degrees.
       endAngle (int or float, optional): The ending angle, in degrees.
       style (int, optional): The arc style, one of OPEN (an open arc), CHORD (closed with a straight line between the ends), or PIE (closed with two lines to the center).
       color (Color, optional): The color.
       fill (bool, optional): Whether the arc is filled in (True) or just an outline (False).
       thickness (int, optional): The outline thickness, in pixels.
       rotation (int or float, optional): How far to turn the arc, in degrees, counter-clockwise.
       visibility (int, optional): How visible the arc is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, x, y, radius, startAngle=PI, endAngle=TWO_PI, style=OPEN, color=Color.BLACK, fill=False, thickness=1, rotation=0, visibility=100):
      """"""
      x1 = x - radius
      y1 = y - radius
      x2 = x + radius
      y2 = y + radius

      Arc.__init__(self, x1, y1, x2, y2, startAngle, endAngle, style, color, fill, thickness, rotation, visibility)

   def __str__(self):
      x, y       = self.getCenter()
      # radius from the un-rotated outline, so it stays the circle's true radius even if
      # the arc has been scaled or turned
      xPoints    = self._visibleUnrotatedOutline()[0]
      radius     = self._asNumber((max(xPoints) - min(xPoints)) / 2.0)
      startAngle = self._startAngle
      endAngle   = self._endAngle
      style      = self._style
      rotation   = self.getRotation()
      color      = self.getColor()
      fill       = self.getFill()
      thickness  = self.getThickness()
      return f'ArcCircle(x = {x}, y = {y}, radius = {radius}, startAngle = {startAngle}, endAngle = {endAngle}, style = {style}, color = {color}, fill = {fill}, thickness = {thickness}, rotation = {rotation}, visibility = {self.getVisibility()})'

   # ── Size ────────────────────────────────────────────────────────────────

   def _anchorsTopLeftOnResize(self):
      return False   # an arc-circle always grows from its center

   def setSize(self, width, height):
      """Set the arc-circle's size.

      Its width and height are always the same; if they differ, the width is used for both.

      Args:
          width (int or float): The new diameter, in pixels.
          height (int or float): The new diameter, in pixels (should match the width).
      """
      if width != height:
         print(f"{type(self).__name__}.setSize(): the width and height of a {type(self).__name__} should be the same (they were '{width}' and '{height}').  Using the width.")

      Arc.setSize(self, width, width)

   # ── Radius ────────────────────────────────────────────────────────────────

   def getRadius(self):
      """Return the arc-circle's radius.

      Returns:
          radius (int or float): The radius, in pixels.
      """
      radius = self.getWidth() / 2
      radius = self._asNumber(radius)
      return radius

   def setRadius(self, radius):
      """Set the arc-circle's radius.

      Args:
          radius (int or float): The new radius, in pixels.
      """
      diameter = radius * 2
      self.setWidth(diameter)


class Polyline(Graphics):
   """Create a connected series of line segments.

   The xPoints and yPoints lists are parallel: the first corner is (xPoints[0],
   yPoints[0]), the next is (xPoints[1], yPoints[1]), and so on. The path is left open
   (the last corner is not joined back to the first); for a closed shape, use Polygon.

   Args:
       xPoints (list[int or float]): The horizontal positions of the corners, in pixels.
       yPoints (list[int or float]): The vertical positions of the corners, in pixels.
       color (Color, optional): The color.
       thickness (int, optional): The line thickness, in pixels.
       rotation (int or float, optional): How far to turn the shape, in degrees, counter-clockwise.
       visibility (int, optional): How visible the shape is, from 0 (invisible) to 100 (fully visible).
   """

   def __init__(self, xPoints, yPoints, color=Color.BLACK, thickness=1, rotation=0, visibility=100):
      """"""
      if len(xPoints) != len(yPoints):
         raise ValueError(f'{type(self).__name__}(): xPoints and yPoints must have the same number of points (they had {len(xPoints)} and {len(yPoints)} points).')

      Graphics.__init__(self, color, False, thickness)

      # the points define the shape.  Its center is the middle of their bounding box,
      # and the points are kept relative to that center so the shape's box sits centered
      # on the origin like every other drawable.  A new item has no parent, so this
      # center is already in scene coordinates.
      self._centerX = (min(xPoints) + max(xPoints)) / 2.0
      self._centerY = (min(yPoints) + max(yPoints)) / 2.0
      self._localXPoints = [x - self._centerX for x in xPoints]
      self._localYPoints = [y - self._centerY for y in yPoints]
      self._rotation   = float(rotation)
      self._visibility = max(0, min(100, int(visibility)))

      _handler().sendCommand('create', self._objectId, {
         'type':       'Polyline',
         'cx':         self._centerX,
         'cy':         self._centerY,
         'xPoints':    self._localXPoints,
         'yPoints':    self._localYPoints,
         'rotation':   self._rotation,
         'sx':         self._scaleX,
         'sy':         self._scaleY,
         'color':      self._color,
         'thickness':  self._thickness,
         'visibility': self._visibility,
      })

   def __str__(self):
      xPoints, yPoints = self._visibleUnrotatedOutline()
      return (f'Polyline(xPoints = {xPoints}, yPoints = {yPoints}, '
              f'color = {self.getColor()}, thickness = {self.getThickness()}, '
              f'rotation = {self.getRotation()}, visibility = {self.getVisibility()})')

   # ── Shape from points ──────────────────────────────────────────────────────────
   # A point-defined shape works out its own size from its points and, like a Group,
   # grows by scaling rather than by moving them.

   def _baseExtent(self):
      width  = max(self._localXPoints) - min(self._localXPoints)
      height = max(self._localYPoints) - min(self._localYPoints)
      return (width, height)

   def _localHitOutline(self):
      onesRow = [1.0] * len(self._localXPoints)
      return np.array([self._localXPoints, self._localYPoints, onesRow], dtype=float)

   def _resize(self, targetWidth, targetHeight, currentWidth, currentHeight):
      # a point-defined shape grows by scaling rather than by moving its points: scale
      # from the current size, or from the points' own span when the current size is zero
      pointSpanWidth  = max(self._localXPoints) - min(self._localXPoints)
      pointSpanHeight = max(self._localYPoints) - min(self._localYPoints)
      if currentWidth:
         self._scaleX *= targetWidth / currentWidth
      elif pointSpanWidth:
         self._scaleX = targetWidth / pointSpanWidth
      if currentHeight:
         self._scaleY *= targetHeight / currentHeight
      elif pointSpanHeight:
         self._scaleY = targetHeight / pointSpanHeight
      self._invalidateSceneMatrix()
      self._markParentExtentDirty()
      self._pushTransform()

   def getEndpoints(self):
      """Return the polyline's corners.

      The corners turn with the shape, so a rotated polyline's endpoints are its actual
      tilted corners.

      Returns:
          xPoints (list[int or float]): The horizontal positions of the corners, in pixels.
          yPoints (list[int or float]): The vertical positions of the corners, in pixels.
      """
      coordinates = self._sceneHitOutline()
      xPoints = [self._asNumber(value) for value in coordinates[0]]
      yPoints = [self._asNumber(value) for value in coordinates[1]]
      return xPoints, yPoints

   def _setLocalPoints(self, xPoints, yPoints):
      """"""
      centerOffsetX = (min(xPoints) + max(xPoints)) / 2.0
      centerOffsetY = (min(yPoints) + max(yPoints)) / 2.0
      self._localXPoints = [value - centerOffsetX for value in xPoints]
      self._localYPoints = [value - centerOffsetY for value in yPoints]

      # shifting the points within our own frame moves the box's center; carry that move
      # up into the parent's frame so the shape does not appear to jump
      localMatrix      = self._localMatrix()
      rotationAndScale = localMatrix[:2, :2]
      centerShift      = rotationAndScale @ np.array([centerOffsetX, centerOffsetY])
      self._centerX += float(centerShift[0])
      self._centerY += float(centerShift[1])

      self._invalidateSceneMatrix()
      self._markParentExtentDirty()
      self._pushTransform()
      self._pushPoints()

   def _pushPoints(self):
      """"""
      _handler().sendCommand('setPoints', self._objectId, {
         'xPoints': self._localXPoints,
         'yPoints': self._localYPoints,
      })

   # ── Hit Testing ───────────────────────────────────────────────────────────────

   def contains(self, x, y):
      """Report whether a point lies on the polyline.

      Tests whether the point is on (or very near) the line itself.

      Args:
          x (int or float): The horizontal position to test, in pixels.
          y (int or float): The vertical position to test, in pixels.

      Returns:
          contains (bool): True if the point is on the polyline, False otherwise.
      """
      xPoints, yPoints = self._sceneHitOutline()
      nearnessAllowed = max(self._thickness, 1) / 2.0
      contains = _pointNearPath(x, y, xPoints, yPoints, nearnessAllowed)
      return contains


class Line(Polyline):
   """Create a line between two points.

   Args:
       x1 (int or float): The horizontal position of one end, in pixels.
       y1 (int or float): The vertical position of one end, in pixels.
       x2 (int or float): The horizontal position of the other end, in pixels.
       y2 (int or float): The vertical position of the other end, in pixels.
       color (Color, optional): The color.
       thickness (int, optional): The line thickness, in pixels.
       rotation (int or float, optional): How far to turn the line, in degrees, counter-clockwise.
       visibility (int, optional): How visible the line is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, x1, y1, x2, y2, color=Color.BLACK, thickness=1, rotation=0, visibility=100):
      """"""
      Graphics.__init__(self, color, False, thickness)

      # a line is a two-point shape; its center is the midpoint of the two endpoints,
      # which the points are then kept relative to (see Polyline)
      self._centerX = (x1 + x2) / 2.0
      self._centerY = (y1 + y2) / 2.0
      self._localXPoints = [x1 - self._centerX, x2 - self._centerX]
      self._localYPoints = [y1 - self._centerY, y2 - self._centerY]
      self._rotation   = float(rotation)
      self._visibility = max(0, min(100, int(visibility)))

      _handler().sendCommand('create', self._objectId, {
         'type':       'Line',
         'cx':         self._centerX,
         'cy':         self._centerY,
         'xPoints':    self._localXPoints,
         'yPoints':    self._localYPoints,
         'rotation':   self._rotation,
         'sx':         self._scaleX,
         'sy':         self._scaleY,
         'color':      self._color,
         'thickness':  self._thickness,
         'visibility': self._visibility,
      })

   def __str__(self):
      xPoints, yPoints = self._visibleUnrotatedOutline()
      x1, x2 = xPoints
      y1, y2 = yPoints
      return (f'Line(x1 = {x1}, y1 = {y1}, x2 = {x2}, y2 = {y2}, '
              f'color = {self.getColor()}, thickness = {self.getThickness()}, '
              f'rotation = {self.getRotation()}, visibility = {self.getVisibility()})')

   # ── Length ────────────────────────────────────────────────────────────────

   def getLength(self):
      """Return the line's length.

      Returns:
          length (int or float): The distance between the line's two ends, in pixels.
      """
      xPoints, yPoints = self._sceneHitOutline()
      deltaX = xPoints[1] - xPoints[0]
      deltaY = yPoints[1] - yPoints[0]
      length = self._asNumber(np.hypot(deltaX, deltaY))
      return length

   def setLength(self, length):
      """Set the line's length.

      Keeps the first end and the direction fixed, and moves the second end so the line is
      the given length.

      Args:
          length (int or float): The new length, in pixels.
      """
      localX1, localX2 = self._localXPoints
      localY1, localY2 = self._localYPoints
      directionX = localX2 - localX1
      directionY = localY2 - localY1
      currentLength = np.hypot(directionX, directionY)
      if currentLength == 0:
         # the endpoints sit on top of each other, so grow along the x direction
         newX2 = localX1 + length
         newY2 = localY1
      else:
         unitX = directionX / currentLength
         unitY = directionY / currentLength
         newX2 = localX1 + length * unitX
         newY2 = localY1 + length * unitY
      self._setLocalPoints([localX1, newX2], [localY1, newY2])


class Polygon(Polyline):
   """Create a polygon from parallel lists of corner coordinates.

   The xPoints and yPoints lists are parallel: the first corner is (xPoints[0],
   yPoints[0]), the next is (xPoints[1], yPoints[1]), and so on. Unlike a Polyline, the
   shape is closed (the last corner joins back to the first).

   Args:
       xPoints (list[int or float]): The horizontal positions of the corners, in pixels.
       yPoints (list[int or float]): The vertical positions of the corners, in pixels.
       color (Color, optional): The color.
       fill (bool, optional): Whether the polygon is filled in (True) or just an outline (False).
       thickness (int, optional): The outline thickness, in pixels.
       rotation (int or float, optional): How far to turn the polygon, in degrees, counter-clockwise.
       visibility (int, optional): How visible the polygon is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, xPoints, yPoints, color=Color.BLACK, fill=False, thickness=1, rotation=0, visibility=100):
      """"""
      if len(xPoints) != len(yPoints):
         raise ValueError(f'{type(self).__name__}(): xPoints and yPoints must have the same number of points (they had {len(xPoints)} and {len(yPoints)} points).')

      Graphics.__init__(self, color, fill, thickness)

      # the points define the shape, kept relative to the middle of their bounding box
      # so the box sits centered on the origin (see Polyline)
      self._centerX = (min(xPoints) + max(xPoints)) / 2.0
      self._centerY = (min(yPoints) + max(yPoints)) / 2.0
      self._localXPoints = [x - self._centerX for x in xPoints]
      self._localYPoints = [y - self._centerY for y in yPoints]
      self._rotation   = float(rotation)
      self._visibility = max(0, min(100, int(visibility)))

      _handler().sendCommand('create', self._objectId, {
         'type':       'Polygon',
         'cx':         self._centerX,
         'cy':         self._centerY,
         'xPoints':    self._localXPoints,
         'yPoints':    self._localYPoints,
         'rotation':   self._rotation,
         'sx':         self._scaleX,
         'sy':         self._scaleY,
         'color':      self._color,
         'fill':       self._fill,
         'thickness':  self._thickness,
         'visibility': self._visibility,
      })

   def __str__(self):
      xPoints, yPoints = self._visibleUnrotatedOutline()
      return (f'Polygon(xPoints = {xPoints}, yPoints = {yPoints}, '
              f'color = {self.getColor()}, fill = {self.getFill()}, '
              f'thickness = {self.getThickness()}, rotation = {self.getRotation()}, visibility = {self.getVisibility()})')

   # ── Hit Testing ───────────────────────────────────────────────────────────────

   def contains(self, x, y):
      """Report whether a point lies inside the polygon.

      Args:
          x (int or float): The horizontal position to test, in pixels.
          y (int or float): The vertical position to test, in pixels.

      Returns:
          contains (bool): True if the point is inside the polygon, False otherwise.
      """
      xPoints, yPoints = self._sceneHitOutline()
      contains = _pointInPolygon(x, y, xPoints, yPoints)
      return contains


class Icon(Graphics):
   """Create an image loaded from a file.

   Give just a width to scale the image proportionally; give both a width and a height
   to stretch it to that exact size.

   Args:
       filename (str): The image file to load, ending in ".jpg" or ".png".
       width (int or float, optional): The width to scale the image to, in pixels. Defaults to the image's own width.
       height (int or float, optional): The height to scale the image to, in pixels. Defaults to the image's own height.
       backgroundColor (Color, optional): The color of the rectangle behind the image. Defaults to clear (no backing).
       fill (bool, optional): Whether the backing rectangle is filled in (True) or just an outline (False).
       thickness (int, optional): The backing rectangle's outline thickness, in pixels.
       rotation (int or float, optional): How far to turn the image, in degrees, counter-clockwise.
       visibility (int, optional): How visible the image is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, filename, width=None, height=None, backgroundColor=Color.CLEAR, fill=True, thickness=0, rotation=0, visibility=100):
      """"""
      Graphics.__init__(self, backgroundColor, fill, thickness)

      self._filename   = filename
      self._rotation   = float(rotation)
      self._visibility = max(0, min(100, int(visibility)))
      self._pixelCache = None   # local copy of the pixel colors; cleared when the image changes

      _handler().sendCommand('create', self._objectId, {
         'type':       'Icon',
         'filename':   filename,
         'width':      width,
         'height':     height,
         'rotation':   rotation,
         'color':      self._color,       # styles the rectangle behind the image
         'fill':       self._fill,
         'thickness':  self._thickness,
         'visibility': self._visibility,
      })

      # the renderer loads the image and works out its size, so ask it for the resolved
      # dimensions when the caller left them open
      if width is None or height is None:
         result = _handler().sendQuery('getSize', self._objectId)
         self._baseWidth  = result[0]
         self._baseHeight = result[1]
      else:
         self._baseWidth  = width
         self._baseHeight = height

      # start with the icon's top-left at the origin (its center is half its size in)
      self._centerX = self._baseWidth  / 2.0
      self._centerY = self._baseHeight / 2.0
      self._pushTransform()

   def __str__(self):
      # report the visible (scaled) size with rotation taken out, since that is what the
      # constructor takes
      xPoints, yPoints = self._visibleUnrotatedOutline()
      width  = self._asNumber(max(xPoints) - min(xPoints))
      height = self._asNumber(max(yPoints) - min(yPoints))
      return (f'Icon(filename = "{self._filename}", width = {width}, height = {height}, '
              f'backgroundColor = {self.getBackgroundColor()}, fill = {self.getFill()}, '
              f'thickness = {self.getThickness()}, rotation = {self.getRotation()}, visibility = {self.getVisibility()})')

   # ── Background color ──────────────────────────────────────────────────────
   # An Icon's color, fill, and thickness style a rectangle behind the image; these read
   # more clearly named after the background, and forward to the inherited color methods.

   def getBackgroundColor(self):
      """Return the color of the rectangle behind the image.

      Returns:
          color (Color): The background color.
      """
      color = self.getColor()
      return color

   def setBackgroundColor(self, color=None):
      """Set the color of the rectangle behind the image.

      Args:
          color (Color, optional): The new background color. If omitted, a color-selection dialog opens.
      """
      self.setColor(color)

   # ── Save ────────────────────────────────────────────────────────────────

   def save(self, filename, width=None, height=None):
      """Save the image to a file.

      Args:
          filename (str): The file to write, ending in ".jpg" or ".png".
          width (int or float, optional): The width of the saved image, in pixels. Defaults to the image's current width.
          height (int or float, optional): The height of the saved image, in pixels. Defaults to the image's current height.
      """
      result = _handler().sendQuery('write', self._objectId, {'filename': filename, 'width': width, 'height': height})
      success, resolvedPath = result[0], result[1]
      if success:
         print(f'{type(self).__name__}.save(): saved canvas to "{resolvedPath}"')
      else:
         print(f'{type(self).__name__}.save(): failed to save "{resolvedPath}"')

   # ── Crop ────────────────────────────────────────────────────────────────

   def crop(self, x, y, width, height):
      """Crop the image to a rectangular region.

      Keeps the part of the image starting at (x, y) and extending the given width and
      height; the rest is discarded.

      Args:
          x (int or float): The horizontal start of the region, in pixels from the image's top-left.
          y (int or float): The vertical start of the region, in pixels from the image's top-left.
          width (int or float): The width of the region to keep, in pixels.
          height (int or float): The height of the region to keep, in pixels.
      """
      # remember where the kept region currently sits, so it does not jump
      currentLeft, currentTop = self.getPosition()
      self._baseWidth  = int(width)
      self._baseHeight = int(height)
      self._pixelCache = None   # the image changed, so drop the cached pixels
      _handler().sendCommand('crop', self._objectId, {'x': x, 'y': y, 'width': width, 'height': height})
      self.setPosition(currentLeft + x, currentTop + y)

   # ── Pixel Manipulation ────────────────────────────────────────────────────────────

   def getPixel(self, column, row):
      """Return the color of one pixel.

      The image origin (0, 0) is at the top-left.

      Args:
          column (int): The pixel's column (its horizontal position in the image).
          row (int): The pixel's row (its vertical position in the image).

      Returns:
          pixel (list[int]): The pixel's red, green, blue, and alpha values, for example
              [255, 0, 0, 255]. Alpha runs from 0 (fully transparent) to 255 (fully opaque).
      """
      if self._pixelCache is None:  # fetch local cache, if needed
         self._pixelCache = _handler().sendQuery('getPixels', self._objectId)
      pixel = list(self._pixelCache[row][column])
      return pixel

   def setPixel(self, column, row, color):
      """Set the color of one pixel.

      The image origin (0, 0) is at the top-left.

      Args:
          column (int): The pixel's column (its horizontal position in the image).
          row (int): The pixel's row (its vertical position in the image).
          color (list[int]): The new red, green, and blue values, for example [255, 0, 0]. You
              may add a fourth alpha value, from 0 (fully transparent) to 255 (fully opaque); when
              left off, the pixel is fully opaque.
      """
      self._pixelCache = None  # invalidate local cache
      _handler().sendCommand('setPixel', self._objectId, {'column': column, 'row': row, 'color': color})

   def getPixels(self):
      """Return every pixel in the image.

      The pixels are arranged as a list of rows, each row a list of pixels, each pixel a list
      of red, green, blue, and alpha values. The image's top-left pixel is at [0][0]. Alpha runs
      from 0 (fully transparent) to 255 (fully opaque).

      Returns:
          pixelList (list[list[list[int]]]): The image's pixels, by row then column, each as
              [red, green, blue, alpha].
      """
      if self._pixelCache is None:  # fetch local cache, if needed
         self._pixelCache = _handler().sendQuery('getPixels', self._objectId)
      pixelList = list(self._pixelCache)
      return pixelList

   def setPixels(self, pixelList):
      """Replace every pixel in the image.

      The pixels are arranged as a list of rows, each row a list of pixels, each pixel a list
      of red, green, and blue values. The image's top-left pixel is at [0][0]. Each pixel may add
      a fourth alpha value, from 0 (fully transparent) to 255 (fully opaque); when left off, the
      pixel is fully opaque.

      Args:
          pixels (list[list[list[int]]]): The new pixels, by row then column, each as
              [red, green, blue] or [red, green, blue, alpha].
      """
      self._pixelCache = None  # invalidate local cache
      _handler().sendCommand('setPixels', self._objectId, {'pixels': pixelList})


class Label(Graphics):
   """Create a label that shows a line of text.

   Args:
       text (str): The text to show.
       alignment (int, optional): How the text lines up, one of LEFT, CENTER, or RIGHT.
       textColor (Color, optional): The text color.
       backgroundColor (Color, optional): The color behind the text. Defaults to transparent.
       font (Font, optional): The font, for example Font("Serif", Font.ITALIC, 16). If omitted, the default font is used.
       visibility (int, optional): How visible the label is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, text, alignment=LEFT, textColor=Color.BLACK, backgroundColor=Color.CLEAR, font=None, visibility=100):
      """"""
      Graphics.__init__(self, textColor, False, 1)

      self._text            = str(text)
      self._backgroundColor = backgroundColor.getRGBA()
      self._alignment       = alignment
      self._font            = None
      self._rotation        = 0.0
      self._visibility      = max(0, min(100, int(visibility)))

      # extract Font information
      fontData = None
      if isinstance(font, Font):
         name  = font.getName()
         style = font.getStyle()
         size  = font.getSize()
         self._font = [name, style, size]
         fontData   = [name, style, size]

      _handler().sendCommand('create', self._objectId, {
         'type':            'Label',
         'text':            self._text,
         'alignment':       alignment,
         'textColor':       self._color,
         'backgroundColor': self._backgroundColor,
         'font':            fontData,
         'color':           self._color,
         'rotation':        self._rotation,
         'sx':              self._scaleX,
         'sy':              self._scaleY,
         'visibility':      self._visibility,
      })

      # the renderer measures the text, so ask it for the resolved size, then place the
      # label's top-left at the origin (its center is half its size in)
      result = _handler().sendQuery('getSize', self._objectId)
      self._baseWidth  = result[0]
      self._baseHeight = result[1]
      self._centerX = self._baseWidth  / 2.0
      self._centerY = self._baseHeight / 2.0
      self._pushTransform()

   def __str__(self):
      text            = self.getText()
      alignment       = self.getAlignment()
      textColor       = self.getTextColor()
      backgroundColor = self.getBackgroundColor()
      font            = self.getFont()
      return f'Label(text = "{text}", alignment = {alignment}, textColor = {textColor}, backgroundColor = {backgroundColor}, font = {font}, visibility = {self.getVisibility()})'

   # ── Text ────────────────────────────────────────────────────────────────

   def getText(self):
      """Return the label's text.

      Returns:
          text (str): The label's text.
      """
      text = self._text
      return text

   def setText(self, text):
      """Set the label's text.

      Args:
          text (str): The new text. If it is longer than the label can fit, it is truncated.
      """
      currentLeft, currentTop = self.getPosition()
      self._text = str(text)
      _handler().sendCommand('setText', self._objectId, {'text': self._text})
      result = _handler().sendQuery('getSize', self._objectId)
      self._baseWidth  = result[0]
      self._baseHeight = result[1]
      self.setPosition(currentLeft, currentTop)

   # ── Color ────────────────────────────────────────────────────────────────

   def getTextColor(self):
      """Return the label's text color.

      Returns:
          color (Color): The text color.
      """
      color = self.getColor()
      return color

   def setTextColor(self, color=None):
      """Set the label's text color.

      Args:
          color (Color, optional): The new text color. If omitted, a color-selection dialog opens.
      """
      self.setColor(color)

   def getBackgroundColor(self):
      """Return the label's background color.

      Returns:
          color (Color): The color behind the text.
      """
      color = Color(*self._backgroundColor)
      return color

   def setBackgroundColor(self, color=None):
      """Set the label's background color.

      Args:
          color (Color, optional): The new background color. If omitted, a color-selection dialog opens.
      """
      if color is None:
         color = Color()

      if isinstance(color, Color):
         r, g, b, a = color.getRGBA()
      else:
         raise TypeError(f'{type(self).__name__}.setBackgroundColor(): color should be a Color object (it was {type(color).__name__})')

      self._backgroundColor = [r, g, b, a]
      _handler().sendCommand('setBackgroundColor', self._objectId, {'color': [r, g, b, a]})

   # ── Alignment ────────────────────────────────────────────────────────────────

   def getAlignment(self):
      """Return how the label's text lines up.

      Returns:
          alignment (int): The text alignment, one of LEFT, CENTER, or RIGHT.
      """
      alignment = self._alignment
      return alignment

   def setAlignment(self, alignment):
      """Set how the label's text lines up.

      Args:
          alignment (int): The text alignment, one of LEFT, CENTER, or RIGHT.
      """
      self._alignment = alignment
      _handler().sendCommand('setAlignment', self._objectId, {'alignment': alignment})

   # ── Font ────────────────────────────────────────────────────────────────

   def getFont(self):
      """Return the label's font.

      Returns:
          font (Font): The label's font, or None if it uses the default font.
      """
      font = None

      if self._font is not None:
         name, style, size = self._font
         font = Font(name, style, size)

      return font

   def setFont(self, font):
      """Set the label's font.

      Args:
          font (Font): The new font, for example Font("Serif", Font.ITALIC, 16).
      """
      currentLeft, currentTop = self.getPosition()
      name  = font.getName()
      style = font.getStyle()
      size  = font.getSize()
      self._font = [name, style, size]
      _handler().sendCommand('setFont', self._objectId, {'font': [name, style, size]})
      result = _handler().sendQuery('getSize', self._objectId)
      self._baseWidth  = result[0]
      self._baseHeight = result[1]
      self.setPosition(currentLeft, currentTop)


#######################################################################################
# Group - a collection of Graphics that are manipulated as one object
#######################################################################################
class Group(Drawable):
   """Bundle several drawable objects so they move, turn, and scale together.

   Add a group to a display like any other object. Moving, turning, or resizing the
   group moves, turns, or resizes everything in it together, while each member keeps its
   place within the group.

   Args:
       itemList (list[Drawable], optional): The objects to start the group with.
   """
   def __init__(self, itemList=[]):
      Drawable.__init__(self)

      self._itemList = []     # the child drawables, front to back
      self._dirty    = True   # whether the group's box needs working out again

      _handler().sendCommand('create', self._objectId, {'type': 'Group'})

      # add back to front, so the first item listed ends up on top
      for item in reversed(itemList):
         self.add(item)

   def __str__(self):
      return f'Group(items = {self._itemList})'

   # ── Working out the group's box from its children ──────────────────────────────
   # A Group's size and position come from where its children sit, so they are worked
   # out only when something asks for them and a child has changed since last time.

   def _children(self):
      return self._itemList

   def _baseExtent(self):
      self._calculateSize()
      return (self._baseWidth, self._baseHeight)

   def _getSceneMatrix(self):
      # the group may shift its own origin while working out its box (see the note
      # below), so settle that before building its placement
      self._calculateSize()
      return Drawable._getSceneMatrix(self)

   def _markDirty(self):
      """"""
      self._dirty = True
      self._markParentExtentDirty()

   def _resize(self, targetWidth, targetHeight, currentWidth, currentHeight):
      """"""
      if currentWidth:
         self._scaleX *= targetWidth / currentWidth
      if currentHeight:
         self._scaleY *= targetHeight / currentHeight
      self._invalidateSceneMatrix()
      self._markParentExtentDirty()
      self._pushTransform()

   # ──────────────────────────────────────────────────────────────────────────────
   # TECHNICAL NOTE - keeping a Group centered on its children
   #
   # The geometry in Drawable assumes an item's box is centered on its own origin.  A
   # Group's box, though, is wherever its children happen to be, so whenever the
   # children change the Group moves its own origin back to the center of them.  To do
   # that without anything appearing to jump, the children are nudged one way and the
   # Group is nudged the opposite way by the matching amount.
   # ──────────────────────────────────────────────────────────────────────────────

   def _calculateSize(self):
      """"""
      if self._dirty:
         self._dirty = False   # clear first, so reading the children below cannot loop back in

         if len(self._itemList) == 0:
            self._baseWidth  = 0.0
            self._baseHeight = 0.0
         else:
            # gather every child's corners, placed within this group's frame
            childXPoints = []
            childYPoints = []
            for child in self._itemList:
               cornersInChild = child._localCorners()    # settles any nested group first
               childPlacement = child._localMatrix()
               cornersInGroup = childPlacement @ cornersInChild
               childXPoints.extend(cornersInGroup[0])
               childYPoints.extend(cornersInGroup[1])

            leftEdge   = min(childXPoints)
            rightEdge  = max(childXPoints)
            topEdge    = min(childYPoints)
            bottomEdge = max(childYPoints)

            # where the children's combined box is centered within this group's frame
            contentCenterX = (leftEdge + rightEdge) / 2.0
            contentCenterY = (topEdge + bottomEdge) / 2.0

            # move the group's origin onto that center without anything appearing to
            # shift (see the note above)
            if contentCenterX != 0.0 or contentCenterY != 0.0:
               for child in self._itemList:
                  child._centerX -= contentCenterX
                  child._centerY -= contentCenterY
                  child._pushTransform()
               # the children moved within the group; carry that move up into the
               # parent's frame so the group moves by the matching amount
               groupMatrix      = self._localMatrix()
               rotationAndScale = groupMatrix[:2, :2]
               contentShift     = np.array([contentCenterX, contentCenterY])
               parentShift      = rotationAndScale @ contentShift
               self._centerX += float(parentShift[0])
               self._centerY += float(parentShift[1])
               self._pushTransform()
               self._markParentExtentDirty()

            self._baseWidth  = rightEdge - leftEdge
            self._baseHeight = bottomEdge - topEdge

            self._invalidateSceneMatrix()
            self._pushExtent()

   # ── Adding and removing items ───────────────────────────────────────────────────

   def add(self, item, x=None, y=None):
      """Add an object to the group at the given position.

      Aligns the object's top-left corner (for a Circle, its center) with (x, y), where
      (0, 0) is the display's top-left corner. If x and y are left out, the object keeps
      its current on-screen place as it joins. If the object is already in another group
      or on a display, it is removed from there first.

      Args:
          item (Drawable): The object to add.
          x (int or float, optional): The horizontal position, in pixels. Defaults to the object's current position.
          y (int or float, optional): The vertical position, in pixels. Defaults to the object's current position.
      """
      self.addOrder(item, 0, x, y)

   def addOrder(self, item, order=0, x=None, y=None):
      """Add an object to the group on a given layer and position.

      Same as add(), but also sets the object's layer within the group. Layers run from
      smallest to largest, where 0 is closest to the front.

      Args:
          item (Drawable): The object to add.
          order (int, optional): The layer to place it on; 0 is closest to the front.
          x (int or float, optional): The horizontal position, in pixels. Defaults to the object's current position.
          y (int or float, optional): The vertical position, in pixels. Defaults to the object's current position.
      """
      if not isinstance(item, Drawable):
         raise TypeError(f'{type(self).__name__}.addOrder(): item should be a Drawable object (it was {type(item).__name__})')

      # remember where the item appears now, so it can be kept there after it joins us
      itemOnScreen = item._getSceneMatrix()

      # take the item out of whatever Group or Display currently holds it
      currentParent = item.getGroup()
      if currentParent is None:
         currentParent = item.getDisplay()
      if currentParent is not None:
         currentParent.remove(item)
      item._parent = self

      order = max(0, min(len(self._itemList), order))
      self._itemList.insert(order, item)

      # mirror the addition in the renderer (this also sets the item's drawing order)
      _handler().sendCommand('addChildOrder', self._objectId, {
         'itemId': item._objectId,
         'order':  order,
      })

      # re-express the item relative to the group as it stands now, so it keeps its
      # on-screen look; the _markDirty below re-centers the group consistently afterward
      groupParentMatrix = self._parentSceneMatrix()
      groupLocalMatrix  = self._localMatrix()
      groupOnScreen     = groupParentMatrix @ groupLocalMatrix
      item._bakeReparent(itemOnScreen, groupOnScreen)

      # if the caller gave an explicit position, it replaces the remembered one
      if x is not None or y is not None:
         currentX, currentY = item.getPosition()
         item.setPosition(x if x is not None else currentX, y if y is not None else currentY)

      self._markDirty()

   def remove(self, item):
      """Remove an object from the group.

      The object keeps its current on-screen place as it leaves.

      Args:
          item (Drawable): The object to remove.
      """
      if item in self._itemList:
         # keep the item looking the same as it leaves; with no parent its placement is
         # simply where it appears on screen
         itemOnScreen = item._getSceneMatrix()
         item._parent = None
         self._itemList.remove(item)
         item._bakeReparent(itemOnScreen, np.identity(3))
         _handler().sendCommand('removeChild', self._objectId, {'itemId': item._objectId})
         self._markDirty()

   def removeAll(self):
      """Remove every object from the group.

      A quick way to empty the group.
      """
      for item in list(self._itemList):
         item._parent = None
      self._itemList.clear()
      _handler().sendCommand('removeAll', self._objectId)
      self._markDirty()

   def getOrder(self, item):
      """Return the layer an object sits on within the group.

      Args:
          item (Drawable): The object to look up.

      Returns:
          order (int): The object's layer, where 0 is closest to the front; None if the object is not in the group.
      """
      if item in self._itemList:
         order = self._itemList.index(item)
      else:
         order = None
      return order

   def setOrder(self, item, order):
      """Move an object to a different layer within the group.

      Layers run from smallest to largest, where 0 is closest to the front. Does nothing
      if the object is not in the group.

      Args:
          item (Drawable): The object to re-layer.
          order (int): The layer to move it to; 0 is closest to the front.
      """
      if item in self._itemList:
         self.addOrder(item, order)

   def getItems(self):
      """Return the GUI objects currently in the group.

      Returns:
          itemList (list[Drawable]): A copy of the list of objects in the group.
      """
      itemList = list(self._itemList)  # make a second list, but keeps the same items
      return itemList

#######################################################################################
# MusicControl - special Groups with custom callbacks
#######################################################################################
class MusicControl(Group):
   """Provide the shared behavior of the custom-drawn controls (faders, knobs, pads, buttons).

   MusicControl is a base class. You do not create one yourself. HFader, VFader,
   Rotary, Push, Toggle, and XYPad inherit from it. Because these controls are Groups,
   you can add and remove drawable parts to restyle them. getValue() and setValue() read
   and change the control's value, and changing the value calls the control's update
   function.

   Args:
       action (Callable, optional): The function to call when the control's value changes; it receives the new value.
   """
   def __init__(self, action=None):
      """"""
      Group.__init__(self)
      self._value  = None
      self._action = action
      # Since MusicControls are Groups, users can manipulate them by adding and
      # removing items.  As a result, we need a way to identify the MusicControl's
      # original components without referencing their index in itemList.
      # Also, since Groups' true dimensions change with their items, we use these
      # components' dimensions to resolve value changes from events.
      self._foregroundShape = None
      self._backgroundShape = None
      self._outlineShape    = None

   ##### NEW MUSICCONTROL METHODS
   def _defaultAction(self, *args):
      """"""
      pass

   def _updateAppearance(self):
      """"""
      pass

   def getValue(self):
      """Return the control's current value.

      Returns:
          value (int): The control's current value.
      """
      value = int(self._value)
      return value

   def setValue(self, newValue):
      """Set the control's value.

      If the value changes, the control redraws itself and its update function is called.

      Args:
          newValue (int or float): The new value.
      """
      if newValue != self._value:  # only update if value has changed
         self._value = newValue
         self._updateAppearance()
         if (self._action is not None) and callable(self._action):
            self._action(self._value)  # call user function

   def onAction(self, action):
      """Set up a function to call when the control's value changes.

      This is the same function you can pass when you create the control. Use it to set
      that function later, or to change it. Pass None to remove it.

      Args:
          action (Callable): The function to call; it receives one parameter, the new value.
      """
      self._action = action

   # ── Color ────────────────────────────────────────────────────────────────
   # A MusicControl is drawn from a foreground part (the part that shows the value), a
   # background part behind it, and an outline around it.  Each part is its own shape, so
   # each can be colored on its own.

   def _foregroundShapes(self):
      """"""
      # the shapes that make up the foreground; XYPad adds its crosshair lines to these
      return [self._foregroundShape]

   def _colorShapes(self, shapes, color, methodName):
      """"""
      if color is None:
         color = Color()  # default color brings up color select dialog (just once for all the shapes)
      if not isinstance(color, Color):
         raise TypeError(f'{type(self).__name__}.{methodName}(): color should be a Color object (it was {type(color).__name__})')
      for shape in shapes:
         if shape is not None:
            shape.setColor(color)

   def getColor(self):
      """Return the control's main color.

      This is the foreground color, the color of the part that shows the value.

      Returns:
          color (Color): The foreground color.
      """
      color = self.getForegroundColor()
      return color

   def setColor(self, color=None):
      """Set the control's main color.

      This colors the foreground, the part that shows the value. To color the other parts,
      use setBackgroundColor() and setOutlineColor().

      Args:
          color (Color, optional): The new foreground color. If omitted, a color-selection dialog opens.
      """
      self.setForegroundColor(color)

   def getForegroundColor(self):
      """Return the color of the foreground (the part that shows the value).

      Returns:
          color (Color): The foreground color.
      """
      color = self._foregroundShape.getColor()
      return color

   def setForegroundColor(self, color=None):
      """Set the color of the foreground (the part that shows the value).

      Args:
          color (Color, optional): The new foreground color. If omitted, a color-selection dialog opens.
      """
      self._colorShapes(self._foregroundShapes(), color, 'setForegroundColor')

   def getBackgroundColor(self):
      """Return the color of the background (the part behind the foreground).

      Returns:
          color (Color): The background color.
      """
      color = self._backgroundShape.getColor()
      return color

   def setBackgroundColor(self, color=None):
      """Set the color of the background (the part behind the foreground).

      Args:
          color (Color, optional): The new background color. If omitted, a color-selection dialog opens.
      """
      self._colorShapes([self._backgroundShape], color, 'setBackgroundColor')

   def getOutlineColor(self):
      """Return the color of the outline around the control.

      Returns:
          color (Color): The outline color.
      """
      color = self._outlineShape.getColor()
      return color

   def setOutlineColor(self, color=None):
      """Set the color of the outline around the control.

      Args:
          color (Color, optional): The new outline color. If omitted, a color-selection dialog opens.
      """
      self._colorShapes([self._outlineShape], color, 'setOutlineColor')

   # ── Fill ────────────────────────────────────────────────────────────────

   def getFill(self):
      """Report whether the control's background is filled in.

      Returns:
          isFilled (bool): True if the background is filled in, False if it is just an outline.
      """
      isFilled = self._backgroundShape.getFill()
      return isFilled

   def setFill(self, fill):
      """Set whether the control's background is filled in.

      This colors the area behind the foreground solidly (True) or leaves it empty (False).

      Args:
          fill (bool): True to fill the background in, False for just an outline.
      """
      self._backgroundShape.setFill(fill)

   # ── Thickness ────────────────────────────────────────────────────────────────

   def getThickness(self):
      """Return the thickness of the control's outline.

      Returns:
          thickness (int): The outline thickness, in pixels.
      """
      thickness = self._outlineShape.getThickness()
      return thickness

   def setThickness(self, thickness):
      """Set the thickness of the control's outline.

      Args:
          thickness (int): The new outline thickness, in pixels.
      """
      self._outlineShape.setThickness(thickness)

#######################################################################################
class HFader(MusicControl):
   """Create a horizontal fader (a slider) the user can drag left and right.

   The fader fills the box with corners (x1, y1) and (x2, y2).

   Args:
       x1 (int or float): The horizontal position of the top-left corner, in pixels.
       y1 (int or float): The vertical position of the top-left corner, in pixels.
       x2 (int or float): The horizontal position of the bottom-right corner, in pixels.
       y2 (int or float): The vertical position of the bottom-right corner, in pixels.
       minValue (int, optional): The smallest value the fader can take.
       maxValue (int, optional): The largest value the fader can take.
       startValue (int or float, optional): The fader's starting value. Defaults to halfway between minValue and maxValue.
       action (Callable, optional): The function to call when the fader moves; it receives the new value.
       foregroundColor (Color, optional): The color of the filled level.
       backgroundColor (Color, optional): The color behind the level.
       outlineColor (Color, optional): The outline color.
       thickness (int, optional): The outline thickness, in pixels.
       rotation (int or float, optional): How far to turn the fader, in degrees, counter-clockwise.
       visibility (int, optional): How visible the fader is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, x1, y1, x2, y2, minValue=0, maxValue=999, startValue=None, action=None, foregroundColor=Color.RED, backgroundColor=Color.BLACK, outlineColor=Color.BLACK, thickness=3, rotation=0, visibility=100):
      """"""
      MusicControl.__init__(self, action)

      # calculate dimensions
      localX = min(x1, x2)
      localY = min(y1, y2)
      width  = abs(x1 - x2)
      height = abs(y1 - y2)

      # initialize internal shapes with (0, 0) position
      self._backgroundShape = Rectangle(
         0, 0, width, height,
         color=backgroundColor,
         fill=True,
         thickness=0,
         rotation=0
      )
      self._foregroundShape = Rectangle(
         0, 0, width, height,
         color=foregroundColor,
         fill=True,
         thickness=0,
         rotation=0
      )
      self._outlineShape = Rectangle(
         0, 0, width, height,
         color=outlineColor,
         fill=False,
         thickness=thickness,
         rotation=0
      )

      self.add(self._backgroundShape)
      self.add(self._foregroundShape)
      self.add(self._outlineShape)

      # set starting attributes
      self.setPosition(localX, localY)
      self.setRotation(rotation)
      self.setVisibility(visibility)

      if startValue is None:
         startValue = (minValue + maxValue) / 2

      self._minValue = minValue
      self._maxValue = maxValue
      self.setValue(startValue)

      # register default behavior events
      self.onMouseDown(self._defaultAction)
      self.onMouseDrag(self._defaultAction)

   def __str__(self):
      x1, y1          = self._backgroundShape.getPosition()
      width, height   = self._backgroundShape.getSize()
      x2              = x1 + width
      y2              = y1 + height
      foregroundColor = self._foregroundShape.getColor()
      backgroundColor = self._backgroundShape.getColor()
      outlineColor    = self._outlineShape.getColor()
      thickness       = self._outlineShape.getThickness()
      rotation        = self.getRotation()
      return f'HFader(x1 = {x1}, y1 = {y1}, x2 = {x2}, y2 = {y2}, minValue = {self._minValue}, maxValue = {self._maxValue}, startValue = {self.getValue()}, action = {self._action}, foreground = {foregroundColor}, background = {backgroundColor}, outline = {outlineColor}, thickness = {thickness}, rotation = {rotation}, visibility = {self.getVisibility()})'

   # OVERRIDDEN METHODS
   def _defaultAction(self, ex, ey):
      """"""
      # update fader value based on mouse position on the fader
      fx = self._backgroundShape.getX()  # visual fader position
      x  = ex - fx                       # local event position

      valueRatio = x / self._backgroundShape.getWidth()        # (0.0 - 1.0)
      valueRatio = max(0.0, min(1.0, valueRatio))              # clamp ratio
      valueRange = self._maxValue - self._minValue             # possible values
      newValue   = self._minValue + (valueRatio * valueRange)  # scale to range
      self.setValue(newValue)                                  # update value

   def _updateAppearance(self):
      """"""
      valueRatio = (self._value - self._minValue) / (self._maxValue - self._minValue)  # (0.0 - 1.0)
      width, height = self._backgroundShape.getSize()
      x,     y      = self._backgroundShape.getPosition()
      padding       = self._outlineShape.getThickness() / 2

      fWidth  = (width  - (2 * padding))  # find maximum fader bar dimensions
      fHeight = (height - (2 * padding))  # ...
      fx      = x + padding               # ...
      fy      = y + padding               # ...
      fWidth  = fWidth * valueRatio       # scale to value

      # size first, then position: in the new model resizing pins the center, so we
      # set the size and then move the top-left to where the bar should start
      self._foregroundShape.setSize(fWidth, fHeight)
      self._foregroundShape.setPosition(fx, fy)

   def setValue(self, newValue):
      """Set the fader's value.

      The value is in the fader's own minValue–maxValue range. The fill moves to match,
      and the update function is called.

      Args:
          newValue (int or float): The new value, between minValue and maxValue.
      """
      newValue = max(self._minValue, min(self._maxValue, newValue))  # clamp value
      MusicControl.setValue(self, newValue)  # update value and call user function


class VFader(HFader):
   """Create a vertical fader (a slider) the user can drag up and down.

   The fader fills the box with corners (x1, y1) and (x2, y2).

   Args:
       x1 (int or float): The horizontal position of the top-left corner, in pixels.
       y1 (int or float): The vertical position of the top-left corner, in pixels.
       x2 (int or float): The horizontal position of the bottom-right corner, in pixels.
       y2 (int or float): The vertical position of the bottom-right corner, in pixels.
       minValue (int, optional): The smallest value the fader can take.
       maxValue (int, optional): The largest value the fader can take.
       startValue (int or float, optional): The fader's starting value. Defaults to halfway between minValue and maxValue.
       action (Callable, optional): The function to call when the fader moves; it receives the new value.
       foregroundColor (Color, optional): The color of the filled level.
       backgroundColor (Color, optional): The color behind the level.
       outlineColor (Color, optional): The outline color.
       thickness (int, optional): The outline thickness, in pixels.
       rotation (int or float, optional): How far to turn the fader, in degrees, counter-clockwise.
       visibility (int, optional): How visible the fader is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, x1, y1, x2, y2, minValue=0, maxValue=999, startValue=None, action=None, foregroundColor=Color.RED, backgroundColor=Color.BLACK, outlineColor=Color.BLACK, thickness=3, rotation=0, visibility=100):
      """"""
      HFader.__init__(self, x1, y1, x2, y2, minValue, maxValue, startValue,
                      action, foregroundColor, backgroundColor,
                      outlineColor, thickness, rotation, visibility)

   def __str__(self):
      x1, y1          = self._backgroundShape.getPosition()
      width, height   = self._backgroundShape.getSize()
      x2              = x1 + width
      y2              = y1 + height
      foregroundColor = self._foregroundShape.getColor()
      backgroundColor = self._backgroundShape.getColor()
      outlineColor    = self._outlineShape.getColor()
      thickness       = self._outlineShape.getThickness()
      rotation        = self.getRotation()
      return f'VFader(x1 = {x1}, y1 = {y1}, x2 = {x2}, y2 = {y2}, minValue = {self._minValue}, maxValue = {self._maxValue}, startValue = {self.getValue()}, action = {self._action}, foreground = {foregroundColor}, background = {backgroundColor}, outline = {outlineColor}, thickness = {thickness}, rotation = {rotation}, visibility = {self.getVisibility()})'

   # OVERRIDDEN METHODS
   def _defaultAction(self, ex, ey):
      """"""
      # update fader value based on mouse position on the fader
      fy = self._backgroundShape.getY()  # visual fader position
      y  = ey - fy                       # local event position

      valueRatio = 1- (y / self._backgroundShape.getHeight())  # (0.0 - 1.0)
      valueRatio = max(0.0, min(1.0, valueRatio))              # clamp ratio
      valueRange = self._maxValue - self._minValue             # possible values
      newValue   = self._minValue + (valueRatio * valueRange)  # scale to range
      self.setValue(newValue)                                  # update value

   def _updateAppearance(self):
      """"""
      valueRatio = (self._value - self._minValue) / (self._maxValue - self._minValue)  # (0.0 - 1.0)
      width, height = self._backgroundShape.getSize()
      x,     y      = self._backgroundShape.getPosition()
      padding       = self._outlineShape.getThickness() / 2

      fWidth  = (width  - (2 * padding))  # find maximum fader bar dimensions
      fHeight = (height - (2 * padding))  # ...
      fx      = x + padding               # ...
      fy      = y + padding               # ...
      # As the ratio decreases, the fader bar's height decreases,
      # while its y position increases downward, giving the illusion
      # of shrinking.  We do a little algebra to offset y appropriately.
      fy      = fy + (fHeight * (1 - valueRatio))
      fHeight = fHeight * valueRatio

      # size first, then position: in the new model resizing pins the center, so we
      # set the size and then move the top-left to where the bar should start
      self._foregroundShape.setSize(fWidth, fHeight)
      self._foregroundShape.setPosition(fx, fy)

   def setValue(self, newValue):
      """Set the fader's value.

      The value is in the fader's own minValue–maxValue range. The fill moves to match,
      and the update function is called.

      Args:
          newValue (int or float): The new value, between minValue and maxValue.
      """
      newValue = max(self._minValue, min(self._maxValue, newValue))  # clamp value
      MusicControl.setValue(self, newValue)  # update value and call user function


class Rotary(MusicControl):
   """Create a rotary knob the user can turn.

   The knob fills the box with corners (x1, y1) and (x2, y2). Its lowest and highest
   values sit at the bottom, and it turns through arcWidth degrees in between.

   Args:
       x1 (int or float): The horizontal position of the top-left corner, in pixels.
       y1 (int or float): The vertical position of the top-left corner, in pixels.
       x2 (int or float): The horizontal position of the bottom-right corner, in pixels.
       y2 (int or float): The vertical position of the bottom-right corner, in pixels.
       minValue (int, optional): The smallest value the knob can take.
       maxValue (int, optional): The largest value the knob can take.
       startValue (int or float, optional): The knob's starting value. Defaults to halfway between minValue and maxValue.
       action (Callable, optional): The function to call when the knob turns; it receives the new value.
       foregroundColor (Color, optional): The color of the level shown by the knob.
       backgroundColor (Color, optional): The color behind the knob.
       outlineColor (Color, optional): The outline color.
       thickness (int, optional): The outline thickness, in pixels.
       arcWidth (int or float, optional): How far the knob turns from lowest to highest, in degrees. A typical value is 300.
       rotation (int or float, optional): How far to turn the whole control, in degrees, counter-clockwise.
       visibility (int, optional): How visible the knob is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, x1, y1, x2, y2, minValue=0, maxValue=999, startValue=None, action=None, foregroundColor=Color.RED, backgroundColor=Color.BLACK, outlineColor=Color.BLUE, thickness=3, arcWidth=300, rotation=0, visibility=100):
      """"""
      MusicControl.__init__(self, action)

      # calculate dimensions
      localX     = min(x1, x2)
      localY     = min(y1, y2)
      width      = abs(x1 - x2)
      height     = abs(y1 - y2)
      startAngle = 90 + arcWidth//2
      endAngle   = startAngle + arcWidth

      # initialize internal shapes
      self._backgroundShape = Arc(
         0, 0, width, height,
         startAngle, endAngle,
         style=PIE,
         color=backgroundColor,
         fill=True,
         thickness=0,
         rotation=0
      )
      self._foregroundShape = Arc(
         0, 0, width, height,
         startAngle, endAngle,
         style=PIE,
         color=foregroundColor,
         fill=True,
         thickness=0,
         rotation=0
      )
      self._outlineShape = Arc(
         0, 0, width, height,
         startAngle, endAngle,
         style=PIE,
         color=outlineColor,
         fill=False,
         thickness=thickness,
         rotation=0
      )

      self.add(self._backgroundShape)
      self.add(self._foregroundShape)
      self.add(self._outlineShape)

      # set starting attributes
      self.setPosition(localX, localY)
      self.setRotation(rotation)
      self.setVisibility(visibility)

      if startValue is None:
         startValue = (minValue + maxValue) / 2

      self._minValue = minValue
      self._maxValue = maxValue
      self._arcWidth = arcWidth
      self.setValue(startValue)

      # register default behavior events
      self.onMouseDown(self._defaultAction)
      self.onMouseDrag(self._defaultAction)

   def __str__(self):
      x1, y1          = self._backgroundShape.getPosition()
      width, height   = self._backgroundShape.getSize()
      x2              = x1 + width
      y2              = y1 + height
      foregroundColor = self._foregroundShape.getColor()
      backgroundColor = self._backgroundShape.getColor()
      outlineColor    = self._outlineShape.getColor()
      thickness       = self._outlineShape.getThickness()
      rotation        = self.getRotation()
      return f'Rotary(x1 = {x1}, y1 = {y1}, x2 = {x2}, y2 = {y2}, minValue = {self._minValue}, maxValue = {self._maxValue}, startValue = {self.getValue()}, action = {self._action}, foreground = {foregroundColor}, background = {backgroundColor}, outline = {outlineColor}, thickness = {thickness}, arcWidth = {self._arcWidth}, rotation = {rotation}, visibility = {self.getVisibility()})'

   # OVERRIDDEN METHODS
   def _defaultAction(self, ex, ey):
      """"""
      # update rotary value based on mouse position
      rx, ry = self._backgroundShape.getPosition()  # visual rotary position
      x = ex - rx                                   # local event position
      y = ey - ry                                   # ...

      width, height = self._backgroundShape.getSize()
      cx = width / 2                                       # local rotary center
      cy = height / 2                                      # ...
      dx = x - cx                                          # vector to event pos
      dy = cy - y                                          # ...
      mouseAngle = np.degrees(np.arctan2(dy, dx)) % 360    # angle (in degrees)
      startAngle = 90 + self._arcWidth/2                   # rotary start
      eventWidth = (startAngle - mouseAngle) % 360         # from start to mouse

      if 0 <= eventWidth <= self._arcWidth:  # skip if width outside of arc
         valueRatio = eventWidth / self._arcWidth                 # (0.0 - 1.0)
         valueRatio = max(0.0, min(1.0, valueRatio))              # clamp ratio
         valueRange = self._maxValue - self._minValue             # possible values
         newValue   = self._minValue + (valueRatio * valueRange)  # scale to range
         self.setValue(newValue)                                  # set value

   def _updateAppearance(self):
      """"""
      valueRatio = (self._value - self._minValue) / (self._maxValue - self._minValue)  # 0.0 to 1.0
      arcWidth   = self._arcWidth * valueRatio                                          # scale to value
      self._foregroundShape._setArcWidth(arcWidth)

   def setValue(self, newValue):
      """Set the knob's value.

      The value is in the knob's own minValue–maxValue range. The knob turns to match, and
      the update function is called.

      Args:
          newValue (int or float): The new value, between minValue and maxValue.
      """
      newValue = max(self._minValue, min(self._maxValue, newValue))  # clamp value
      MusicControl.setValue(self, newValue)  # update value and call user function


class Push(MusicControl):
   """Create a push-and-hold button.

   The button is on (True) only while it is held down. It fills the box with corners
   (x1, y1) and (x2, y2).

   Args:
       x1 (int or float): The horizontal position of the top-left corner, in pixels.
       y1 (int or float): The vertical position of the top-left corner, in pixels.
       x2 (int or float): The horizontal position of the bottom-right corner, in pixels.
       y2 (int or float): The vertical position of the bottom-right corner, in pixels.
       action (Callable, optional): The function to call when the button is pressed or released; it receives the new value.
       foregroundColor (Color, optional): The color while pressed.
       backgroundColor (Color, optional): The color behind the button.
       outlineColor (Color, optional): The outline color.
       thickness (int, optional): The outline thickness, in pixels.
       rotation (int or float, optional): How far to turn the button, in degrees, counter-clockwise.
       visibility (int, optional): How visible the button is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, x1, y1, x2, y2, action=None, foregroundColor=Color.RED, backgroundColor=Color.BLACK, outlineColor=Color.CLEAR, thickness=3, rotation=0, visibility=100):
      """"""
      MusicControl.__init__(self, action)

      # calculate dimensions
      localX  = min(x1, x2)
      localY  = min(y1, y2)
      width   = abs(x1 - x2)
      height  = abs(y1 - y2)
      padding = thickness//2 + 1

      # initialize internal shapes
      self._backgroundShape = Rectangle(
         0, 0, width, height,
         color=backgroundColor,
         fill=True,
         thickness=0,
         rotation=0
      )
      self._foregroundShape = Rectangle(
         padding, padding, (width - padding), (height - padding),
         color=foregroundColor,
         fill=True,
         thickness=0,
         rotation=0
      )
      self._outlineShape = Rectangle(
         0, 0, width, height,
         color=outlineColor,
         fill=False,
         thickness=thickness,
         rotation=0
      )

      self.add(self._backgroundShape)
      self.add(self._foregroundShape)
      self.add(self._outlineShape)

      # set starting attributes
      self.setPosition(localX, localY)
      self.setRotation(rotation)
      self.setVisibility(visibility)
      self.setValue(False)

      # register default behavior events
      self.onMouseDown(self._defaultAction)
      self.onMouseUp(self._secondaryAction)
      self.onMouseExit(self._secondaryAction)

   def __str__(self):
      x1, y1          = self._backgroundShape.getPosition()
      width, height   = self._backgroundShape.getSize()
      x2              = x1 + width
      y2              = y1 + height
      foregroundColor = self._foregroundShape.getColor()
      backgroundColor = self._backgroundShape.getColor()
      outlineColor    = self._outlineShape.getColor()
      thickness       = self._outlineShape.getThickness()
      rotation        = self.getRotation()
      return f'Push(x1 = {x1}, y1 = {y1}, x2 = {x2}, y2 = {y2}, action = {self._action}, foreground = {foregroundColor}, background = {backgroundColor}, outline = {outlineColor}, thickness = {thickness}, rotation = {rotation}, visibility = {self.getVisibility()})'

   # OVERRIDDEN METHODS
   def _defaultAction(self, ex, ey):
      """"""
      # this event triggers only on mouseDown
      self.setValue(True)

   def _secondaryAction(self, ex, ey):
      """"""
      # this event triggers on mouseUp or mouseExit
      self.setValue(False)

   def _updateAppearance(self):
      """"""
      if self._value:
         self._foregroundShape._show()
      else:
         self._foregroundShape._hide()
   
   def getValue(self):
      """Report whether the button is currently held down.

      Returns:
          value (bool): True if the button is held down, False otherwise.
      """
      value = bool(self._value)
      return value
   
   def setValue(self, newValue):
      """Set whether the button is pressed.

      Redraws the button and calls its update function.

      Args:
          newValue (bool): True to press the button, False to release it.
      """
      if newValue != self._value:  # only update if value has changed
         self._value = newValue
         self._updateAppearance()
         if (self._action is not None) and callable(self._action):
            self._action(self._value)  # call user function


class Toggle(Push):
   """Create a toggle button that switches on and off with each click.

   The button fills the box with corners (x1, y1) and (x2, y2).

   Args:
       x1 (int or float): The horizontal position of the top-left corner, in pixels.
       y1 (int or float): The vertical position of the top-left corner, in pixels.
       x2 (int or float): The horizontal position of the bottom-right corner, in pixels.
       y2 (int or float): The vertical position of the bottom-right corner, in pixels.
       action (Callable, optional): The function to call when the toggle changes; it receives the new value.
       foregroundColor (Color, optional): The color when on.
       backgroundColor (Color, optional): The color behind the toggle.
       outlineColor (Color, optional): The outline color.
       thickness (int, optional): The outline thickness, in pixels.
       rotation (int or float, optional): How far to turn the toggle, in degrees, counter-clockwise.
       visibility (int, optional): How visible the toggle is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, x1, y1, x2, y2, action=None, foregroundColor=Color.RED, backgroundColor=Color.BLACK, outlineColor=Color.CLEAR, thickness=3, rotation=0, visibility=100):
      """"""
      Push.__init__(self, x1, y1, x2, y2, action, foregroundColor, backgroundColor, outlineColor, thickness, rotation, visibility)

   def __str__(self):
      x1, y1          = self._backgroundShape.getPosition()
      width, height   = self._backgroundShape.getSize()
      x2              = x1 + width
      y2              = y1 + height
      foregroundColor = self._foregroundShape.getColor()
      backgroundColor = self._backgroundShape.getColor()
      outlineColor    = self._outlineShape.getColor()
      thickness       = self._outlineShape.getThickness()
      rotation        = self.getRotation()
      return f'Toggle(x1 = {x1}, y1 = {y1}, x2 = {x2}, y2 = {y2}, action = {self._action}, foreground = {foregroundColor}, background = {backgroundColor}, outline = {outlineColor}, thickness = {thickness}, rotation = {rotation}, visibility = {self.getVisibility()})'

   # OVERRIDDEN METHODS
   def _defaultAction(self, ex, ey):
      """"""
      self.setValue(not self._value)

   def _secondaryAction(self, ex, ey):
      """"""
      pass


class XYPad(MusicControl):
   """Create an XY pad, a 2-D control whose value follows a bubble the user drags.

   The pad fills the box with corners (x1, y1) and (x2, y2). Its value is an (x, y) pair
   giving the bubble's position within the pad.

   Args:
       x1 (int or float): The horizontal position of the top-left corner, in pixels.
       y1 (int or float): The vertical position of the top-left corner, in pixels.
       x2 (int or float): The horizontal position of the bottom-right corner, in pixels.
       y2 (int or float): The vertical position of the bottom-right corner, in pixels.
       action (Callable, optional): The function to call when the bubble moves; it receives the new [x, y] value.
       foregroundColor (Color, optional): The color of the bubble.
       backgroundColor (Color, optional): The color behind the bubble.
       outlineColor (Color, optional): The outline color.
       outlineThickness (int, optional): The outline thickness, in pixels.
       trackerRadius (int or float, optional): The radius of the bubble, in pixels.
       crosshairThickness (int, optional): The thickness of the crosshair lines, in pixels. Defaults to the outline thickness.
       rotation (int or float, optional): How far to turn the pad, in degrees, counter-clockwise.
       visibility (int, optional): How visible the pad is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, x1, y1, x2, y2, action=None, foregroundColor=Color.RED, backgroundColor=Color.BLACK, outlineColor=Color.CLEAR, outlineThickness=2, trackerRadius=10, crosshairThickness=None, rotation=0, visibility=100):
      """"""
      MusicControl.__init__(self, action)

      # calculate dimensions
      localX  = min(x1, x2)
      localY  = min(y1, y2)
      width   = abs(x1 - x2)
      height  = abs(y1 - y2)

      if crosshairThickness is None:
         crosshairThickness = outlineThickness

      # initialize internal shapes
      self._backgroundShape = Rectangle(
         0, 0, width, height,
         color=backgroundColor,
         fill=True,
         thickness=0,
         rotation=0
      )
      self._trackerXLine = Line(
         0, 0, 0, height,  # vertical line
         color=foregroundColor,
         thickness=crosshairThickness,
         rotation=0
      )
      self._trackerYLine = Line(
         0, 0, width, 0,  # horizontal line
         color=foregroundColor,
         thickness=crosshairThickness,
         rotation=0
      )
      self._foregroundShape = Circle(
         width/2, height/2,
         trackerRadius,
         color=foregroundColor,
         fill=False,
         thickness=crosshairThickness
         )
      self._outlineShape = Rectangle(
         0, 0, width, height,
         color=outlineColor,
         fill=False,
         thickness=outlineThickness,
         rotation=0
      )

      self.add(self._backgroundShape)
      self.add(self._trackerXLine)
      self.add(self._trackerYLine)
      self.add(self._foregroundShape)
      self.add(self._outlineShape)

      # set starting attributes
      self.setPosition(localX, localY)
      self.setRotation(rotation)
      self.setVisibility(visibility)
      self.setValue(width/2, height/2)

      # register default behavior events
      self.onMouseDown(self._defaultAction)
      self.onMouseDrag(self._defaultAction)

   def __str__(self):
      x1, y1             = self._backgroundShape.getPosition()
      width, height      = self._backgroundShape.getSize()
      x2                 = x1 + width
      y2                 = y1 + height
      foregroundColor    = self._foregroundShape.getColor()
      backgroundColor    = self._backgroundShape.getColor()
      outlineColor       = self._outlineShape.getColor()
      outlineThickness   = self._outlineShape.getThickness()
      trackerRadius      = self._foregroundShape.getRadius()
      crosshairThickness = self._foregroundShape.getThickness()
      rotation           = self.getRotation()

      return f'XYPad(x1 = {x1}, y1 = {y1}, x2 = {x2}, y2 = {y2}, action = {self._action}, foreground = {foregroundColor}, background = {backgroundColor}, outline = {outlineColor}, outlineThickness = {outlineThickness}, trackerRadius = {trackerRadius}, crosshairThickness = {crosshairThickness}, rotation = {rotation}, visibility = {self.getVisibility()})'

   # OVERRIDDEN METHODS
   def _foregroundShapes(self):
      """"""
      # an XYPad's foreground is the bubble plus its two crosshair lines
      return [self._foregroundShape, self._trackerXLine, self._trackerYLine]

   def _defaultAction(self, ex, ey):
      """"""
      mx, my = self._backgroundShape.getPosition()  # visual XYPad position
      x = ex - mx                                   # local event position
      y = ey - my                                   # ...
      self.setValue(x, y)

   def _updateAppearance(self):
      """"""
      vx, vy = self._value                          # local value position
      mx, my = self._backgroundShape.getPosition()  # visual XYPad position
      x = mx + vx                                   # visual value position
      y = my + vy                                   # ...

      self._trackerXLine.setX(x)
      self._trackerYLine.setY(y)
      self._foregroundShape.setCenter(x, y)

   def getValue(self):
      """Return the bubble's position within the pad.

      Returns:
          x (int or float): The horizontal position of the bubble within the pad, in pixels.
          y (int or float): The vertical position of the bubble within the pad, in pixels.
      """
      x, y = self._value
      return x, y

   def setValue(self, x, y):
      """Set the bubble's position within the pad.

      Positions outside the pad are clamped to its edges. Moves the bubble and calls the
      update function.

      Args:
          x (int or float): The new horizontal position within the pad, in pixels.
          y (int or float): The new vertical position within the pad, in pixels.
      """
      width, height = self._backgroundShape.getSize()
      x = max(0, min(x, width))            # clamp values
      y = max(0, min(y, height))           # ...
      MusicControl.setValue(self, [x, y])  # update value and call user function


#######################################################################################
# Control - system-styled interactable objects
#######################################################################################
class Control(Drawable):
   """Provide the shared behavior of the system-styled widgets.

   Control is a base class. You do not create one yourself. Button, CheckBox, Slider,
   DropDownList, TextField, and TextArea inherit from it. These widgets look like your
   operating system's own controls.

   Like any drawable object, a control can be moved, turned, made bigger or smaller, and
   faded. Two things to know about its size: resizing a control with setSize() keeps its
   text at the normal size and just makes the control's box bigger or smaller, while
   putting a control in a Group and resizing the group scales the whole control, text and
   all.
   """
   def __init__(self):
      Drawable.__init__(self)
      self._action = None   # the function called when the user uses this control

   def onAction(self, action):
      """Set up a function to call when the user uses this control.

      This is the same function you can pass when you create the control. Use it to set
      that function later, or to change it. Pass None to remove it. A text area has no
      such action.

      Args:
          action (Callable): The function to call when the control is used. What it
              receives depends on the control: a Button's gets nothing, a CheckBox's gets
              True or False, a Slider's gets the value, a DropDownList's gets the chosen
              item, and a TextField's gets the typed text.
      """
      self._action = action

   def _refit(self):
      """"""
      currentLeft, currentTop = self.getPosition()
      result = _handler().sendQuery('getSize', self._objectId)
      self._baseWidth  = result[0]
      self._baseHeight = result[1]
      self.setPosition(currentLeft, currentTop)

#######################################################################################
class Button(Control):
   """Create a clickable button.

   Args:
       text (str, optional): The text shown on the button.
       action (Callable, optional): The function to call each time the button is pressed; it receives no parameters.
       color (Color, optional): The button color.
       rotation (int or float, optional): How far to turn the button, in degrees, counter-clockwise.
       visibility (int, optional): How visible the button is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, text='', action=None, color=Color.LIGHT_GRAY, rotation=0, visibility=100):
      """"""
      Control.__init__(self)

      self._action = action
      self._color  = color.getRGBA()

      _handler().sendCommand('create', self._objectId, {
         'type':  'Button',
         'text':  str(text),
         'color': self._color,
      })

      self._refit()

      # always register, so onAction() can set or change the function later
      def _onClicked():
         if self._action is not None and callable(self._action):
            self._action()
      _handler().registerEvent(self._objectId, 'clicked', _onClicked)

      self.setRotation(rotation)
      self.setVisibility(visibility)

   def __str__(self):
      return f'Button(text = "{self.getText()}", action = {self._action}, color = {self.getColor()}, rotation = {self.getRotation()}, visibility = {self.getVisibility()})'

   def getText(self):
      """Return the button's text.

      Returns:
          text (str): The text shown on the button.
      """
      text = _handler().sendQuery('getText', self._objectId)[0]
      return text

   def setText(self, text):
      """Set the button's text.

      Args:
          text (str): The new text to show on the button.
      """
      _handler().sendCommand('setText', self._objectId, {'text': str(text)})
      self._refit()

   def getColor(self):
      """Return the button's color.

      Returns:
          color (Color): The button's background color.
      """
      color = Color(*self._color)
      return color

   def setColor(self, color=None):
      """Set the button's color.

      Colors the button's background; its text stays black so it remains easy to read.

      Args:
          color (Color, optional): The new button background color. If omitted, a color-selection dialog opens.
      """
      if color is None:
         color = Color()  # default color brings up color select dialog
      if not isinstance(color, Color):
         raise TypeError(f'{type(self).__name__}.setColor(): color should be a Color object (it was {type(color).__name__})')
      r, g, b, a  = color.getRGBA()
      self._color  = [r, g, b, a]
      _handler().sendCommand('setColor', self._objectId, {'color': self._color})


class CheckBox(Control):
   """Create a checkbox the user can check and uncheck.

   Args:
       text (str, optional): The text shown beside the checkbox.
       action (Callable, optional): The function to call when the checkbox changes; it receives one parameter, True if it was just checked or False if it was just unchecked.
       color (Color, optional): The checkbox color.
       rotation (int or float, optional): How far to turn the checkbox, in degrees, counter-clockwise.
       visibility (int, optional): How visible the checkbox is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, text='', action=None, color=Color.CLEAR, rotation=0, visibility=100):
      """"""
      Control.__init__(self)

      self._action = action
      self._color  = color.getRGBA()

      _handler().sendCommand('create', self._objectId, {
         'type':  'CheckBox',
         'text':  str(text),
         'color': self._color,
      })

      self._refit()

      # always register, so onAction() can set or change the function later
      def _onStateChanged(checked):
         if self._action is not None and callable(self._action):
            self._action(checked)
      _handler().registerEvent(self._objectId, 'stateChanged', _onStateChanged)

      self.setRotation(rotation)
      self.setVisibility(visibility)

   def __str__(self):
      return f'CheckBox(text = "{self.getText()}", action = {self._action}, color = {self.getColor()}, rotation = {self.getRotation()}, visibility = {self.getVisibility()})'

   def getText(self):
      """Return the checkbox's text.

      Returns:
          text (str): The text shown beside the checkbox.
      """
      text = _handler().sendQuery('getText', self._objectId)[0]
      return text

   def setText(self, text):
      """Set the checkbox's text.

      Args:
          text (str): The new text to show beside the checkbox.
      """
      _handler().sendCommand('setText', self._objectId, {'text': str(text)})
      self._refit()

   def getColor(self):
      """Return the checkbox's color.

      Returns:
          color (Color): The color filling the area behind the box and its label.
      """
      color = Color(*self._color)
      return color

   def setColor(self, color=None):
      """Set the checkbox's color.

      Colors the area behind the box and its label; the label text stays black so it
      remains easy to read.

      Args:
          color (Color, optional): The new checkbox color. If omitted, a color-selection dialog opens.
      """
      if color is None:
         color = Color()  # default color brings up color select dialog
      if not isinstance(color, Color):
         raise TypeError(f'{type(self).__name__}.setColor(): color should be a Color object (it was {type(color).__name__})')
      r, g, b, a  = color.getRGBA()
      self._color  = [r, g, b, a]
      _handler().sendCommand('setColor', self._objectId, {'color': self._color})

   def isChecked(self):
      """Report whether the checkbox is checked.

      Returns:
          isChecked (bool): True if the checkbox is checked, False otherwise.
      """
      isChecked = _handler().sendQuery('isChecked', self._objectId)[0]
      return isChecked

   def check(self):
      """Check the checkbox.

      Works just like the user clicking it: if the box was not already checked, it becomes
      checked and the checkbox's function is called with True.
      """
      _handler().sendCommand('check', self._objectId)

   def uncheck(self):
      """Uncheck the checkbox.

      Works just like the user clicking it: if the box was already checked, it becomes
      unchecked and the checkbox's function is called with False.
      """
      _handler().sendCommand('uncheck', self._objectId)


class Slider(Control):
   """Create a slider the user can drag to choose a value.

   Args:
       orientation (int, optional): The slider direction, either HORIZONTAL or VERTICAL.
       minValue (int, optional): The smallest value the slider can take.
       maxValue (int, optional): The largest value the slider can take.
       startValue (int or float, optional): The slider's starting value. Defaults to halfway between minValue and maxValue.
       action (Callable, optional): The function to call when the slider moves; it receives one parameter, the new value.
       color (Color, optional): The color of the slider's handle and the filled part of its track.
       rotation (int or float, optional): How far to turn the slider, in degrees, counter-clockwise.
       visibility (int, optional): How visible the slider is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, orientation=HORIZONTAL, minValue=0, maxValue=100, startValue=None, action=None, color=Color.LIGHT_GRAY, rotation=0, visibility=100):
      """"""
      Control.__init__(self)

      if startValue is None:
         startValue = int((minValue + maxValue) / 2)

      self._action    = action
      self._orientation = orientation
      self._minValue    = minValue
      self._maxValue    = maxValue
      self._color       = color.getRGBA()

      _handler().sendCommand('create', self._objectId, {
         'type':        'Slider',
         'orientation': orientation,
         'minValue':    minValue,
         'maxValue':    maxValue,
         'startValue':  startValue,
         'color':       self._color,
      })

      self._refit()

      # always register, so onAction() can set or change the function later
      def _onValueChanged(value):
         if self._action is not None and callable(self._action):
            self._action(value)
      _handler().registerEvent(self._objectId, 'valueChanged', _onValueChanged)

      self.setRotation(rotation)
      self.setVisibility(visibility)

   def __str__(self):
      return f'Slider(orientation = {self._orientation}, minValue = {self._minValue}, maxValue = {self._maxValue}, startValue = {self.getValue()}, action = {self._action}, color = {self.getColor()}, rotation = {self.getRotation()}, visibility = {self.getVisibility()})'

   def getColor(self):
      """Return the slider's color.

      Returns:
          color (Color): The color of the handle and the filled part of the track.
      """
      color = Color(*self._color)
      return color

   def setColor(self, color=None):
      """Set the slider's color.

      Colors the handle and the filled part of the track (the part up to the handle).

      Args:
          color (Color, optional): The new slider color. If omitted, a color-selection dialog opens.
      """
      if color is None:
         color = Color()  # default color brings up color select dialog
      if not isinstance(color, Color):
         raise TypeError(f'{type(self).__name__}.setColor(): color should be a Color object (it was {type(color).__name__})')
      r, g, b, a  = color.getRGBA()
      self._color  = [r, g, b, a]
      _handler().sendCommand('setColor', self._objectId, {'color': self._color})

   def getValue(self):
      """Return the slider's current value.

      Returns:
          value (int or float): The current value, between minValue and maxValue.
      """
      value = _handler().sendQuery('getValue', self._objectId)[0]
      return value

   def setValue(self, value):
      """Set the slider's value.

      Works just like the user dragging the slider: if the value changes, the slider moves
      to match and the slider's function is called with the new value.

      Args:
          value (int or float): The new value, between minValue and maxValue.
      """
      _handler().sendCommand('setValue', self._objectId, {'value': int(value)})


class DropDownList(Control):
   """Create a drop-down list the user can pick one item from.

   Args:
       items (list[str], optional): The items to show, for example ["item1", "item2", "item3"].
       action (Callable, optional): The function to call when an item is picked; it receives one parameter, the selected item as a string.
       color (Color, optional): The list color.
       rotation (int or float, optional): How far to turn the list, in degrees, counter-clockwise.
       visibility (int, optional): How visible the list is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, items=[], action=None, color=Color.LIGHT_GRAY, rotation=0, visibility=100):
      """"""
      Control.__init__(self)

      self._action = action
      self._items    = list(items)
      self._color    = color.getRGBA()

      _handler().sendCommand('create', self._objectId, {
         'type':  'DropDownList',
         'items': self._items,
         'color': self._color,
      })

      self._refit()

      # always register, so onAction() can set or change the function later
      def _onActivated(index):
         if self._action is not None and callable(self._action):
            self._action(self._items[index])
      _handler().registerEvent(self._objectId, 'activated', _onActivated)

      self.setRotation(rotation)
      self.setVisibility(visibility)

   def __str__(self):
      return f'DropDownList(items = {self._items}, action = {self._action}, color = {self.getColor()}, rotation = {self.getRotation()}, visibility = {self.getVisibility()})'

   def getColor(self):
      """Return the drop-down list's color.

      Returns:
          color (Color): The list's background color.
      """
      color = Color(*self._color)
      return color

   def setColor(self, color=None):
      """Set the drop-down list's color.

      Colors the list's background; its text stays black so it remains easy to read.

      Args:
          color (Color, optional): The new list color. If omitted, a color-selection dialog opens.
      """
      if color is None:
         color = Color()  # default color brings up color select dialog
      if not isinstance(color, Color):
         raise TypeError(f'{type(self).__name__}.setColor(): color should be a Color object (it was {type(color).__name__})')
      r, g, b, a  = color.getRGBA()
      self._color  = [r, g, b, a]
      _handler().sendCommand('setColor', self._objectId, {'color': self._color})


class TextField(Control):
   """Create a single-line text field the user can type into.

   Args:
       text (str, optional): The text to start with.
       columns (int, optional): The width of the field, in characters.
       action (Callable, optional): The function to call when the user presses Enter in the field; it receives one parameter, the field's contents as a string.
       color (Color, optional): The field color.
       font (Font, optional): The font, for example Font("Serif", Font.ITALIC, 16). If omitted, the default font is used.
       rotation (int or float, optional): How far to turn the field, in degrees, counter-clockwise.
       visibility (int, optional): How visible the field is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, text='', columns=8, action=None, color=Color.WHITE, font=None, rotation=0, visibility=100):
      """"""
      Control.__init__(self)

      self._action = action
      self._columns  = columns
      self._font     = None
      self._color    = color.getRGBA()

      _handler().sendCommand('create', self._objectId, {
         'type':    'TextField',
         'text':    str(text),
         'columns': columns,
         'color':   self._color,
         'font':    None,
      })

      self._refit()

      if font is not None:
         self.setFont(font)

      # always register, so onAction() can set or change the function later
      def _onReturnPressed(text):
         if self._action is not None and callable(self._action):
            self._action(text)
      _handler().registerEvent(self._objectId, 'returnPressed', _onReturnPressed)

      self.setRotation(rotation)
      self.setVisibility(visibility)

   def __str__(self):
      return f'TextField(text = "{self.getText()}", columns = {self._columns}, action = {self._action}, color = {self.getColor()}, font = {self.getFont()}, rotation = {self.getRotation()}, visibility = {self.getVisibility()})'

   def getText(self):
      """Return the text in the field.

      Returns:
          text (str): The field's contents.
      """
      text = _handler().sendQuery('getText', self._objectId)[0]
      return text

   def setText(self, text):
      """Set the text in the field.

      Args:
          text (str): The new contents of the field.
      """
      _handler().sendCommand('setText', self._objectId, {'text': str(text)})

   def getColor(self):
      """Return the field's color.

      Returns:
          color (Color): The field's background color.
      """
      color = Color(*self._color)
      return color

   def setColor(self, color=None):
      """Set the field's color.

      Colors the field's background; the text you type stays black so it remains easy to
      read.

      Args:
          color (Color, optional): The new field color. If omitted, a color-selection dialog opens.
      """
      if color is None:
         color = Color()  # default color brings up color select dialog
      if not isinstance(color, Color):
         raise TypeError(f'{type(self).__name__}.setColor(): color should be a Color object (it was {type(color).__name__})')
      r, g, b, a  = color.getRGBA()
      self._color  = [r, g, b, a]
      _handler().sendCommand('setColor', self._objectId, {'color': self._color})

   def getFont(self):
      """Return the field's font.

      Returns:
          font (Font): The field's font, or None if it uses the default font.
      """
      font = font = Font(*self._font) if self._font is not None else None
      return font

   def setFont(self, font):
      """Set the field's font.

      Args:
          font (Font): The new font, for example Font("Serif", Font.ITALIC, 16).
      """
      name       = font.getName()
      style      = font.getStyle()
      size       = font.getSize()
      self._font = [name, style, size]
      _handler().sendCommand('setFont', self._objectId, {'font': [name, style, size]})


class TextArea(Control):
   """Create a multi-line text area the user can type into.

   If the text is taller than the area, a scroll bar appears on the right.

   Args:
       text (str, optional): The text to start with.
       columns (int, optional): The width of the area, in characters.
       rows (int, optional): The height of the area, in lines.
       color (Color, optional): The area color.
       font (Font, optional): The font, for example Font("Serif", Font.ITALIC, 16). If omitted, the default font is used.
       rotation (int or float, optional): How far to turn the area, in degrees, counter-clockwise.
       visibility (int, optional): How visible the area is, from 0 (invisible) to 100 (fully visible).
   """
   def __init__(self, text='', columns=8, rows=5, color=Color.WHITE, font=None, rotation=0, visibility=100):
      """"""
      Control.__init__(self)

      self._columns = columns
      self._rows    = rows
      self._font    = None
      self._color   = color.getRGBA()

      _handler().sendCommand('create', self._objectId, {
         'type':    'TextArea',
         'text':    str(text),
         'columns': columns,
         'rows':    rows,
         'color':   self._color,
         'font':    None,
      })

      self._refit()

      if font is not None:
         self.setFont(font)

      self.setRotation(rotation)
      self.setVisibility(visibility)

   def __str__(self):
      return f'TextArea(text = "{self.getText()}", columns = {self._columns}, rows = {self._rows}, color = {self.getColor()}, font = {self.getFont()}, rotation = {self.getRotation()}, visibility = {self.getVisibility()})'

   def getText(self):
      """Return the text in the area.

      Returns:
          text (str): The area's contents.
      """
      text = _handler().sendQuery('getText', self._objectId)[0]
      return text

   def setText(self, text):
      """Set the text in the area.

      Args:
          text (str): The new contents of the area.
      """
      _handler().sendCommand('setText', self._objectId, {'text': str(text)})

   def getColor(self):
      """Return the area's color.

      Returns:
          color (Color): The area's background color.
      """
      color = Color(*self._color)
      return color

   def setColor(self, color=None):
      """Set the area's color.

      Colors the area's background; the text you type stays black so it remains easy to
      read.

      Args:
          color (Color, optional): The new area color. If omitted, a color-selection dialog opens.
      """
      if color is None:
         color = Color()  # default color brings up color select dialog
      if not isinstance(color, Color):
         raise TypeError(f'{type(self).__name__}.setColor(): color should be a Color object (it was {type(color).__name__})')
      r, g, b, a  = color.getRGBA()
      self._color  = [r, g, b, a]
      _handler().sendCommand('setColor', self._objectId, {'color': self._color})

   def getFont(self):
      """Return the area's font.

      Returns:
          font (Font): The area's font, or None if it uses the default font.
      """
      font = font = Font(*self._font) if self._font is not None else None
      return font

   def setFont(self, font):
      """Set the area's font.

      Args:
          font (Font): The new font, for example Font("Serif", Font.ITALIC, 16).
      """
      if font is not None:
         name       = font.getName()
         style      = font.getStyle()
         size       = font.getSize()
         self._font = [name, style, size]
         _handler().sendCommand('setFont', self._objectId, {'font': [name, style, size]})


class Menu():
   """Create a menu, for use on a display's menu bar or as a pop-up.

   Build a menu by adding items to it with addItem() or addItemList(), then attach it to
   a display with addMenu() (for the menu bar) or addPopupMenu() (for a right-click
   menu).

   Args:
       title (str): The menu's name, as shown on the menu bar.
   """

   def __init__(self, title):
      """"""
      self._objectId = _nextObjectId()
      self._name     = title
      self._actions  = []   # per-item callbacks; index matches itemIndex sent to renderer

      _handler().sendCommand('create', self._objectId, {
         'type':  'Menu',
         'title': str(title),
      })

      def _onItemTriggered(itemIndex):
         if 0 <= itemIndex < len(self._actions):
            action = self._actions[itemIndex]
            if callable(action):
               action()

      _handler().registerEvent(self._objectId, 'itemTriggered', _onItemTriggered)

   def __str__(self):
      return f'Menu(menuName = "{self._name}")'

   def __repr__(self):
      return str(self)

   def addItem(self, item='', action=None):
      """Add an item to the menu.

      Args:
          item (str, optional): The item's text, as shown in the menu.
          action (Callable, optional): The function to call when the item is selected; it receives no parameters.
      """
      itemIndex = len(self._actions)
      self._actions.append(action)
      _handler().sendCommand('addItem', self._objectId, {
         'text':      str(item),
         'itemIndex': itemIndex,
      })

   def addItemList(self, itemList=[''], actionList=[]):
      """Add several items to the menu at once.

      The two lists are parallel and must be the same length: each item's text is paired
      with the function to call when it is selected.

      Args:
          itemList (list[str], optional): The items' text.
          actionList (list[Callable], optional): The functions to call, one per item.
      """
      for i in range(len(itemList)):
         item   = itemList[i]
         action = actionList[i] if i < len(actionList) else None
         self.addItem(item, action)

   def addSeparator(self):
      """Add a separator line to the menu.

      Useful for grouping related items.
      """
      _handler().sendCommand('addSeparator', self._objectId)

   def addSubmenu(self, menu):
      """Add a submenu to the menu.

      Used to build nested, hierarchical menus.

      Args:
          menu (Menu): The menu to nest inside this one.
      """
      if not isinstance(menu, Menu):
         raise TypeError(f'{type(self).__name__}.addSubmenu(): menu should be a Menu object (it was {type(menu).__name__})')
      _handler().sendCommand('addSubmenu', self._objectId, {'submenuId': menu._objectId})

   def enable(self):
      """Enable the menu, so its items can be selected.
      """
      _handler().sendCommand('enable', self._objectId)

   def disable(self):
      """Disable the menu, graying it out so its items cannot be selected.
      """
      _handler().sendCommand('disable', self._objectId)


#######################################################################################
# Tests
#######################################################################################

if __name__ == "__main__":
   pass
