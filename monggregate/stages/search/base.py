"""xxx"""

from datetime import datetime
from typing import Any, Callable, Literal
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self
    
from monggregate.base import pyd, BaseModel
from monggregate.stages.stage import Stage
from monggregate.search.collectors import Facet, Facets
from monggregate.search.operators import(
    Autocomplete,
    Compound,
    Equals,
    Exists,
    MoreLikeThis,
    Range,
    Regex,
    Text,
    Wildcard,
    AnyOperator
)
from monggregate.search.operators.compound import ClauseType
from monggregate.search.commons import FuzzyOptions

# Enums
# -----------------------------------------------------
OperatorLiteral = Literal[
    "autocomplete",
    "compound",
    "equals",
    "exists",
    "facet",
    "more_like_this",
    "range",
    "regex",
    "text",
    "wildcard"
]


class SearchConfig(BaseModel):
    """Internals"""

    index : str = "default"
    count : dict|None
    highlight : dict|None
    return_stored_source : bool = False
    score_details : bool  = False

    @property
    def statement():
        """Returns the statement of the stage"""

        raise NotImplementedError("statement method must be implemented in subclasses")

class SearchBase(Stage, SearchConfig):
    """xxxx"""

    collector : Facet|None
    operator : AnyOperator|None
    minimum_should_match : int = 0 # specific to Compound

    @pyd.root_validator(pre=True)
    @classmethod
    def init(cls, values:dict)->dict:
        """Initializes Search with Compound operator."""

        if "collector" not in values and "operator" not in values:
            minimum_should_match = values.get("minimum_should_match") or values.get("minimumShouldMatch")
            if minimum_should_match is None:
                minimum_should_match = 0
            values["operator"] = Compound(minimum_should_match=minimum_should_match)
        
        return values
    
    @pyd.validator("operator", pre=True, always=True)
    @classmethod
    def validate_operator(cls, value:dict, values:dict)->dict|None:
        """Ensures that either collector or operator is provided."""

        collector = values.get("collector")

        if collector is None and value is None:
            raise TypeError("Either collector or operator must be provided")
        elif collector and value:
            raise TypeError("Only one of collector or operator can be provided")
        
        return value
    
    @property
    def statement():
        """Returns the statement of the stage"""

        raise NotImplementedError("statement method must be implemented in subclasses")
    

     #---------------------------------------------------------
    # Constructors
    #---------------------------------------------------------
    @classmethod
    def from_operator(
        cls, 
        operator_name:OperatorLiteral,
        path:str|list[str]|None=None,
        query:str|list[str]|None=None,
        fuzzy:FuzzyOptions|None=None,
        score:dict|None=None,
        **kwargs:Any)->Self:
        """Instantiates a search stage from a search operator"""

        # FIXME : This could lead in duplicated arguments in kwargs <VM, 02/05/2023>
        kwargs.update(
            {
                "path":path,
                "query":query,
                "fuzzy":fuzzy,
                "score":score
            }
        )

        return cls.__get_constructors_map__(operator_name)(**kwargs)

    @classmethod
    def init_autocomplete(
        cls,
        query:str|list[str], 
        path:str, 
        token_order:str="any",
        fuzzy:FuzzyOptions|None=None,
        score:dict|None=None,
        **kwargs:Any)->Self:
        """
        Creates a search stage with an autocomplete operator
        
        Summary:
        -----------------------------
        This stage searches for a word or phrase that contains a sequence of characters from an incomplete input string.

        """

        base_params = SearchConfig(**kwargs).dict()
        cls.__reduce_kwargs(kwargs)

        autocomplete_statement = Autocomplete(
            query=query,
            path=path,
            token_order=token_order,
            fuzzy=fuzzy,
            score=score,
            **kwargs
        )

        return cls(**base_params, operator=autocomplete_statement)
    
    @classmethod
    def init_compound(
        cls,
        minimum_should_clause:int=1,
        *,
        must : list[AnyOperator]=[],
        must_not : list[AnyOperator]=[],
        should : list[AnyOperator]=[],
        filter : list[AnyOperator]=[],
        **kwargs:Any
        
    )->Self:

        base_params = SearchConfig(**kwargs).dict()
        cls.__reduce_kwargs(kwargs)

        compound_statement = Compound(
            must=must,
            must_not=must_not,
            should=should,
            filter=filter,
            minimum_should_clause=minimum_should_clause,
            **kwargs
        )

        return cls(**base_params, operator=compound_statement)

    @classmethod
    def init_equals(
        cls,
        path:str,
        value:str|int|float|bool|datetime,
        score:dict|None=None,
        **kwargs:Any
        )->Self:
        """
        Creates a search stage with an equals operator

        Summary:
        --------------------------------
        This checks whether a field matches a value you specify.
        You may want to use this for filtering purposes post textual search.
        That is you may want to use it in a compound query or as, the second stage of your search.
        
        """

        base_params = SearchConfig(**kwargs).dict()
        equals_statement = Equals(
            path=path,
            value=value,
            score=score
        )

        return cls(**base_params, operator=equals_statement)

    @classmethod
    def init_exists(cls, path:str, **kwargs:Any)->Self:
        """
        Creates a search stage with an exists operator

        Summary:
        --------------------------------
        This checks whether a field matches a value you specify.
        You may want to use this for filtering purposes post textual search.
        That is you may want to use it in a compound query or as, the second stage of your search.
        
        """

        base_params = SearchConfig(**kwargs).dict()
        exists_statement = Exists(path=path)

        return cls(**base_params, operator=exists_statement)
    
    @classmethod
    def init_facet(cls, **kwargs:Any)->Self:
        """
        Creates a search stage with a facet operator

        Summary:
        --------------------------------

        """
        
        base_params = SearchConfig(**kwargs).dict()
        cls.__reduce_kwargs(kwargs)
        
        operator = kwargs.pop("operator", None)
        facet_ = Facet(operator=operator, **kwargs)

        return cls(**base_params, collector=facet_)
    
    @classmethod
    def init_more_like_this(cls, like:dict|list[dict], **kwargs:Any)->Self:
        """
        Creates a search stage  with a more_like_this operator

        Summary:
        --------------------------------
        The moreLikeThis operator returns documents similar to input documents. 
        The moreLikeThis operator allows you to build features for your applications 
        that display similar or alternative results based on one or more given documents.

        """
        
        base_params = SearchConfig(**kwargs).dict()
        more_like_this_stasement = MoreLikeThis(like=like)

        return cls(**base_params, operator=more_like_this_stasement)

    @classmethod
    def init_range(
        cls,
        path:str|list[str],
        gt:int|float|datetime|None=None,
        lt:int|float|datetime|None=None,
        gte:int|float|datetime|None=None,
        lte:int|float|datetime|None=None,
        score:dict|None=None,
        **kwargs:Any
    )->Self:
        """
        Creates a search stage with a range operator

        Summary:
        --------------------------------
        This checks whether a field value falls into a specific range
        You may want to use this for filtering purposes post textual search.
        That is you may want to use it in a compound query or as, the second stage of your search.
        
        
        """

        base_params = SearchConfig(**kwargs).dict()
        range_statement = Range(
            path=path,
            gt=gt,
            gte=gte,
            lt=lt,
            lte=lte,
            score=score
        )

        return cls(**base_params, operator=range_statement)

    @classmethod
    def init_regex(
        cls,
        query:str|list[str],
        path:str|list[str],
        allow_analyzed_field:bool=False,
        score:dict|None=None,
        **kwargs:Any
    )->Self:
        """
        Creates a search stage with a regex operator.

        Summary:
        ----------------------------
        regex interprets the query field as a regular expression. regex is a term-level operator, meaning that the query field isn't analyzed (read processed).
        
        """

        base_params = SearchConfig(**kwargs).dict()
        regex_statement = Regex(
            query=query,
            path=path,
            allow_analyzed_field=allow_analyzed_field,
            score=score
        )

        return cls(**base_params, operator=regex_statement)

    @classmethod
    def init_text(
        cls,
        query:str|list[str],
        path:str|list[str],
        fuzzy:FuzzyOptions|None=None,
        score:dict|None=None,
        synonyms:str|None=None,
        **kwargs:Any
    )->Self:
        """
        Creates a search stage with a text opertor

        Summary:
        ---------------------------------
        The text operator performs a full-text search using the analyzer that you specify in the index configuration. 
        If you omit an analyzer, the text operator uses the default standard analyzer.
        
        """

        base_params = SearchConfig(**kwargs).dict()
        cls.__reduce_kwargs(kwargs)

        text_statement = Text(
            query=query,
            path=path,
            score=score,
            fuzzy=fuzzy,
            synonyms=synonyms
        )

        return cls(**base_params, operator=text_statement)

    @classmethod
    def init_wildcard(
        cls,
        query:str|list[str],
        path:str|list[str],
        allow_analyzed_field:bool=False,
        score:dict|None=None,
        **kwargs:Any
    )->Self:
        """
        Creates a search stage with a wildcard opertor

        Summary:
        ---------------------------------
        The wildcard operator enables queries which use special characters in the search string that can match any character.
        
        """

        base_params = SearchConfig(**kwargs).dict()
        cls.__reduce_kwargs(kwargs)
        
        wilcard_statement = Wildcard(
            query=query,
            path=path,
            allow_analyzed_field=allow_analyzed_field,
            score=score
        )

        return cls(**base_params, operator=wilcard_statement)
    
    #-----------------------------------------
    # Compound Search Pipelinenized functions
    #-----------------------------------------
    def autocomplete(
            self, 
            type:ClauseType, 
            *,
            query:str|list[str], 
            path:str,
            token_order:str="any",
            fuzzy:FuzzyOptions|None=None,
            score:dict|None=None
            )->Self:
        """xxx"""

        if isinstance(self.operator, Compound):
            self.operator.autocomplete(
                type=type,
                query=query,
                path=path,
                token_order=token_order,
                fuzzy=fuzzy,
                score=score
            )
        else:
            raise TypeError(f"Cannot call autocomplete on {self.operator}")
        
        return self
    
    def equals(self, type:ClauseType, path:str, value:str|int|float|bool|datetime, score:dict|None=None)->Self:
        """xxx"""

        if isinstance(self.operator, Compound):
            self.operator.equals(
                type=type,
                path=path,
                value=value,
                score=score
            )
        else:
            raise TypeError(f"Cannot call equals on {self.operator}")
        
        return self
    
    def exists(self, type:ClauseType, path:str)->Self:
        """xxx"""

        if isinstance(self.operator, Compound):
            self.operator.exists(
                type=type,
                path=path
            )
        else:
            raise TypeError(f"Cannot call exists on {self.operator}")
        
        return self
    
    def range(
            self,
            type:ClauseType,
            *,
            path:str|list[str],
            gt:int|float|datetime|None=None,
            lt:int|float|datetime|None=None,
            gte:int|float|datetime|None=None,
            lte:int|float|datetime|None=None,
            score:dict|None=None
        )->Self:
        """xxx"""

        if isinstance(self.operator, Compound):
            self.operator.range(
                type=type,
                path=path,
                gt=gt,
                lt=lt,
                gte=gte,
                lte=lte,
                score=score
            )
        else:
            raise TypeError(f"Cannot call range on {self.operator}")
        
        return self
    
    def regex(
            self,
            type:ClauseType,
            *,
            query:str|list[str],
            path:str|list[str],
            allow_analyzed_field:bool=False,
            score:dict|None=None
        )->Self:
        """xxx"""

        if isinstance(self.operator, Compound):
            self.operator.regex(
                type=type,
                query=query,
                path=path,
                allow_analyzed_field=allow_analyzed_field,
                score=score
            )
        else:
            raise TypeError(f"Cannot call regex on {self.operator}")
        
        return self
    
    def text(
            self,
            type:ClauseType,
            *,
            query:str|list[str],
            path:str|list[str],
            fuzzy:FuzzyOptions|None=None,
            score:dict|None=None,
            synonyms:str|None=None
        )->Self:
        """xxx"""

        if isinstance(self.operator, Compound):
            self.operator.text(
                type=type,
                query=query,
                path=path,
                fuzzy=fuzzy,
                score=score,
                synonyms=synonyms
            )
        else:
            raise TypeError(f"Cannot call text on {self.operator}")
        
        return self
    
    def wildcard(
            self,
            type:ClauseType,
            *,
            query:str|list[str],
            path:str|list[str],
            allow_analyzed_field:bool=False,
            score:dict|None=None
        )->Self:
        """xxx"""

        if isinstance(self.operator, Compound):
            self.operator.wildcard(
                type=type,
                query=query,
                path=path,
                allow_analyzed_field=allow_analyzed_field,
                score=score
            )
        else:
            raise TypeError(f"Cannot call wildcard on {self.operator}")
        
        return self

    #-----------------------------------------
    # Nested Compound Search
    #-----------------------------------------
    def compound(self,
                 type:ClauseType,
                 must:list[AnyOperator]=[],
                 must_not:list[AnyOperator]=[],
                 should:list[AnyOperator]=[],
                 filter:list[AnyOperator]=[],
                 minimum_should_match:int=0,
                )->Compound:
        """xxx"""

        if isinstance(self.operator, Compound):
            _coumpound = self.operator.compound(
                type=type,
                must=must,
                must_not=must_not,
                should=should,
                filter=filter,
                minimum_should_match=minimum_should_match
            )
        else:
            raise TypeError(f"Cannot call compound on {self.operator}")
        
        return _coumpound

    #-----------------------------------------
    # Utility functions
    #-----------------------------------------
    @classmethod
    def __get_constructors_map__(cls, operator_name:str)->Callable:
        """Returns appropriate constructor from operator name"""

        _constructors_map = {
            "autocomplete":cls.init_autocomplete,
            "compound":cls.init_compound,
            "equals":cls.init_equals,
            "exists":cls.init_exists,
            "facet":cls.init_facet,
            "more_like_this":cls.init_more_like_this,
            "range":cls.init_range,
            "regex":cls.init_regex,
            "text":cls.init_text,
            "wildcard":cls.init_wildcard
        }

        return _constructors_map[operator_name]
    
    
    @classmethod
    def __reduce_kwargs(cls, kwargs:dict)->None:
        """
        Parses kwargs arguments to avoid passing arguments twice
        
        In particular removes SearchBase arguments from kwargs:
            - index, 
            - count, 
            - highlight, 
            - return_stored_source, 
            - score_details
        
        """

        kwargs.pop("index", None)
        kwargs.pop("count", None)
        kwargs.pop("highlight", None)
        kwargs.pop("return_stored_source", None)
        kwargs.pop("score_details", None)