import os
import re
from itertools import chain
from bs4 import BeautifulSoup
import markdown
import html2text
from IPython.display import HTML


class LoggableItem(object):
    
    re_name_acronym = re.compile(r"^(.*?)(?:\s\((.*)\))?$")
    
    def __init__(self,path=None,parent=None,name=None,acronym=None):
        
        self.children = []
        self.parent = parent
        self.acronym = None
        self.name = None
        self.frontMatter = None
        self.log = None
        
        if (path is not None):            
            if (os.path.isdir(path)):
                self.path = path
            else:
                raise Exception("path must be a directory")
        
            self.name, self.acronym = LoggableItem.re_name_acronym.findall(os.path.split(path)[1])[0]
            
            self._retrieveChildrenFromFS()
            self._readFrontMatterFromFS()
            self._readLogFromFS()

        else:
            if not name and not acronym:
                raise Exception("A name and or acronym must be provided")
            
            self.acronym = acronym if name else None
            self.name = name if name else acronym

            if self.acronym:
                self.acronym = self.hierarchyAcronym
                    
    def _readFrontMatterFromFS(self):
        self.frontMatter = FrontMatterDocument(os.path.join(self.path,str(self)+".md"))
            
    def _readLogFromFS(self):
        self.log = LogDocument(os.path.join(self.path,str(self)+".log.md"))
    
    def _retrieveChildrenFromFS(self):
        self.children = [LoggableItem(os.path.join(self.path,d),parent=self) for d in os.listdir(self.path) if os.path.isdir(os.path.join(self.path,d))]
    
    def __repr__(self):
        if self.acronym:
            return "%s (%s)" % (self.name,self.acronym)
        else:
            return self.name
    
    def iterChildrenRecursive(self):
        for child in self.children:
            yield child
            for subchild in child.iterChildrenRecursive():
                yield subchild
    
    @property
    def hierarchyAcronym(self):
        acronym = self.acronym
        if not acronym:
            acronym = self.name.replace(" ","")
        acronym = acronym.split(".")[-1]
            
        parent = self.parent
        while parent is not None:
            
            acronym = parent.lastHierarchyAcronym + "." + acronym
            parent = parent.parent
        
        return acronym
    
    @property
    def lastHierarchyAcronym(self):
        return self.hierarchyAcronym.split(".")[-1]
        
    @property
    def frontMatterFile(self):
        return os.path.join(self.path,str(self)+".md")
            



class MarkdownDocument(object):
    def __init__(self,path):
        self.path = path
        self.html = ""
        self.markdown = ""
        self.soup = BeautifulSoup()
        
        try:
            self._readFromFS()
        except:
            pass
    
    def _readFromFS(self):
        with file(self.path,'r') as f:
            self.markdown = f.read()
            md = markdown.Markdown()
            self.html = md.convert(self.markdown)
            self.soup = BeautifulSoup(self.html)
            
    def _repr_html_(self):
        return self.html
            
        



class FrontMatterDocument(MarkdownDocument):
    def __init__(self,path):
        MarkdownDocument.__init__(self,path)
        
        self.tags = readTags(self.soup)
    
    



class LogMessage(object):
    def __init__(self,header=None, content=None):
        self.header = header
        self.content = content
    
    def _repr_html_(self):
        soup = BeautifulSoup();
        soup.append(self.header)
        for c in self.content:
            soup.append(c)
        return soup
        



class LogDocument(MarkdownDocument):
    def __init__(self,path):
        MarkdownDocument.__init__(self,path)
        self.logMessages = []
        
        self._getLogMessages()
    
    def _getLogMessages(self):
        logHeaders = [log_h2 for log_h2 in self.soup.findAll('h2')]
        if len(logHeaders) > 1:
            for i,logHeader in enumerate(logHeaders[:-1]):
                nextLogHeader = logHeaders[i+1]
                content = []
                for sibbling in logHeader.find_next_siblings():
                    if sibbling is not nextLogHeader:
                        content.append(sibbling)
                    else:
                        break
                self.logMessages.append(LogMessage(logHeader,content))
            
            self.logMessages.append(LogMessage(logHeaders[-1],logHeaders[-1].find_next_siblings()))
                        
        if len(logHeaders) == 1:
            self.logMessages.append(LogMessage(logHeaders[0],logHeaders[0].find_next_siblings()))
            
        



def readTags(soup):
    h2_tags = soup.find('h2',text=["Tags","tags","TAGS"])
    if (h2_tags):
        p_tags = h2_tags.findNext()
        if (p_tags.name == 'p'):
            return [tag.strip() for tag in p_tags.text.split(',')]



def writeTags(soup,tags):
    h2_tags = soup.find('h2',text=["Tags","tags","TAGS"])
    
    if not h2_tags:
        h2_tags = soup.body.append("<h2>Tags</h2>")
        
    p_tags = h2_tags.findNext()

    tagsString = ", ".join(tags)
    if (p_tags and p_tags.name == 'p'):
        p_tags.string = tagsString
    else:
        h2_tags.insert_after(r"<p>%s</p>" % tagsString)



