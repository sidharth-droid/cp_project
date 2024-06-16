from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import pandas as pd
from .models import Complains  

file_path = 'D:\Documents\sidharth\cp_cell\Exports.xlsx'

def export_to_excel():
  
    data = Complains.objects.all().values()  

    df = pd.DataFrame(data)

    df.to_excel(file_path, index=False, engine='openpyxl')
    print(f"Data exported to {file_path}")

@receiver(post_save, sender=Complains)
def model_saved(sender, instance, **kwargs):
    print("Model instance saved")
    export_to_excel()

@receiver(post_delete, sender=Complains)
def model_deleted(sender, instance, **kwargs):
    print("Model instance deleted")
    export_to_excel()
