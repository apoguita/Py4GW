import Py4GW

from .Item import Bag, Item
import PyInventory 

class ItemArray:
    @staticmethod
    def CreateBagList(*bag_ids):
        """
        Given a variable number of integer bag IDs, convert them to Bag enums.
    
        :param bag_ids: A variable number of integers representing bag IDs. e.g. (1, 2, 3, 4, 7, 10)
        :return: A list of Bag enum members.
        """
        bags_to_check = []
    
        for bag_id in bag_ids:
            try:
                # Convert the integer to Bag enum and add to the list
                bags_to_check.append(Bag(bag_id))
            except ValueError:
                Py4GW.Console.Log("CreateBagList",f"Invalid bag ID: {bag_id}", Py4GW.Console.MessageType.Error)

        return bags_to_check

    @staticmethod
    def GetItemArray(bags_to_check):
        """
        Given a list of Bag enum members, retrieve the item IDs across all those bags.
    
        :param bags_to_check: A list of Bag enum members (output from CreateBagList).
        :return: A consolidated list of item IDs across the specified bags.
        """
        all_item_ids = []  # To store item IDs from all bags
    
        for bag_enum in bags_to_check:
            try:
                # Create a Bag instance
                
                bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
            
                # Get all items in the bag
                items_in_bag = bag_instance.GetItems()
            
                # Extract item IDs and append to the result list
                item_ids_in_bag = [item.item_id for item in items_in_bag]
                all_item_ids.extend(item_ids_in_bag)

            except Exception as e:
                Py4GW.Console.Log("GetItemArray", f"Error retrieving items from {bag_enum.name}: {str(e)}", Py4GW.Console.MessageType.Error)
    
        return all_item_ids

    @staticmethod
    def GetAllBags():
        """
        Returns a list of all Bag enums that are valid for use with GetItemArray().
        Skips NoBag automatically.
        """
        valid_bags = []

        for bag in Bag:
            if bag == Bag.NoBag:
                continue
            items = ItemArray.GetItemArray([bag])
            if items:
                valid_bags.append(bag)

        return valid_bags
    
    @staticmethod
    def GetBag(bag: int):
        """
        Returns a Bag instance for the given bag enum.
        Returns None if the bag is invalid or has no items.
        """
        items = ItemArray.GetItemArray([bag])
        if not items:
            return None

        try:
            bag_instance = PyInventory.Bag(bag, str(bag))
            bag_instance.GetContext()
            return bag_instance
        except Exception:
            return None

    class Filter:
        @staticmethod
        def ByAttribute(item_array, attribute, condition_func=None, negate=False):
            """
            Filters items by an attribute from the Item class, using map and filter.
            """
            def attribute_filter(item_id):
                # Use map to dynamically fetch the attribute value for each item
                if hasattr(Item, attribute):
                    attr_value = getattr(Item, attribute)(item_id)

                    # Apply condition_func if provided, otherwise check the boolean value
                    result = condition_func(attr_value) if condition_func else bool(attr_value)

                    # Negate the result if required
                    return not result if negate else result

                # If attribute does not exist, exclude by default
                return False if not negate else True

            # Use filter to apply the attribute_filter to the item array
            return list(filter(attribute_filter, item_array))


        @staticmethod
        def ByCondition(item_array, filter_func):
            """
            Filters the item array using Python's built-in filter function.
            non_white_items = Filter.ByCondition(
                item_array,
                lambda item_id: not Item.Rarity.IsWhite(item_id)
            )

            """
            # Apply the filter function directly using Python's filter
            return list(filter(filter_func, item_array))



    class Manipulation:
        @staticmethod
        def Merge(array1, array2):
            """
            Merges two agent arrays, removing duplicates (union).

            Args:
                array1 (list[int]): First agent array.
                array2 (list[int]): Second agent array.

            Returns:
                list[int]: A merged array with unique agent IDs.

            Example:
                merged_agents = Filters.MergeAgentArrays(array1, array2)
            """
            return list(set(array1).union(set(array2)))

        @staticmethod
        def Subtract(array1, array2):
            """
            Returns agents that are in the first array but not in the second (difference).

            Args:
                array1 (list[int]): First agent array.
                array2 (list[int]): Second agent array.

            Returns:
                list[int]: Agents present in array1 but not in array2.

            Example:
                difference_agents = Filters.SubtractAgentArrays(array1, array2)
            """
            return list(set(array1) - set(array2))

        @staticmethod
        def Intersect(array1, array2):
            """
            Returns agents that are present in both arrays (intersection).

            Args:
                array1 (list[int]): First agent array.
                array2 (list[int]): Second agent array.

            Returns:
                list[int]: Agents present in both arrays.

            Example:
                intersected_agents = Filters.IntersectAgentArrays(array1, array2)
            """
            return list(set(array1).intersection(set(array2)))
            
    class Sort:
        @staticmethod
        def SortByAttribute(item_array, attribute, reverse=False):
            """
            Sorts items by an attribute from the Item class, with support for ascending or descending order.
            sorted_by_value_desc = Sort.SortByAttribute(item_array, 'Properties.GetValue', reverse=True)
            """
            # Use map to extract attribute values for sorting
            def get_attribute_value(item_id):
                if hasattr(Item, attribute):
                    return getattr(Item, attribute)(item_id)
                raise ValueError(f"Invalid attribute: {attribute}")

            # Sort using the extracted attribute values
            return sorted(item_array, key=get_attribute_value, reverse=reverse)

        @staticmethod
        def SortByCondition(item_array, condition_func, reverse=False):
            """
            Sorts items based on a custom condition function.
            sorted_by_value_desc = Sort.SortByCondition(
                item_array,
                lambda item_id: Item.Properties.GetValue(item_id),
                reverse=True
            )
            """
            # Sort directly using the condition function
            return sorted(item_array, key=condition_func, reverse=reverse)

