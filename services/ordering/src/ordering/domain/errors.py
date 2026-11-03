class DomainError(Exception):
    pass


class InvalidQuantity(DomainError):
    pass


class ItemNotInCart(DomainError):
    pass


class EmptyCart(DomainError):
    pass


class InvalidOrderTransition(DomainError):
    pass
