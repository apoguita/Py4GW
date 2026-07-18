# PyTrading.pyi

class PyTrading:
    @staticmethod
    def OpenTradeWindow(agent_id: int) -> None:
        """Open a trade window with a specific agent."""
        ...

    @staticmethod
    def AcceptTrade() -> bool:
        """Accept the current trade."""
        ...

    @staticmethod
    def CancelTrade() -> bool:
        """Cancel the current trade."""
        ...

    @staticmethod
    def ChangeOffer() -> bool:
        """Change the current trade offer."""
        ...

    @staticmethod
    def SubmitOffer(gold: int) -> bool:
        """Submit the current trade offer with specified gold amount."""
        ...

    @staticmethod
    def RemoveItem(slot: int) -> bool:
        """Remove an item from the trade offer by slot index."""
        ...

    @staticmethod
    def GetItemOffered(item_id: int) -> object | None:
        """Get details of an item offered in the trade by item ID."""
        ...

    @staticmethod
    def IsItemOffered(item_id: int) -> bool:
        """Check if an item is offered in the trade by item ID."""
        ...

    @staticmethod
    def OfferItem(item_id: int, quantity: int = 0) -> bool:
        """Offer an item for trade by item ID and optional quantity."""
        ...

    @staticmethod
    def IsTradeOffered() -> bool:
        """Check if a trade is currently offered."""
        ...

    @staticmethod
    def IsTradeInitiated() -> bool:
        """Check if a trade has been initiated."""
        ...

    @staticmethod
    def IsTradeAccepted() -> bool:
        """Check if a trade has been accepted."""
        ...
