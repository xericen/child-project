import peewee as pw

base = wiz.model("portal/season/orm").base("childcheck")

class Model(base):
    class Meta:
        db_table = 'nutrition_foods'
        table_comment = '국가표준식품성분 로컬 DB (55만건)'

    id            = pw.AutoField()
    food_code     = pw.CharField(max_length=50, null=True, index=True)
    food_name     = pw.CharField(max_length=200, null=False, index=True)
    category      = pw.CharField(max_length=100, null=True)
    serving_size  = pw.CharField(max_length=50, null=True, default='100g')
    calories      = pw.FloatField(default=0)
    protein       = pw.FloatField(default=0)
    fat           = pw.FloatField(default=0)
    carbohydrate  = pw.FloatField(default=0)
    sugar         = pw.FloatField(default=0)
    fiber         = pw.FloatField(default=0)
    calcium       = pw.FloatField(default=0)
    iron          = pw.FloatField(default=0)
    phosphorus    = pw.FloatField(default=0)
    potassium     = pw.FloatField(default=0)
    sodium        = pw.FloatField(default=0)
    vitamin_a     = pw.FloatField(default=0)
    vitamin_c     = pw.FloatField(default=0)
    source        = pw.CharField(max_length=50, null=True, default='api_import')
    origin        = pw.CharField(max_length=200, null=True)
    created_at    = pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP')])
