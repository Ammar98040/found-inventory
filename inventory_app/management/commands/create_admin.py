"""
أمر Django لإنشاء مسؤول (Admin) في النظام
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventory_app.models import UserProfile


class Command(BaseCommand):
    help = 'إنشاء حساب مسؤول جديد'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='اسم المستخدم')
        parser.add_argument('--password', type=str, help='كلمة المرور')
        parser.add_argument('--email', type=str, help='البريد الإلكتروني', default='')

    def handle(self, *args, **options):
        username = options.get('username')
        password = options.get('password')
        email = options.get('email', '')

        if not username:
            username = input('اسم المستخدم: ')
        
        if not password:
            password = input('كلمة المرور: ')

        # التحقق من وجود المستخدم
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'المستخدم {username} موجود بالفعل!'))
            return

        # إنشاء المستخدم
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            is_superuser=True,
            is_staff=True
        )

        # إنشاء UserProfile
        UserProfile.objects.create(
            user=user,
            user_type='admin',
            is_active=True
        )

        self.stdout.write(self.style.SUCCESS(f'✅ تم إنشاء المسؤول {username} بنجاح!'))

