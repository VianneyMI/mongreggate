"""
Module definining an interface to MongoDB `$bucketAuto` stage operation in aggregation pipeline.
"""

from typing import Any
from monggregate.base import pyd
from monggregate.stages.stage import Stage
from monggregate.fields import FieldName
from monggregate.operators.accumulators.accumulator import AccumulatorExpression
from monggregate.utils import StrEnum, validate_field_path


class GranularityEnum(StrEnum):
    """Supported values of granularity are"""

    R5 = "R5"
    R10 = "R10"
    R20 = "R20"
    R40 = "R40"
    R80 = "R80"
    _1_2_5 = "1-2-5"
    E6 = "E6"
    E12 = "E12"
    E24 = "E24"
    E48 = "E48"
    E96 = "E96"
    E192 = "E192"
    POWERSOF2 = "POWERSOF2"


class BucketAuto(Stage):
    """
    Abstraction of MongoDB `$bucketAuto` stage that aggregates documents into buckets automatically computed to satisfy the number of buckets desired
    and provided as an input.

    Parameters
    ----------
    by : str|list[str]|set[str]
        An expression to group documents. To specify a field path prefix 
        the field name with a dollar sign $ and enclose it in quotes.
    buckets : int
        Number of buckets desired.
    output : dict
        A document that specifieds the fields to include in the oupput 
        documents in addition to the `_id`field. To specify the field to 
        include, you must use accumulator expressions.

        The defaut count field is not included in the output document when output is specified.
        Explicitly specify the count expression as part of the output document to include it:
            
            >>> {
                <outputfield1>: { <accumulator>: <expression1> },
                ...
                count: { $sum: 1 }
                }

                
    granularity : str | None
        A string that specifies the preferred number series to use to ensure that the calculated
        boundary edges end on preferred round numbers of their powers of 10.

        Available only if all groupBy values are numeric and none of them are NaN.
        [wikipedia](https://en.wikipedia.org/wiki/Preferred_number)

        
    Online MongoDB documentation
    ----------------------------
    Categorizes incoming documents into a specific number of groups, called buckets, based on a specified expression.
    Bucket boundaries are automatically determined in an attempt to evenly distribute the documents into the specified number of buckets.
    Each bucket is represented as a document in the output. The document for each bucket contains:
        
    - An `_id` object that specifies the bounds of the bucket.

        - The `_id`.min field specifies the inclusive lower bound for the bucket.
        - The `_id`.max field specifies the upper bound for the bucket. This bound is exclusive for all buckets except the final bucket in the series, where it is inclusive.
    - A count field that contains the number of documents in the bucket. The count field is included by default when the output document is not specified.
        
    The `$bucketAuto` stage has the following form:

        >>> {
            `$bucketAuto`: {
                groupBy: <expression>,
                buckets: <number>,
                output: {
                    <output1>: { <$accumulator expression> },
                    ...
                    }
                granularity: <string>
                }
            }

    
    [Source](https://www.mongodb.com/docs/manual/reference/operator/aggregation/bucketAuto/)
    """

    # Attributes
    # ----------------------------------------------------------------------------
    by : Any = pyd.Field(...,alias="group_by") # probably should restrict type to field_paths an operator expressions
    buckets : int = pyd.Field(..., gt=0)
    output : dict[FieldName, AccumulatorExpression] | None = None# Accumulator Expressions #TODO : Define type and use it here
    granularity : GranularityEnum | None = None


    # Validators
    # ----------------------------------------------------------------------------
    _validate_by = pyd.validator("by", pre=True, always=True, allow_reuse=True)(validate_field_path) # re-used pyd.validators

    # Output
    #-----------------------------------------------------------------------------
    @property
    def statement(self) -> dict:

      # NOTE : maybe it would be better to use _to_unique_list here
      # or to further validate by.
      return   self.resolve({
            "$bucketAuto" : {
                "groupBy" : self.by,
                "buckets" : self.buckets,
                "output" : self.output,
                "granularity" : self.granularity.value if self.granularity else None
            }
        })