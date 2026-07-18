from ctypes import Structure, c_uint
from .Globals import (
    SHMEM_MAX_NUMBER_OF_ATTRIBUTES,
)

#region Attributes   
class AttributeUnitStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Id", c_uint),
        ("Value", c_uint),
        ("BaseValue", c_uint),
    ]
    
    # Type hints for IntelliSense
    Id: int
    Value: int
    BaseValue: int
    
    def reset(self) -> None:
        """Reset all fields to zero."""
        self.Id = 0
        self.Value = 0
        self.BaseValue = 0
        
class AttributesStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Attributes", AttributeUnitStruct * SHMEM_MAX_NUMBER_OF_ATTRIBUTES),
    ]
    
    # Type hints for IntelliSense
    Attributes: list[AttributeUnitStruct]
    
    def reset(self) -> None:
        """Reset all fields to zero."""
        for i in range(SHMEM_MAX_NUMBER_OF_ATTRIBUTES):
            self.Attributes[i].reset()
            
    def from_context(self, agent_id: int) -> None:
        from ...Agent import Agent
        attributes = Agent.GetAttributes(agent_id)
        for attribute_id in range(SHMEM_MAX_NUMBER_OF_ATTRIBUTES):
            attribute = next((attr for attr in attributes if int(attr.attribute_id) == attribute_id), None)
            self.Attributes[attribute_id].Id = attribute_id if attribute else 0
            self.Attributes[attribute_id].Value = attribute.level if attribute else 0
            self.Attributes[attribute_id].BaseValue = attribute.level_base if attribute else 0
    

            
  