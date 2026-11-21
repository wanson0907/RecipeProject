import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from recipes.models import Recipe


class Command(BaseCommand):
    help = "CSV 파일 경로를 받아 대량의 레시피 데이터를 일괄 등록합니다."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="등록할 CSV 파일 경로")

    def handle(self, *args, **options):
        csv_path = options["csv_path"]

        if not os.path.exists(csv_path):
            raise CommandError(f"파일을 찾을 수 없습니다: {csv_path}")

        User = get_user_model()
        admin_user, _ = User.objects.get_or_create(
            username="chef_admin",
            defaults={"is_staff": True, "is_superuser": True}
        )

        created_count = 0
        # UTF-8 또는 CP949(엑셀 한글) 인코딩 대응
        encodings = ["utf-8-sig", "utf-8", "cp949"]
        success = False

        for enc in encodings:
            try:
                with open(csv_path, mode="r", encoding=enc) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        title = row.get("title", "").strip()
                        if not title:
                            continue

                        description = row.get("description", "").strip()
                        ingredients = row.get("ingredients", "").replace("\\n", "\n").strip()
                        steps = row.get("steps", "").replace("\\n", "\n").strip()

                        Recipe.objects.update_or_create(
                            title=title,
                            defaults={
                                "author": admin_user,
                                "description": description,
                                "ingredients": ingredients,
                                "steps": steps,
                            }
                        )
                        created_count += 1
                success = True
                break
            except (UnicodeDecodeError, KeyError):
                continue

        if not success:
            raise CommandError("CSV 파일을 읽는 중 인코딩 또는 열 이름(title, description, ingredients, steps) 오류가 발생했습니다.")

        self.stdout.write(
            self.style.SUCCESS(f"✅ CSV 파일로부터 {created_count}개의 레시피를 성공적으로 등록했습니다! (총 레시피: {Recipe.objects.count()}개)")
        )
