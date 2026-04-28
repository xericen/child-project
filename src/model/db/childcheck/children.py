import peewee as pw

base = wiz.model("portal/season/orm").base("childcheck")

class Model(base):
    class Meta:
        db_table = 'children'
        table_comment = '자녀 기본 정보'

    id        = pw.AutoField()                                                                              # 정수 자동증가
    user_id   = pw.IntegerField(null=False)                                                                  # 부모 사용자 ID (users.id 참조)
    name      = pw.CharField(max_length=50, null=False)                                                     # 자녀 이름
    birthdate = pw.DateField(null=False)                                                                    # 생년월일
    twin_type = pw.CharField(
        max_length=20,
        null=False,
        constraints=[pw.SQL("DEFAULT '없음'")]
    )                                                                                                       # 쌍둥이 구분 (없음/쌍둥이A·B/세쌍둥이A·B·C)
    allergy_checked = pw.BooleanField(default=False, constraints=[pw.SQL('DEFAULT 0')])                     # 알레르기 체크 완료 여부
    class_name = pw.CharField(max_length=50, null=True, default=None)                                        # 소속 반 이름 (강아지반, 토끼반 등)
    profile_photo = pw.CharField(max_length=255, null=True, default=None)                                   # 프로필 사진 파일명
    created_at = pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP')])                        # 생성일시
    updated_at = pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')])  # 수정일시