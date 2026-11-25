# Lab 3: API data page
# TODO: Rename this file to fit your page. Keep the number at the front, since it sets the
#       page's order in the sidebar (for example, 2_Pokedex.py).
#
# This page shows data from your API, processed with your own Python code. No AI on this page.
# It should have:
#   - at least 2 meaningful user inputs (for example st.selectbox, st.text_input, st.slider)
#   - at least 2 dynamic visuals that change based on the user's input: charts, displays of
#     images, or other visualizations (see the example website for examples!)

import requests
import streamlit as st
import pandas as pd
import plotly.express as px


baseUrl = "https://api.fda.gov/drug/shortages.json"

def drugsData():
  drugsList = []
  skip = 0
  drugCount = 1000
  while drugCount == 1000:
    endpoint = baseUrl + "?limit=1000&skip=" + str(skip)
    response = requests.get(endpoint)
    data = response.json()
    drugs = data["results"]
    for drug in drugs:
      drugsList.append(drug)
    drugCount = len(drugs)
    skip += 1000 
  return drugsList

def filteredDrugData(medications):
  filteredDrugs = []
  for med in medications:
    year = None
    if "initial_posting_date" in med:
      date = med["initial_posting_date"]
    else:
      date = ""
    if date != "":
      parts = date.split("/")
      if len(parts) == 3:
        if parts[2].isdigit():
          year = int(parts[2])
    if "generic_name" in med:
      genericName = med["generic_name"]
    else:
      genericName = "Unknown"
    if "status" in med:
      status = med["status"]
    else:
      status = "Unknown"
    if "shortage_reason" in med:
      reason = med["shortage_reason"]
    else:
      reason = "Unknown"
    if "openfda" in med:
      openfda = med["openfda"]
      if "brand_name" in openfda:
        brandNames = openfda["brand_name"]
      else:
        brandNames = []
    else:
      brandNames = []
    filteredDrug = {"generic_name": genericName, "brand_names": brandNames, "year": year, "status": status, "reason": reason}
    filteredDrugs.append(filteredDrug)
  return filteredDrugs


def filterByMed(medications, name):
    drugMatches = []
    genericMatches = []
    name = name.strip().lower()
    for med in medications:
        genericName = med["generic_name"].strip().lower()
        if name == genericName:
            if genericName not in genericMatches:
                genericMatches.append(genericName)
        for brand in med["brand_names"]:
            if name == brand.strip().lower():
                if genericName not in genericMatches and genericName != "unknown" and genericName:
                    genericMatches.append(genericName)
    for med in medications:
        genericName = med["generic_name"].strip().lower()
        if genericName in genericMatches:
            drugMatches.append(med)
        else:
            for brand in med["brand_names"]:
                if name == brand.strip().lower():
                    drugMatches.append(med)
                    break
    return drugMatches

def filterByYear(medications, start, end):
  drugMatches = []
  for med in medications:
    year = med["year"]
    try:
      if start <= year and year <= end:
        drugMatches.append(med)
    except:
        year = None
  return drugMatches

def barChartValues(medications):
    yearDict = {}
    for med in medications:
        year = med["year"]
        if year not in yearDict:
            yearDict[year] = 1
        else:
            yearDict[year] += 1
    sortedYearDict = sorted(yearDict)
    sortedCountDict = {}
    for year in sortedYearDict:
        sortedCountDict[year] = yearDict[year]
    numYears = len(sortedCountDict)
    return (sortedCountDict, numYears)

    
def countForFeatures(medications, feature):
    countDict = {}
    for med in medications:
        val = med[feature]
        if val not in countDict:
            countDict[val] = 1
        else:
            countDict[val] += 1
    return countDict

def getMedNames(medications):
    medNames = []
    for med in medications:
        genericName = med["generic_name"]
        if genericName.lower() not in medNames and genericName.lower() != "unknown":
            medNames.append(genericName.lower())
        for brand in med["brand_names"]:
            if brand.lower() not in medNames and brand:
                medNames.append(brand.lower())
    medNames.sort()
    return medNames
                         

def getRange(medications):
    yearsList = []
    for med in medications:
        year = med["year"]
        if year != None:
            yearsList.append(year)
    if yearsList:
        yearsList.sort()
        startYear = yearsList[0]
        endYear = yearsList[-1]
        return (startYear, endYear)
    else:
        return (None, None)
          

def getStatus(medications):
    statusDict = countForFeatures(medications, "status")
    if not statusDict:
        return "No Data Available"
    else:
        if "Current" in statusDict:
            return "Current ⚠️"
        if len(statusDict) == 1:
            if "Resolved" in statusDict:
                return "Resolved 🎉"
            if "Discontinued" in statusDict:
                return "Discontinued ⏸️"
    return "Unclear"

def getShortageReasonings(medications):
    reasonDict = countForFeatures(medications, "reason")
    reasonsList = []
    countsList = []
    for (reason,count) in reasonDict.items():
        reasonsList.append(reason)
        countsList.append(count)
    return (reasonsList, countsList)
    
    
def setUp():
    st.set_page_config(page_title="DrugDex", layout="wide")
    st.header("Drug Deficiency Discoverer 🔎", divider="gray", text_alignment="center")
    st.write("*Discover FDA reported drug shortages by medication and initial posting year. Explore shortage statuses and reported reasonings!*")
    st.divider()
    
def displaySections(totalReports, numYears, status):
    col1, col2, col3 = st.columns(3, gap="large")
    col1.metric("Total Reports", totalReports)
    col2.metric("Number of Years with Reports", numYears)
    col3.metric("FDA Reported Shortage Status", status)
    

def barChart(yearCounts, startYear, endYear):
    
    yearsList = []
    countsList = []
    for year in range(startYear, endYear+1):
        yearsList.append(year)
        if year in yearCounts:
            countsList.append(yearCounts[year])
        else:
            countsList.append(0)
    df = pd.DataFrame({"Year": yearsList, "Reports": countsList})
    st.write("**Drug Shortage Listings by Year**")
    st.bar_chart(
        df,
        x="Year",
        y="Reports",
        color="#90B4C1"
    )

def pieChart(medications):
    (reasonsList, countsList) = getShortageReasonings(medications)
    pieChart = px.pie(
        names=reasonsList,
        values=countsList,
        title="Top Reported Reasons for Drug Shortage",
        color_discrete_sequence=["#8DA9C4", "#B5C7D9", "#7889AD", "#A9A1C7", "#C6D8D9"]
    )
    st.plotly_chart(pieChart, width="stretch")


# calling functions
setUp()
try:
    ogData = drugsData()
    medications = filteredDrugData(ogData)
    medNames = getMedNames(medications)
    initialYear, lastYear = getRange(medications)
except:
    st.error("Unable to retrieve or process FDA medication data.")
    st.write(str(error))
    st.stop()

# handling missing data
if not medNames:
    st.warning("No data about this medication available")
    st.stop()
if initialYear == None or lastYear == None:
    st.warning("No posting years were found")
    st.stop()

# inputs
selectedMed = st.selectbox(
    "Select a medication:",
    medNames
)
if initialYear == lastYear:
    startYear = initialYear
    endYear = lastYear
    st.write("Valid Initial Posting Year:", initialYear)
else:
    startYear, endYear = st.slider(
        "Select a year range:",
        min_value=initialYear,
        max_value=lastYear,
        value=(initialYear, lastYear),
        step=1
    )

# filtering data
medMatches = filterByMed(medications, selectedMed)
filteredMatches = filterByYear(medMatches, startYear, endYear)

# metrics
totalReports = len(filteredMatches)
yearCounts, numYears = barChartValues(filteredMatches)
shortageStatus = getStatus(medMatches)
displaySections(totalReports, numYears, shortageStatus)
st.write("NOTE: Shortage status is based on all listings for the selected medication, disregarding selected year range.")
st.divider()

# visuals
if not filteredMatches:
    st.info("No shortage listings were found for this medication within the selected year range.")
else:
    barCol, pieCol = st.columns(2, gap="large")
    with barCol:
        barChart(yearCounts, startYear, endYear)
    with pieCol:
        pieChart(filteredMatches)

# disclaimer
st.divider()
st.caption("**Data Source**: U.S. Food and Drug Administration (openFDA Drug Shortages API).")
st.caption("**Disclaimer**: All reports are grouped by initial posting year. Listing numbers do not account for the severity of each drug shortage on different demographics or regions.")







        
  
  

  
    
      
  

  
