 
import os
import subprocess
import n4d.server.core as n4dcore
import n4d.responses
import datetime
import json


class LliurexUpManager:

	def __init__(self):

		self.enabledAutoUpgradeToken="/etc/systemd/system/multi-user.target.wants/lliurex-up-auto-upgrade.service"
		self.lliurexUpAutoToken="/var/run/lliurex-up-auto-upgrade.token"
		self.lliurexUpAutoRunToken="/var/run/lliurex-up-auto-upgrade.lock"
		self.lliurexUpAutoControlPath="/etc/lliurex-up-auto-upgrade"
		self.lliurexUpAutoControlFile=os.path.join(self.lliurexUpAutoControlPath,"lliurex-up-auto-upgrade.json")
		self._createEnvironment()

	#def __init__

	def _createEnvironment(self):

		createFile=False
		attemps=3
		weeksOfPause=0

		if not os.path.exists(self.lliurexUpAutoControlPath):
			os.mkdir(self.lliurexUpAutoControlPath)
			createFile=True

		if not os.path.exists(self.lliurexUpAutoControlFile):
			createFile=True

		if createFile:
			self._create_control_file(attemps,weeksOfPause)

	#def _createEnvironment

	def _create_control_file(self,attemps,weeksOfPause):

		tmp={}
		tmp["atttempsAvailables"]=attemps
		today=datetime.date.today()
		if weeksOfPause==0:
			nextDay=today+datetime.timedelta(days=1)
		else:
			nextDay=today+datetime.timedelta(days=7*weeksOfPause)
		
		nextDay=nextDay.isoformat()
		tmp["dateToUpdate"]=nextDay
		tmp["weeksOfPause"]=weeksOfPause

		try:
			with open(self.lliurexUpAutoControlFile,'w') as fd:
				json.dump(tmp,fd)
		except:
			pass

	#def _create_control_file

	def _read_control_file(self):

		currentContent={}
		if os.path.exists(self.lliurexUpAutoControlFile):
			try:
				with open(self.lliurexUpAutoControlFile,'r') as fd:
					currentContent=json.load(fd)
			except:
				pass

		return currentContent

	#def _read_control_file

	def _update_control_file(self,weeksOfPause):

		currentContent=self._read_control_file()

		if len(currentContent)==0:
			attemps=3
			weeksOfPause=0
		else:
			if weeksOfPause==0:
				attemps=currentContent["atttempsAvailables"]-1
			else:
				attemps=0
		
		self._create_control_file(attemps,weeksOfPause)

	#def update_control_file

	def manage_auto_update_service(self,enable):
		
		result=True
		attemps=3
		weeksOfPause=0

		if enable:
			if not self.is_auto_update_enabled()["return"]:
				try:
					cmd="systemctl enable lliurex-up-auto-upgrade.service"
					p=subprocess.run(cmd,shell=True,check=True)
				except subprocess.CalledProcessError as e:
					result=False
					pass

			if result:
				self._create_control_file(attemps,weeksOfPause)
		else:
			if self.is_auto_update_enabled()["return"]:
				try:
					cmd="systemctl disable lliurex-up-auto-upgrade.service"
					p=subprocess.run(cmd,shell=True,check=True)
				except subprocess.CalledProcessError as e:
					result=False

		return n4d.responses.build_successful_call_response(result)	

	#def manage_auto_update_service 
			
	def stop_auto_update_service(self,weeksOfPause=0,isSystemUpdate=False):

		result=True
		attemps=3

		ret=self.is_auto_update_active()["return"]

		if ret:
			if not self.is_auto_update_running()["return"]:
				try:
					cmd="systemctl stop lliurex-up-auto-upgrade.service"
					p=subprocess.run(cmd,shell=True,check=True)
					if os.path.exists(self.lliurexUpAutoToken):
						os.remove(self.lliurexUpAutoToken)
				except subprocess.CalledProcessError as e:
					result=False

		if isSystemUpdate:
			self._create_control_file(attemps,weeksOfPause)
		else:
			self._update_control_file(weeksOfPause)

		return n4d.responses.build_successful_call_response(result)	
	
	#def stop_auto_update_service

	def is_auto_update_active(self):

		result=False

		cmd="systemctl is-active lliurex-up-auto-upgrade.service"
		p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
		pout=p.communicate()[0].decode().strip()

		if pout=="active":
			result=True

		return n4d.responses.build_successful_call_response(result)	
	
	#def is_auto_update_active

	def is_auto_update_enabled(self):

		result=False

		if os.path.exists(self.enabledAutoUpgradeToken):
			result=True

		return n4d.responses.build_successful_call_response(result)	

	#def is_auto_update_enabled

	def is_auto_update_running(self):

		result=False

		if os.path.exists(self.lliurexUpAutoRunToken):
			result=True

		return n4d.responses.build_successful_call_response(result)	
	
	#def is_auto_update_running

	def can_cancel_auto_upgrade(self):

		result=False
		currentContent=self._read_control_file()
		try:
			if currentContent["atttempsAvailables"]>0:
				result=True
		except:
			pass	
		
		return n4d.responses.build_successful_call_response(result)			

	#def can_cancel_auto_upgrade

	def initialize_control_file(self):

		attemps=3
		weeksOfPause=0

		self._create_control_file(attemps,weeksOfPause)
		
		return n4d.responses.build_successful_call_response(True)			

	#def initialize_control_file	

#def LliurexUpManager
	
