import wx
import images
import time
from math import sin, cos, pi
import threading
import thread
import random
import ScoreKeeper

EVT_RESULT_ID = wx.NewId()
EVT_STARTLISTENER_ID = wx.NewId()
EVT_STOPLISTENER_ID = wx.NewId()

DARTBOARD_REFMAG = 380
DARTBOARD_REFANG = pi/20

DARTBOARD_TAN = '#F4E5C8'
DARTBOARD_BLACK = '#1C1D18'
DARTBOARD_RED = '#DD5035'
DARTBOARD_GREEN = '#03845B'

DARTS_HOME_POS = [ (10, 200), (10, 250), (10, 300), (760, 200), (760, 250), (760, 300)]

DART_CENTER_X = 500.0
DART_CENTER_Y = 250.0

def LISTEN_EVENT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_RESULT_ID, func)

class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, action, player, dartNum, dart):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.action = action
        self.player = player
        self.dartNum = dartNum
        self.dart = dart
        
class MyCanvas(wx.Panel):
    def __init__(self, parent, id,):
        wx.Panel.__init__(self, parent, id)

        self.SetBackgroundColour('#D18B3D')
        bmp = images.DartImage1.GetBitmap()
        mask = wx.Mask(bmp, '#010000') #make transparent bg
        bmp.SetMask(mask)
        self.bmp = bmp
        
        # dart ids
        self.objids = []
        self.objmovable = []
        
        # create a PseudoDC to record our drawing
        self.pdc = wx.PseudoDC()
        self.DoDrawing(self.pdc)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda x:None)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouse)
        
        # vars for handling mouse clicks
        self.dragid = -1
        self.lastpos = (0,0)

    def OnMouse(self, event):
        if event.LeftDown():
            x,y = event.GetX(), event.GetY()
            l = self.pdc.FindObjects(x, y, 5)
            for id in l:
                self.dragid = id
                self.lastpos = (event.GetX(),event.GetY())
                break
        elif event.Dragging() or event.LeftUp():
            if self.dragid != -1:
                if self.objmovable[self.objids.index(self.dragid)]:
                    x,y = self.lastpos
                    dx = event.GetX() - x
                    dy = event.GetY() - y
                    r = self.pdc.GetIdBounds(self.dragid)       #get the previous location
                    self.pdc.TranslateId(self.dragid, dx, dy)   #find the new x,y
                    r2 = self.pdc.GetIdBounds(self.dragid)      #get the new location
                    r = r.Union(r2)                             #combine the two rectangles
                    r.Inflate(4,4)                              #inflate to compensate
                    self.RefreshRect(r, False)                  #repaint the rectangle
                    self.lastpos = (event.GetX(),event.GetY())
            if event.LeftUp():
                self.dragid = -1
                #correctScore.set()

    def OnPaint(self, event):
        # Create a buffered paint DC.  It will create the real
        # wx.PaintDC and then blit the bitmap to it when dc is
        # deleted.  
        dc = wx.BufferedPaintDC(self)
        #print 'paint'
        # use PrepateDC to set position correctly
        self.PrepareDC(dc)
        # we need to clear the dc BEFORE calling PrepareDC
        bg = wx.Brush(self.GetBackgroundColour())
        dc.SetBackground(bg)
        dc.Clear()
        
        rect = wx.Rect(0, 0, 250,500)
        rect.SetPosition((0, 0))
        dc.GradientFillLinear(rect, '#2A6E31', '#389442', wx.NORTH)
        dc.DrawText("Player 1", 30, 40)
        rect.SetPosition((750, 0))
        dc.GradientFillLinear(rect, '#2A6E31', '#389442', wx.NORTH)
        dc.DrawText("Player 2", 780, 40)
        rect.SetPosition((20, 80))
        
        rgn = self.GetUpdateRegion()
        r = rgn.GetBox()
        # repair only damaged window
        self.pdc.DrawToDCClipped(dc,r)

    def DoDrawing(self, dc):
        #Draw the dart board
        self.DoDrawDartBoard(dc)
    
        dc.BeginDrawing()
        for i in range(6):
            id = wx.NewId()
            dc.SetId(id)
            w,h = self.bmp.GetSize()
            x, y = DARTS_HOME_POS[i]
            dc.DrawBitmap(self.bmp,x,y,True)
            dc.SetIdBounds(id,wx.Rect(x,y,w,h))
            self.objids.append(id)
            self.objmovable.append(False)
        dc.EndDrawing()
        
    def DoDrawDartBoard(self, dc):
        dc.SetPen(wx.Pen('black', 1))
        
        #Centre of dartboard
        x = DART_CENTER_X
        y = DART_CENTER_Y
        
        #wire thickness 1.5 mm
        radii = [ 223.68,   170.0,   162.0,   107.0,   99.0,  31.8/2,  12.7/2] #in mm
        #radii = [250, 190, 178, 120, 110, 18, 10]
        
        #Outer circle, full solid
        dc.SetBrush(wx.Brush(DARTBOARD_BLACK))
        dc.DrawCircle(x, y, 19.0/17.0*radii[0])
        
        ringcolours = [DARTBOARD_GREEN, DARTBOARD_RED]
        areacolours = [DARTBOARD_TAN, DARTBOARD_BLACK]
        
        #Draw Sectors, outside in
        for circle in range(1,5):
            colourpair = ringcolours if circle % 2 == 1 else areacolours
            for sector in range(20):
                theta1 = sector*pi/10 + DARTBOARD_REFANG
                theta2 = (sector-1)*pi/10 + DARTBOARD_REFANG
                x1 = x+19.0/17.0*radii[circle]*cos(theta1)
                y1 = y+19.0/17.0*radii[circle]*sin(theta1)
                x2 = x+19.0/17.0*radii[circle]*cos(theta2)
                y2 = y+19.0/17.0*radii[circle]*sin(theta2)
                colour = colourpair[sector%2]
                dc.SetBrush(wx.Brush(colour))
                dc.DrawArc(x1, y1, x2, y2, x, y)
                #sector 15 is the top
        
        dc.SetBrush(wx.Brush(DARTBOARD_GREEN))
        dc.DrawCircle(x, y, 19.0/17.0*radii[5])
        dc.SetBrush(wx.Brush(DARTBOARD_RED))
        dc.DrawCircle(x, y, 19.0/17.0*radii[6])    
    
    def MoveDart(self, dartNum, p, movable):
        dartID = self.objids[dartNum]
        self.objmovable[dartNum] = movable
        r = self.pdc.GetIdBounds(dartID)
        dx = p[0] - r[0]
        dy = p[1] - r[1]        
        self.pdc.TranslateId(dartID, dx, dy)
        r2 = self.pdc.GetIdBounds(dartID)
        r = r.Union(r2)
        r.Inflate(4,4)
        self.RefreshRect(r, False)
    
class ListenerThread(threading.Thread):
    def __init__(self, parent_window):
        """init listener thread class"""
        threading.Thread.__init__(self)
        self.parent_window = parent_window
        self.DoClose = 0
        self.start()
        
    def run(self):
        """Start Listener Thread."""
        player = 1
        dartnum = 1
        while 1:
            if updateUI.isSet():
                #Get last dart in current dart set
                lastDart = None;
                
                currentDartSet = scoreKeeper.currentDartSet
                
                i = -1
                
                for dart in currentDartSet:
                    if dart != None:
                        lastDart = dart
                        i += 1
                    else:
                        break
                
                if lastDart == None:
                    wx.PostEvent(self.parent_window, ResultEvent("reset", scoreKeeper.currentPlayer, i, lastDart))
                else:
                    wx.PostEvent(self.parent_window, ResultEvent("update", scoreKeeper.currentPlayer, i, lastDart))
                    
                updateUI.clear()
        
            #if self.DoClose:
            #    wx.PostEvent(self.parent_window, ResultEvent(None))
            #    return
            #wx.PostEvent(self.parent_window, ResultEvent(dart))
        
    def close(self):
        """Close Listener Thread."""
        self.DoClose = 1
        print 'Listener Terminated'
        
#AppGUI is instance of application.  This initializes all the widgets
class AppGUI(wx.App):
    def __init__(self):
        wx.App.__init__(self, redirect=False)
        
    def OnInit(self):
    
        #----------------------------------------------------------
        #Create a frame
        frame = wx.Frame(None, -1, title='Rene Desdartes', size=(1000, 580),
                        style=wx.DEFAULT_FRAME_STYLE)
        #----------------------------------------------------------
        #Create menubar and status bar and bind events
        menuBar = wx.MenuBar()
        fileMenu = wx.Menu()
        
        fileMenu.Append(EVT_STARTLISTENER_ID, "&New Game", "Starts a new game")
        self.Bind(wx.EVT_MENU, self.StartGame, id=EVT_STARTLISTENER_ID)
        
        fileMenu.Append(EVT_STOPLISTENER_ID, "&End Game", "Starts a new game")
        self.Bind(wx.EVT_MENU, self.StopGame, id=EVT_STOPLISTENER_ID)
        
        fileMenu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Exit Application")
        self.Bind(wx.EVT_MENU, self.OnClose, id=wx.ID_EXIT)
        
        menuBar.Append(fileMenu, "&File")
        frame.SetMenuBar(menuBar)

        frame.CreateStatusBar()
        
        #frame.SetTransparent(150)
        #----------------------------------------------------------
        #Create event handler for listening
        LISTEN_EVENT(self, self.OnListen)
        self.listener = None
        #----------------------------------------------------------
        #Create panel as drawing surface
        panel = MyCanvas(frame, wx.ID_ANY)
        panel.SetFocus()
        self.panel = panel
        
        #----------------------------------------------------------
        frame.Show(True)
        frame.Fit()
        
        self.SetTopWindow(frame)
        self.frame = frame 
        return True
               
    def StartGame (self, event):
        """Start second thread for listening to events"""
        if not self.listener: #only have one listener
            #self.status.SetLabel('Listening')
            print 'listening'
            self.listener = ListenerThread(self)
    
    def StopGame (self, event):
        """Stop second thread for listening to events"""
        if self.listener:
            #self.status.SetLabel('Game Stopped')
            print 'Stop'
            self.listener.close()
    
    def OnClose (self, event):
        if self.listener:
            self.listener.close() #close the listener thread
            print 'Close'
        self.frame.Close()
        
    def OnListen(self, event):
        """Listened"""
        if event.action is None:
            # Thread aborted (using our convention of None return)
            print 'aborted'
            self.listener = None
        elif event.action == "update":
            if event.player == scoreKeeper.playerOne:
                dartNum  = event.dartNum
            else:
                dartNum = event.dartNum + 3
            
            x = DART_CENTER_X + event.dart.magnitude/DARTBOARD_REFMAG*190*cos(event.dart.angle)
            y = DART_CENTER_Y - event.dart.magnitude/DARTBOARD_REFMAG*190*sin(event.dart.angle)
            
            self.panel.MoveDart(dartNum, (x, y), True)
            
        elif event.action == "reset":
            for i in range(6):
                self.panel.MoveDart(i, DARTS_HOME_POS[i], False)
        
        
class GUIThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
    def run(self):
        self.App = AppGUI()
        self.App.MainLoop()
    
    def initUIEvent(self, event):
        global updateUI
        updateUI = event
        
    def initCorrectScoreEvent(self, event):
        global correctScore
        correctScore = event
    
    def initScoreKeeper(self, object):
        global scoreKeeper
        scoreKeeper = object