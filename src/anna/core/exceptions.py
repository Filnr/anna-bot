class GoalAlreadyExistsError(Exception):
    pass

class DatabaseUnavailableError(Exception):
    pass

class GoalDoesNotExistError(Exception):
    pass

class GoalCantBeDeletedError(Exception):
    pass