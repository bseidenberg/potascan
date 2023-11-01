#!/usr/bin/env python
"""
Hello World, but with more meat.
"""

import wx, wx.lib.scrolledpanel
import pota

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

class SpotWidget(wx.StaticBoxSizer):
    '''A widget to represent spots. Also contains business logic for scanning and [FIXME: Confirm?] rig interface'''
    def __init__(self, parent, call, park, freq, *args, **kw):
        self.box = wx.StaticBox(parent, label=call)
        self.box.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOXHIGHLIGHTTEXT))
        super().__init__(self.box, wx.VERTICAL, *args, **kw)
        self.Add(wx.StaticText(parent, label="PARK: " + park), 0, flag=wx.ALL, border=5)
        self.Add(wx.StaticText(parent, label="Freq: " + freq), 0, flag=wx.ALL, border=5)
        self.freq = freq

    def MakeActive(self):
        # TODO: Color to constant, yadda yadda
        self.box.SetBackgroundColour(wx.Colour(0, 255, 0))

    def Reset(self):
        self.box.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOXHIGHLIGHTTEXT))

    def GetFreq(self):
        return self.freq


class MainAppFrame(wx.Frame):
    """
    The main window for POTAScan
    """

    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(MainAppFrame, self).__init__(*args, **kw)

        # This seems like a good default size
        # TODO: Min Size?
        self.SetSize(wx.Size(1200,800))

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
        self.SetStatusText("POTAScan v0.0.1") # $5 says I forget to increment this

        # We're done with the GUI stuff! Here's some business logic!
        # Initialize the POTA spot controller and load the current spots
        self.pc = pota.PotaSpotController()
        self.pc.refresh()
        self.OnSpotRedraw(None)
        ''' This is used to track the active spot during span'''
        self.current_spot = None


    ''' Draws the Radio Controls section of the GUI '''
    def radioSection(self, parent):
        # We have stuff laid out horizontally
        hbox_radio = wx.BoxSizer(wx.HORIZONTAL)

        # The interval selection
        txt_speed = wx.StaticText(parent, label="Interval: ")
        hbox_radio.Add(txt_speed, proportion=0, flag=wx.ALIGN_CENTER_VERTICAL)
        spin_interval = wx.SpinCtrl(parent, min=0, max=60, initial=10, style=wx.SP_ARROW_KEYS)
        hbox_radio.Add(spin_interval, proportion=0, flag=wx.ALL, border=5)

        # And now, our scan button
        btn_scan = wx.Button(parent, label="Scan")
        hbox_radio.Add(btn_scan, proportion=0, flag=wx.EXPAND|wx.ALL, border=5)

        # TODO FIXME: Temp bind
        self.Bind(wx.EVT_BUTTON, self.nextSpot, btn_scan)

        return hbox_radio


    # TODO: This is still boilerplate from the getting started
    def makeMenuBar(self):
        """
        A menu bar is composed of menus, which are composed of menu items.
        This method builds a set of menus and binds handlers to be called
        when the menu item is selected.
        """

        # Make a file menu with Hello and Exit items
        fileMenu = wx.Menu()
        # The "\t..." syntax defines an accelerator key that also triggers
        # the same event
        helloItem = fileMenu.Append(-1, "&Hello...\tCtrl-H",
                "Help string shown in status bar for this menu item")
        fileMenu.AppendSeparator()
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
        self.Bind(wx.EVT_MENU, self.OnHello, helloItem)
        self.Bind(wx.EVT_MENU, self.OnExit,  exitItem)
        self.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)

    def makeToolbar(self):
        toolbar = self.CreateToolBar(style=wx.TB_TEXT)
        self.combo_bands = wx.ComboBox(toolbar, value="ALL", style=wx.CB_READONLY, choices=list(BAND_STRINGS_TO_BANDS))
        try:
            refresh =  wx.ArtProvider.GetBitmapBundle(wx.ART_REDO)
        except AttributeError:
            # Older versions of wxPython (<4.1) don't have the above
            refresh = wx.ArtProvider.GetBitmap(wx.ART_REDO)

        refresh = toolbar.AddTool(wx.ID_REFRESH, "Reload", refresh)
        toolbar.AddControl(wx.StaticText( toolbar, wx.ID_ANY, "Band:"))

        toolbar.AddControl(self.combo_bands, label="Bands")

        toolbar.Realize()
        self.Bind(wx.EVT_TOOL, self.OnSpotRedraw, refresh)
        self.Bind(wx.EVT_COMBOBOX, self.OnSpotRedraw, self.combo_bands)

    def OnSpotRedraw(self, event):
        # We only refresh on the refresh button
        if event is not None and event.GetEventType() == wx.wxEVT_TOOL and event.GetId() == wx.ID_REFRESH:
            self.pc.refresh()
        # TODO: Stop Scan
        self.sizer_spots.Clear(delete_windows=True)
        band = BAND_STRINGS_TO_BANDS[self.combo_bands.GetValue()]

        # We have to maintain this as a class member because I can't make sizer.GetItems() do what I want
        self.spots = list(map(lambda x: SpotWidget(self.scrpanel, x['activator'], x['reference'], x['frequency']),
                          self.pc.getSpots(mode=pota.Mode.SSB, band=band)))

        for spot in self.spots:
            self.sizer_spots.Add(spot, 0, flag = wx.ALL, border=5)
        self.scrpanel.Layout()


    '''Function to move to the next spot'''
    def nextSpot(self, event):
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
        self.current_spot = next;


    def OnExit(self, event):
        """Close the frame, terminating the application."""
        self.Close(True)


    # FIXME: Boilerplate, cleanup
    def OnHello(self, event):
        """Say hello to the user."""
        wx.MessageBox("Hello again from wxPython")


    def OnAbout(self, event):
        """Display an About Dialog"""
        # TODO: Make this sync with the status bar
        wx.MessageBox("POTAScan v0.0.1 by WY2K",
                      "About POTAScan",
                      wx.OK|wx.ICON_INFORMATION)


if __name__ == '__main__':
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    frm = MainAppFrame(None, title='POTAScan v0.1')
    frm.Show()
    app.MainLoop()
