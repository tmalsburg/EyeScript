# -*- coding: utf-8 -*-

"""Script for clementine - A cleft experiment.
Presents sentences to the subject.  Each sentence is followed by a yes/no comprehension question.
"""
######################
# IMPORT STATEMENTS
######################
import EyeScript as es
import os
import time
import pylink
from EyeScript.defaults import defaultParams

##################################
# EXPERIMENT INITIALIZATION
##################################
es.Experiment(session_info = ['session','time','age','gender','study','glasses','nativelang','origin','hsleep','alc24'],
			align=('left','center'),margins=[20,0,20,0]
			,font_size=18
			,font_name='arial'
			#,font_name='c:\windows\fonts\COURE.TTF'
			#,edf_prefix="exmpl"
			)


##################################
# TRIAL DEFINITION
##################################
correctFeedback = es.ContinueDisplay("Richtig!",align=('center','center'),duration=800,continue_text="")
incorrectFeedback = es.ContinueDisplay("Falsch!",align=('center','center'),duration=800,continue_text="")
class ReadingTrial(es.Trial):
	def __init__(self,stim):
		self.slides = []
		imageName = "%s_%s_%s_s"%(stim['experiment'],
							stim['itemnumber'],
							stim['condition'],
							#str(i)
							)
		nr_lines = len(stim['sentence'].split('\n'))
		self.slides.append(es.TextDisplay(unicode(stim['sentence']),name='slide_1',
								font_size=14,
								response_device=es.EyeLinkButtons,
								logging=['rt','resp'],
								possible_resp = ["Y"],background_for=self,
								screen_image_file=os.path.join('screenimages', imageName+"1.jpg"),
								interest_area_file=os.path.join('interestareas', imageName+"1.ias"),
								nr_lines = nr_lines
								))
		####
		self.question = es.ContinueDisplay(stim['question'],name='question',
								font_size=16,
								align=('center','center'),
								vertical_spacing=0,
								response_device=es.EyeLinkButtons,
								possible_resp = ['left trigger','right trigger'],
								#cresp=stim['cresp'] == "1" and "left trigger" or "right trigger",
								cresp=stim['cresp'] == "Y" and "right trigger" or "left trigger",
								continue_text = u'links: NEIN            rechts: JA'
								)
		self.setMetadata(stim)
	def run(self):
		if self.trialNumber%15==0:
			es.calibrateTracker()
		#es.driftCorrect()
		es.startRecording()
		#pylink.endRealTimeMode()	## solves problem of not working key response and sound output
		for slide in self.slides:
			x, y = defaultParams['gcTargetCoords']
			if slide.params['nr_lines'] > 1:
				y = y - 0.5*(slide.params['nr_lines']-1)*(defaultParams['vertical_spacing']+slide.params['singleline_height'])
			es.gcFixation(target = (x,y))
			slide.run()
		es.stopRecording()
		self.question.run()
		#if self.question['acc']:
		#	correctFeedback.run()
		#else:
		#	 incorrectFeedback.run()

		


##################################
# PRACTICE TRIAL
##################################
class PracticeTrial(es.Trial):
	def __init__(self,stim):
		self.slides = []
		imageName = "%s_%s_%s_s"%(stim['experiment'],
							stim['itemnumber'],
							stim['condition'],
							#str(i)
							)
		nr_lines = len(stim['sentence'].split('\n'))
		self.slides.append(es.TextDisplay(unicode(stim['sentence']),name='slide_1',
								font_size=14,
								response_device=es.EyeLinkButtons,
								logging=['rt','resp'],
								possible_resp = ["Y"],background_for=self,
								screen_image_file=os.path.join('screenimages', imageName+"1.jpg"),
								interest_area_file=os.path.join('interestareas', imageName+"1.ias"),
								nr_lines = nr_lines
								))
		####
		self.question = es.ContinueDisplay(stim['question'],name='question',
								font_size=16,
								align=('center','center'),
								vertical_spacing=0,
								response_device=es.EyeLinkButtons,
								possible_resp = ['left trigger','right trigger'],
								#cresp=stim['cresp'] == "1" and "left trigger" or "right trigger",
								cresp=stim['cresp'] == "Y" and "right trigger" or "left trigger",
								continue_text = u'links: NEIN            rechts: JA'
								)
		self.setMetadata(stim)
	def run(self):
		#es.driftCorrect()
		es.startRecording()
		for slide in self.slides:
			x, y = defaultParams['gcTargetCoords']
			if slide.params['nr_lines'] > 1:
				y = y - 0.5*(slide.params['nr_lines']-1)*(slide.params['vertical_spacing']+slide.params['singleline_height'])
			es.gcFixation(target = (x,y))
			slide.run()
		es.stopRecording()
		self.question.run()
		if self.question['acc']:
			correctFeedback.run()
		else:
			incorrectFeedback.run()

			
			
##########################
# SESSION DEFINITION
##########################
def session():
	practStimList = es.StimList("clementine.practice.et3.txt", order='sequential')
	stimList = es.LatinSquareList("clementine.items.et3.txt")
	practTrialList = [PracticeTrial(stim) for stim in practStimList]
	trialList = [ReadingTrial(stim) for stim in stimList]
	es.calibrateTracker()
	es.ContinueDisplay(u"Willkommen zum Experiment.", response_device=es.Keyboard).run()
	
	es.ContinueDisplay(u"Lies die Sätze und drücke die Daumentaste, wenn du fertig bist. "
					   u"\nDann beantworte die Frage mit den Zeigefingertasten."
					   u"\nZuerst wirst du ein paar Übungssätze lesen.",
					   vertical_spacing=10).run()
	for tr in practTrialList: tr.record()
	es.ContinueDisplay(u"Nun beginnen die Experimentalsätze.").run()
	for tr in trialList: tr.record()
	es.TextDisplay(u"Vielen Dank für die Teilnahme. "
				   u"\nLeertaste zum beenden.", response_device=es.Keyboard).run()

#######################
# RUNNING THE SESSION
#######################
es.runSession(session)
