from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('locations', '0002_irreversible')]

    operations = [migrations.RunSQL('SELECT 1', reverse_sql='SELECT 1')]
