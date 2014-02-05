# -*- coding: utf-8 -*-
import random
import codecs
from experiment import getExperiment
class StimList(list):
    """Contains stimuli and metadata
    
    Stimuli are retrieved from a StimList randomly without replacement.
    The stimuli and metadata for each trial are contained in dictionaries which are returned by the retrieve method
    or by an iterator (e.g. iteration over a StimList in a for-loop)
    """
    def __init__(self,stimuli=[],order='random'):
        """
        Generate a list of stimuli from a file or a list of lists
        
        The __init__ method takes as an argument EITHER a filename OR a list of lists.
        If a filename, it should be a tab-delimited text file, where the first line contains headers, e.g.

        Word    Frequency
        very    796
        oval    8

        If the argument is a list, the list structure should be like the text file structure, containing a list
        for each stimulus, e.g.

        [['Word','Frequency'],['very',796],['oval',8]]

        The resulting StimList will be a list of dictionaries where each dictionary represents the stimuli and metadata for a trial
        These keys for these dictionaries are the column headers of the input file,
        or the names in the first list in the list of lists if that is given as an argument.
        """
        self.order = order
        list.__init__(self,self.generateList(stimuli))
        self.resetList()
        
    def generateList(self,stimuli):
        """Construct the list of stimuli either from a tab-delimited file or from a similarly structured list of lists
        
        Child classes may override this method to customize the format of the file or the construction of the stimulus list.
        """
        try:
            # On Mac, Excel uses \r to delimit the rows rather than \n (grr...)
            # so we'll try both ways
            splitByNewline = codecs.open(stimuli,'r','utf8').readlines() # split lines by \n
            lines = []
            for line in splitByNewline: lines.extend(line.split('\r'))
            lines = [[item.replace('\\n','\n') for item in line.rstrip().split('\t')] for line in lines if line.strip() != ""]
                    
        except TypeError:
            lines = stimuli
        if lines:
            thelist = [dict(zip(lines[0],line)) for line in lines[1:]]
        else:
            thelist = []
        return thelist
        
    def resetList(self):
        """Start sampling from the beginning of the list, reshuffling the list if order == 'random'
        """
        if self.order == 'random':
            random.shuffle(self)
            self.remainingStimuli = self[:]
        elif self.order == 'sequential':
            self.remainingStimuli = self[-1::-1]
        else:
            raise "Unknown ordering %s specified for %s"%(self.order,self.__class__.__name__)


    def retrieve(self):
        """
        Return the stimuli and metadata for the next trial as a dictionary
        """
        value = self.remainingStimuli.pop()
        if not self.remainingStimuli:                  # If we're out of stimuli
            self.resetList()
        return value

#    def __len__(self):
#        """Return the length of the stimulus list
#        
#        Allows the len function to be used on the stimulus list
#        """
#        return len(self)
#    
#    def __iter__(self):
#        """
#        Allows for-loop iteration over the items in the StimList
#
#        e.g. if sl is a StimList, 'for stim in sl:" will loop over all the stimuli/metadata dictionaries
#        If the retrieve method has been called previously, iteration will start with the next item that hasn't yet been retrieved
#        """
#        while self.remainingStimuli:
#            yield self.remainingStimuli.pop()
#        else:
#            self.resetList()

class LatinSquareList(StimList):
    """Builds lists for subjects based on their ID so that the experimental conditions are balanced

    Subject 1 gets the first condition of the first item of each experiment,
    the second condition of the second item of each experiment, etc.;
    subject 2 gets the second condition of the first item, the third condition of the second item, etc.

    The __init__ method reads in a tab-delimited text file.  The file must have at least these column headers:  "experiment", "condition", "itemnumber".
    
    Alternatively, lists can be decoupled from subject IDs by specifying the list_number argument to __init__, which will take the place of the subject's ID number.
    """

    def __init__(self,stimuli=[],order='random',list_number=None):
        if list_number == None: self.list_number = getExperiment()['subject']
        else: self.list_number = list_number
        StimList.__init__(self, stimuli=stimuli, order=order)
        
    def generateList(self,stimuli):
        """
        Build the list according to the subject's ID
        """
        thelist = StimList.generateList(self,stimuli)
        return self.selectStimuli(thelist)
    
    def selectStimuli(self,thelist):
        #To implement this, we create an 'experiments' dictionary whose keys are the experiments, and whose values
        #are dictionaries with three keys: 'conditions','itemnumbers','items'.
        #For each experiment 'expt', experiments[expt]['conditions'] is a list of the conditions in that experiment.
        #experiments[expt]['itemnumbers'] is a list of the itemnumbers in that experiment.
        #experiments[expt]['items'] is a dictionary containing the items themselves,
        #indexed by itemnumber and condition, so that for every itemnumber and condition in expt,
        #experiments[expt]['items'][itemnumber,condition] gives the specific item in that experiment with
        #the given itemnumber and condition.
        experiments = {}
        for stim in thelist:
            expt = experiments.setdefault(stim['experiment'],{'conditions':[],'itemnumbers':[],'items':{}})
            if not stim['condition'] in expt['conditions']: expt['conditions'].append(stim['condition'])
            if not stim['itemnumber'] in expt['itemnumbers']: expt['itemnumbers'].append(stim['itemnumber'])
            expt['items'][stim['itemnumber'],stim['condition']]=stim

        thelist = []
                
        for expt,exptDict in experiments.items():
            if expt == 'filler':
                #Every subject will see all the fillers.
                thelist.extend(exptDict['items'].values())
            else:
                thelist.extend(
                    [exptDict['items'][itemnumber,exptDict['conditions'][(i+self.list_number-1)
                                                                          %len(exptDict['conditions'])]]
                     for i,itemnumber in enumerate(exptDict['itemnumbers'])])
        return thelist


def parseRegions(text,parse_underscores = True):
    """Produce interest area labels for a text string with regions delimited with \ and words grouped together with _
    
    parseRegions is useful when words or regions of interest in sentences don't appear in the same places in different items
    for instance, if the main verb of the sentence occurs at word 3 in some items and word 4 for other items (in the same condition)
    or if the length of a relative clause of interest varies across items (within a single condition)
    In these cases, you can delimit the regions of the sentence using \ and parse them with parseRegions.
    
    parseRegions is also useful if there are words that you want to group together, for instance verbs that are compound in some items but not all.
    You can group the words with an underscore and parse the sentences with parseRegions (setting parse_underscores to True).
    
    parseRegions takes a string of text and returns a 2-tuple consisting of the text stripped of the delimiters, and a list of region labels.
    The region labels have the form Word.Regionnumber.WordNumberWithinRegion.WordParticleNumberWithinCompound
    
    Example:
    >>> parseRegions('The light \ that the kid turned_on \ was bright.',parse.underscores = True)
    ('The light that the kid turned on was bright.', ['The.1.1.1', 'light.1.2.1', 'that.2.1.1', 'the.2.2.1', 'kid.2.3.1', 'turned.2.4.1', 'on.2.4.2', 'was.3.1.1', 'bright.3.2.1'])
    >>> parseRegions('The light \ that the kid turned_on \ was bright.',parse.underscores = False)
    ('The light that the kid turned on was bright.', ['The.1.1', 'light.1.2', 'that.2.1', 'the.2.2', 'kid.2.3', 'turned_on.2.4', 'was.3.1', 'bright.3.2'])    
    """
    if parse_underscores:
        return (text.replace('_'," ").replace(' \\ ',' '),
                ['%s.%d.%d.%d'%(particle.replace('.',""),regionnum+1,wordnum+1,particlenum+1)
                 for regionnum,region in enumerate(text.split(' \\ '))
                 for wordnum,word in enumerate(region.split())
                 for particlenum,particle in enumerate(word.split("_"))
                 ]
                )
    else:
        return (text.replace(' \\ ',' '),
                ['%s.%d.%d'%(word.replace('.',""),regionnum+1,wordnum+1)
                 for regionnum,region in enumerate(text.split(' \\ '))
                 for wordnum,word in enumerate(region.split())
                 ]
                )

class LingerList(LatinSquareList):
    """
    Parses a Linger-formatted items file.
    Every item should be formatted like:
    
    # experiment itemnumber condition
    This is the sample sentence.
    ? Is this the sample question? Y

    The question is optional.  Currently you can only specify have one question per stimulus (in contrast with Linger).
    The stimulus sentence (or sentences) may take up multiple lines.
    """
    def generateList(self,stimuli):
        file = open(stimuli,'r')
        splitByNewline = file.readlines() # split lines by \n
        lines = []
        for line in splitByNewline: lines.extend(line.split('\r'))
        lines = [line.strip() for line in lines]
        lines.reverse()
        file.close()
        thelist = []
        line = ""
        while True:
            while True:
                if line.strip() and line.strip()[0] == "#": break
                if not lines: break
                line = lines.pop()
            if not lines: break
            metadata = line.split()
            if len(metadata) != 4:
                raise "Expecting metadata in format '# experiment itemnumber condition'; got '%s'"%line
            stim = {'experiment':metadata[1],'itemnumber':metadata[2],'condition':metadata[3]}
            stimlines = []
            while lines:
                line = lines.pop()
                if line.strip() and line.strip()[0] in ['?','#']: break
                stimlines.append(line)
            stim['sentence']= '\n'.join(stimlines).strip()
            if line.strip()[0] == '?':
                stim['question'] = line[1:-1].strip()
                stim['cresp'] = line[-1]
            thelist.append(stim)
        return self.selectStimuli(thelist)
            
