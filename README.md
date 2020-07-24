# settlExt_validation
Search for settlement points obtained from different sources that are close to the extent polygons that will be validated



The input data files are the settlement polygons and settlement points derived from the ecopia building footprints,
and point feature classes with toponyms from all possible data sources.

The model will search for settlement points obtained from different sources that are close to the ecopia settlements
(within 500m from city boundaries), and will join the settlement names to the ecopia city centroids.

The ecopia settlement model is now updated with the settlement names.
The place names from each data source are joined in dedicated fields that are labeled with the data source name.

Each ecopia settlement point will get an index "1" for each associated data source that was previously joined.

The last column of the settlement point file represents the sum of these indexes,
and it shows how many data sources have one or more settlement points associated with that specific location.

Validation of the settlement points can be prioritized based on the sum of indexes.

Distant features are saved separately for further validation.
