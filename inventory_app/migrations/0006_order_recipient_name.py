from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory_app', '0005_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='recipient_name',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='اسم المستلم'),
        ),
    ]


