import datetime

class Struct:
    def __init__(self):
        self.admin = False
        self.userId = None
        self._Server = wiz.model("struct/server")

    def getUserId(self):
        if self.userId is not None:
            return self.userId
        return wiz.session.user_id()

    def getUserEmail(self):
        user_id = self.getUserId()
        userdb = self.db("users")
        user = userdb.get(fields="email", id=user_id)
        if user is not None:
            return user['email']
        return None

    def isAdmin(self):
        if self.admin:
            return True
        role = wiz.session.get("membership")
        return role == 'admin'

    def setAdmin(self, isAdmin=True):
        self.admin = isAdmin
        return self

    def setUserid(self, user_id):
        self.userId = user_id
        return self
    
    def db(self, name):
        orm = wiz.model("portal/season/orm")
        return orm.use(name)

    @property
    def server(self):
        return self._Server(self)

Model = Struct()