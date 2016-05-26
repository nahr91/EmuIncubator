import Adafruit_BBIO.GPIO as GPIO
import BB_SHT15_lib
import motor
import time
import os
import threading
import sqlite3

conn = sqlite3.connect('/home/ubuntu/testDB.db')

maxTemp = 36.4 	#Emu	#37.8	#Gen
minTemp = 36.1	#Emu	#37.6	#Gen
maxHumi = 29	#Emu	#55	#Gen
minHumi = 24	#Emu	#50	#Gen



class incubadora(object):

	def __init__(self):
		
		self.Tdes=36.25
		self.periodo=10.0
		self.maxTemp = 36.4  #Emu    #37.8   #Gen
		self.minTemp = 36.1  #Emu    #37.6   #Gen
		self.maxHumi = 29    #Emu    #55     #Gen
		self.minHumi = 26    #Emu    #50     #Gen

		self.stop=1

		self.st1='Bombilla ceramica Off'
		self.st2='Ventiladores Off'
		self.st3='Humidificador Off'
		self.SHT15 = BB_SHT15_lib.BB_SHT15()
		time.sleep(0.5)
		self.motorDC = motor.motor()
		time.sleep(0.5)
		self.iTemp = self.SHT15.temperature()
		time.sleep(0.5)
		self.iHumi = self.SHT15.humidity()

		LOW = 0
		HIGH = 1
		self.motorDC.preexecute() # Starting PWM for the EN of the motors
		self.motorDC.motorSpeed(39)
		GPIO.setup("P8_22", GPIO.OUT) # Motor giro Derecha
		GPIO.cleanup()
		GPIO.setup("P8_23", GPIO.OUT) # Motor giro Izquierda
		GPIO.cleanup()

		GPIO.setup("P8_26", GPIO.OUT) # RELE TEMP
		GPIO.cleanup()
		GPIO.setup("P8_27", GPIO.OUT) # RELE HUMI
		GPIO.cleanup()
		GPIO.setup("P8_28", GPIO.OUT) # RELE HUMI
		GPIO.cleanup()
		self.lastiTemp=0
		self.estado=0
		time.sleep(0.5)

	def hiloDatos(self):
		while self.stop:
			try:
                		self.iTemp = self.SHT15.temperature()
				time.sleep(0.75)
                		self.iHumi = self.SHT15.humidity()
				self.sleep(0.75)

			except:
				print'Error en lectura de sensores'
				print 'Relanzando...'
				time.sleep(0.5)		

	def hiloTemp(self):
		lt=time.time()		
		while self.stop:
			try:
				error=(self.Tdes-self.iTemp)/(self.Tdes-23.0)
				t=time.time()-lt
				if t<(self.periodo*(error+0.16)):
					GPIO.output("P8_26", GPIO.HIGH)
					self.st1='Bombilla ceramica On'
					#print self.st1
				elif t>(self.periodo*(error+0.16)):
					GPIO.output("P8_26", GPIO.LOW)
					self.st1='Bombilla ceramica Off'
					#print self.st1
				if t>self.periodo:
					lt=time.time()
			except:
				print 'Error lectura temperatura'
				print 'Relanzando....'

	def hiloHum(self):
		while self.stop:
			try:
				if self.iHumi > self.maxHumi:
					GPIO.output("P8_28", GPIO.HIGH)
					self.st2='Ventiladores On'	
				elif self.iHumi < self.minHumi:
					GPIO.output("P8_27", GPIO.HIGH)
					self.st3='Humidificador On'
				else:
					GPIO.output("P8_28", GPIO.LOW)
					GPIO.output("P8_27", GPIO.LOW)
					self.st2='Ventiladores Off'
					self.st3='Humidificador Off'
			except:
				print 'Error lectura Humedad'
				print 'Relanzando....'

	def hiloMotor(self):
		while self.stop:
			try:
				f = open('/home/ubuntu/incubadoraEmu/motor.txt', 'r')
				motor = str(f.read(2));
				f.close()
				#print (motor)
				if ( motor == "00" or motor == "01" ): # 00 or 01 = Motor stopped 
					GPIO.output("P8_22", GPIO.LOW)	
					GPIO.output("P8_23", GPIO.LOW)		
				elif motor == "10": #Motor turning left
					GPIO.output("P8_22", GPIO.HIGH)
					GPIO.output("P8_23", GPIO.LOW)	
				elif motor == "11" : #Motor turning right
					GPIO.output("P8_22", GPIO.LOW)
					GPIO.output("P8_23", GPIO.HIGH)
			except:
				print 'Error motor'
				print 'Relanzando....'
	def hiloBDsqlite3(self):
		while(true):
			sleep(5)
		 	#Insert a row of data
			c.execute("INSERT INTO READ (date, temp, humi) VALUES (\'"+str(time.strftime("%c"))+"\',\'"+str(self.iTemp)+"\',\'"+str(self.iHumi)+"\')"
			# Save (commit) the changes
			conn.commit()
	def hiloVis(self):
		while True:
			try:
				os.system('clear')
				print 'Temperatura: '+str(self.iTemp)
				print 'Humedad: '+str(self.iHumi)
				print'--------------------------------'
				print self.st1
				print self.st2
				print self.st3
				time.sleep(0.5)
			except KeyboardInterrupt:
				self.stop=0
				print 'Deteniendo programa....'
				break
			except:
				print 'Error en la visualizacion de datos'

	def run(self):
		hD=threading.Thread(target=self.hiloDatos)
		hT=threading.Thread(target=self.hiloTemp)
		hH=threading.Thread(target=self.hiloHum)
		hM=threading.Thread(target=self.hiloMotor)
		hBD=threading.Thread(target=self.hiloBDsqlite3)
		hV=threading.Thread(target=self.hiloVis)
		hD.start()
		hT.start()
		hH.start()
		hM.start()
		hBD.start()
		hV.start()
		hD.join()
	        hT.join()
	       	hM.join()
	       	hBD.join()
        	hV.join()
        	hH.join()
		os.system('clear')
		print 'FIN DEL PROGRAMA'

if __name__=="__main__":
    incubadora().run()


