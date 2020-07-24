
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Set the necessary product code
# Import arcpy module
# by Eniko Kelly; October 2019


import arcpy
import arcpy.management
import os
import pandas as pd

#Settlement model with Validation Index for Mozambique and South Sudan
#The input data files are the settlement polygons and settlement points derived from the ecopia building footprints,
# and point feature classes with toponyms from all possible data sources.
#The model will search for settlement points obtained from different sources that are close to the ecopia settlements
# (within 500m from city boundaries), and will join the settlement names to the ecopia city centroids.
# The ecopia settlement model is now updated with the settlement names.
# The place names from each data source are joined in dedicated fields that are labeled with the data source name.
#Each ecopia settlement point will get an index "1" for each associated data source that was previously joined.
# The last column of the settlement point file represents the sum of these indexes,
# and it shows how many data sources have one or more settlement points geographically associated with that specific location.
#Validation of the settlement points can be prioritized based on the sum of indexes.
#Distant features are saved separately for further validation.


#find for each feature in the settlement data files the nearest ecopia settlement point.
# Local variables: features from which distance will be calculated

#DEFINE INPUTS
hdx_locations = r'\\dataserver1\bmgfgrid\analysis\MOZ\School_Data\hdx_location.shp'
NGA = r'\\dataserver1\BMGFGRID\analysis\MOZ\School_Data\NGA_PopulatedPlaces.shp'
NA = r'\\dataserver1\BMGFGRID\analysis\MOZ\School_Data\NA_locality.shp'


#feature to which distance will be calculated
MOZ_bldgs_Aggregate_shp = r'\\dataserver1\BMGFGRID\analysis\MOZ\School_Data\MOZ_bldgs_Aggregate.shp'
#feature to which the results will be joined
MOZ_settl_centroids = r'\\dataserver1\BMGFGRID\analysis\MOZ\School_Data\MOZ_settl_centroids.shp'

#DEFINE OUTPUTS
# settlement points with near distances
hdx_locality_near = r'\\dataserver1\BMGFGRID\analysis\MOZ\School_Data\hdx_locality_near.shp'
hdx_locality_dist = r'\\dataserver1\BMGFGRID\analysis\MOZ\School_Data\hdx_locality_dist.shp'
NGA_locality_near = r'\\dataserver1\BMGFGRID\analysis\MOZ\School_Data\NGA_locality_near.shp'
NGA_locality_dist = r'\\dataserver1\BMGFGRID\analysis\MOZ\School_Data\NGA_locality_dist.shp'
NA_locality_near = r'\\dataserver1\BMGFGRID\analysis\MOZ\School_Data\NA_locality_near.shp'
NA_locality_dist = r'\\dataserver1\BMGFGRID\analysis\MOZ\School_Data\NA_locality_dist.shp'

#execute near analysis:
for inFeature in [hdx_locations, NGA, NA]:
    arcpy.Near_analysis(inFeature, MOZ_bldgs_Aggregate_shp, "", "NO_LOCATION", "NO_ANGLE", "PLANAR")


#DEFINE THE NEW COLUMNS THAT WILL BE LABELED WITH THE DATA SOURCE NAME AND IMPORT THE SETTLEMENT NAMES
#NOTE: The ranking mus tbe the same in both lists!!! If the sequence is not respected, the column labels will be assigned incorrectly.
settl_locations = [hdx_locations, NGA, NA]
ColNames = ["Sett_Name", "FULL_NAM_2", "FULL_NAM_2"]  #column that contains the settlement names of data source1, source2, source3.
NewCol = ["hdx_settl", "NGA_settl", "NA_settl"]                #new column of settlement names from data source1, source2, source3.

#attach the new columns
for inFeature, cnames in zip(settl_locations, NewCol):
    arcpy.AddField_management(inFeature, cnames, "TEXT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

#import the settlement names to the new columns
for inFeature, cnames, colnames in zip(settl_locations, NewCol, ColNames):
    cursor = arcpy.UpdateCursor(inFeature)
    for row in cursor:
        row.setValue(cnames, row.getValue(colnames))
        cursor.updateRow(row)

#SELECT FEATURES COLSE TO THE BOUNDARIES OF THE ECOPIA CITY MODEL
settl_locations = [hdx_locations, NGA]
nearSettl = [hdx_locality_near, NGA_locality_near]   #I worked without NA settlements that have projection problems
#select and save features
for inFeature, nearFeature in zip(settl_locations, nearSettl):
    arcpy.Select_analysis(inFeature, nearFeature, "\"NEAR_DIST\" <=0.0044")  #select settlements not more than 500m away

#SELECT DISTANT FEATURES
distSettl = [hdx_locality_dist, NGA_locality_dist]
for inFeature, distFeature in zip(settl_locations, distSettl):
    arcpy.Select_analysis(inFeature, distFeature, "\"NEAR_DIST\" >0.0044")   ##select settlements more than 500m away

# BUILD GROUP OF THE SETTLEMENTS THAT ARE CLOSE TO THE CITY MODEL BASED ON THE FEATURE IDs
# Process: Table To Excel is the first step
#inputs:
settl_locations = [hdx_locations, NGA]
NewCol = ["hdx_settl", "NGA_settl"]
# DEFINE OUTPUTS:
hdx_near_excel = r'\\dataserver1\BMGFGRID\analysis\MOZ\School_Data\hdx_near_excel.xls'
nga_near_excel = r'\\dataserver1\BMGFGRID\analysis\MOZ\School_Data\nga_near_excel.xls'
near_excel = [hdx_near_excel, nga_near_excel]
#process
for inFeature, exfile in zip(nearSettl, near_excel):
    arcpy.TableToExcel_conversion(inFeature, exfile)

#DEFINE OUTPUTS OF THE GROUPED DATA
hdx_near_settl_csv = r'\\dataserver1\BMGFGRID\analysis\MOZ\School_Data\hdx_near_settl.csv'
nga_near_settl_csv = r'\\dataserver1\BMGFGRID\analysis\MOZ\School_Data\nga_near_settl.csv'
all_near = [hdx_near_settl_csv, nga_near_settl_csv]

#group values on settlement polygon IDs (NEAR_FID):
for exfile, col, nearcsv in zip(near_excel, NewCol, all_near):
    df = pd.read_excel(exfile, sheet_name='Sheet1', encoding="ISO-8859-1")
    df=df.groupby('NEAR_FID')[col].unique().reset_index()
    df.to_csv(nearcsv, encoding="ISO-8859-1")


# Process: Add Join
arcpy.MakeFeatureLayer_management(MOZ_settl_centroids, "tempLayer")

#DEFINE OUTPUT FEATURE CLASS (FINAL RESULT).
MOZ_settl_joined = r'\\dataserver1\BMGFGRID\analysis\MOZ\School_Data\MOZ_settl_join.shp'

for nearcsv in all_near:
    arcpy.AddJoin_management("tempLayer", "ORIG_FID", nearcsv, "NEAR_FID", "KEEP_ALL")
arcpy.CopyFeatures_management("tempLayer", MOZ_settl_joined)

#attach new columns
fc = MOZ_settl_joined

#attach the new columns and calculate how many settlement points from different sources fall close to the settlement model.
fieldname = ["hdx_near_2", "nga_near_2"]
settl_index = ["hdx_indx", "nga_indx"]

for ix in settl_index:
    arcpy.AddField_management(fc, ix, "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

for fname, ix in zip(fieldname, settl_index):
    with arcpy.da.UpdateCursor(fc,[fname, ix])as cursor:
        for row in cursor:
            if row[0]> ' ':
                row[1] = 1
            else:
                row[1] = 0
            cursor.updateRow(row)


arcpy.AddField_management(fc, "counts", "LONG", "5", "", "", "", "NULLABLE", "NON_REQUIRED", "")
field1 = "hdx_indx"
field2 = "nga_indx"
field3 = "counts"

cursor = arcpy.UpdateCursor(fc)
for row in cursor:
    row.setValue(field3, row.getValue(field1) + row.getValue(field2))
    cursor.updateRow(row)





