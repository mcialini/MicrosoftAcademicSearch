#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Go through PaperAuthor.csv only at first

- remove punctuation ("." "-" etc.)
- convert unicode strings into ascii representation
- convert all names into uppercase
- store each name as tuple (Last, Else)


- two authornames who worked on same paper, have same last name
- 
'''

import unicodedata as uni
import csv
import re
import time
import itertools
import collections
       
currentTime = lambda: int(round(time.time()))

authornames = {} # store {name: [ids]} from Authors that are in PaperAuthor
authorids = {} # store {id: name} for Authors
duplicates = {} # stores {id: [duplicates]} for Authors
index = {} # stores {id: [aliases]} from PaperAuthor
lastNames = {} # store {last name : freq} from Author

alias = 0
merged = 0
outofseq = 0
abbreviated = 0
mergedabbrev = 0
dropped = 0


def findDuplicates(name, ID):
    
    global alias,outofseq,merged,abbreviated,mergedabbrev,dropped
    
    combined = name.split(" ")
    combined = [x for x in combined if x]
      
    '''
    before doing any other checks, go through list of KNOWN aliases for author
    from PaperAuthor and see if they exist under different ids
    '''    
    aliases = index.get(ID)
    if aliases is not None:
        print aliases
        for a in aliases:
            c = a.split(" ")
            if len(c) >= 2:
                freq = lastNames.get(c[-1])
                if a!= name and (len(c) > 2 or freq < 30):
                    aa = authornames.get(a)
                    if (aa is not None):
                        #print ID, '"' + name + '"', '"' + a + '"'
                        alias+=1
                        return aa

    '''
    1. check for all possible merges of two subnames in author
    '''    
    for i in range(len(combined)-1):
        str1 = " ".join(combined[0:i] + [combined[i]+combined[i+1]] + combined[i+2:])
        # search for the merged name in authornames
        a = authornames.get(str1)
        if a is not None: # this merged name exists already, so they are duplicates
            #print ID, "[", name, "] [", str1, "]" 
            merged+=1
            return a      
                         
    '''
    2. check for various orderings of name elements
    ''' 
    for p in itertools.permutations(combined):
        p1 = " ".join(p)
        if p1 != name:
            a = authornames.get(p1)
            if a is not None: 
                #print ID, combined, p 
                outofseq+=1
                return a  
        
    abbrevs = [x[0] for x in combined if x]  
    '''
    3. check if initials were accidentally concatenated
    '''   
    if len(abbrevs) == 3:
        s = abbrevs[0] + abbrevs[1] + " " + combined[2]
        if s != name:
            a = authornames.get(s)
            # if there is an author with this abbreviation
            if a is not None:
                #print ID,'"',name,'" "',s,'"'
                mergedabbrev +=1
                return a 
    
    '''
    4. check for all possible abbreviations of an author
       only considers names which have more than 2 parts 
    ''' 
    if len(combined) > 2:
        #print name,abbrevs
        for o in itertools.product('01',repeat=len(abbrevs)-1):
            s = ""
            o = [int(x) for x in o]
            for i in range (len(o)):
                s += abbrevs[i] if o[i] else combined[i]
                s += " "
            s += combined[-1]
            if s != name:
                a = authornames.get(s)
                # if there is an author with this abbreviation
                if a is not None:
                    #print ID,'"',name,'" "',s,'"'
                    abbreviated +=1
                    return a    
    elif len(combined) == 2: # length is 2, so we need to be careful
        freq = lastNames.get(combined[0])
        if freq is not None and freq < 30:
            s = abbrevs[0] + " " + combined[1]
            if s != name:
                a = authornames.get(s)
                # if there is an author with this abbreviation
                if a is not None:
                    #print "Found abbrev:",ID,'"',name,'" "',s,'"'
                    abbreviated +=1
                    toreturn = []                    
                    for i in a:
                        iname = authorids[i].split(" ")
                        if iname[-1] == combined[-1] and (iname[0] == combined[0] or len(iname[0]) == 1):
                            toreturn.append(i)
                    return toreturn    
                        
    '''
    5. if a name has more than two parts, check if one subname has been dropped
    '''
    #freq = lastNames.get(combined[-1])
    if len(combined) > 2:
        s = combined[0]
        numMiddles = len(combined)-2
        for o in itertools.product('012',repeat=numMiddles):
            s = combined[0] + " "
            o = [int(x) for x in o]    
            for i in range (len(o)):
                if o[i] == 1:
                    s+=combined[i+1] + " "
                elif o[i] == 2:
                    s+=abbrevs[i+1] + " "
            s += combined[-1]
            if s != name:
                a = authornames.get(s)
                if a is not None:
                    #print ID,'"',name,'" "',s,'"'
                    dropped +=1
                    return a            
        
        
        
'''''''''''''''''''''''''''''''''''''''''''''
READ THROUGH PAPERAUTHORS
CREATE A DICTIONARY {ID:[ALIASES]}
'''''''''''''''''''''''''''''''''''''''''''''

cr = csv.reader(open("pa2/PaperAuthor.csv","r"))
cr.next()   # skip header line
start = currentTime()
rows = 0
for row in cr:
    rows+=1
    ID = row[1]
    name = uni.normalize('NFKD',unicode(row[2])).encode('ascii','ignore')
    name = re.sub('[.\'-]','', row[2].upper())   
    combined = name.split(' ')
    combined = [x for x in combined if x not in {"JR","II","III"}]
    name = " ".join(combined)        
    # CHECK IF THIS ID IS ALREADY IN DICTIONARY
    aliases = index.get(ID)
    if index.get(ID) is not None:
        index[ID].append(name)
        #print index[ID]
    else:
        index[ID] = [name] 
        #print name, index[ID]
        
    #print index[ID][0]      
    
    if rows % 100000 == 0:
        print "-----------------"
        print "Read",rows,"entries"
    
end = currentTime()
print "Read through",rows,"lines in PaperAuthor.csv in", end-start, "s"


'''''''''''''''''''''''''''''''''''''''''''''
READ THROUGH AUTHORS
CREATE A DICTIONARY {NAME:[IDS]}
CREATE A DICTIONARY {ID: [DUP_IDS]}
'''''''''''''''''''''''''''''''''''''''''''''

cr = csv.reader(open("pa2/Author.csv","r"))
cr.next()   # skip header line
start = currentTime()
total = 0
rows = 0
for row in cr:
    rows+=1
    ID = row[0]
    name = uni.normalize('NFKD',unicode(row[1])).encode('ascii','ignore')
    name = re.sub('[.\'-]','', name.upper())
    combined = name.split(' ')
    combined = [x for x in combined if x and x not in {"JR","II","III"}]
    name = " ".join(combined)        

    if combined:
        l = lastNames.get(combined[-1])  
        if l is None:
            lastNames.update({combined[-1] : 1})
        else:
            l += 1
            
    aliases = index.get(ID)
    # IF ALIASES IS NONE, THIS AUTHOR ID DIDNT WRITE A PAPER, SO DON'T DO ANYTHING ELSE
    if aliases:
        # A PAPER WAS WRITTEN BY THIS ID
        # SEE IF THE NAME IS WITHIN AUTHORS
        knownIDs = authornames.get(name) # should return all ids associated with that name       
       
        # if there are no ids associated with that name
        if knownIDs is None: 
            dups = duplicates.get(ID)
            
            # and that id has not been encountered 
            if dups is None: 
                # add an entry for this id to duplicates 
                duplicates.update({ID: [ID]})           
            authornames.update({name : [ID]})                         
        else:
            # there ARE ids associated with this name  
            # see if the exact name,id pair has already been encountered 
            dups = duplicates.get(ID)
            if dups is None: 
                # same name but unique id, duplicate
                duplicates.update({ID : [ID] + knownIDs})
                total += 1            
                for i in knownIDs:
                    duplicates[i].append(ID)     
        
    dups = duplicates.get(ID)  
    if dups is None:
        duplicates.update({ID:[ID]}) 
        
    authorids.update({ID: name})
          
    if rows % 100000 == 0:
        print "-----------------"
        print "Read",rows,"entries"
    #print paperID, ID, name, affiliation
    
end = currentTime()
print "Read through",rows,"of Author.csv in ", end-start, "s"
print len(authornames),"entries added to authornames "

    
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''
go through authornames
for each name do a search for variations of the name
if any are found, add them to duplicates
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''
for key, ids in authornames.iteritems():
    ID = ids[0]    
    others = findDuplicates(key, ID)
    if others is not None: 
        if len(others) <=7:
            for i in others:
                if i != ID:
                    authornames[key].append(i)
                    duplicates[ID].append(i)
                    # add ID to each of its neighbors duplicate list
                    duplicates[i].append(ID)
                    j = authorids.get(i)
                    if j is not None:
                        k = authornames.get(j)
                        if k is not None: k.append(ID)
        else:
            print key,ID, "dropping:"
            for o in others:
                print "\t",authorids[o]

    
print "\n\n*********************************"
print "Num aliases found:",alias,"(", round((float(alias)/rows),4),")"
print "Num out of sequence names:",outofseq,"(", round((float(outofseq)/rows),4),")"
print "Num accidentally merged names:",merged,"(", round((float(merged)/rows),4),")"
print "Num abbreviated names:",abbreviated,"(", round((float(abbreviated)/rows),4),")"
print "Num accidentally merged abbrevs:",mergedabbrev,"(", round((float(mergedabbrev)/rows),4),")"
print "Num with dropped subnames:",dropped,"(", round((float(dropped)/rows),4),")"
print "total =", (alias+outofseq+merged+abbreviated+mergedabbrev+dropped)



'''''''''''''''''''''''''''''''''''''''''''''
WRITE THE LIST OF DUPLICATES INTO TEST.CSV
'''''''''''''''''''''''''''''''''''''''''''''
duplist = collections.OrderedDict(sorted(duplicates.items()))

cw = csv.writer(open('pa2/test1.csv','wb'))
cw.writerow(["AuthorId","DuplicateAuthorIds"])
num = 0
dup = 0
list1 = []
for (key, dups) in duplist.iteritems():
    for i in dups:
        if i not in list1:
            list1.append(i)
            dup+=1
    s = ""
    for i in list1:
        s = s + '"' + authorids.get(i) + '" ' 
    row = [key,' '.join(list1)]
    cw.writerow(row)
    num+=1
    list1 = []
print "Wrote", num, "entries into test1.csv"
print dup,"duplicates were found"

