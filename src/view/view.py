from PyQt5 import QtWidgets, QtCore, QtGui, uic
from src import RSC_DIR, DEFAULT, CONFIG_DIR, KEY, update_default
from src.view.utils import protector
from src.view import graph, ui
from cryptography import fernet
import json
import os


class View(QtWidgets.QMainWindow):
    """
    this class is a part of the MVP app design, it shows all the user interface
    and send signals for specific actions

    """
    closed = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(RSC_DIR, "ui", "MainView.ui"), self)
        self.resize(*DEFAULT['window_size'])
        self.move(*DEFAULT['window_position'])

        # set short cuts
        self.save = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+S'), self)
        self.save.activated.connect(self.saveSettings)

        self.restore = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+R'), self)
        self.restore.activated.connect(self.restoreSettings)

        self.newsession = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+N'), self)
        self.newsession.activated.connect(self.openSession)
        self.session = None
        self._password = None
        self.sync = True

        self.modules = json.load(open(os.path.join(CONFIG_DIR, "modules.json"), "rb"))
        self.initStyle()
        self.initUI()

    def initStyle(self):
        """
        This method initialize styles and useful icons
        """
        # create menu and actions for stylesheet and themes
        self.theme, self.style = None, None

        def getAction(name, function):
            name = os.path.splitext(name)[0]
            act = QtWidgets.QAction(name, self)
            act.triggered.connect(lambda: function(name))
            return act

        # add menus
        menuStyles = self.menuPreferences.addMenu('Styles')
        for style in os.listdir(os.path.join(RSC_DIR, 'qss')):
            menuStyles.addAction(getAction(style, self.loadStyle))

        menuThemes = self.menuPreferences.addMenu('Themes')
        for theme in os.listdir(os.path.join(RSC_DIR, 'theme')):
            menuThemes.addAction(getAction(theme, self.loadTheme))

        # load default style and theme
        self.loadTheme()
        self.loadStyle()

    def loadTheme(self, theme=DEFAULT['theme']):
        with open(os.path.join(RSC_DIR, "theme", theme + ".json"), "r") as f:
            self.theme = json.load(f)
        if self.style is not None:
            QtWidgets.qApp.setStyleSheet(self.style % self.theme['qss'])

    def loadStyle(self, style=DEFAULT['style']):
        if style is None:
            return QtWidgets.qApp.setStyleSheet('')

        with open(os.path.join(RSC_DIR, "qss", style+".qss"), "r") as f:
            self.style = f.read()
        if self.theme is not None:
            QtWidgets.qApp.setStyleSheet(self.style % self.theme['qss'])
        else:
            QtWidgets.qApp.setStyleSheet(self.style)

    def initUI(self):
        """
        This method init widgets UI for the main window
        """
        self.setTabPosition(QtCore.Qt.RightDockWidgetArea, QtWidgets.QTabWidget.West)
        self.setTabPosition(QtCore.Qt.LeftDockWidgetArea, QtWidgets.QTabWidget.East)

        self.settings = {'graph': {}}

        self.actionOpenSession.triggered.connect(self.loadSession)
        self.actionNewSession.triggered.connect(self.newSession)

        self.graph = graph.QGraph(self, 'horizontal')
        self.setCentralWidget(self.graph)
        self.setWindowState(QtCore.Qt.WindowActive)

    def getParameters(self, key, dic=None):
        if dic is None:
            dic = self.modules
        if isinstance(dic, dict):
            if key in dic:
                return dic.get(key)
            for v in dic.values():
                par = self.getParameters(key, v)
                if par is not None:
                    return par

    def addWidgetInDock(self, widget, side=QtCore.Qt.RightDockWidgetArea, unique=True):
        """
        put widget inside a qdock widget

        Parameters
        ----------
        widget: QWidget

        Return
        ------
        dock: QDockWidget

        """
        if unique and isinstance(widget.parent(), QtWidgets.QDockWidget):
            dock = widget.parent()
            self.restoreDockWidget(dock)
        else:
            dock = QtWidgets.QDockWidget()
            dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea | QtCore.Qt.LeftDockWidgetArea)
            dock.setFeatures(QtWidgets.QDockWidget.AllDockWidgetFeatures)

            docks = self.findChildren(QtWidgets.QDockWidget)

            dock.setWidget(widget)
            self.addDockWidget(side, dock)

            # tabify dock to existant docks
            for dk in docks:
                if self.dockWidgetArea(dk) == side:
                    self.tabifyDockWidget(dk, dock)
                    break

        dock.show()
        dock.raise_()
        return dock

    def openSession(self):
        """
        open dialog to orient on load or create new session
        """
        dialog = ui.QCustomDialog("open session", os.path.join(RSC_DIR, "ui", "openSession.ui"), self)
        dialog.exec()
        if not os.path.exists(os.path.join(CONFIG_DIR, "sessions")):
            os.makedirs(os.path.join(CONFIG_DIR, "sessions"))

        if dialog.out == "Load session":
            return self.loadSession()
        elif dialog.out == "New session":
            return self.newSession()
        return False

    def loadSession(self):
        """
        load existing session
        """
        sessions = [i[:-5] for i in os.listdir(os.path.join(CONFIG_DIR, "sessions")) if i != '.gitignore']
        if DEFAULT['last_session'] in sessions:
            session_ind = sessions.index(DEFAULT['last_session'])
        else:
            session_ind = 0
        session, ok = QtWidgets.QInputDialog.getItem(self, "Sessions", 'open session:', sessions, session_ind, False)
        if ok:
            self._password = None
            self.graph.deleteAll()
            self.session = session
            self.setWindowTitle(session)
            self.loadSettings(False)
            self.restoreSettings()
            update_default(last_session=session)
            return True
        else:
            return self.openSession()

    def newSession(self):
        """
        create new session
        """
        dialog = ui.QCustomDialog("new session", os.path.join(RSC_DIR, "ui", "newSession.ui"), self)
        dialog.exec()
        if dialog.out == 'Cancel':
            return self.openSession()
        elif dialog.out == 'Ok':
            self._password = dialog.password.text() if dialog.password.text() else None
            self.session = dialog.name.text()
            self.setWindowTitle(self.session)
            self.graph.deleteAll()
            self.saveSettings()
            return True

    @protector("Critical")
    def loadSettings(self, append=False):
        """
        load settings,
        if settings cannot be loaded ask for password to decrypt data
        """
        path = os.path.join(CONFIG_DIR, 'sessions', self.session + '.json')
        if not os.path.isfile(path):
            return

        try:
            with open(path, 'r') as fp:
                settings = json.load(fp)

        except json.decoder.JSONDecodeError:
            password, ok = QtWidgets.QInputDialog.getText(None, "Load session", 'password:',
                                                          QtWidgets.QLineEdit.Password)
            if not ok:
                return self.loadSession()
            key = password + KEY[len(password):]
            crypt = fernet.Fernet(key.encode('utf-8'))

            self._password = password
            with open(path, 'rb') as fp:
                data = fp.read()
            try:
                decrypted_data = crypt.decrypt(data)
            except fernet.InvalidToken:
                return self.loadSettings(append)

            settings = json.loads(decrypted_data.decode('utf-8'))

        if append:
            self.settings.update(settings)
        else:
            self.settings = settings            #

    @protector("Critical")
    def saveSettings(self):
        """
        save settings, encrypt settings if a password is specified
        """
        self.settings['graph'] = self.graph.getSettings()

        if self._password is not None:
            key = self._password + KEY[len(self._password):]
            settings = json.dumps(self.settings).encode('utf-8')
            crypt = fernet.Fernet(key.encode('utf-8'))

            encrypted_settings = crypt.encrypt(settings)
            with open(os.path.join(CONFIG_DIR, 'sessions', self.session + '.json'), 'wb') as fp:
                fp.write(encrypted_settings)

        else:
            with open(os.path.join(CONFIG_DIR, 'sessions', self.session + '.json'), 'w') as fp:
                json.dump(self.settings, fp, indent=4)

    def restoreSettings(self):
        self.graph.setSettings(self.settings['graph'])

    def closeEvent(self, event):
        self.closed.emit()
        update_default(window_size=[self.size().width(), self.size().height()],
                       window_position=[self.pos().x(), self.pos().y()])
        QtWidgets.QMainWindow.closeEvent(self, event)
