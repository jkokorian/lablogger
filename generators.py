from math import ceil,log
import operator
from numpy import cumsum

def generateIncrementalCombinations(*sequences):
    totallength = reduce(operator.mul, [len(s) for s in sequences])
    cumlengths = [1]+list(cumsum([len(s) for s in sequences]))
    arrays = []

    for iSequence,s in enumerate(sequences):
        a = [s[(i//(cumlengths[iSequence]))%len(s)] for i in range(totallength)]
        arrays.append(a)

    return ["".join([str(a[i]) for a in arrays]) for i in range(totallength)]   

def generateAlphabeticalNames(amount,base = 26):
    numerals = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    size = int(ceil(log(amount)/log(base)))

    return ["".join(reversed([numerals[(i//(base**iPos))%base] for iPos in range(size)])) for i in range(amount)]
                
        
    
def generateNumericalNames(amount):
    return [str(i+1) for i in range(0,amount)]
   
   
def generateAlphaNumericalNames(amount):
    numerals0=range(10)
    numerals1="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return [numerals1[i//10]+str(numerals0[i%10]) for i in range(260)]
    
    
def getAppropriateGenerator(amount):
    if (amount <= 26):
        return generateAlphabeticalNames()
    if (amount<200):
        return generateNumericalNames(amount)
    elif (amount>=200 and amount <= 260):
        return generateAlphaNumericalNames(amount)
    else:
        return generateAlphabeticalNames(amount)


    
def parseGeneratorExpression(expression):
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    start, end = expression.split("..")
    
    if start.upper() in alphabet and end.upper() in alphabet:
        minRange = alphabet.find(start.upper())
        maxRange = alphabet.find(end.upper())+1
        if start.islower():
            return list(alphabet[minRange:maxRange].lower())
        else:
            return list(alphabet[minRange:maxRange]) 
    else:
        minRange = int(start)
        maxRange = int(end)+1
        return range(minRange,maxRange)