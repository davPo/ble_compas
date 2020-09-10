from blecompas.helper import Vector

class Compas():
    def __init__(self):
        self.bleaddress = ""
        self._version= ""
        self._snumber = ""
        self.valueheading = 0
        self.valuepolar = ""
        self.valuebattery = ""
        self.valuemagnetometer = Vector()
        self.valueaccelerometer = Vector()

    @property
    def version(self):
        return self._version

    @property
    def serialnumber(self):
        return self._snumber

    def connect(self):
        pass

    def disconnect(self):
        pass

    def getBatteryVoltage(self):
        pass

    def getHeading(self):
        pass

    def getRSSI(self):
        pass

    def getMagnetometerRaw(self):
        pass

    def getAccelerometermeterRaw(self):
        pass

    def _getSensorRaw(self):
        pass

    def applyMagnetometerCorrection(self):
        pass

    def clearMagnetometerCorrection(self):
        pass

    def _applyCorrection(matrix):
        pass

    def _clearCorrection(matrix):
        pass