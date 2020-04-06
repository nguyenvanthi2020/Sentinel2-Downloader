from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.core import *
from .Sentinel2_Download_Dialog import *
from .Sentinel2_Download_Library import *

# ---------------------------------------------

class s2_menu:
	
	def __init__(self, iface):
		self.iface = iface
		self.s2_menu = None

	def ifee_add_submenu(self, submenu):
		if self.s2_menu != None:
			self.s2_menu.addMenu(submenu)
		else:
			self.iface.addPluginToMenu("&s2dl", submenu.menuAction())

	def initGui(self):


		# Khởi tạo IFEE trên menubar của QGIS
		self.s2_menu = QMenu(QCoreApplication.translate("s2download", "Sentinel-2 Download"))
		self.iface.mainWindow().menuBar().insertMenu(self.iface.firstRightStandardMenu().menuAction(), self.s2_menu)


        # Menu  

		iconv = QIcon(os.path.dirname(__file__) + "/icons/vieticon.png")
		self.viet_action = QAction(iconv, u'Sentinel-2 for Commune Downloader (Vietnam)', self.iface.mainWindow())
		self.viet_action.triggered.connect(self.s2viet)
		self.s2_menu.addAction(self.viet_action)
		
		iconw = QIcon(os.path.dirname(__file__) + "/icons/worldicon.png")
		self.world_action = QAction(iconw, u'Sentinel-2 Downloader (World)', self.iface.mainWindow())
		self.world_action.triggered.connect(self.s2world)
		self.s2_menu.addAction(self.world_action)
        
		self.first_start = True
        
	def unload(self):
		if self.s2_menu != None:
			self.iface.mainWindow().menuBar().removeAction(self.s2_menu.menuAction())
		else:
			self.iface.removePluginMenu("&s2dl", self.geoprocessing_menu.menuAction())
			self.iface.removePluginMenu("&s2dl", self.tool_menu.menuAction())


	##########################	


        
	def s2viet(self):
		dialog = s2viet_dialog(self.iface)
		dialog.exec_()
        
	def s2world(self):
		dialog = s2world_dialog(self.iface)
		dialog.exec_()
