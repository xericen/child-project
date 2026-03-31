import random
import string

class Server:
    def __init__(self, struct):
        self.struct = struct

    def _generate_code(self):
        """중복 없는 8자리 영숫자 서버 코드 생성"""
        Servers = wiz.model("db/login_db/servers")
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            existing = Servers.select().where(Servers.server_code == code).first()
            if not existing:
                return code

    def create(self, name, director_name, director_id):
        """어린이집 서버 생성 및 서버 코드 발급"""
        Servers = wiz.model("db/login_db/servers")
        ServerMembers = wiz.model("db/login_db/server_members")

        server_code = self._generate_code()

        server = Servers.create(
            server_code=server_code,
            name=name,
            director_name=director_name,
            director_id=director_id
        )

        ServerMembers.create(
            server_id=server.id,
            user_id=director_id,
            role='director'
        )

        return {
            'id': server.id,
            'server_code': server_code,
            'name': name,
            'director_name': director_name
        }

    def find_by_code(self, server_code):
        """서버 코드로 서버 조회"""
        Servers = wiz.model("db/login_db/servers")
        server = Servers.select().where(Servers.server_code == server_code).first()
        if not server:
            return None
        return {
            'id': server.id,
            'server_code': server.server_code,
            'name': server.name,
            'director_name': server.director_name
        }

    def join(self, server_id, user_id, role):
        """서버에 멤버 참여"""
        ServerMembers = wiz.model("db/login_db/server_members")

        existing = ServerMembers.select().where(
            (ServerMembers.server_id == server_id) &
            (ServerMembers.user_id == user_id)
        ).first()
        if existing:
            raise Exception("이미 참여한 서버입니다.")

        ServerMembers.create(
            server_id=server_id,
            user_id=user_id,
            role=role
        )

Model = Server
