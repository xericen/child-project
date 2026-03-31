import peewee as pw

base = wiz.model("portal/season/orm").base("login_db")

class Model(base):
    class Meta:
        db_table = 'servers'
        table_comment = '어린이집 서버 정보'

    id = pw.AutoField()
    server_code = pw.CharField(max_length=8, unique=True, null=False)          # 서버 회원번호 (고유 코드)
    name = pw.CharField(max_length=100, null=False)                            # 어린이집명
    director_name = pw.CharField(max_length=100, null=False)                   # 원장 이름
    director_id = pw.IntegerField(null=False)                                  # 원장 사용자 ID (users FK)
    created_at = pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP')])
