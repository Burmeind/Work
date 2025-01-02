import os
from pathlib import Path
import wx
import wx.grid
import wx.lib.inspection
import pandas as pd
import oracledb
import winsound
import datetime
import yaml

hide = False

#  python -m PyInstaller --onefile main.py --hidden-import cryptography.hazmat.primitives.kdf.pbkdf2 --hide-console hide-early

class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, id=wx.ID_ANY, title=u"Verifier", pos=wx.DefaultPosition,
                          size=wx.Size(817, 480), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        # get events handler
        self.functions = EventsHandler(self)

        # create menus
        # File Menu
        file_menu = wx.Menu()
        self.import_file = wx.MenuItem(file_menu, wx.ID_ANY, u'Import', wx.EmptyString, wx.ITEM_NORMAL)
        self.export_file = wx.MenuItem(file_menu, wx.ID_ANY, u'Export', wx.EmptyString, wx.ITEM_NORMAL)

        file_menu.Append(self.import_file)
        file_menu.Append(self.export_file)

        # Connection Menu
        connection_menu = wx.Menu()
        self.connect = wx.MenuItem(connection_menu, wx.ID_ANY, u'Connect', wx.EmptyString, wx.ITEM_NORMAL)
        self.disconnect = wx.MenuItem(connection_menu, wx.ID_ANY, u'Disconnect', wx.EmptyString, wx.ITEM_NORMAL)

        connection_menu.Append(self.connect)
        connection_menu.Append(self.disconnect)

        # Data menu
        data_menu = wx.Menu()
        self.reset_all = wx.MenuItem(data_menu, wx.ID_ANY, u'Reset All', wx.EmptyString, wx.ITEM_NORMAL)

        data_menu.Append(self.reset_all)

        # create menu bar
        menu_bar = wx.MenuBar(0)
        menu_bar.Append(file_menu, u'File')
        menu_bar.Append(connection_menu, u'Connection')
        menu_bar.Append(data_menu, u'Data')

        self.SetMenuBar(menu_bar)

        # create main panel
        self.main_panel = wx.Panel(self, wx.ID_ANY)

        # create choice control box
        choice_box_choices = [u'Staging Location', u'Carrier Move ID', u'Shipment ID']
        self.choice_box = wx.Choice(self.main_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, choice_box_choices, 0)
        self.choice_box.SetSelection(0)

        # create text control labels
        # self.static_text0 = wx.StaticText(self.main_panel, wx.ID_ANY, u'Staging Location', wx.DefaultPosition, wx.DefaultSize, 0)
        self.static_text1 = wx.StaticText(self.main_panel, wx.ID_ANY, u'Pallet ID', wx.DefaultPosition, wx.DefaultSize, 0)
        self.static_text2 = wx.StaticText(self.main_panel, wx.ID_ANY, u'Part Number', wx.DefaultPosition, wx.DefaultSize, 0)
        self.static_text3 = wx.StaticText(self.main_panel, wx.ID_ANY, u'Rev Level/Lot Number', wx.DefaultPosition, wx.DefaultSize, 0)
        self.static_text4 = wx.StaticText(self.main_panel, wx.ID_ANY, u'Quantity', wx.DefaultPosition, wx.DefaultSize, 0)

        # create text controls
        self.text_control_stoloc = wx.TextCtrl(self.main_panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                               wx.DefaultSize, wx.TE_PROCESS_ENTER)
        self.text_control_lodnum = wx.TextCtrl(self.main_panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                               wx.DefaultSize, wx.TE_PROCESS_ENTER)
        self.text_control_prtnum = wx.TextCtrl(self.main_panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                               wx.DefaultSize, wx.TE_PROCESS_ENTER)
        self.text_control_revlvl = wx.TextCtrl(self.main_panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                               wx.DefaultSize, wx.TE_PROCESS_ENTER)
        self.text_control_untqty = wx.TextCtrl(self.main_panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                               wx.DefaultSize, wx.TE_PROCESS_ENTER)

        # create buttons
        # self.button_reset_all = wx.Button(self.main_panel, wx.ID_ANY, u"Reset All", wx.DefaultPosition, wx.DefaultSize, 0)
        self.button_reset_stoloc = wx.Button(self.main_panel, wx.ID_ANY, u"Reset Staging Location", wx.DefaultPosition, wx.DefaultSize, 0)
        self.button_reset_lodnum = wx.Button(self.main_panel, wx.ID_ANY, u"Reset Pallet", wx.DefaultPosition, wx.DefaultSize, 0)

        # create notebook
        self.notebook = wx.Notebook(self.main_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)

        # create pages for notebook
        self.page_all = GridPanel(self.notebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.page_stoloc = GridPanel(self.notebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.page_lodnum = GridPanel(self.notebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.page_errors = GridPanel(self.notebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)

        # add pages to notebook
        self.notebook.AddPage(self.page_all, u"All Items", False)
        self.notebook.AddPage(self.page_stoloc, u"Staging Location", False)
        self.notebook.AddPage(self.page_lodnum, u"Pallet", False)
        self.notebook.AddPage(self.page_errors, u"Errors", False)
        self.notebook.SetSelection(0)

        self.__set_properties()
        self.__set_layout()
        self.__set_bindings()

    def __set_properties(self):

        # Disable text controls to start
        self.text_control_stoloc.Enable(False)
        self.text_control_lodnum.Enable(False)
        self.text_control_prtnum.Enable(False)
        self.text_control_revlvl.Enable(False)
        self.text_control_untqty.Enable(False)

        # disable buttons to start
        # self.button_reset_all.Enable(False)
        self.button_reset_stoloc.Enable(False)
        self.button_reset_lodnum.Enable(False)

    def __set_layout(self):
        main_panel_fgsizer = wx.FlexGridSizer(3, 5, (5, 2))
        main_panel_fgsizer.AddGrowableCol(0)
        main_panel_fgsizer.AddGrowableCol(1)
        main_panel_fgsizer.AddGrowableCol(2)
        main_panel_fgsizer.AddGrowableCol(3)
        main_panel_fgsizer.AddGrowableCol(4)

        main_panel_fgsizer.Add(self.choice_box, flag=wx.EXPAND)
        # main_panel_fgsizer.Add(self.static_text0, flag=wx.EXPAND)
        main_panel_fgsizer.Add(self.static_text1, flag=wx.EXPAND)
        main_panel_fgsizer.Add(self.static_text2, flag=wx.EXPAND)
        main_panel_fgsizer.Add(self.static_text3, flag=wx.EXPAND)
        main_panel_fgsizer.Add(self.static_text4, flag=wx.EXPAND)

        main_panel_fgsizer.Add(self.text_control_stoloc, flag=wx.EXPAND)
        main_panel_fgsizer.Add(self.text_control_lodnum, flag=wx.EXPAND)
        main_panel_fgsizer.Add(self.text_control_prtnum, flag=wx.EXPAND)
        main_panel_fgsizer.Add(self.text_control_revlvl, flag=wx.EXPAND)
        main_panel_fgsizer.Add(self.text_control_untqty, flag=wx.EXPAND)

        # main_panel_fgsizer.Add(self.button_reset_all, flag=wx.EXPAND)
        main_panel_fgsizer.Add(self.button_reset_stoloc, flag=wx.EXPAND)
        main_panel_fgsizer.Add(self.button_reset_lodnum, flag=wx.EXPAND)

        main_panel_vsizer = wx.BoxSizer(wx.VERTICAL)
        main_panel_vsizer.Add(main_panel_fgsizer, proportion=1, flag=wx.EXPAND)
        main_panel_vsizer.Add(self.notebook, proportion=5, flag=wx.EXPAND)

        self.main_panel.SetSizer(main_panel_vsizer)

    def __set_bindings(self):
        # bind events
        # menu bar
        self.Bind(wx.EVT_MENU, self.functions.import_data, id=self.import_file.GetId())
        self.Bind(wx.EVT_MENU, self.functions.export_data, id=self.export_file.GetId())
        self.Bind(wx.EVT_MENU, self.functions.connect, id=self.connect.GetId())
        self.Bind(wx.EVT_MENU, self.functions.disconnect, id=self.disconnect.GetId())
        self.Bind(wx.EVT_MENU, self.functions.reset_all, id=self.reset_all.GetId())

        # choice box control
        self.choice_box.Bind(wx.EVT_CHOICE, self.functions.do_choice)

        # text controls
        self.text_control_stoloc.Bind(wx.EVT_TEXT_ENTER, self.functions.location_input)
        self.text_control_lodnum.Bind(wx.EVT_TEXT_ENTER, self.functions.pallet_input)
        self.text_control_prtnum.Bind(wx.EVT_TEXT_ENTER, self.functions.part_input)
        self.text_control_revlvl.Bind(wx.EVT_TEXT_ENTER, self.functions.detail_input)
        self.text_control_untqty.Bind(wx.EVT_TEXT_ENTER, self.functions.quantity_input)

        # buttons
        # self.button_reset_all.Bind(wx.EVT_BUTTON, self.functions.reset_all)
        self.button_reset_stoloc.Bind(wx.EVT_BUTTON, self.functions.reset_stoloc)
        self.button_reset_lodnum.Bind(wx.EVT_BUTTON, self.functions.reset_lodnum)


class EventsHandler:
    def __init__(self, parent):
        self.gui = parent

        self.all_data = pd.DataFrame
        self.error_data = pd.DataFrame

        self.connection = None
        self.connected = False

        # Oracle DB settings
        print(os.getcwd())
        with open(os.path.expanduser('~/DHLVerifierConfig.yml')) as stream:
            try:
                configdata = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                exit()
        self.oracle_user = configdata['connection']['oracle_user']
        self.oracle_pass = configdata['connection']['oracle_pass']
        self.oracle_hostname = configdata['connection']['oracle_hostname']
        self.oracle_port = configdata['connection']['oracle_port']
        self.oracle_service_name = configdata['connection']['oracle_service_name']
        self.oracle_connection = None

        global hide
        hide = configdata['other']['hide']

        self.current_stage_id = None  # is actually stage ID OR shipment ID OR carrier move ID
        self.current_pallet_id = None
        self.current_part_id = None
        self.current_revlvl = None  # is actually revision level OR lot number
        self.current_quantity = None

        self.last_stage_id = None
        self.last_pallet_id = None

        self.last_data_load = ''

        self.error_row = False

        self.CHOICE_STAGING = 0
        self.CHOICE_CAR_MOVE = 1
        self.CHOICE_SHIP_ID = 2

        self.input_choice = self.CHOICE_STAGING


    # menu button event handlers
    def import_data(self, event):
        if event is not None:

            with wx.FileDialog(self, 'Open file', wildcard='Excel files (*.csv;*.xls;*.xlsx)|*.csv;*.xls;*.xlsx',
                               style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return False  # the user changed their mind

                # Proceed loading the file chosen by the user
                open_file_pathname = fileDialog.GetPath()
                self.get_data_from_file(file_path=open_file_pathname)

    def get_data_from_file(self, file_path):
        self.last_data_load = file_path
        self.all_data = pd.DataFrame

        try:
            if file_path.endswith('.xls') or file_path.endswith('.xlsx'):
                self.all_data = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                self.all_data = pd.read_csv(file_path)
            else:
                wx.LogError('Incorrect Filetype Selected')
                return False
            self.all_data.columns = self.all_data.columns.str.upper()

        except IOError:
            wx.LogError(f'Cannot open file "{file_path}".')
            return False

        if not all(item in self.all_data.columns for item in ['CARMOV', 'SHIPID', 'LOCVRC', 'STOLOC', 'LODNUM',
                                                              'PRTNUM', 'REVLVL', 'LOTNUM', 'UNTQTY']):
            wx.LogError('File does not have proper headers.\n'
                        'CARMOV, SHIPID, LOCVRC, STOLOC, LODNUM,\nPRTNUM, REVLVL, LOTNUM, UNTQTY')
            return False

        self.refresh_all_grid()
        return True

    def export_data(self, event):

        path = os.path.join(os.path.expanduser('~'), 'Documents', 'Verifier')
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        now = datetime.datetime.now()
        all_data_filename = now.strftime('%Y%m%d%H%M%S') + '_' + os.getlogin() + '.csv'
        error_data_filename = now.strftime('%Y%m%d%H%M%S') + '_errors_' + os.getlogin() + '.csv'

        if not self.all_data.empty:
            self.all_data.to_csv(path_or_buf=Path.joinpath(path,all_data_filename))
        if not self.error_data.empty:
            self.error_data.to_csv(path_or_buf=Path.joinpath(path,error_data_filename))

    def connect(self, event):

        try:
            self.oracle_connection = oracledb.connect(user=self.oracle_user, password=self.oracle_pass,
                                                      dsn=f'{self.oracle_hostname}:{self.oracle_port}/'
                                                          f'{self.oracle_service_name}')

            if not self.__oracle_test_connection():
                raise ConnectionError
            winsound.PlaySound('Windows Logon Sound.wav', winsound.SND_FILENAME)
            self.connected = True
            self.all_data = self.oracle_get_data()
            self.last_data_load = 'ORACLE'
            self.refresh_all_grid()
            self.enable_clear_focus_text_control(self.gui.text_control_stoloc)
            # self.gui.button_reset_all.Enable(True)

        except ValueError | ConnectionError:
            winsound.PlaySound('Windows Critical Stop.wav', winsound.SND_FILENAME)
            wx.LogError('Failed to connect to Oracle DB')
            self.connected = False

    def disconnect(self, event):
        self.oracle_connection.close()

    # choice box control input event handler
    def do_choice(self, event):
        self.input_choice = self.gui.choice_box.GetSelection()
        if self.input_choice == self.CHOICE_STAGING:
            self.gui.notebook.SetPageText(1, 'Staging Location')
            self.gui.button_reset_stoloc.SetLabel('Reset Staging Location')
        elif self.input_choice == self.CHOICE_CAR_MOVE:
            self.gui.notebook.SetPageText(1, 'Carrier Move')
            self.gui.button_reset_stoloc.SetLabel('Reset Carrier Move')
        elif self.input_choice == self.CHOICE_SHIP_ID:
            self.gui.notebook.SetPageText(1, 'Shipment')
            self.gui.button_reset_stoloc.SetLabel('Reset Shipment')

    # text control input event handlers
    def location_input(self, event):
        self.current_stage_id = self.gui.text_control_stoloc.GetValue().upper()
        refresh_stage_data = False

        if not self.last_stage_id:
            # last stage is empty means we just started and need to refresh

            refresh_stage_data = True
        elif self.current_stage_id != self.last_stage_id:
            # we\'ve scanned a new stage location
            if self.check_if_stage_complete(location=self.last_stage_id):
                # if previous stage was complete, refresh with new data
                refresh_stage_data = True
            elif self.warn(text='You\'ve scanned a new stage location.'
                                '\nPress Proceed to put current stage location in error.'):
                # popup warning for new stage location
                refresh_stage_data = True
                error_stage_data = self.get_stage_location_data(location=self.current_stage_id).query('VERIFIED != "1"')
                self.place_data_in_error(data=error_stage_data, modify_all_data=True)
            else:
                # reset location text control value
                self.gui.text_control_stoloc.ChangeValue(value=self.last_stage_id)
                # ECF on pallet id text control
                self.enable_clear_focus_text_control(self.gui.text_control_lodnum)
        elif self.current_stage_id == self.last_stage_id and self.warn(text='You\'ve scanned the same stage ID.'  
                                                                       '\nPress Proceed to refresh.'):
            # same ID scanned twice. send warning about refresh
            refresh_stage_data = True

        if refresh_stage_data:
            if not self.refresh_stoloc_grid(self.current_stage_id):
                self.error(text='No data found.')
                self.enable_clear_focus_text_control(self.gui.text_control_stoloc)
            else:
                self.enable_clear_focus_text_control(self.gui.text_control_lodnum)
                self.gui.button_reset_stoloc.Enable()
                self.last_stage_id = self.current_stage_id

    def pallet_input(self, event):
        self.current_pallet_id = self.gui.text_control_lodnum.GetValue().upper()
        refresh = False
        if not self.last_pallet_id:
            refresh = True
            self.gui.button_reset_lodnum.Enable(True)
        elif self.last_pallet_id != self.current_pallet_id:
            if self.check_if_pallet_complete(location=self.current_stage_id, pallet=self.last_pallet_id):
                refresh = True
            elif self.warn(text='You\'ve scanned a new pallet\nPress Proceed to place current pallet in error'):
                error_pallet_data = self.get_pallet_data(location=self.current_stage_id,
                                                         pallet=self.last_pallet_id).query('VERIFIED != "1"')
                self.place_data_in_error(data=error_pallet_data, modify_all_data=True)
                self.refresh_all_grid()
                self.refresh_stoloc_grid(location=self.current_stage_id)

                refresh = True
        elif self.warn(text='You\'ve scanned the same pallet ID.\nPress Proceed to refresh pallet data'):
            refresh = True
        else:
            self.enable_clear_focus_text_control(self.gui.text_control_lodnum)

        if refresh:
            if not self.refresh_pallet_grid(location=self.current_stage_id, pallet=self.current_pallet_id):
                if self.warn(text='No data found for this pallet.\nPress Proceed to start error record.'):
                    self.error_row = True
                    self.enable_clear_focus_text_control(self.gui.text_control_prtnum)
                else:
                    self.enable_clear_focus_text_control(self.gui.text_control_lodnum)
            else:
                self.last_pallet_id = self.current_pallet_id
                self.enable_clear_focus_text_control(self.gui.text_control_prtnum)

    def part_input(self, event):
        self.current_part_id = self.gui.text_control_prtnum.GetValue().upper()

        if self.error_row:
            self.enable_clear_focus_text_control(self.gui.text_control_revlvl)
            return

        if self.current_part_id == self.current_pallet_id:
            self.enable_clear_focus_text_control(self.gui.text_control_prtnum)
        else:
            new_pallet_data = self.get_pallet_data(location=self.current_stage_id, pallet=self.current_part_id)
            if not new_pallet_data.empty:
                if self.check_if_pallet_complete(location=self.current_stage_id, pallet=self.current_pallet_id):
                    self.gui.text_control_lodnum.ChangeValue(value=self.current_part_id)
                    self.current_pallet_id = self.current_part_id
                    self.refresh_pallet_grid(location=self.current_stage_id, pallet=self.current_pallet_id)
                elif self.warn(text='You\'ve scanned a new pallet\nPress Proceed to place current pallet in error'):
                    error_pallet_data = self.get_pallet_data(location=self.current_stage_id,
                                                             pallet=self.current_pallet_id) .query('VERIFIED != "1"')
                    self.place_data_in_error(data=error_pallet_data, modify_all_data=True)
                    self.gui.text_control_lodnum.ChangeValue(value=self.current_part_id)
                    self.current_pallet_id = self.current_part_id
                    self.refresh_all_grid()
                    self.refresh_stoloc_grid(location=self.current_stage_id)
                    self.refresh_pallet_grid(location=self.current_stage_id, pallet=self.current_pallet_id)
                    return
                else:
                    self.enable_clear_focus_text_control(self.gui.text_control_prtnum)

            else:
                stage_location_data = self.get_stage_location_data(location=self.current_part_id)
                if not stage_location_data.empty:
                    if self.check_if_stage_complete(location=self.current_stage_id):
                        self.gui.text_control_stoloc.ChangeValue(value=self.current_part_id)
                        self.current_stage_id = self.current_part_id
                        self.refresh_stoloc_grid(location=self.current_stage_id)
                    elif self.warn(text='You\'ve scanned a new stage location\nPress Proceed to put current stage location in error'):
                        error_stage_data = self.get_stage_location_data(location=self.current_stage_id).query('VERIFIED != "1"')
                        self.place_data_in_error(data=error_stage_data, modify_all_data=True)
                        self.gui.text_control_stoloc.ChangeValue(value=self.current_part_id)
                        self.current_stage_id = self.current_part_id
                        self.refresh_stoloc_grid(location=self.current_stage_id)
                        return
                    else:
                        self.enable_clear_focus_text_control(self.gui.text_control_prtnum)
                else:
                    unverified_part_data = self.get_part_data(location=self.current_stage_id, pallet=self.current_pallet_id,
                                                              partnum=self.current_part_id).query(f'VERIFIED != "1"')
                    if unverified_part_data.empty:
                        if self.warn(text='Part not located on pallet.\nPress OK to begin error record.'):
                            self.error_row = True
                            self.enable_clear_focus_text_control(self.gui.text_control_revlvl)
                    else:
                        self.enable_clear_focus_text_control(self.gui.text_control_revlvl)

    def detail_input(self, event):
        self.current_revlvl = self.gui.text_control_revlvl.GetValue().upper()

        if self.error_row:
            self.enable_clear_focus_text_control(self.gui.text_control_untqty)
            return

        if self.current_revlvl == '' or self.current_revlvl == '----' or self.current_revlvl == self.current_part_id:
            self.current_revlvl = '----'
            self.gui.text_control_revlvl.ChangeValue(value='----')
            unverified_detail_data = self.get_detail_data_no_revlvl_lotnum(location=self.current_stage_id,
                                                                           pallet=self.current_pallet_id,
                                                                           prtnum=self.current_part_id).query(f'VERIFIED != "1"')

        else:
            unverified_detail_data = self.get_detail_data(location=self.current_stage_id, pallet=self.current_pallet_id,
                                                          prtnum=self.current_part_id, revlvllotnum=self.current_revlvl).\
                                                          query(f'VERIFIED != "1"')

        if unverified_detail_data.empty:
            if self.warn(text='RevLvl/LotNum not found\nPress Proceed to create an error record'):
                # check if this needs to be added to errors
                self.error_row = True
                self.enable_clear_focus_text_control(self.gui.text_control_untqty)
        else:
            # check if there is more than one line in self.detail_data
            # check if unit quantity is needed ( >1 )
            # get indices
            if unverified_detail_data.iloc[0]['UNTQTY'] == 1 or unverified_detail_data.iloc[0]['UNTQTY'] - unverified_detail_data.iloc[0]['VRFQTY'] == 1:

                self.set_first_line_verified(unverified_detail_data)

                self.disable_clear_text_control(self.gui.text_control_revlvl)
                self.enable_clear_focus_text_control(self.gui.text_control_prtnum)

            else:
                self.enable_clear_focus_text_control(self.gui.text_control_untqty)

    def quantity_input(self, event):
        self.current_quantity = self.gui.text_control_untqty.GetValue().upper()
        if self.current_quantity == '':
            self.current_quantity = 1

        try:
            if self.current_quantity == self.current_revlvl or self.current_quantity == self.current_part_id:
                raise ValueError
            self.current_quantity = int(self.current_quantity)

        except ValueError:
            if self.warn(text='You''ve scanned an invalid quantity.\nPress OK to clear.'):
                self.enable_clear_focus_text_control(self.gui.text_control_untqty)
            return

        self.process_quantity(self.current_quantity)

    # button input handlers
    def reset_all(self, event):
        if not self.warn(text='Pressing Proceed will clear all grids\nand reload the data.'):
            return

        self.gui.page_all.clear_grid()
        self.gui.page_stoloc.clear_grid()
        self.gui.page_lodnum.clear_grid()

        self.disable_clear_text_control(self.gui.text_control_untqty)
        self.disable_clear_text_control(self.gui.text_control_revlvl)
        self.disable_clear_text_control(self.gui.text_control_prtnum)
        self.disable_clear_text_control(self.gui.text_control_lodnum)

        self.gui.notebook.SetSelection(0)

        if self.last_data_load == 'ORACLE':
            self.disconnect(event=None)
            self.connect(event=None)
        elif self.last_data_load != '':
            self.get_data_from_file(self.last_data_load)

    def reset_stoloc(self, event):
        if not self.warn(text='Pressing Proceed will clear all scans\n from the current ' + self.gui.notebook.GetPageText(1)):
            return

        stage_location_data = self.get_stage_location_data(location=self.current_stage_id)

        for index, row in stage_location_data.iterrows():
            self.all_data.at[index, 'VRFQTY'] = 0
            self.all_data.at[index, 'VERIFIED'] = '0'

        self.refresh_stoloc_grid(location=self.current_stage_id)

    def reset_lodnum(self, event):
        if not self.warn(
                text='Pressing Proceed will clear all scans\n from the current pallet'):
            return

        pallet_location_data = self.get_pallet_data(location=self.current_stage_id, pallet=self.current_pallet_id)

        for index, row in pallet_location_data.iterrows():
            self.all_data.at[index, 'VRFQTY'] = 0
            self.all_data.at[index, 'VERIFIED'] = '0'

        self.refresh_pallet_grid(location=self.current_stage_id, pallet=self.current_pallet_id)

    # grid modification functions
    def refresh_all_grid(self):
        if self.all_data is not None and not self.all_data.empty:
            self.gui.page_all.clear_grid()
            self.gui.page_stoloc.clear_grid()
            self.gui.page_lodnum.clear_grid()
            i = 0
            for index, row in self.all_data.iterrows():
                self.gui.page_all.add_grid_row(index, row)
                self.all_data.at[index, 'all_data_grid_index'] = i
                i += 1
            self.gui.page_all.refresh_layout()

    def refresh_stoloc_grid(self, location):
        if self.all_data is not None and not self.all_data.empty and location != '':
            self.gui.page_stoloc.clear_grid()
            self.gui.page_lodnum.clear_grid()

            stage_location_data = self.get_stage_location_data(location)

            if stage_location_data.empty:
                return False

            i = 0
            for index, row in stage_location_data.iterrows():
                self.all_data.at[index, 'stage_location_grid_index'] = i
                self.gui.page_stoloc.add_grid_row(i, row)
                i += 1

            self.gui.page_stoloc.refresh_layout()

            self.gui.notebook.SetSelection(1)

            self.disable_clear_text_control(self.gui.text_control_prtnum)
            self.disable_clear_text_control(self.gui.text_control_revlvl)
            self.disable_clear_text_control(self.gui.text_control_untqty)

            self.enable_clear_focus_text_control(self.gui.text_control_lodnum)
            return True

    def refresh_pallet_grid(self, location, pallet):
        self.gui.page_lodnum.clear_grid()

        pallet_data = self.get_pallet_data(location, pallet)
        if pallet_data.empty:
            return False

        i = 0
        for index, row in pallet_data.iterrows():
            self.all_data.at[index, 'pallet_location_grid_index'] = i
            self.gui.page_lodnum.add_grid_row(i, row)
            i += 1

        self.gui.page_lodnum.refresh_layout()

        self.gui.notebook.SetSelection(2)

        self.disable_clear_text_control(self.gui.text_control_revlvl)
        self.disable_clear_text_control(self.gui.text_control_untqty)
        self.enable_clear_focus_text_control(self.gui.text_control_prtnum)
        return True

    def set_first_line_verified(self, detail_data):
        self.all_data.at[detail_data.iloc[0].name, 'VERIFIED'] = '1'
        self.all_data.at[detail_data.iloc[0].name, 'VRFQTY'] = detail_data.iloc[0]['UNTQTY']

        all_data_index = int(detail_data.iloc[0]['all_data_grid_index'])
        self.gui.page_all.set_row_color(index=all_data_index, color=wx.GREEN)

        storage_location_index = int(detail_data.iloc[0]['stage_location_grid_index'])
        self.gui.page_stoloc.set_row_color(index=storage_location_index, color=wx.GREEN)

        pallet_index = int(detail_data.iloc[0]['pallet_location_grid_index'])
        self.gui.page_lodnum.set_row_color(index=pallet_index, color=wx.GREEN)

    def set_first_line_partially_verified(self, detail_data, quantity):
        self.all_data.at[detail_data.iloc[0].name, 'VRFQTY'] = detail_data.iloc[0]['VRFQTY'] + quantity

        all_data_index = int(detail_data.iloc[0]['all_data_grid_index'])
        self.gui.page_all.set_row_color(index=all_data_index, color=wx.YELLOW)

        storage_location_index = int(detail_data.iloc[0]['stage_location_grid_index'])
        self.gui.page_stoloc.set_row_color(index=storage_location_index, color=wx.YELLOW)

        pallet_index = int(detail_data.iloc[0]['pallet_location_grid_index'])
        self.gui.page_lodnum.set_row_color(index=pallet_index, color=wx.YELLOW)

    # data retrieval helper functions
    def get_stage_location_data(self, location):
        if self.input_choice == self.CHOICE_STAGING:
            return self.all_data.query(f'STOLOC == "{location}" | LOCVRC == "{location}"')
        elif self.input_choice == self.CHOICE_CAR_MOVE:
            return self.all_data.query(f'CARMOV == "{location}"')
        elif self.input_choice == self.CHOICE_SHIP_ID:
            return self.all_data.query(f'SHIPID == "{location}"')

    def get_pallet_data(self, location, pallet):
        return self.get_stage_location_data(location).query(f'LODNUM == "{pallet}"')

    def get_part_data(self,location, pallet, partnum):
        return self.get_pallet_data(location, pallet).query(f'PRTNUM == "{partnum}"')

    def get_detail_data_no_revlvl_lotnum(self, location, pallet, prtnum):
        return self.get_pallet_data(location, pallet).query(f'PRTNUM == "{prtnum}" & REVLVL == "----" & LOTNUM == "----"')

    def get_detail_data(self, location, pallet, prtnum, revlvllotnum):
        return self.get_pallet_data(location, pallet).query(f'PRTNUM == "{prtnum}" & '
                                                            f'(REVLVL == "{revlvllotnum}" | LOTNUM == "{revlvllotnum}")')

    # data checking functions
    def check_if_stage_complete(self, location=''):
        stage_location_data = self.get_stage_location_data(location)
        return stage_location_data.query(f'VERIFIED != "1"').empty

    def check_if_pallet_complete(self, location='', pallet=''):
        pallet_data = self.get_pallet_data(location, pallet)
        return pallet_data.query(f'VERIFIED != "1"').empty

    # row processors
    def process_quantity(self, quantity):

        if self.error_row:
            self.process_error_row(quantity)
            self.disable_clear_text_control(self.gui.text_control_untqty)
            self.disable_clear_text_control(self.gui.text_control_revlvl)
            self.gui.notebook.SetSelection(3)
            self.enable_clear_focus_text_control(self.gui.text_control_prtnum)
            return

        if self.current_revlvl == '----':
            unverified_detail_data = self.get_detail_data_no_revlvl_lotnum(location=self.current_stage_id,
                                                                           pallet=self.current_pallet_id,
                                                                           prtnum=self.current_part_id).query(f'VERIFIED != "1"')

        else:
            unverified_detail_data = self.get_detail_data(location=self.current_stage_id, pallet=self.current_pallet_id,
                                                          prtnum=self.current_part_id,
                                                          revlvllotnum=self.current_revlvl).query(f'VERIFIED != "1"')

        if unverified_detail_data.empty or self.error_row:
            self.process_error_row(quantity)
            self.disable_clear_text_control(self.gui.text_control_untqty)
            self.disable_clear_text_control(self.gui.text_control_revlvl)
            self.gui.notebook.SetSelection(3)
            self.enable_clear_focus_text_control(self.gui.text_control_prtnum)
            return

        else:
            quantity_left_on_line = unverified_detail_data.iloc[0]['UNTQTY'] - unverified_detail_data.iloc[0]['VRFQTY']
            if quantity_left_on_line == quantity:

                self.set_first_line_verified(unverified_detail_data)

            elif quantity_left_on_line < quantity:
                self.set_first_line_verified(unverified_detail_data)
                self.process_quantity(quantity - quantity_left_on_line)

            elif quantity_left_on_line > quantity:
                self.set_first_line_partially_verified(unverified_detail_data, quantity)

            self.disable_clear_text_control(self.gui.text_control_untqty)
            self.disable_clear_text_control(self.gui.text_control_revlvl)
            self.enable_clear_focus_text_control(self.gui.text_control_prtnum)

    def process_error_row(self, quantity):

        if self.input_choice == self.CHOICE_STAGING:
            row = pd.DataFrame(data={'CARMOV': [''], 'SHIPID': [''],
                                     'STOLOC': [self.current_stage_id], 'LODNUM': [self.current_pallet_id],
                                     'PRTNUM': [self.current_part_id], 'REVLVL': [self.current_revlvl],
                                     'LOTNUM': ['----'], 'UNTQTY': [quantity], 'VRFQTY': [quantity],
                                     'VERIFIED': ['0']})
        elif self.input_choice == self.CHOICE_CAR_MOVE:
            row = pd.DataFrame(data={'CARMOV': [self.current_stage_id], 'SHIPID': [''],
                                     'STOLOC': [''], 'LODNUM': [self.current_pallet_id],
                                     'PRTNUM': [self.current_part_id], 'REVLVL': [self.current_revlvl],
                                     'LOTNUM': ['----'], 'UNTQTY': [quantity], 'VRFQTY': [quantity],
                                     'VERIFIED': ['0']})
        elif self.input_choice == self.CHOICE_SHIP_ID:
            row = pd.DataFrame(data={'CARMOV': [''], 'SHIPID': [self.current_stage_id],
                                     'STOLOC': [''], 'LODNUM': [self.current_pallet_id],
                                     'PRTNUM': [self.current_part_id], 'REVLVL': [self.current_revlvl],
                                     'LOTNUM': ['----'], 'UNTQTY': [quantity], 'VRFQTY': [quantity],
                                     'VERIFIED': ['0']})
        self.place_data_in_error(data=row)

    def place_data_in_error(self, data=pd.DataFrame, modify_all_data=False):
        if data.empty:
            return False

        if self.error_data.empty:
            error_data_index = 0
            self.error_data = data.copy(deep=True)
        else:
            error_data_index = self.error_data.shape[0]
            self.error_data = pd.concat([self.error_data, data])
        i = error_data_index
        for index, row in data.iterrows():
            self.gui.page_errors.add_grid_row(i, row)
            self.gui.page_errors.set_row_color(i, color=wx.RED)
            if modify_all_data:
                self.all_data.at[index, 'VERIFIED'] = "-1"
            i += 1

        self.gui.page_errors.refresh_layout()
        self.error_row = False

    # oracle functions
    def __oracle_test_connection(self):
        cur = self.oracle_connection.cursor()
        cur.execute('select 1 from DLXUSABBP1.rcvlin where rownum = 1')
        res = cur.fetchall()
        cur.close()
        return res is not None

    def oracle_get_data(self):
        query = '''
            select carmov, shipid, locvrc, stoloc, lodnum, prtnum, revlvl, lotnum, sum(untqty) untqty, vrfqty, verified from (
                    select 
                        car_move.car_move_id carmov,
                        shipment.ship_id shipid,
                        locmst.locvrc,
                        invlod.stoloc,
                        invlod.lodnum,
                        invdtl.prtnum,
                        invdtl.revlvl,
                        invdtl.lotnum,
                        invdtl.untqty,
                        0 vrfqty,
                        '0' verified
                    from
                        DLXUSABBP1.invlod invlod
                    join DLXUSABBP1.invsub invsub on
                        invsub.lodnum = invlod.lodnum
                    join DLXUSABBP1.invdtl invdtl on
                        invdtl.subnum = invsub.subnum
                    join DLXUSABBP1.locmst locmst on
                        invlod.stoloc = locmst.stoloc
                    and invlod.wh_id = locmst.wh_id
                    join DLXUSABBP1.shipment_line shipment_line on
                        invdtl.ship_line_id = shipment_line.ship_line_id
                    join DLXUSABBP1.shipment shipment on
                        shipment_line.ship_id = shipment.ship_id
                    join DLXUSABBP1.stop stop on
                        shipment.stop_id = stop.stop_id
                    join DLXUSABBP1.car_move car_move on
                        stop.car_move_id = car_move.car_move_id
                    where
                        locmst.arecod = 'SSTG'
                     or locmst.arecod = 'SRSTG'
                    )

                    group by  carmov, shipid, locvrc, stoloc, lodnum, prtnum, revlvl, lotnum,  vrfqty, verified
                    order by
                        stoloc,
                        carmov,
                        shipid,
                        lodnum,
                        prtnum,
                        revlvl,
                        lotnum,
                        untqty desc
        '''
        data = pd.read_sql(sql=query, con=self.oracle_connection)
        data.columns = data.columns.str.upper()
        return data

    # text control enable / disable functions
    def enable_clear_focus_text_control(self, control):
        control.Enable()
        control.Clear()
        control.SetFocus()

    def disable_clear_text_control(self, control):
        control.Disable()
        control.Clear()

    # dialog boxes
    def warn(self, text):
        with WarningDialog(self.gui, text=text) as dlg:
            return dlg.ShowModal() == wx.ID_OK

    def error(self, text):
        with ErrorDialog(self.gui, text=text) as dlg:
            return dlg.ShowModal() == wx.ID_OK


class GridPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        # initialize wx.Panel
        super().__init__(*args, **kwargs)

        # create grid
        self.grid = wx.grid.Grid(self, -1, size=(1, 1))
        self.__set_properties()
        self.__set_layout()
        self.__set_bindings()

    def __set_properties(self):
        self.grid.CreateGrid(0, 9)

        self.grid.EnableEditing(False)
        self.grid.EnableGridLines(True)
        self.grid.EnableDragGridSize(False)
        self.grid.SetMargins(0, 0)

        # Columns
        self.grid.AutoSizeColumns()
        self.grid.EnableDragColMove(False)
        self.grid.EnableDragColSize(True)
        self.grid.SetColLabelValue(0, u"Carrier Move")
        self.grid.SetColLabelValue(1, u"Shipment ID")
        self.grid.SetColLabelValue(2, u"Storage Location")
        self.grid.SetColLabelValue(3, u"Pallet ID")
        self.grid.SetColLabelValue(4, u"Part Number")
        self.grid.SetColLabelValue(5, u"Rev Level")
        self.grid.SetColLabelValue(6, u"Lot Number")
        self.grid.SetColLabelValue(7, u"Unit Quantity")
        self.grid.SetColLabelValue(8, u"Scanned Quantity")
        self.grid.SetColLabelAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)

        # Rows
        self.grid.EnableDragRowSize(True)
        self.grid.SetRowLabelAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)

        # Label Appearance

        # Cell Defaults
        self.grid.SetDefaultCellAlignment(wx.ALIGN_LEFT, wx.ALIGN_TOP)
        self.grid.SetMinSize(wx.Size(480, -1))

    def __set_layout(self):
        # create box sizer
        sizer = wx.BoxSizer(wx.VERTICAL)

        # add grid to sizer
        sizer.Add(self.grid, 0, wx.EXPAND | wx.ALL, 1)

        # set panel sizer
        self.SetSizer(sizer)

        # run layout
        self.Layout()

    def __set_bindings(self):
        self.grid.Bind(wx.EVT_KEY_DOWN, self.__eat_copy_from_grid)

    def __eat_copy_from_grid(self, event):
        """
       Blocks copy event.
       """
        # Ctrl+C or Ctrl+Insert
        if event.ControlDown() and event.GetKeyCode() in [67, 322]:
            return
        else:
            event.Skip()

    def add_grid_row(self, index, data):
        # Add row and set data on grid
        global hide
        self.grid.AppendRows(numRows=1)
        self.grid.SetCellValue(row=index, col=0, s=str(data['CARMOV']))
        self.grid.SetCellValue(row=index, col=1, s=str(data['SHIPID']))
        self.grid.SetCellValue(row=index, col=2, s=str(data['STOLOC']))
        self.grid.SetCellValue(row=index, col=8, s=str(data['VRFQTY']))
        self.grid.SetCellValue(row=index, col=3, s=str(data['LODNUM']))
        self.grid.SetCellValue(row=index, col=4, s=str(data['PRTNUM']))
        self.grid.SetCellValue(row=index, col=5, s=str(data['REVLVL']))
        self.grid.SetCellValue(row=index, col=6, s=str(data['LOTNUM']))
        if not hide or data['VRFQTY'] == data['UNTQTY'] or data['VERIFIED'] == '-1':
            self.grid.SetCellValue(row=index, col=7, s=str(data['UNTQTY']))
        elif data['VRFQTY'] == 0:
            self.grid.SetCellValue(row=index, col=7, s='*****')
        elif data['VRFQTY'] > 0:
            self.grid.SetCellValue(row=index, col=7, s='*****')

        if data['VERIFIED'] == '-1':
            row_color = wx.RED
        elif data['VRFQTY'] == data['UNTQTY']:
            row_color = wx.GREEN
        elif data['VRFQTY'] > 0:
            row_color = wx.YELLOW
        else:
            if index % 2:
                row_color = wx.LIGHT_GREY
            else:
                row_color = wx.WHITE

        self.set_row_color(index=index, color=row_color)

    def clear_grid(self):
        self.grid.ClearGrid()
        num_rows = self.grid.GetNumberRows()
        if num_rows > 0:
            self.grid.DeleteRows(pos=0, numRows=num_rows)

    def set_row_color(self, index, color=(240, 240, 240, 255)):
        for i in range(self.grid.GetNumberCols()):
            self.grid.SetCellBackgroundColour(row=index, col=i, colour=color)
        self.grid.ForceRefresh()

    def refresh_layout(self):
        self.grid.AutoSize()
        self.grid.ForceRefresh()
        self.Layout()

# ---------------------------------------------------------------------------


class WarningDialog (wx.Dialog):

    def __init__(self, parent, text=''):
        winsound.Beep(400,250)
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=wx.EmptyString, pos=wx.DefaultPosition,
                           style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP | wx.ICON_WARNING)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        self.warning_text = wx.StaticText(self, wx.ID_ANY, text, wx.DefaultPosition, wx.DefaultSize,
                                          wx.ALIGN_CENTER_HORIZONTAL)

        self.button_ok = wx.Button(self, wx.ID_OK, label='Proceed')
        self.button_cancel = wx.Button(self, wx.ID_CANCEL)

        self.__set_properties()
        self.__set_layout()
        self.__set_bindings()

    def __set_properties(self):
        self.warning_text.Wrap(-1)
        self.button_cancel.SetDefault()

    def __set_layout(self):
        main_vsizer = wx.BoxSizer(wx.VERTICAL)
        main_vsizer.Add(self.warning_text, 1, wx.ALL | wx.EXPAND)

        dialog_button_sizer = wx.StdDialogButtonSizer()
        dialog_button_sizer.AddButton(self.button_ok)
        dialog_button_sizer.AddButton(self.button_cancel)
        dialog_button_sizer.Realize()

        main_vsizer.Add(dialog_button_sizer, 1, wx.ALIGN_CENTER_HORIZONTAL)

        self.SetSizer(main_vsizer)
        self.Layout()
        self.Centre(wx.BOTH)

    def __set_bindings(self):
        pass

    def __del__(self):
        pass

    # ---------------------------------------------------------------------------


class ErrorDialog(wx.Dialog):

    def __init__(self, parent, text=''):
        winsound.Beep(400,250)
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=wx.EmptyString, pos=wx.DefaultPosition,
                           style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP | wx.ICON_ERROR)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        self.warning_text = wx.StaticText(self, wx.ID_ANY, text, wx.DefaultPosition, wx.DefaultSize,
                                          wx.ALIGN_CENTER_HORIZONTAL)

        self.button_ok = wx.Button(self, wx.ID_OK, label='Proceed')
        self.button_cancel = wx.Button(self, wx.ID_CANCEL)

        self.__set_properties()
        self.__set_layout()
        self.__set_bindings()

    def __set_properties(self):
        self.warning_text.Wrap(-1)
        self.button_cancel.SetDefault()

    def __set_layout(self):
        main_vsizer = wx.BoxSizer(wx.VERTICAL)
        main_vsizer.Add(self.warning_text, 1, wx.ALL | wx.EXPAND)

        dialog_button_sizer = wx.StdDialogButtonSizer()
        dialog_button_sizer.AddButton(self.button_ok)
        dialog_button_sizer.AddButton(self.button_cancel)
        dialog_button_sizer.Realize()

        main_vsizer.Add(dialog_button_sizer, 1, wx.ALIGN_CENTER_HORIZONTAL)

        self.SetSizer(main_vsizer)
        self.Layout()
        self.Centre(wx.BOTH)

    def __set_bindings(self):
        pass

    def __del__(self):
        pass

# ---------------------------------------------------------------------------


class MyApp(wx.App):
    def OnInit(self):
        print('Running wxPython ' + wx.version())
        # Set Current directory to the one containing this file
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        self.SetAppName('Verifier')

        # Create the main window
        self.frm = MainFrame()
        self.SetTopWindow(self.frm)

        self.frm.Show()
        return True

# ---------------------------------------------------------------------------


if __name__ == '__main__':
    app = MyApp()
    # wx.lib.inspection.InspectionTool().Show()
    app.MainLoop()
    if app.frm.functions.connection is not None:
        app.frm.functions.disconnect(event=None)
