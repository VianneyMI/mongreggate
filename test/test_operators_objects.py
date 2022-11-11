"""Module gathering the tests of the objects operators"""

# pylint: disable=import-error
import pytest
from monggregate.operators.objects import(
    MergeObjects, merge_objects,
    ObjectToArray, object_to_array
)

@pytest.mark.operator
@pytest.mark.unit
@pytest.mark.functional
class TestObjectsOperators:
    """This class only aims at reusing the markers"""

    def test_merge_objects(self)->None:
        """Testes the $mergeObjects operator"""

        merge_objects_op = MergeObjects(
            expression = "$quantity"
        )

        # Unit test
        # --------------
        assert merge_objects_op

        # Functinal test
        # ---------------
        assert merge_objects_op.statement == merge_objects("$quantity") == {
            "$mergeObjects" : "$quantity"
        }

    def test_object_to_array(self)->None:
        """Testes the $mergeObjects operator"""

        object_to_array_op = ObjectToArray(
            expression = "$dimensions"
        )

        # Unit test
        # --------------
        assert object_to_array_op

        # Functinal test
        # ---------------
        assert object_to_array_op.statement == object_to_array("$dimensions") == {
            "$objectToArray" : "$dimensions"
        }