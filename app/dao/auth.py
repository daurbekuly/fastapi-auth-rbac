from app.dao.base import BaseDAO
from app.models.auth import Role, BusinessElement, AccessRule

class RoleDAO(BaseDAO): model = Role
class ElementDAO(BaseDAO): model = BusinessElement
class RuleDAO(BaseDAO): model = AccessRule