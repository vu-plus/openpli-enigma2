from ServiceReference import ServiceReference
from Components.config import config
from timer import TimerEntry as TimerObject
from urllib import quote
import xml

class FallbackTimerList():

	def __init__(self, session, fallbackFunction=None):
		self.session = session
		self.fallbackFunction = fallbackFunction
		if config.usage.remote_fallback_enabled.value and config.usage.remote_fallback_external_timer.value and config.usage.remote_fallback.value:
			self.url = config.usage.remote_fallback.value.rsplit(":", 1)[0]
		else:
			self.url = None
		self.getFallbackTimerList()

	def getUrl(self, url):
		print "[FallbackTimer] getURL", url
		from twisted.web.client import getPage
		return getPage("%s/%s" % (self.url, url), headers={})

	def getFallbackTimerList(self):
		self.list = []
		if self.url:
			try:
				self.getUrl("web/timerlist").addCallback(self.gotFallbackTimerList).addErrback(self.errorUrlFallback)
			except:
				self.errorUrlFallback(_("Unexpected error while retreiving fallback tuner's timer information"))
		else:		
			self.fallback(True)

	def gotFallbackTimerList(self, data):
		try:
			root = xml.etree.cElementTree.fromstring(data)
		except Exception, e:
			self.fallback(False, e)
		self.list = [
				FallbackTimerClass(
					service_ref = str(timer.findtext("e2servicereference", '').encode("utf-8", 'ignore')),
					name = str(timer.findtext("e2name", '').encode("utf-8", 'ignore')),
					disabled = int(timer.findtext("e2disabled", 0)),
					timebegin = int(timer.findtext("e2timebegin", 0)),
					timeend = int(timer.findtext("e2timeend", 0)),
					duration = int(timer.findtext("e2duration", 0)),
					startprepare = int(timer.findtext("e2startprepare", 0)),
					state = int(timer.findtext("e2state", 0)),
					repeated = int(timer.findtext("e2repeated", 0)),
					justplay = int(timer.findtext("e2justplay", 0)),
					eit = int(timer.findtext("e2eit", -1)),
					afterevent = int(timer.findtext("e2afterevent", 0)),
					dirname = str(timer.findtext("e2dirname", '').encode("utf-8", 'ignore')),
					description = str(timer.findtext("e2description", '').encode("utf-8", 'ignore')),
					flags = "",
					conflict_detection = 0)
			for timer in root.findall("e2timer")
		]
		print "[FallbackTimer] read %s timers from fallback tuner" % len(self.list)
		self.session.nav.RecordTimer.setFallbackTimerList(self.list)
		self.fallback(True)
		
	def removeTimer(self, timer, fallbackFunction):
		self.fallbackFunction = fallbackFunction
		self.getUrl("web/timerdelete?sRef=%s&begin=%s&end=%s" % (timer.service_ref, timer.begin, timer.end)).addCallback(self.getUrlFallback).addErrback(self.errorUrlFallback)

	def toggleTimer(self, timer, fallbackFunction):
		self.fallbackFunction = fallbackFunction
		self.getUrl("web/timertogglestatus?sRef=%s&begin=%s&end=%s" % (timer.service_ref, timer.begin, timer.end)).addCallback(self.getUrlFallback).addErrback(self.errorUrlFallback)
	
	def cleanupTimers(self, fallbackFunction):
		self.fallbackFunction = fallbackFunction
		if self.url:
			self.getUrl("web/timercleanup?cleanup=true").addCallback(self.getUrlFallback).addErrback(self.errorUrlFallback)	
		else:
			self.fallback()

	def addTimer(self, timer, fallbackFunction):
		self.fallbackFunction = fallbackFunction
		url = "web/timeradd?sRef=%s&begin=%s&end=%s&name=%s&description=%s&disabled=%s&justplay=%s&afterevent=%s&repeated=%s&dirname=%s&eit=%s" % (
			timer.service_ref,
			timer.begin,
			timer.end,
			quote(timer.name.decode('utf8').encode('utf8','ignore')),
			quote(timer.description.decode('utf8').encode('utf8','ignore')),
			timer.disabled,
			timer.justplay,
			timer.afterEvent,
			timer.repeated,
			None,
			timer.eit or 0,
		)
		self.getUrl(url).addCallback(self.getUrlFallback).addErrback(self.errorUrlFallback)	

	def editTimer(self, service_ref_prev, begin_prev, end_prev, timer, fallbackFunction):
		self.fallbackFunction = fallbackFunction
		url = "web/timerchange?sRef=%s&begin=%s&end=%s&name=%s&description=%s&disabled=%s&justplay=%s&afterevent=%s&repeated=%s&channelOld=%s&beginOld=%s&endOld=%s&dirname=%s&eit=%s" % (
			timer.service_ref,
			timer.begin,
			timer.end,
			quote(timer.name.decode('utf8').encode('utf8','ignore')),
			quote(timer.description.decode('utf8').encode('utf8','ignore')),
			timer.disabled,
			timer.justplay,
			timer.afterEvent,
			timer.repeated,
			service_ref_prev,
			begin_prev,
			end_prev,
			None,
			timer.eit or 0,
		)
		self.getUrl(url).addCallback(self.getUrlFallback).addErrback(self.errorUrlFallback)

	def getUrlFallback(self, data):
		print "[FallbackTimer] getURLFallback", data
		try:
			root = xml.etree.cElementTree.fromstring(data)
			if root[0].text == 'True':
				self.getFallbackTimerList()
			else:
				self.fallback(False, root[1].text)
		except:
				self.fallback(False, "Unexpected Error")
	
	def errorUrlFallback(self, error):
		print "[FallbackTimer] errorURLFallback", error
		self.fallback(False, error)

	def fallback(self, answer=True, message=""):
		if self.fallbackFunction:
			self.fallbackFunction(answer, message)

class FallbackTimerClass(TimerObject):
	def __init__(self, service_ref = "", name = "", disabled = 0, \
			timebegin = 0, timeend = 0, duration = 0, startprepare = 0, \
			state = 0, repeated = 0, justplay = 0, eit = 0, afterevent = 0, \
			dirname = "", description = "", flags = "", conflict_detection = 0):
		self.service_ref = ServiceReference(service_ref and ':'.join(service_ref.split(':')[:11]) or None)
		self.name = name
		self.disabled = disabled
		self.begin = timebegin
		self.end = timeend
		self.duration = duration
		self.startprepare = startprepare
		self.state = state
		self.repeated = repeated
		self.justplay = justplay
		self.eit = eit
		self.afterEvent = afterevent
		self.dirname = dirname
		self.description = description
		self.flags = flags
		self.conflict_detection = conflict_detection

		self.external = True
		self.always_zap = False
		self.zap_wakeup = False
		self.pipzap = False
		self.rename_repeat = False
		self.record_ecm = False
		self.descramble = True
		self.tags = []
		self.repeatedbegindate = timebegin