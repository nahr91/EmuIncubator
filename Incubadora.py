import Adafruit_BBIO.GPIO as GPIO
import BB_SHT15_lib
import motor
import time
import os
import threading
import sqlite3
from datetime import datetime, date

maxTemp = 36.4 	#Emu	#37.8	#Gen
minTemp = 36.1	#Emu	#37.6	#Gen
maxHumi = 29	#Emu	#55	#Gen
minHumi = 24	#Emu	#50	#Gen



class incubadora(object):

	def __init__(self):
		#time.sleep(60)
		self.Tdes=36.3
		self.periodo=8.0
		self.maxTemp = 36.4  #Emu    #37.8   #Gen
		self.minTemp = 36.1  #Emu    #37.6   #Gen
		self.maxHumi = 29    #Emu    #55     #Gen
		self.minHumi = 26    #Emu    #50     #Gen
		self.stop=True
		errorSensor = False
		self.st1='Bombilla ceramica Off'
		self.st2='Ventiladores Off'
		self.st3='Humidificador Off'
		self.st4='Motor Off'
		
		self.SHT15 = BB_SHT15_lib.BB_SHT15()
		time.sleep(0.5)
		self.iTemp = self.SHT15.temperature()
		time.sleep(0.5)
		self.iHumi = self.SHT15.humidity()		
		time.sleep(0.5)
		self.motorDC = motor.motor()
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
			except KeyboardInterrupt:
				self.stop=False
			except:
				print'Error en lectura de sensores'
				print 'Relanzando...'
				time.sleep(0.5)		

	def hiloTemp(self):
		lt=time.time()		
		while self.stop:
			try:
				error=(self.Tdes-self.iTemp)/(self.Tdes-35)
				t=time.time()-lt
                                if self.iTemp>self.Tdes:
                                        GPIO.output("P8_26", GPIO.LOW)
                                        self.st1='Bombilla ceramica Off'
				elif self.iTemp>=34.5:
					if t<(self.periodo*(error+0.1)):
						GPIO.output("P8_26", GPIO.HIGH)
						self.st1='Bombilla ceramica On'
						#print self.st1
					elif t>(self.periodo*(error+0.1)):
						GPIO.output("P8_26", GPIO.LOW)
						self.st1='Bombilla ceramica Off'
						#print self.st1
					if t>self.periodo:
						lt=time.time()
				elif self.iTemp<34:
					GPIO.output("P8_26", GPIO.HIGH)
                                        self.st1='Bombilla ceramica On'
                        except KeyboardInterrupt:
                                self.stop=False

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
                        except KeyboardInterrupt:
                                self.stop=False
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
					self.st4='Motor Off'		
				elif motor == "10": #Motor turning left
					GPIO.output("P8_22", GPIO.HIGH)
					GPIO.output("P8_23", GPIO.LOW)
					self.st4='Motor Left'	
				elif motor == "11" : #Motor turning right
					GPIO.output("P8_22", GPIO.LOW)
					GPIO.output("P8_23", GPIO.HIGH)
					self.st4='Motor Right'
                        except KeyboardInterrupt:
                                self.stop=False
			except:
				print 'Error motor'
				print 'Relanzando....'

	def hiloVis(self):
		while self.stop:
			try:
				os.system('clear')
				print 'Temperatura: '+str(self.iTemp)
				print 'Humedad: '+str(self.iHumi)
				print'--------------------------------'
				print self.st1
				print self.st2
				print self.st3
				print self.st4
#				print "INSERT INTO READ(date, temp, humi)  VALUES("+str(datetime.now())+",\'"+str(self.iTemp)+"\',\'"+str(self.iHumi)+"\')"
#				print datetime.now()
				time.sleep(0.5)
                        except KeyboardInterrupt:
                                self.stop=False
			except:
				print 'Error en la visualizacion de datos'
        def hiloBDsqlite3(self):
		while self.stop:
			time.sleep(5)
			try:
				conn = sqlite3.connect('/home/ubuntu/testDB.db')
				c=conn.cursor()
				#Insert a row of data
				c.execute("INSERT INTO READ(date, temp, humi)  VALUES(\'"+str(datetime.now())+"\',\'"+str(self.iTemp)+"\',\'"+str(self.iHumi)+"\')")
				# Save (commit) the changes
				conn.commit()
				conn.close()
			except:
				print 'Error BD sqlite3'


	def run(self):
		hD=threading.Thread(target=self.hiloDatos)
		hT=threading.Thread(target=self.hiloTemp)
		hH=threading.Thread(target=self.hiloHum)
		hM=threading.Thread(target=self.hiloMotor)
		hV=threading.Thread(target=self.hiloVis)
		hBD=threading.Thread(target=self.hiloBDsqlite3)
		hD.start()
		hT.start()
		hH.start()
		hM.start()
		hV.start()
		hBD.start()
		#a=raw_input()
		#self.stop=False
		hD.join()
	        hT.join()
	       	hM.join()
        	hV.join()
        	hH.join()
        	hBD.join()
                GPIO.output("P8_26", GPIO.LOW)
                GPIO.output("P8_28", GPIO.LOW)
                GPIO.output("P8_27", GPIO.LOW)
                GPIO.output("P8_22", GPIO.LOW)
                GPIO.output("P8_23", GPIO.LOW)
#		os.system('clear')
		print 'FIN DEL PROGRAMA'

if __name__=="__main__":
    incubadora().run()


