import peewee as pw

base = wiz.model("portal/season/orm").base("login_db")

class Model(base):
    class Meta:
        db_table = 'server_members'
        table_comment = '서버 참여 멤버'

    id = pw.AutoField()
    server_id = pw.IntegerField(null=False, index=True)                        # 서버 ID (servers FK)
    user_id = pw.IntegerField(null=False, index=True)                          # 사용자 ID (users FK)
    role = pw.CharField(max_length=10, null=False)                             # 역할 (director/teacher/parent)
    joined_at = pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP')])
