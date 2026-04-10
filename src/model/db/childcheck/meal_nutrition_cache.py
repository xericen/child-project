import peewee as pw

base = wiz.model("portal/season/orm").base("childcheck")

class Model(base):
    class Meta:
        db_table = 'meal_nutrition_cache'
        table_comment = '식단 영양분석 캐시 (식약처 API 결과 저장)'

    id            = pw.AutoField()
    server_id     = pw.IntegerField(null=False, index=True)
    meal_date     = pw.DateField(null=False, index=True)
    age_group     = pw.CharField(max_length=10, null=False)                     # '1~2세' or '3~5세'
    total_calories = pw.FloatField(default=0)
    total_protein  = pw.FloatField(default=0)
    total_fat      = pw.FloatField(default=0)
    total_carbs    = pw.FloatField(default=0)
    total_calcium  = pw.FloatField(default=0)
    total_iron     = pw.FloatField(default=0)
    stage1_json   = pw.TextField(null=True)                                     # stage1 전체 결과 JSON
    analyzed_at   = pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP')])
