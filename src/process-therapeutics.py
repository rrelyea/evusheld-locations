from fileinput import filename
import json
from io import StringIO
import os
import sys
from os.path import exists
import requests
from urllib.parse import urlparse
import csv

def get5digitZip(rawZip):
  if len(rawZip) == 3:
    return '00' + rawZip
  elif len(rawZip) == 4:
    return '0' + rawZip 
  elif len(rawZip) == 5:
    return rawZip 
  elif len(rawZip) > 5:
    return rawZip[0:5]
    
def updateZipCodeFilesForDrug( drugs ):
  localBasePath = "../../"

  with open(localBasePath + "data/therapeutics-last-processed.txt", "r") as lastProcessed_file:
    lastProcessedDate = lastProcessed_file.readline()
    print("last processed: " + lastProcessedDate)

  newLastProcessedDate = None
  with open(localBasePath + "data/therapeutics-archive.json", "r") as read_file:
      publishings = json.load(read_file)
      urls = []

      for publishing in publishings:
        updateDate = publishing["update_date"]
        if updateDate > lastProcessedDate:
          urls.append(publishing["archive_link"]["url"])
          newLastProcessedDate = updateDate

  # download all new files
  for url in sorted(urls):
    filename = os.path.basename(urlparse(url).path)
    targetPath = localBasePath + 'data/therapeutics/'
    while not os.path.exists(targetPath):
      os.mkdir(targetPath)
    mabsFile = localBasePath + 'data/therapeutics/' + filename
    if not exists(mabsFile):
      print("downloading " + url)
      r = requests.get(url, allow_redirects=True)
      therapeuticsFile = open(mabsFile, 'wb')
      therapeuticsFile.write(r.content)
      therapeuticsFile.close()

  for drug in drugs:
      targetPath = localBasePath + 'data/dose-details/' + drug.lower() + '/'
      while not os.path.exists(targetPath):
        os.mkdir(targetPath)

  # calculate all zip codes, by looking at latest data file
  url = sorted(urls)[len(urls) - 1]
  filename = os.path.basename(urlparse(url).path)
  targetPath = localBasePath + 'data/therapeutics/'
  while not os.path.exists(targetPath):
    os.mkdir(targetPath)
  mabsFile = localBasePath + 'data/therapeutics/' + filename
  therapeuticsFile = open(mabsFile, 'r', encoding='utf8')
  zipSet = set()
  reader = csv.reader(therapeuticsFile)
  for columns in reader:
    zip = get5digitZip(columns[6])
    if zip != "00Zip" and (columns[8] in drugs) and zip[0] == '0':
      zipSet.add(zip)
  therapeuticsFile.close()

  print('zip codes for ' + mabsFile + ':' + str(len(zipSet)))

  for zipCode in sorted(zipSet):
    print(zipCode, end=', ', flush=True)
    zipFile = [None] * len(drugs)
    filename = os.path.basename(urlparse(url).path)
    therapeuticsFile = localBasePath + 'data/therapeutics/'+filename
    timeStamp = filename.replace('rxn6-qnx8_','').replace('.csv','')
    with open(therapeuticsFile, 'r', encoding='utf8') as data:
      reader = csv.reader(data)
      for columns in reader:
        zip = get5digitZip(columns[6])
        provider = columns[0]
        if "," in provider:
          provider = '"' + provider + '"'
        if zip == zipCode and columns[8] in drugs:
          index = drugs.index(columns[8])
          if zipFile[index] == None:
            zipFile[index] = open(localBasePath + 'data/dose-details/' + columns[8].lower() + '/' + str(zipCode)+'.csv', "a",encoding='utf8')
          f = zipFile[index]
          f.write(timeStamp + ',' + zip + ',' + provider)
          for i in range(9, 14):
            if i < len(columns):
              f.write(',' + columns[i])
            else:
              f.write(',')
          f.write('\n')
  return newLastProcessedDate

lastProcessedDate = updateZipCodeFilesForDrug(['Evusheld','Paxlovid','Sotrovimab', 'Bebtelovimab'])
with open("../../data/therapeutics-last-processed.txt", "w") as lastProcessed_file:
  lastProcessed_file.write(lastProcessedDate)

