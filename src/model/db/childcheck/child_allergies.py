import peewee as pw

base = wiz.model("portal/season/orm").base("childcheck")

class Model(base):
    class Meta:
        db_table = 'child_allergies'
        table_comment = '자녀 알레르기 정보'

    id               = pw.AutoField()                                                                              # 정수 자동증가
    child_id         = pw.IntegerField(null=False)                                                                 # children.id 참조
    allergy_type     = pw.CharField(
                           max_length=10,
                           null=False
                       )                                                                                           # 알레르기 종류 (계란/우유/땅콩/기타)
    other_detail     = pw.CharField(max_length=100, null=True)                                                     # 기타 알레르기 상세 내용
    is_severe        = pw.BooleanField(default=False, constraints=[pw.SQL('DEFAULT 0')])                           # 중증 여부
    needs_substitute = pw.BooleanField(default=False, constraints=[pw.SQL('DEFAULT 0')])                           # 대체식 필요 여부
    created_at       = pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP')])                         # 생성일시
    updated_at       = pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')])  # 수정일시