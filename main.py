#!/usr/bin/env python
"""
Hello World, but with more meat.
"""

import wx, wxutils
import pota

class MainAppFrame(wx.Frame):
    """
    The main window for POTAScan
    """
    
    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(MainAppFrame, self).__init__(*args, **kw)

        # create a panel in the frame
        pnl = wx.Panel(self)


        # This vertical sizer holds the various sections of our program
        vbox = wx.BoxSizer(wx.VERTICAL)
        pnl.SetSizer(vbox)

        # This holds our spots
        # TODO: Grid?
        gs_spots = wx.WrapSizer(orient=wx.HORIZONTAL)
        # FIXME: Move this to button, etc
        pc = pota.PotaSpotController()
        pc.refresh()
        demo_spots = map(lambda x: self.createSpotPanel(pnl, x['activator'], x['reference'], x['frequency']),
                          pc.getSpots(mode=pota.Mode.SSB))
        for spot in demo_spots: 
            gs_spots.Add(spot, 0, flag = wx.ALL, border=5)


        vbox.Add(gs_spots, 1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)

        # Line for seperation
        vbox.Add(wx.StaticLine(pnl), 0, wx.ALL|wx.EXPAND, 5)


        vbox.Add(self.radioSection(pnl), 0, flag=wx.ALL, border=10)



        # create a menu bar
        self.makeMenuBar()

        # TODO: Toolbar goes here

        # TODO: Output real status
        # and a status bar
        self.CreateStatusBar()
        self.SetStatusText("Welcome to wxPython!")

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