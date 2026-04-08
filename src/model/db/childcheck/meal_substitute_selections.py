import peewee as pw

base = wiz.model("portal/season/orm").base("childcheck")

class Model(base):
    class Meta:
        db_table = 'meal_substitute_selections'
        table_comment = '교사/원장 대체식 선택 이력'

    id              = pw.AutoField()
    meal_id         = pw.IntegerField(null=False, index=True)                   # 식단(meals) FK
    original_item   = pw.CharField(max_length=100, null=False)                  # 원본 메뉴 (예: 가자미조림)
    substitute_item = pw.CharField(max_length=100, null=False)                  # 대체 메뉴 (예: 가자미구이)
    is_selected     = pw.BooleanField(default=False, constraints=[pw.SQL('DEFAULT 0')])  # 대체식 선택여부
    selected_by     = pw.IntegerField(null=True)                                # 선택한 사용자 ID
    created_at      = pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP')])
    updated_at      = pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')])
