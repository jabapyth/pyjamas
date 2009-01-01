from pyjamas.ui import Button, RootPanel
from pyjamas.ui import Label, Grid, CellFormatter, RowFormatter
from pyjamas.ui import HTMLTable, TextBox
from pyjamas.ui import KeyboardListener
from pyjamas import Window


class GridEdit:
    def onModuleLoad(self):
        
        self.input = TextBox()
        self.input.setEnabled(False)
        self.input.addKeyboardListener(self)

        self.g=Grid()
        self.g.resize(5, 5)
        self.g.setHTML(0, 0, "<b>Grid Edit</b>")
        self.g.setBorderWidth(2)
        self.g.setCellPadding(4)
        self.g.setCellSpacing(1)
        self.g.setWidth("500px")
        self.g.setHeight("120px")
        self.g.addTableListener(self)
        
        self.initGrid()
        RootPanel().add(self.input)
        RootPanel().add(self.g)

    def onKeyDown(self, sender, keycode, modifiers):
        pass

    def onKeyUp(self, sender, keycode, modifiers):
        pass

    def onKeyPress(self, sender, keycode, modifiers):
        if keycode == KeyboardListener.KEY_ESCAPE:
            self.input.setEnabled(False)
        elif keycode == KeyboardListener.KEY_ENTER:
            self.input.setEnabled(False)
            val = self.input.getText()
            self.set_grid_value(self.row, self.col, val)
            
    def onCellClicked(self, sender, row, col):
        self.row = row
        self.col = col
        val = self.values[row][col]
        self.input.setText(val)
        self.input.setEnabled(True)

    def set_grid_value(self, row, col, val):
        self.values[row][col] = val
        if val == "":
            val = "&nbsp;"
        self.g.setHTML(row, col, val)

    def initGrid(self):
        
        self.values = {}
        for y in range(5):
            self.values[y] = {}
            for x in range(5):
                self.values[y][x] = ""
        for y in range(5):
            for x in range(5):
                val = self.values[y][x]
                self.set_grid_value(y, x, val)




