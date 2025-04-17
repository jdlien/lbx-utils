from dataclasses import dataclass, field
from typing import Union, List, Optional, Any

@dataclass
class GroupObject:
    """Object representing a group of elements with flex layout."""
    x: Union[str, float] = "0pt"
    y: Union[str, float] = "0pt"
    width: Union[str, float] = "auto"
    height: Union[str, float] = "auto"
    direction: str = "row"
    justify: str = "start"
    align: str = "start"
    gap: Union[str, float, int] = 0
    padding: Union[str, float, int] = 0
    wrap: bool = False
    background_color: str = "#FFFFFF"
    border_style: Optional[str] = None
    objects: List[Any] = field(default_factory=list)
    id: Optional[str] = None
    name: Optional[str] = None

    # Store original position from YAML if explicitly set
    _original_x: Optional[Union[str, float]] = None
    _original_y: Optional[Union[str, float]] = None
    _positioned: bool = False

@dataclass
class ContainerObject:
    """
    Object representing a container that holds elements with flex layout
    but doesn't create a visible group element in XML.
    """
    x: Union[str, float] = "0pt"
    y: Union[str, float] = "0pt"
    width: Optional[Union[str, float]] = None
    height: Optional[Union[str, float]] = None
    direction: str = "row"
    justify: str = "start"
    align: str = "start"
    gap: Union[str, float, int] = 0
    padding: Union[str, float, int] = 0
    wrap: bool = False
    objects: List[Any] = field(default_factory=list)
    id: Optional[str] = None
    name: Optional[str] = None

    # Store original position from YAML if explicitly set
    _original_x: Optional[Union[str, float]] = None
    _original_y: Optional[Union[str, float]] = None
    _positioned: bool = False