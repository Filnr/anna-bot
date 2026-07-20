class GoalAlreadyExistsError(Exception):
    pass

class DatabaseUnavailableError(Exception):
    pass

class GoalDoesNotExistError(Exception):
    pass

class GoalCantBeDeletedError(Exception):
    pass

class IncomeAlreadyExistsError(Exception):
    pass

class IncomeDoesNotExistError(Exception):
    pass

class IncomeCantBeDeletedError(Exception):
    pass

class ExpenseAlreadyExistsError(Exception):
    pass

class ExpenseDoesNotExistError(Exception):
    pass

class ExpenseCantBeDeletedError(Exception):
    pass

class ExpenseCreationError(Exception):
    pass