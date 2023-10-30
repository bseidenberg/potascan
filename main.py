#!/usr/bin/env python
"""
Hello World, but with more meat.
"""

import wx, wxutils, wx.lib.scrolledpanel
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

class MainAppFrame(wx.Frame):
    """
    The main window for POTAScan
    """
    
    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(MainAppFrame, self).__init__(*args, **kw)
        self.SetSize(wx.Size(1200,800))

            # Initialize the POTA spot controller
        self.pc = pota.PotaSpotController()


        # create a panel in the frame
        self.pnl = wx.Panel(self)


        # This vertical sizer holds the various sections of our program
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.pnl.SetSizer(vbox)

        # This holds our spots
        # TODO: Scrolling still isn't working
        self.sizer_spots = wx.WrapSizer(orient=wx.HORIZONTAL)

        self.scrpanel = wx.ScrolledWindow(self.pnl, style=wx.VSCROLL)
        self.scrpanel.SetScrollRate(10, 10)

        self.scrpanel.SetSizer(self.sizer_spots)

        vbox.Add(self.scrpanel, 1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)


        # Line for seperation
        vbox.Add(wx.StaticLine(self.pnl), 0, wx.ALL|wx.EXPAND, 5)


        vbox.Add(self.radioSection(self.pnl), 0, flag=wx.ALL, border=10)



        # create a menu bar
        self.makeMenuBar()

        # TODO: Toolbar goes here
        self.makeToolbar()

        # TODO: Output real status
        # and a status bar
        self.CreateStatusBar()
        self.SetStatusText("POTAScan v0.0.1")
        self.pc.refresh()
        self.OnSpotRedraw(None)



    def createSpotPanel(self, parent, call, park, freq):
        # TODO: Figure out scrolling
        box = wx.StaticBox(parent, label=call)
        box.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOXHIGHLIGHTTEXT))
        spot_pnl = wx.StaticBoxSizer(box, wx.VERTICAL)
        spot_pnl.Add(wx.StaticText(parent, label="PARK: " + park), 0, flag=wx.ALL, border=5)
        spot_pnl.Add(wx.StaticText(parent, label="Freq: " + freq), 0, flag=wx.ALL, border=5)
        return spot_pnl



    def radioSection(self, parent):
        # Now the radio section (TODO: Refactor to function)
        hbox_radio = wx.BoxSizer(wx.HORIZONTAL)
        txt_speed = wx.StaticText(parent, label="Interval: ")
        hbox_radio.Add(txt_speed, proportion=0, flag=wx.ALIGN_CENTER_VERTICAL)
        spin_interval = wx.SpinCtrl(parent, min=0, max=60, initial=10, style=wx.SP_ARROW_KEYS)
        hbox_radio.Add(spin_interval, proportion=0, flag=wx.ALL, border=5)
        btn_scan = wxutils.Button(parent, "Scan", action=None)
        hbox_radio.Add(btn_scan, proportion=0, flag=wx.EXPAND|wx.ALL, border=5)
        return hbox_radio


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
        refresh = toolbar.AddTool(wx.ID_REFRESH, "Reload", wx.ArtProvider.GetBitmapBundle(wx.ART_REDO))
        toolbar.AddControl(wx.StaticText( toolbar, wx.ID_ANY, "Band:"))

        toolbar.AddControl(self.combo_bands, label="Bands")

        toolbar.Realize()
        self.Bind(wx.EVT_TOOL, self.OnSpotRedraw, refresh)
        self.Bind(wx.EVT_COMBOBOX, self.OnSpotRedraw, self.combo_bands)
    
    def OnSpotRedraw(self, event):
        # We only refresh on the refresh button
        if event is not None and event.GetEventType() == wx.wxEVT_TOOL and event.GetId() == wx.ID_REFRESH:
            self.pc.refresh()
        self.sizer_spots.Clear(delete_windows=True)
        band = BAND_STRINGS_TO_BANDS[self.combo_bands.GetValue()]

        demo_spots = map(lambda x: self.createSpotPanel(self.scrpanel, x['activator'], x['reference'], x['frequency']),
                          self.pc.getSpots(mode=pota.Mode.SSB, band=band))
        
        for spot in demo_spots: 
            self.sizer_spots.Add(spot, 0, flag = wx.ALL, border=5)
        self.scrpanel.Layout()


        


    def OnExit(self, event):
        """Close the frame, terminating the application."""
        self.Close(True)


    def OnHello(self, event):
        """Say hello to the user."""
        wx.MessageBox("Hello again from wxPython")


    def OnAbout(self, event):
        """Display an About Dialog"""
        wx.MessageBox("This is a wxPython Hello World sample",
                      "About Hello World 2",
                      wx.OK|wx.ICON_INFORMATION)


if __name__ == '__main__':
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    frm = MainAppFrame(None, title='POTAScan v0.1')
    frm.Show()
    app.MainLoop()