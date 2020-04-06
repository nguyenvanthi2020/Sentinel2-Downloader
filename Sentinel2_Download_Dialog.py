import os.path
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.core import *
from PyQt5.QtWidgets import *
from .Sentinel2_Download_Library import *
from qgis.gui import QgsMessageBar
import sys
import operator

import ee

ee.Initialize()
import json
from json import *
from datetime import date
from datetime import time
from datetime import timedelta
from datetime import datetime
from ee_plugin import Map
from itertools import groupby
import pathlib
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/forms")

from sentinel2_download_dialog_world import *
from sentinel2_download_dialog_vietnam import *


class s2viet_dialog(QDialog, Ui_Dialogv):
    def __init__(self, iface):

        QDialog.__init__(self)
        self.iface = iface
        self.setupUi(self)
        self.inputMay.setText('30')
        self.inputKhoang.setText('3')
        self.inputBuffer.setText('0')
        self.laydanhsachtinh()
        self.comboTinh.currentIndexChanged.connect(self.laydanhsachhuyen)
        self.comboHuyen.currentIndexChanged.connect(self.laydanhsachxa)
        self.tohopmau()
        self.button_box.accepted.connect(self.run)
        # Add base map
        base_map = QgsProject.instance().mapLayersByName('Google Satellite')
        if len(base_map) == 0:
            urlWithParams = 'type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0'
            rlayer = QgsRasterLayer(urlWithParams, 'Google Satellite', 'wms')
            if rlayer.isValid():
                QgsProject.instance().addMapLayer(rlayer)
            else:
                self.iface.messageBar().pushMessage(
                    "Không mở được bản đồ nền!",
                    level=Qgis.Success, duration=5)

    def layngay(self, chuoingay):
        input_date = chuoingay
        str_Input = [int(''.join(i)) for is_digit, i in groupby(input_date, str.isdigit) if is_digit]

        str_Output = date(int(str_Input[1]), int(str_Input[2]), int(str_Input[3]))

        self.ketqua = str(str_Output)
        return self.ketqua

    def run(self):
        """Run method that performs all the real work"""
        # ee.Initialize()
        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        # if self.first_start == True:
        #    self.first_start = False
        #    self.dlg = s2viet_dialog()

        # self.show()

        # result = self.exec_()

        # if result:
        # Get date
        batdau = self.dateBdau.date()
        ketthuc = self.dateKthuc.date()
        bd_date = str(batdau)
        kt_date = str(ketthuc)
        # Get info
        tinhchon = self.comboTinh.currentText()
        huyenchon = self.comboHuyen.currentText()
        xachon = self.comboXa.currentText()
        mtinh = int(self.laymacode()['tcode'])
        mhuyen = int(self.laymacode()['hcode'])
        mxa = int(self.laymacode()['xcode'])
        xavt = self.laymacode()['xvt']
        may = int(self.inputMay.text())
        khoang = int(self.inputKhoang.text())

        ngayBatdau = str(self.layngay(bd_date))
        ngayKetthuc = str(self.layngay(kt_date))

        hcxvn = ee.FeatureCollection("users/nguyenvanthi/RGX_WGS84")
        commune = hcxvn.filter(ee.Filter(ee.Filter.eq('MATINH', mtinh))) \
            .filter(ee.Filter(ee.Filter.eq('MAHUYEN', mhuyen))) \
            .filter(ee.Filter(ee.Filter.eq('MAXA', mxa)))
        # Get buffer

        sbuffer = int(self.inputBuffer.text())
        # input_geometry = commune.geometry().getInfo()["coordinates"]
        # print(input_geometry)
        # input_region = ee.Geometry.Polygon(input_geometry)
        if sbuffer == 0:
            commune_buffered = commune
        else:
            commune_buffered = commune.geometry().buffer(sbuffer)

        # Band combinations
        rgbMethod = self.comboRGB.currentIndex()
        if rgbMethod == 0:
            bands = ['B4', 'B3', 'B2']  # Natural Color
        elif rgbMethod == 1:
            bands = ['B8', 'B4', 'B3']  # Color Infrared
        elif rgbMethod == 2:
            bands = ['B12', 'B8A', 'B4']  # Short-wave Infrared
        elif rgbMethod == 3:
            bands = ['B11', 'B8', 'B2']  # Agriculture  
        elif rgbMethod == 4:
            bands = ['B12', 'B11', 'B2']  # Geology
        elif rgbMethod == 5:
            bands = ['B4', 'B3', 'B1']  # Bathymetric
        elif rgbMethod == 6:
            bands = ['B12', 'B11', 'B4']  # False Uban
        elif rgbMethod == 7:
            bands = ['B12', 'B11', 'B8A']  # Atmosphere
        elif rgbMethod == 8:
            bands = ['B8', 'B11', 'B2']  # Healthy Vegetable
        elif rgbMethod == 9:
            bands = ['B8', 'B11', 'B4']  # Land/Water
        elif rgbMethod == 10:
            bands = ['B812', 'B8', 'B3']  # Natural Atmosphere Removed
        elif rgbMethod == 11:
            bands = ['B12', 'B11', 'B4']  # False Uban
        elif rgbMethod == 12:
            bands = ['B12', 'B8', 'B4']  # Shortwave Infrared
        else:
            bands = ['B11', 'B8', 'B4']  # Vegetable analysis
        
        S2_Collection = ee.ImageCollection("COPERNICUS/S2") \
            .filterDate(ngayBatdau, ngayKetthuc).select(bands) \
            .filterBounds(commune_buffered) \
            .filterMetadata('CLOUDY_PIXEL_PERCENTAGE', "less_than", may) \
            .sort('CLOUD_COVERAGE_ASSESSMENT', True)
        # Get the first image in the collection
        S2 = S2_Collection.first()

        vizParams = {'bands': bands, 'min': 0, 'max': 2000, 'gamma': 0.8}

        image_date1 = ee.Date(S2.get('system:time_start')).format('Y-M-d').getInfo()

        soluonganh = S2_Collection.size().getInfo()

        tmp = self.khoangngay(image_date1, khoang)

        S22 = ee.ImageCollection("COPERNICUS/S2").filterDate(tmp['bd'], tmp['kt']) \
            .select(bands) \
            .filterBounds(commune_buffered) \
            .median()

        Map.centerObject(commune, 14)
        Map.addLayer(S2.clip(commune_buffered), vizParams, "S2_" + str(xachon) + "_" + image_date1 + " (Ảnh đơn)")
        Map.addLayer(S22.clip(commune_buffered), vizParams, "S2_" + str(xachon) + "_" + image_date1 + " (Tập hợp)")
        Map.addLayer(commune_buffered, {'color': 'red'}, "RG_" + str(xachon), False, 0.2)
        ### Message bar info
        self.iface.messageBar().pushMessage(
            "Mở thành công ảnh Sentiel-2 của " + xachon + " " + huyenchon + " " + tinhchon + "!",
            level=Qgis.Success, duration=10)
        # input_geo = commune.geometry().bounds()
        #Check if Export CheckBox is checked then run export
        if self.checkBox.isChecked() == True:
            listCoords = ee.Array.cat(commune_buffered.coordinates(), 1)
            xCoords = listCoords.slice(1, 0, 1)
            yCoords = listCoords.slice(1, 1, 2)
            xMin = xCoords.reduce('min', [0]).get([0, 0])
            xMax = xCoords.reduce('max', [0]).get([0, 0])
            yMin = yCoords.reduce('min', [0]).get([0, 0])
            yMax = yCoords.reduce('max', [0]).get([0, 0])
            geo_export = ee.Geometry.Rectangle(xMin, yMin, xMax, yMax)
            ### Save image to Google Drive3
            image = S22.clip(geo_export)
            name = xavt + '-' + str(image_date1)
            downConfig = {'scale': 10, "maxPixels": 1.0E13, 'driveFolder': 'image_gee'}
            task = ee.batch.Export.image(image, name, downConfig)
            task.start()
            self.iface.messageBar().pushMessage(
                "Đã lưu ảnh của " + xachon + " " + huyenchon + " " + tinhchon + " vào thưu mục image_ee trên Google Drive!",
                level=Qgis.Success, duration=10)


    def khoangngay(self, tmp_imagedate, nday):

        str_tmp = tmp_imagedate.split('-')

        imagedate = date(int(str_tmp[0]), int(str_tmp[1]), int(str_tmp[2]))
        today = date.today()
        dtime = timedelta(days=nday)

        hs = today - imagedate
        if hs < dtime:
            sdate = imagedate - hs - dtime
            edate = today
        else:
            sdate = imagedate - dtime
            edate = imagedate + dtime

        self.template_value = {
            'bd': str(sdate),
            'kt': str(edate),
        }
        return self.template_value

    def laydanhsachtinh(self):
        self.comboTinh.clear()
        tinhs = docdstinh()

        for tinh in tinhs:
            tname = tinh['TINH']
            tcode = tinh['MATINH']
            self.comboTinh.addItems([tname])

    def laydanhsachhuyen(self):
        self.comboHuyen.clear()
        tentinh = self.comboTinh.currentText()
        listhuyen = docdshuyen()

        for chon in listhuyen:
            if chon['TINH'] == tentinh:
                hname = chon['HUYEN']
                hcode = chon['MAHUYEN']
                self.comboHuyen.addItems([hname])

    def laydanhsachxa(self):
        self.comboXa.clear()
        tentinh = self.comboTinh.currentText()
        tenhuyen = self.comboHuyen.currentText()

        listxa = docdsxa()

        for xachon in listxa:
            if xachon['HUYEN'] == tenhuyen:
                xname = xachon['XA']
                xcode = xachon['MAXA']
                self.comboXa.addItems([xname])

    def laymacode(self):
        tenxa = self.comboXa.currentText()
        tentinh = self.comboTinh.currentText()
        tenhuyen = self.comboHuyen.currentText()
        listxa = docdsxa()
        for xachon in listxa:
            if xachon['XA'] == tenxa:
                if xachon['HUYEN'] == tenhuyen:
                    if xachon['TINH'] == tentinh:
                        xcode = xachon['MAXA']
                        hcode = xachon['MAHUYEN']
                        tcode = xachon['MATINH']
                        xavt = xachon['XAVT']
                        huyenvt = xachon['HUYENVT']
                        tinhvt = xachon['TINHVT']
                        macode = {
                            'xcode': xcode,
                            'hcode': hcode,
                            'tcode': tcode,
                            'xvt': xavt,
                            'hvt': huyenvt,
                            'tvt': tinhvt
                        }
                        return macode

    def tohopmau(self):
        self.comboRGB.clear()
        listTohop = ['Màu tự nhiên (B4-B3-B2)', 'Màu giả hồng ngoại (B8-B4-B3)', 'Hồng ngoại sóng ngắn (B12-B8A-B4)', 'Nông nghiệp (B11-B8-B2)', 'Địa chất học (B12-B11-B2)', 'Độ sâu (B4-B3-B1)',
                     'Màu giả đô thị (B12-B11-B4)', 'Xâm nhập khí quyển (B12-B11-B8A)', 'Thực vật khỏe mạnh (B8-B11-B2)', 'Đất/Nước (B8-B11-B4)', 'Màu tự nhiên đã loại khí quyển (B12-B8-B3)',
                     'Hồng ngoại sóng ngắn (B12-B8-B4)', 'Phân tích thực vật (B11-B8-B4)']
        self.comboRGB.addItems(listTohop)


class s2world_dialog(QDialog, Ui_Dialogw):
    def __init__(self, iface):
        QDialog.__init__(self)
        self.iface = iface
        self.setupUi(self)
        self.inputMayw.setText('30')
        self.inputKhoangw.setText('3')
        
        self.rgb()
        self.buttonBoxw.accepted.connect(self.run)
        # Add base map
        base_map = QgsProject.instance().mapLayersByName('Google Satellite')
        if len(base_map) == 0:
            urlWithParams = 'type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0'
            rlayer = QgsRasterLayer(urlWithParams, 'Google Satellite', 'wms')
            if rlayer.isValid():
                QgsProject.instance().addMapLayer(rlayer)
            else:
                self.iface.messageBar().pushMessage(
                    "Không mở được bản đồ nền!",
                    level=Qgis.Success, duration=5)

    def run(self):
        batdau = self.dateBdauw.date()
        ketthuc = self.dateKthucw.date()
        bd_date = str(batdau)
        kt_date = str(ketthuc)
        # Get info

        may = int(self.inputMayw.text())
        khoang = int(self.inputKhoangw.text())

        ngayBatdau = str(getdate(bd_date))
        ngayKetthuc = str(getdate(kt_date))

        topLat_value = float(self.topLat.text())
        bottomLat_value = float(self.bottomLat.text())
        leftLong_value = float(self.leftLong.text())
        rightLong_value = float(self.rightLong.text())

        input_geometry = ee.Geometry.Rectangle([leftLong_value, bottomLat_value, rightLong_value, topLat_value])

        lat = (topLat_value + bottomLat_value) / 2
        long = (leftLong_value + rightLong_value) / 2

        # Band combinations
        rgbMethod = self.comboRGBw.currentIndex()
        textrgb = self.comboRGBw.currentText()
        if rgbMethod == 0:
            bands = ['B4', 'B3', 'B2']  # Natural Color
        elif rgbMethod == 1:
            bands = ['B8', 'B4', 'B3']  # Color Infrared
        elif rgbMethod == 2:
            bands = ['B12', 'B8A', 'B4']  # Short-wave Infrared
        elif rgbMethod == 3:
            bands = ['B11', 'B8', 'B2']  # Agriculture  
        elif rgbMethod == 4:
            bands = ['B12', 'B11', 'B2']  # Geology
        elif rgbMethod == 5:
            bands = ['B4', 'B3', 'B1']  # Bathymetric
        elif rgbMethod == 6:
            bands = ['B12', 'B11', 'B4']  # False color Urban
        elif rgbMethod == 7:
            bands = ['B12', 'B11', 'B8A']  # Atmospheric penetration
        elif rgbMethod == 8:
            bands = ['B8', 'B11', 'B2']  # Healthy vegetation
        elif rgbMethod == 9:
            bands = ['B8', 'B11', 'B4']  # Land/Water
        elif rgbMethod == 10:
            bands = ['B12', 'B8', 'B3']  # Natural Colors with Atmospheric Removal
        elif rgbMethod == 11:
            bands = ['B12', 'B8', 'B4']  # Shortwave Infrared
        else:
            bands = ['B11', 'B8', 'B4']  # Vegetation Analysis

        S2_Collection = ee.ImageCollection("COPERNICUS/S2") \
            .filterDate(ngayBatdau, ngayKetthuc).select(bands) \
            .filterBounds(input_geometry) \
            .filterMetadata('CLOUDY_PIXEL_PERCENTAGE', "less_than", may) \
            .sort('CLOUD_COVERAGE_ASSESSMENT', True)
        # Get the first image in the collection
        S2 = S2_Collection.first()

        vizParams = {'bands': bands, 'min': 0, 'max': 2000, 'gamma': 0.8}

        image_date1 = ee.Date(S2.get('system:time_start')).format('Y-M-d').getInfo()

        soluonganh = S2_Collection.size().getInfo()

        tmp = getdatebubffer(image_date1, khoang)
        if self.outputName.text() =='':
            name = 'NotDefinedName'
        else:
            name = self.outputName.text()
            
        S22 = ee.ImageCollection("COPERNICUS/S2").filterDate(tmp['bd'], tmp['kt']) \
            .select(bands) \
            .filterBounds(input_geometry) \
            .median() \
            .clip(input_geometry)
        Map.setCenter(long, lat, 13)
        Map.addLayer(S2.clip(input_geometry), vizParams, "S2_" + name + '-' + textrgb + "_" + image_date1 + " (Single)")
        Map.addLayer(S22, vizParams, "S2_" + name + '-' + textrgb + "_" + image_date1 + " (Median)")
        Map.addLayer(input_geometry, {'color': 'red'}, name, False, 0.2)
        
        ### Message bar info
        self.iface.messageBar().pushMessage(
            "Open Sentiel-2 image for costum location successfully!",
            level=Qgis.Success, duration=10)
        ### Save image to Google Drive3
        export2Drive = self.checkBox.isChecked()
        image = S22
        if export2Drive == True:   
            downConfig = {'scale': 10, "maxPixels": 1.0E13, 'driveFolder': 'image_gee'}
            task = ee.batch.Export.image(image, name + '_' + image_date1, downConfig)
            task.start()
            self.iface.messageBar().pushMessage(
                "The Sentiel-2 image is saved to folder image_ee on your Google Drive successfully!",
                level=Qgis.Success, duration=10)

    def rgb(self):
        self.comboRGBw.clear()
        listTohop = ['Natural color (B4-B3-B2)', 'False color infrared (B8-B4-B3)', 'Short-wave infrared (B12-B8A-B4)',
                     'Agriculture (B11-B8-B2)', 'Geology (B12-B11-B2)', 'Bathymetric (B4-B3-B1)',
                     'False color Urban (B12-B11-B4)', 'Atmospheric penetration (B12-B11-B8A)',
                     'Healthy vegetation (B8-B11-B2)',
                     'Land/Water (B8-B11-B4)', 'Natural Colors with Atmospheric Removal (B12-B8-B3)',
                     'Shortwave Infrared (B12-B8-B4)', 'Vegetation Analysis (B11-B8-B4)']
        self.comboRGBw.addItems(listTohop)
