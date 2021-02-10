# -*- coding: utf-8 -*-

import wx
from pathlib import Path
from backend import FixExif


# This one handles the view on the left

class TreeViewer(wx.TreeCtrl):
    def __init__(self, parent, textbox, backend):
        self.textbox = textbox
        self.backend = backend  # where the actual data will be stored
        self.tree_ui = None  # where the ui tree will be stored
        super().__init__(parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                         wx.TR_HAS_BUTTONS | wx.TR_HIDE_ROOT | wx.TR_SINGLE)
        self.update_ui_tree()  # fill the tree view
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.__on_selection_change)

    def update_ui_tree(self):
        if self.tree_ui is not None:
            self.DeleteAllItems()
        self.tree_ui = self.AddRoot("Folders")  # create the ui tree data structure from scratch
        if self.backend.folders is not None:
            for f in self.backend.folders:
                node = self.AppendItem(self.tree_ui, f)
                self.SetItemData(node, f)  # save a copy of the folder name in the item
            self.SetFocusedItem(self.GetLastChild(self.tree_ui))  # changes the focus
            # self.Expand(self.tree_ui)

    def __on_selection_change(self, event):
        item = event.GetItem()
        if item is not None:
            assert type(item) == wx.TreeItemId
            folder = self.GetItemData(item)
            self.textbox.ChangeValue(
                f"This folder contains {len(self.backend.get_all_files([folder]))} WhatsApp media files (videos and "
                f"images)")
            # from https://docs.wxpython.org/wx.TextCtrl.html#wx-textctrl , Change value won't trigger the edit event


class MainPanel(wx.Panel):

    def __init__(self, parent, backend):
        super().__init__(parent)
        self.backend = backend
        self.textCtrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.ALIGN_TOP | wx.TE_READONLY)
        self.treeCtrl = TreeViewer(self, self.textCtrl, backend)
        self.applyButton = wx.Button(self)
        self.applyButton.SetLabelText("Apply")
        self.applyButton.Bind(wx.EVT_BUTTON, self.on_apply_button_click)
        self.fix_backend_printer()
        self.__set_layout()

    def fix_backend_printer(self):  # TODO find a better way to achieve this
        self.backend.Ui.set_textbox(self.textCtrl)

    def __set_layout(self):
        # First param is always the parent. Readonly cause the root shouldn't be writeable
        # All of this sizer thing is magic. The 1 must be kept as such otherwise the items will be shrunk. I had
        # followed about 8 guides, none of them worked, i ended up with a broken ui, plus some segfaults cause yeah.
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer.Add(self.treeCtrl, 1, wx.ALL | wx.EXPAND)  # place the tree into this sizer
        h_sizer.AddSpacer(0)  # probably useless

        right_sizer = wx.BoxSizer(wx.VERTICAL)
        right_sizer.Add(self.textCtrl, 1, wx.ALL | wx.EXPAND)
        right_sizer.Add(self.applyButton, 1, wx.ALL | wx.EXPAND)
        # The 1 is for the proportion
        h_sizer.Add(right_sizer, 1, wx.ALL | wx.EXPAND)
        h_sizer.AddSpacer(0)
        self.SetSizer(h_sizer)

    def on_apply_button_click(self, evcmd):
        msgbox = wx.MessageBox(
            "Have you made a backup copy of your images/videos?\nIf yes, and your folder isn't on a microSD, "
            "press Ok to start the procedure.",
            "Warning", wx.OK | wx.CANCEL | wx.CANCEL_DEFAULT | wx.ICON_INFORMATION)
        if msgbox == wx.OK:
            self.textCtrl.ChangeValue("Starting...\n")
            self.backend.fix_files()
            self.TopLevelParent.SetTitle('Whatsapp Media Timeline Fixer [applied]')
            wx.MessageBox("Finished!", "", wx.OK | wx.ICON_INFORMATION)


class MainFrame(wx.Frame):  # Main container 4 all the UI stuff

    def __init__(self, backend):
        super().__init__(parent=None, title='Whatsapp Media Timeline Fixer')  # Builds the window
        # A frame requires a panel inside
        self.backend = backend  # No ui there
        self.panel = MainPanel(self, backend)
        self.menu = wx.Menu()
        self.menu_bar = wx.MenuBar()
        self.shortcutsTable = None
        self.keyboardShortcuts = None

        self.__create_menu()
        self.Show()

    def __create_open_entry(self):
        self.keyboardShortcuts = {"open": wx.AcceleratorEntry()}
        self.keyboardShortcuts["open"].Set(wx.ACCEL_CTRL, ord('O'), wx.ID_OPEN)
        open_menu_entry = self.menu.Append(wx.ID_OPEN, "Open folder... (Ctrl+O)")
        self.Bind(wx.EVT_MENU, self.__on_open_click, open_menu_entry)

    def __create_about_entry(self):
        about_entry = self.menu.Append(wx.ID_ABOUT, "About", "You are curious. I like u :)")
        self.Bind(wx.EVT_MENU, self.__on_about_click, about_entry)

    def __create_menu(self):
        self.__create_open_entry()
        self.__create_about_entry()

        self.menu_bar.Append(self.menu, "File")
        self.SetMenuBar(self.menu_bar)
        self.shortcutsTable = wx.AcceleratorTable([self.keyboardShortcuts[key] for key in self.keyboardShortcuts])
        self.SetAcceleratorTable(self.shortcutsTable)
        self.Show()

    def __on_open_click(self, event):
        #  not sure about the None here
        openFileDialog = wx.DirDialog(None, "Open folders with photos/videos", "Folder with photos/videos",
                                      wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)  # Well, wx.DD_MULTIPLE seems to
        # exist only in the docs.
        # TODO make DD_MULTIPLE work
        openFileDialog.SetPath(str(Path.home()))  # always set the home directory
        if openFileDialog.ShowModal() == wx.ID_OK:
            # dirnames = openFileDialog.GetPaths()
            dirnames = [openFileDialog.GetPath()]
            self.backend.set_folders(dirnames)
            self.panel.treeCtrl.update_ui_tree()
            self.TopLevelParent.SetTitle('Whatsapp Media Timeline Fixer [not applied]')
        else:
            wx.MessageBox(f"No folder selected!", 'Warning', wx.OK | wx.ICON_WARNING)
        openFileDialog.Destroy()

    def __on_about_click(self, event):
        wx.MessageBox(f"""Written by Focshole\nhttps://github.com/Focshole/whatsapp-media-exif-fixer""", 'About', wx.OK)


class BackendPrinter:
    def __init__(self, textbox=None):
        self.__textbox = textbox

    def set_textbox(self,
                    txtb):  # this will be updated again once it will have created the window. It is very ugly,
        # needs to be changed
        self.__textbox = txtb

    def print(self, text):
        if self.__textbox is None:
            wx.MessageBox(text, "Information", wx.OK)
        else:
            self.__textbox.ChangeValue(self.__textbox.GetValue() + text + "\n")

    def warn(self, text):
        wx.MessageBox(text, "Warning", wx.OK | wx.ICON_WARNING)

    def error(self, text):
        wx.MessageBox(text, "Error", wx.OK | wx.ICON_ERROR)
        exit(-1)


class MainApp:
    def __init__(self):
        self.app = wx.App()
        bp = BackendPrinter()
        backend = FixExif(bp)
        self.frame = MainFrame(backend)
        self.app.MainLoop()
