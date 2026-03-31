import peewee as pw

base = wiz.model("portal/season/orm").base("childcheck")

class Model(base):
    class Meta:
        db_table = 'allergy_categories'
        table_comment = '알레르기 카테고리 (8종 분류 + 주의/대체식품)'

    id               = pw.AutoField()
    category_name    = pw.CharField(max_length=32, null=False)
    allergy_numbers  = pw.TextField(null=False)
    caution_foods    = pw.TextField(null=False)
    substitute_foods = pw.TextField(null=False)
    description      = pw.TextField(null=True)
    created_at       = pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP')])
