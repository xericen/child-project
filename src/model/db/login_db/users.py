import peewee as pw

base = wiz.model("portal/season/orm").base("login_db")

class Model(base):
    class Meta:
        db_table = 'users'
        table_comment = '서비스 전체 사용자'

    id = pw.AutoField()                                                                            # 정수 자동증가 (0부터)
    email = pw.CharField(max_length=255, unique=True, null=False)                                 # 이메일 (고유)
    password = pw.TextField(null=False)                                                            # 비밀번호
    nickname = pw.CharField(max_length=100, null=False)                                           # 닉네임
    child_name = pw.CharField(max_length=100, null=True)                                           # 자녀 이름 (부모만)
    role = pw.CharField(
        max_length=10,
        null=False,
        constraints=[pw.SQL("DEFAULT 'parent'")]
    )                                                                                              # 역할 (director/teacher/parent)
    created_at = pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP')])               # 생성일시
    birth_date = pw.DateField(null=True)                                                           # 생년월일 (부모만 입력)
    verified = pw.BooleanField(default=False, constraints=[pw.SQL('DEFAULT 0')])                   # 이메일 인증 여부
    class_name = pw.CharField(max_length=50, null=True)                                            # 반 이름 (교사만)
    approved = pw.BooleanField(default=False, constraints=[pw.SQL('DEFAULT 0')])                   # 가입 승인 여부
    phone = pw.CharField(max_length=20, null=True)                                                 # 전화번호
    app_installed = pw.BooleanField(default=False, constraints=[pw.SQL('DEFAULT 0')])              # 앱 설치 여부
