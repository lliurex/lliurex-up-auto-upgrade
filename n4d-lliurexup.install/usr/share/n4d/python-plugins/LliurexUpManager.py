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
		self.cancellationsAvailables=3
		self.weeksOfPause=0
		self.extensionPause=5
		self.limitWeeksOfPause=5
		self.dateToUpdate=datetime.date.today()

	#def __init__

	def _createEnvironment(self):

		createFile=False
		if not os.path.exists(self.lliurexUpAutoControlPath):
			os.mkdir(self.lliurexUpAutoControlPath)
			createFile=True

		if not os.path.exists(self.lliurexUpAutoControlFile):
			createFile=True

		if createFile:
			self._init_control_vars()
			self._create_control_file()

	#def _createEnvironment

	def _init_control_vars(self):

		self.cancellationsAvailables=3
		today=datetime.date.today()
		nextDay=today+datetime.timedelta(days=1)
		self.dateToUpdate=nextDay.isoformat()
		self.weeksOfPause=0
		self.extensionPause=5

	#def _init_control_vars

	def _create_control_file(self):

		tmp={}
		tmp["cancellationsAvailables"]=self.cancellationsAvailables
		tmp["dateToUpdate"]=self.dateToUpdate
		tmp["weeksOfPause"]=self.weeksOfPause
		tmp["extensionPause"]=self.extensionPause

		try:
			with open(self.lliurexUpAutoControlFile,'w') as fd:
				json.dump(tmp,fd)

			return True 
		except:
			return False

	#def _create_control_file

	def read_current_config(self):

		currentConfig={}
		ret=self._read_control_file()

		if ret:
			currentConfig["cancellationsAvailables"]=self.cancellationsAvailables
			currentConfig["dateToUpdate"]=self.dateToUpdate
			currentConfig["weeksOfPause"]=self.weeksOfPause
			currentConfig["extensionPause"]=self.extensionPause

		result={"status":ret,"data":currentConfig}
		return n4d.responses.build_successful_call_response(result)

	#def read_current config

	def _read_control_file(self):

		result=True

		if os.path.exists(self.lliurexUpAutoControlFile):
			try:
				with open(self.lliurexUpAutoControlFile,'r') as fd:
					currentContent=json.load(fd)

				try:
					self.cancellationsAvailables=currentContent["cancellationsAvailables"]
				except:
					self.cancellationsAvailables=currentContent["atttempsAvailables"]
		
				self.dateToUpdate=currentContent["dateToUpdate"]
				
				try:
					self.weeksOfPause=currentContent["weeksOfPause"]
					self.extensionPause=currentContent["extensionPause"]
				except:
					pass
				
			except:
				result=False

		return result

	#def _read_control_file

	def _update_control_file(self,cancelUpdate,weeksOfPause):

		ret=self._read_control_file()
		today=datetime.date.today()
		updateFile=False
		
		if ret:
			currentWeeksOfPause=self.weeksOfPause
			if cancelUpdate:
				if self.cancellationsAvailables>0:
					self.cancellationsAvailables=self.cancellationsAvailables-1
					nextDay=today+datetime.timedelta(days=1)
					self.dateToUpdate=nextDay.isoformat()
					updateFile=True

			else:
				if weeksOfPause>0:
					if weeksOfPause<=self.limitWeeksOfPause:
						self.weeksOfPause=weeksOfPause
						self.extensionPause=self.limitWeeksOfPause-self.weeksOfPause

						if currentWeeksOfPause==0:
							nextDay=today
						else:
							nextDay=datetime.date.fromisoformat(self.dateToUpdate)
						
						nextDay=nextDay+datetime.timedelta(days=7*self.weeksOfPause)
						self.dateToUpdate=nextDay.isoformat()
						updateFile=True

		if updateFile:			
			return self._create_control_file()
		else:
			return False

	#def update_control_file

	def manage_auto_update_service(self,enable):
		
		result=True
		if enable:
			if not self.is_auto_update_enabled()["return"]:
				try:
					cmd="systemctl enable lliurex-up-auto-upgrade.service"
					p=subprocess.run(cmd,shell=True,check=True)
				except subprocess.CalledProcessError as e:
					result=False
					pass

			if result:
				self._init_control_vars()
				result=self._create_control_file()
		else:
			if self.is_auto_update_enabled()["return"]:
				try:
					cmd="systemctl disable lliurex-up-auto-upgrade.service"
					p=subprocess.run(cmd,shell=True,check=True)
					return self.stop_auto_update_service(True)
				except subprocess.CalledProcessError as e:
					result=False

		return n4d.responses.build_successful_call_response(result)	

	#def manage_auto_update_service 
			
	def stop_auto_update_service(self,isSystemUpdate=False):

		ret=self._stop_service()

		if ret:
			if isSystemUpdate:
				self._init_control_vars()
				ret=self._create_control_file()
			else:
				cancelUpdate=True
				ret=self._update_control_file(cancelUpdate,0)

		return n4d.responses.build_successful_call_response(ret)	
	
	#def stop_auto_update_service

	def _stop_service(self):

		result=True
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
	
		return result

	#def _stop_service

	def manage_auto_update_pause(self,enable,weeksOfPause=0):

		ret=True
		if enable:
			ret=self._stop_service()
			if ret:
				ret=self._update_control_file(False,weeksOfPause)
		else:
			self._init_control_vars()
			ret=self._create_control_file()

		return n4d.responses.build_successful_call_response(ret)	

	#def manage_auto_update_pause

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
		if self._read_control_file():
			if self.cancellationsAvailables>0:
				result=True

		return n4d.responses.build_successful_call_response(result)			

	#def can_cancel_auto_upgrade

	def initialize_control_file(self):

		self._init_control_vars()
		self._create_control_file()
		
		return n4d.responses.build_successful_call_response(True)			

	#def initialize_control_file	

#def LliurexUpManager
	
