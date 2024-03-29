import os
import re
from itertools import chain
from bs4 import BeautifulSoup
import markdown
import html2text
from IPython.display import HTML


class LoggableItemStore(object):
    def __init__(self,path):
        self.path = path
        self.children = []
        self._retrieveChildrenFromFS()
    
    def _retrieveChildrenFromFS(self):
        self.children = [LoggableItem(os.path.join(self.path,d),parent=self) for d in os.listdir(self.path) if os.path.isdir(os.path.join(self.path,d)) and not d.startswith(".")]
        
    def iterChildrenRecursive(self):
        for child in self.children:
            yield child
            for subchild in child.iterChildrenRecursive():
                yield subchild


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
        self._rawMarkdown = ""
        self.soup = BeautifulSoup()
        
        try:
            self._readFromFS()
        except:
            self._rawMarkdown = self.template
        
        self._parseRawMarkdown()
    
    def _repr_html_(self):
        return self.soup.prettify()
    
    @property
    def markdown(self):
        return html2text.html2text(self.soup.prettify())
    
    def _readFromFS(self):
        with file(self.path,'r') as f:
            self._rawMarkdown = f.read()    
    
    def _writeToFS(self):
        with file(self.path,'w') as f:
            if self.markdown is not self._rawMarkdown:
                f.write(self.markdown)
    
    def _parseRawMarkdown(self):
        md = markdown.Markdown()
        html = md.convert(self._rawMarkdown)
        self.soup = BeautifulSoup(html)
    
    def save(self):
        self._writeToFS()
        
    @property
    def template(self):
        return ""
    
    @property
    def filename(self):
        return os.path.split(self.path)[1]
        
    
    
class FrontMatterDocument(MarkdownDocument):
    def __init__(self,path):
        MarkdownDocument.__init__(self,path)
        
        self.tags = readTags(self.soup)


class LogMessage(object):
    def __init__(self,header=None, content=None):
        self._header = header
        self._content = content
        self._timeIsSpecified = False
        self.datetime = None
        
        self._getDatetimeFromHeader()
    
    def _repr_html_(self):
        return self.html
    
    @property
    def html(self):
        return self._header.prettify() + "".join([c.prettify() for c in self._content])
    
    @property
    def contentMarkdown(self):
        return html2text.html2text(self.html)
    
    def _getDatetimeFromHeader(self):
        #TODO: Very ugly nested try except!!! Do it properly! 
        try:
            self.datetime = strptime(self._header.text,r"%Y-%m-%d %H:%M")
            self._timeIsSpecified = True
        except:
            try:
                self.datetime = strptime(self._header.text,r"%Y-%m-%d %H:%M:%S")
                self._timeIsSpecified = True
            except:
                try:
                    self.datetime = strptime(self._header.text,r"%Y-%m-%d")
                    self._timeIsSpecified = False
                except:
                    self.datetime = None
                    self._timeIsSpecified = False



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
    
    @property
    def template(self):
        return "# %s Log\n\n" % self.filename.strip(".log.md")
            
    
    def newLogMessage(self,message,datetime=None):
        """
        Add a new logmessage for this item.
        """
        
        pass



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









