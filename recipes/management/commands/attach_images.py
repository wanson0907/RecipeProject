from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from recipes.models import Recipe

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".jfif", ".gif"}


class Command(BaseCommand):
    help = (
        "recipe_images 폴더의 사진을 레시피에 한꺼번에 연결합니다. "
        "파일 이름이 '레시피 번호'(예: 1.jpg) 또는 '레시피 제목'(예: 돼지고기 김치찌개.jpg)과 같으면 자동으로 짝지어 줍니다."
    )

    def add_arguments(self, parser):
        parser.add_argument("--dir", default="recipe_images", help="사진이 들어있는 폴더 (기본: recipe_images)")
        parser.add_argument("--overwrite", action="store_true", help="이미 사진이 있는 레시피도 덮어씁니다.")
        parser.add_argument("--list", action="store_true", help="레시피 번호/제목과 사진 유무만 보여줍니다.")

    def handle(self, *args, **options):
        if options["list"]:
            for recipe in Recipe.objects.order_by("id"):
                mark = "사진 있음" if recipe.image else "사진 없음"
                self.stdout.write(f"{recipe.id:>3}  [{mark}]  {recipe.title}")
            return

        folder = Path(options["dir"])
        if not folder.is_absolute():
            folder = Path(settings.BASE_DIR) / folder
        if not folder.is_dir():
            self.stdout.write(self.style.ERROR(f"폴더가 없어요: {folder}\n이 폴더를 만들고 사진을 넣은 뒤 다시 실행하세요."))
            return

        files = {f.stem: f for f in folder.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS}
        if not files:
            self.stdout.write(self.style.WARNING("폴더 안에 사진 파일(jpg, png, webp 등)이 없어요."))
            return

        attached, skipped = 0, 0
        used = set()
        for recipe in Recipe.objects.order_by("id"):
            key = str(recipe.id) if str(recipe.id) in files else recipe.title
            image_file = files.get(key)
            if image_file is None:
                continue
            if recipe.image and not options["overwrite"]:
                skipped += 1
                continue
            with image_file.open("rb") as fh:
                recipe.image.save(image_file.name, File(fh), save=True)
            used.add(image_file.stem)
            attached += 1
            self.stdout.write(f"연결: [{recipe.id}] {recipe.title}  <-  {image_file.name}")

        unmatched = sorted(set(files) - used - {str(r.id) for r in Recipe.objects.all() if r.image and not options['overwrite']})
        self.stdout.write(self.style.SUCCESS(f"완료: {attached}개 연결, {skipped}개는 이미 사진이 있어 건너뜀"))
        if unmatched:
            self.stdout.write(self.style.WARNING("짝을 못 찾은 파일: " + ", ".join(unmatched)))
