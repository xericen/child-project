import peewee as pw

base = wiz.model("portal/season/orm").base("childcheck")

class Model(base):
    class Meta:
        db_table = 'nutrition_mapping'
        table_comment = '메뉴명 → 식약처 식품 영양소 매핑 캐시'

    id            = pw.AutoField()
    menu_name     = pw.CharField(max_length=200, null=False, unique=True, index=True)  # 정제된 메뉴명
    food_code     = pw.CharField(max_length=50, null=True)                              # 식약처 식품코드
    food_name     = pw.CharField(max_length=200, null=True)                             # 식약처 매칭된 식품명
    source        = pw.CharField(max_length=20, null=False, default='api')              # api, ai_estimate, basic, menugen
    nutrients     = pw.TextField(null=True)                                             # 영양소 JSON
    created_at    = pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP')])
    updated_at    = pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')])
