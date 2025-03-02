#!/usr/bin/env python
"""
POTAScan is a utility to download spots from POTA and automatically tune a radio to them, moving to the next spot every N seconds.

-- Benjamin, WY2K

Copyright (C) 2023-2025 Benjamin Seidenberg

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import wx, wx.lib.scrolledpanel, wx.lib.intctrl
import pota
import platform
import Hamlib

# Button labels
SCAN_START_LABEL = "Scan"
SCAN_STOP_LABEL = "Stop"

# Version info
APP_VERSION = "0.1.0"

# Window defaults
DEFAULT_WINDOW_SIZE = (1200, 800)
DEFAULT_SCAN_INTERVAL = 5

def isMac():
    return platform.system() == "Darwin"

BAND_STRINGS_TO_BANDS ={
    "ALL" : None,
    "10 Meters": pota.Band.METERS_10,
    "12 Meters": pota.Band.METERS_12,
    "15 Meters": pota.Band.METERS_15,
    "17 Meters": pota.Band.METERS_17,
    "20 Meters": pota.Band.METERS_20,
    "30 Meters": pota.Band.METERS_30,
    "40 Meters": pota.Band.METERS_40,
    "80 Meters": pota.Band.METERS_80,
    "160 Meters": pota.Band.METERS_160
}

MODE_STRINGS_TO_MODES = {
    "SSB": pota.Mode.SSB,
    "CW": pota.Mode.CW
}

class SpotWidget(wx.StaticBoxSizer):
    '''A widget to represent spots. Also contains business logic for scanning and rig interface'''
    # Class-level attributes will be initialized when wx.App exists
    ACTIVE_BG = None
    ACTIVE_FG = None
    INACTIVE_BG = None
    INACTIVE_FG = None

    @classmethod
    def initColors(cls):
        """Initialize the color constants after wx.App exists"""
        if cls.ACTIVE_BG is None:  # Only initialize once
            cls.ACTIVE_BG = wx.Colour(0x00, 0x64, 0x00)  # Dark green
            cls.ACTIVE_FG = wx.Colour(wx.WHITE)
            cls.INACTIVE_BG = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
            cls.INACTIVE_FG = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)

    def __init__(self, parent, call, park, freq, rig=None, *args, **kw):
        self.box = wx.StaticBox(parent, label=call)
        self.box.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_MENU))
        super().__init__(self.box, wx.VERTICAL, *args, **kw)
        self.labels = [
            wx.StaticText(parent, label="PARK: " + park),
            wx.StaticText(parent, label="Freq: " + freq)
        ]
        for label in self.labels:
            label.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_MENUTEXT))
            self.Add(label, 0, flag=wx.ALL, border=5)

        self.freq = freq
        self.rig = rig

    def MakeActive(self):
        self.box.SetBackgroundColour(self.ACTIVE_BG)
        for label in self.labels:
            label.SetForegroundColour(self.ACTIVE_FG)

        # On Linux (and Windows, if the docs are to be believed), the label
        # is in front of the background. On mac it's not - the background is
        # only the inside of the box
        if not isMac():
            self.box.SetForegroundColour(self.ACTIVE_FG)

        if self.rig:
            # Actually tune the rig!
            hlfreq = int(float(self.freq) * 1e3)
            self.rig.set_freq(Hamlib.RIG_VFO_CURR, hlfreq)
            # At least for my icom, the auto mode switching (USB/LSB) does not happen
            # if the frequency is set via CAT - so set it explicitly
            mode = Hamlib.RIG_MODE_USB if hlfreq > 1e7 else Hamlib.RIG_MODE_LSB
            self.rig.set_mode(mode) 

    def Reset(self):
        self.box.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_MENU))
        for label in self.labels:
            label.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_MENUTEXT))
        self.box.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_MENUTEXT))


    def GetFreq(self):
        return self.freq


class MainAppFrame(wx.Frame):
    """
    The main window for POTAScan
    """

    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(MainAppFrame, self).__init__(*args, **kw)

        # Rig object
        self.rig = None

        # Initialize SpotWidget colors after wx is initialized
        SpotWidget.initColors()

        # This seems like a good default size
        # TODO: Min Size?
        self.SetSize(wx.Size(DEFAULT_WINDOW_SIZE))

        # Menu and Toolbar
        self.makeMenuBar()
        self.makeToolbar()

        # create a panel in the frame
        self.pnl = wx.Panel(self)

        # This vertical sizer holds the various sections of our program
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.pnl.SetSizer(vbox)

        # This holds our spots
        self.sizer_spots = wx.WrapSizer(orient=wx.HORIZONTAL)
        # Put it in a scrolled window so the spots can be scrolled
        # TODO: Scrolling doesn't work right when the contents shrink
        self.scrpanel = wx.ScrolledWindow(self.pnl, style=wx.VSCROLL)
        self.scrpanel.SetScrollRate(10, 10)
        self.scrpanel.SetSizer(self.sizer_spots)

        # Add to our top-level sizer
        vbox.Add(self.scrpanel, 1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)

        # Line for seperation
        vbox.Add(wx.StaticLine(self.pnl), 0, wx.ALL|wx.EXPAND, 5)

        # Here's where we have the controls for the radio
        vbox.Add(self.radioSection(self.pnl), 0, flag=wx.ALL, border=10)

        # We also want a status bar because we're a real mid-2000s looking program
        # TODO: Output real status
        self.CreateStatusBar()
        self.SetStatusText("POTAScan v" + APP_VERSION)

        # We're done with the GUI stuff! Here's some business logic!
        # Timer that we'll use for scanning
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.nextSpot)
        # Initialize the POTA spot controller and load the current spots
        self.pc = pota.PotaSpotController()
        self.pc.refresh()
        ''' This is used to track the active spot during span'''
        self.current_spot = None
        self.OnSpotRedraw(None)
        '''Are we currently scanning?'''
        self.scan_active = False


    def radioSection(self, parent):
        ''' Draws the Radio Controls section of the GUI '''
        # We have stuff laid out horizontally
        hbox_radio = wx.BoxSizer(wx.HORIZONTAL)

        # Port Selection
        txt_port = wx.StaticText(parent, label="rigctld port: ")
        hbox_radio.Add(txt_port, proportion=0, flag=wx.ALIGN_CENTER_VERTICAL)
        self.int_rigctl_port = wx.lib.intctrl.IntCtrl(parent, value=4532)
        hbox_radio.Add(self.int_rigctl_port, proportion=0, flag=wx.EXPAND|wx.ALL, border=5)

        self.btn_connect = wx.Button(parent, label="Connect")
        hbox_radio.Add(self.btn_connect, proportion=0, flag=wx.EXPAND|wx.ALL, border=5)

        # Seperate
        # TODO: This is a hack and there ought to be a much better way to do it
        #       Figure that out and fix it
        hbox_radio.AddStretchSpacer(prop=5)
        hbox_radio.Add(wx.StaticText(parent, label="               "), proportion=1)
        hbox_radio.AddStretchSpacer(prop=5)

        # The interval selection
        txt_speed = wx.StaticText(parent, label="Interval: ")
        hbox_radio.Add(txt_speed, proportion=0, flag=wx.ALIGN_CENTER_VERTICAL)
        self.spin_interval = wx.SpinCtrl(parent, min=0, max=60, initial=DEFAULT_SCAN_INTERVAL, style=wx.SP_ARROW_KEYS)
        hbox_radio.Add(self.spin_interval, proportion=0, flag=wx.ALL, border=5)
        self.Bind(wx.EVT_SPINCTRL, self.OnIntervalSpin, self.spin_interval)

        # And now, our scan button
        self.btn_scan = wx.Button(parent, label=SCAN_START_LABEL)
        self.btn_scan.Disable() # Disabled until we connect
        hbox_radio.Add(self.btn_scan, proportion=0, flag=wx.EXPAND|wx.ALL, border=5)

        # Button action
        self.Bind(wx.EVT_BUTTON, self.OnConnect, self.btn_connect)
        self.Bind(wx.EVT_BUTTON, self.ToggleScan, self.btn_scan)

        return hbox_radio


    def makeMenuBar(self):
        """
        A menu bar is composed of menus, which are composed of menu items.
        This method builds a set of menus and binds handlers to be called
        when the menu item is selected.
        """

        # Make a file menu with Hello and Exit items
        fileMenu = wx.Menu()
        # When using a stock ID we don't need to specify the menu item's
        # label
        exitItem = fileMenu.Append(wx.ID_EXIT)

        # Now a help menu for the about item
        helpMenu = wx.Menu()
        aboutItem = helpMenu.Append(wx.ID_ABOUT)

        # Make the menu bar and add the two menus to it. The '&' defines
        # that the next letter is the "mnemonic" for the menu item. On the
        # platforms that support it those letters are underlined and can be
        # triggered from the keyboard.
        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, "&File")
        menuBar.Append(helpMenu, "&Help")

        # Give the menu bar to the frame
        self.SetMenuBar(menuBar)

        # Finally, associate a handler function with the EVT_MENU event for
        # each of the menu items. That means that when that menu item is
        # activated then the associated handler function will be called.
        self.Bind(wx.EVT_MENU, self.OnExit,  exitItem)
        self.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)

    def makeToolbar(self):
        # TODO: Toolbars look like crap on Mac - make a hbox sizer instead
        toolbar = self.CreateToolBar(style=wx.TB_TEXT)
        try:
            refresh =  wx.ArtProvider.GetBitmapBundle(wx.ART_REDO)
        except AttributeError:
            # Older versions of wxPython (<4.1) don't have the above
            refresh = wx.ArtProvider.GetBitmap(wx.ART_REDO)

        refresh = toolbar.AddTool(wx.ID_REFRESH, "Reload", refresh)

        toolbar.AddSeparator()

        toolbar.AddControl(wx.StaticText( toolbar, wx.ID_ANY, "Mode:"))
        self.combo_mode = wx.ComboBox(toolbar, value="SSB", style=wx.CB_READONLY, choices=list(MODE_STRINGS_TO_MODES))
        toolbar.AddControl(self.combo_mode, label="Modes")

        toolbar.AddSeparator()

        toolbar.AddControl(wx.StaticText( toolbar, wx.ID_ANY, "Band:"))
        self.combo_bands = wx.ComboBox(toolbar, value="ALL", style=wx.CB_READONLY, choices=list(BAND_STRINGS_TO_BANDS))
        toolbar.AddControl(self.combo_bands, label="Bands")

        # All of these result in redrawing the spots
        self.Bind(wx.EVT_TOOL, self.OnSpotRedraw, refresh)
        self.Bind(wx.EVT_COMBOBOX, self.OnSpotRedraw, self.combo_bands)
        self.Bind(wx.EVT_COMBOBOX, self.OnSpotRedraw, self.combo_mode)

        toolbar.Realize()

    def OnSpotRedraw(self, event):
        self.resetScan()
        # We only refresh on the refresh button
        if event is not None and event.GetEventType() == wx.wxEVT_TOOL and event.GetId() == wx.ID_REFRESH:
            self.pc.refresh()
        # TODO: Stop Scan
        self.sizer_spots.Clear(delete_windows=True)
        band = BAND_STRINGS_TO_BANDS[self.combo_bands.GetValue()]
        mode = MODE_STRINGS_TO_MODES[self.combo_mode.GetValue()]

        # Pass the rig instance to each SpotWidget
        self.spots = list(map(lambda x: SpotWidget(self.scrpanel, x['activator'], 
                                                  x['reference'], x['frequency'], 
                                                  rig=self.rig),
                          self.pc.getSpots(mode=mode, band=band)))

        for spot in self.spots:
            self.sizer_spots.Add(spot, 0, flag = wx.ALL, border=5)
        self.scrpanel.Layout()

    def OnConnect(self, event):
        Hamlib.rig_set_debug(Hamlib.RIG_DEBUG_NONE)
        self.rig = Hamlib.Rig(rig_model=Hamlib.RIG_MODEL_NETRIGCTL)
        self.rig.set_conf("rig_pathname", ":" + str(self.int_rigctl_port.GetValue()))

        self.rig.open()
        # Were we successful?
        if (self.rig.error_status != 0):
            msg = "Unable to open rig!\n\n"
            msg += "An error occured: "
            errorstr = Hamlib.rigerror2(self.rig.error_status)
            msg += errorstr
            if errorstr.startswith("IO error"):
                msg += "(wrong rigctld port or rigctld not running?)"
            dlg=wx.MessageDialog(None, msg, "Error", wx.OK|wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # Success! Enable scan and disable ourselves
        self.btn_connect.SetLabel("Connected!")
        self.btn_connect.Disable()
        self.btn_scan.Enable()

    def resetScan(self):
        self.scan_active = False
        self.timer.Stop()
        self.btn_scan.SetLabel(SCAN_START_LABEL)
        if (self.current_spot is not None):
            self.current_spot.Reset()
            self.current_spot = None

    def nextSpot(self, event):
        '''Function to move to the next spot'''
        # Find the next spot
        # TODO: Test this with one spot
        if (self.spots is None or len(self.spots) == 0):
            return # Bail if we have nothing
        if (self.current_spot is not None):
            i = self.spots.index(self.current_spot)
            next = self.spots[(i+1) % len(self.spots)]
            # Reset the current - do it here since we know it's not None
            self.current_spot.Reset()
        else:
            # We haven't started scanning - grab the first
            next = self.spots[0]

        # Go to the next spot
        next.MakeActive()
        # Update the state
        self.current_spot = next

    def ToggleScan(self, event):
        # Scan on
        if not self.scan_active:
            self.scan_active = True
            self.btn_scan.SetLabel(SCAN_STOP_LABEL)
            self.nextSpot(None)
            self.timer.Start(int(self.spin_interval.GetValue()) * 1000)
        # Scan Off
        else:
            self.scan_active = False
            self.timer.Stop()
            self.btn_scan.SetLabel(SCAN_START_LABEL)

    def OnIntervalSpin(self, event):
        '''Resets the interval on the timer iff it's running'''
        if self.timer.IsRunning():
            self.timer.Stop()
            # I can probably get the new interval from the event but eh
            self.timer.Start(int(self.spin_interval.GetValue()) * 1000)

    def OnExit(self, event):
        """Close the frame, terminating the application."""
        if self.rig:
            self.rig.close()
        self.Close(True)

    def OnAbout(self, event):
        """Display an About Dialog"""
        wx.MessageBox("POTAScan v" + APP_VERSION + " by WY2K",
                      "About POTAScan",
                      wx.OK|wx.ICON_INFORMATION)


if __name__ == '__main__':
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    frm = MainAppFrame(None, title='POTAScan v' + APP_VERSION)
    frm.Show()
    app.MainLoop()
