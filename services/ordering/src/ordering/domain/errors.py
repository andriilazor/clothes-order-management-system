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


class CartNotFound(DomainError):
    pass


class InvalidSku(DomainError):
    pass


class QuantityLimitExceeded(DomainError):
    pass
