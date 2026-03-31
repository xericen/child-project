import peewee as pw

base = wiz.model("portal/season/orm").base("childcheck")

class Model(base):
    class Meta:
        db_table = 'meals'
        table_comment = '식단 정보'

    id           = pw.AutoField()
    server_id    = pw.IntegerField(null=False, default=0, index=True)
    meal_type    = pw.CharField(max_length=20, null=False)
    meal_date    = pw.DateField(null=False)
    content      = pw.TextField(null=True)
    allergy_numbers = pw.TextField(null=True)                                   # 알레르기 번호 목록 (JSON 배열, 예: [1,5,6])
    dish_allergies  = pw.TextField(null=True)                                   # 음식별 알레르기 매핑 (JSON, 예: {"미트볼조림":[1,5,6]})
    theme        = pw.CharField(max_length=50, null=True)                       # 식단 테마 (예: 차차밥상, 자연밥상 등)
    kcal         = pw.IntegerField(null=True)                                   # 열량(kcal) - 일일 총 열량
    protein      = pw.FloatField(null=True)                                     # 단백질(g)
    photo_path   = pw.CharField(max_length=500, null=True)
    created_by   = pw.IntegerField(null=False)
    created_at   = pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP')])
    updated_at   = pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')])
