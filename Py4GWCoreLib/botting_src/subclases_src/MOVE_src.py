#region STATES
from typing import TYPE_CHECKING, List, Tuple, Optional, Callable

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass

#region MOVE
class _MOVE:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers

    def XY(self, x:float, y:float, step_name: str=""):
        """Uses autopath to move to (x, y)"""
        if step_name == "":
            step_name = f"MoveTo_{self._config.get_counter('MOVE_TO')}"

        self._helpers.Move.get_path_to(x, y)
        self._helpers.Move.follow_path()

    def XYAndDialog(self, x: float, y: float, dialog_id: int, step_name: str="") -> None:
        self.XY(x, y, step_name=step_name)
        self.parent.Dialogs.AtXY(x, y, dialog_id, step_name=step_name+"_DIALOGAT")

    def XYAndInteractNPC(self, x: float, y: float, step_name: str="") -> None:
        self.XY(x, y, step_name=step_name)
        self.parent.Interact.WithNpcAtXY(x, y, step_name=step_name+"_INTERACT")

    def XYAndInteractGadget(self, x: float, y: float, step_name: str="") -> None:
        self.XY(x, y, step_name=step_name)
        self.parent.Interact.WithGadgetAtXY(x, y, step_name=step_name+"_INTERACT")

    def XYAndInteractItem(self, x: float, y: float, step_name: str="") -> None:
        self.XY(x, y, step_name=step_name)
        self.parent.Interact.WithItemAtXY(x, y, step_name=step_name+"_INTERACT")

    def XYAndExitMap(self, x: float, y: float, target_map_id: int = 0, target_map_name: str = "", step_name: str="") -> None:
        self.XY(x, y, step_name=step_name)
        self.parent.Wait.ForMapLoad(target_map_id=target_map_id, target_map_name=target_map_name)


    def FollowPath(self, path: List[Tuple[float, float]], step_name: str="") -> None:
        """ follow a predefined path of (x, y) points.
        """
        if step_name == "":
            step_name = f"FollowPath_{self._config.get_counter('FOLLOW_PATH')}"

        self._helpers.Move.set_path_to(path)
        self._helpers.Move.follow_path()

    def FollowPathAndDialog(self, path: List[Tuple[float, float]], dialog_id: int, step_name: str="") -> None:
        self.FollowPath(path, step_name=step_name)
        last_point = path[-1]
        self.parent.Dialogs.AtXY(*last_point, dialog_id, step_name=step_name+"_DIALOGAT")

    def FollowPathAndExitMap(self, path: List[Tuple[float, float]], target_map_id: int = 0, target_map_name: str = "", step_name: str="") -> None:
        self.FollowPath(path, step_name=step_name)
        self.parent.Wait.ForMapLoad(target_map_id=target_map_id, target_map_name=target_map_name)

    def FollowAutoPath(self, points: List[Tuple[float, float]], step_name: str = "") -> None:
        """
        For each (x, y) target point, compute an autopath and follow it.
        Input format matches FollowPath, but each point is autpathed independently.
        """
        if step_name == "":
            step_name = f"FollowAutoPath_{self._config.get_counter('FOLLOW_AUTOPATH')}"

        for x, y in points:
            self._helpers.Move.get_path_to(x, y)   # autopath to this target
            self._helpers.Move.follow_path()       # then execute the path

    def FollowModel(self, model_id: int, follow_range: float, exit_condition: Optional[Callable[[], bool]] = lambda:False) -> None:
        self._helpers.Move.follow_model(model_id, follow_range, exit_condition)
        
    def ToModel(self, model_id: int, step_name: str = "") -> None:
        if step_name == "":
            step_name = f"ToModel_{self._config.get_counter('TO_MODEL')}"

        self._helpers.Move.to_model(model_id)
